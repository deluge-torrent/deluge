#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""Simple, bounded-memory file copying for moving storage between volumes.

When libtorrent moves storage across volumes (e.g. to a network share) it falls
back to its own copy routine which, for sparse files (how libtorrent allocates
downloads on Windows), copies in synchronous 16 KiB chunks on its disk thread.
Over SMB that is extremely slow and gives no progress feedback.

Here files are copied with the classic buffered block copy, the same read/write
loop as ``shutil.copyfileobj`` and ``cp``, through a single reusable 1 MiB
buffer, so memory use stays constant whatever the file size and it behaves the
same on every OS for local disks and network shares. Unlike ``shutil.copy2`` it
reports progress and can be cancelled. Data goes to a temporary file that is
fsynced, size-checked and only then atomically renamed into place, so an
interrupted copy never leaves a truncated file that looks complete. Permission
bits and timestamps are preserved where the filesystem allows.
"""

import logging
import os
import shutil
import time

log = logging.getLogger(__name__)

BLOCK_SIZE = 1024 * 1024
RETRIES = 2
RETRY_DELAY = 5
TEMP_SUFFIX = '.deluge-copy'


class CopyCancelled(Exception):
    """Raised when a copy is cancelled."""


class CopyProgress:
    """Bytes copied out of a known total, readable from another thread."""

    def __init__(self, total=0):
        self.total = total
        self.done = 0
        self.cancelled = False

    @property
    def percent(self):
        if not self.total:
            return 0.0
        return min(100.0, self.done / self.total * 100)

    def cancel(self):
        self.cancelled = True


def _copy_once(src, tmp, progress, block_size):
    buf = bytearray(block_size)
    view = memoryview(buf)
    with open(src, 'rb', buffering=0) as fsrc, open(tmp, 'wb', buffering=0) as fdst:
        while True:
            if progress.cancelled:
                raise CopyCancelled()
            nread = fsrc.readinto(buf)
            if not nread:
                break
            fdst.write(view[:nread])
            progress.done += nread
        os.fsync(fdst.fileno())


def copy_file(src, dst, progress=None, block_size=BLOCK_SIZE, retries=RETRIES):
    """Copy a single file from src to dst. An existing dst is never replaced.

    Raises:
        FileExistsError: If dst exists when the copy is ready to be put in place
            (e.g. two names differing only in case on a case-insensitive share).
        OSError: If the copy failed after all retries.
        CopyCancelled: If cancelled via progress.
    """
    if progress is None:
        progress = CopyProgress()
    stat = os.stat(src)
    tmp = dst + TEMP_SUFFIX
    os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)

    start = progress.done
    try:
        for attempt in range(retries + 1):
            try:
                _copy_once(src, tmp, progress, block_size)
                break
            except OSError as ex:
                if attempt == retries:
                    raise
                log.warning('Error copying %s, retrying: %s', src, ex)
                progress.done = start
                time.sleep(RETRY_DELAY)

        copied_size = os.stat(tmp).st_size
        if copied_size != stat.st_size:
            raise OSError(
                f'Size mismatch copying {src}: expected {stat.st_size}, got {copied_size}'
            )
        try:
            os.utime(tmp, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            # On Windows the mode only carries the read-only attribute, which
            # would stop libtorrent writing to the file later.
            if os.name != 'nt':
                shutil.copymode(src, tmp)
        except OSError as ex:
            log.debug('Unable to copy file metadata to %s: %s', tmp, ex)
        if os.path.lexists(dst):
            raise FileExistsError(f'Destination already exists: {dst}')
        os.replace(tmp, dst)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def copy_files(pairs, progress=None, created=None, **kwargs):
    """Copy a list of (src, dst) pairs, sharing one progress across them.

    Args:
        pairs (list of tuple): (source path, destination path) pairs.
        progress (CopyProgress, optional): Its total is set to the sum of sizes.
        created (list, optional): Each destination is appended once in place,
            so a caller can roll back after a failure.
    """
    if progress is None:
        progress = CopyProgress()
    progress.total = sum(os.stat(src).st_size for src, _ in pairs)
    for src, dst in pairs:
        copy_file(src, dst, progress=progress, **kwargs)
        if created is not None:
            created.append(dst)
    return progress


def remove_files(paths):
    """Remove files, ignoring any that cannot be removed."""
    for path in paths:
        try:
            os.remove(path)
        except OSError as ex:
            log.warning('Unable to remove %s: %s', path, ex)


def is_same_device(path_a, path_b):
    """Whether two existing paths reside on the same volume."""
    path_a = os.path.abspath(path_a)
    path_b = os.path.abspath(path_b)
    if os.path.splitdrive(path_a)[0].lower() != os.path.splitdrive(path_b)[0].lower():
        return False
    try:
        return os.stat(path_a).st_dev == os.stat(path_b).st_dev
    except OSError:
        return False
