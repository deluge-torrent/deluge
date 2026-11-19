#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import os

import pytest

from deluge.core import filecopy


def write_file(path, size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(os.urandom(size))
    os.utime(path, (1_000_000_000, 1_000_000_000))


def read(path):
    with open(path, 'rb') as f:
        return f.read()


def test_copy_file_multiple_blocks(tmp_path):
    src = str(tmp_path / 'src' / 'file.bin')
    dst = str(tmp_path / 'dst' / 'sub' / 'file.bin')
    write_file(src, 1000)
    progress = filecopy.CopyProgress(1000)

    filecopy.copy_file(src, dst, progress=progress, block_size=64)

    assert read(dst) == read(src)
    assert os.stat(dst).st_mtime == 1_000_000_000
    assert progress.done == 1000
    assert progress.percent == 100.0
    assert not os.path.exists(dst + filecopy.TEMP_SUFFIX)


def test_copy_empty_file(tmp_path):
    src = str(tmp_path / 'empty')
    dst = str(tmp_path / 'out' / 'empty')
    write_file(src, 0)
    filecopy.copy_file(src, dst)
    assert read(dst) == b''


def test_copy_files_progress_total(tmp_path):
    pairs = []
    for i, size in enumerate((10, 200, 3000)):
        src = str(tmp_path / 'src' / f'{i}.bin')
        write_file(src, size)
        pairs.append((src, str(tmp_path / 'dst' / f'{i}.bin')))

    progress = filecopy.copy_files(pairs, block_size=128)

    assert progress.total == 3210
    assert progress.done == 3210
    for src, dst in pairs:
        assert read(src) == read(dst)


def test_cancel_removes_temp_file(tmp_path):
    src = str(tmp_path / 'src.bin')
    dst = str(tmp_path / 'dst.bin')
    write_file(src, 100)
    progress = filecopy.CopyProgress(100)
    progress.cancel()

    with pytest.raises(filecopy.CopyCancelled):
        filecopy.copy_file(src, dst, progress=progress)

    assert not os.path.exists(dst)
    assert not os.path.exists(dst + filecopy.TEMP_SUFFIX)


def test_retry_after_error(tmp_path, monkeypatch):
    src = str(tmp_path / 'src.bin')
    dst = str(tmp_path / 'dst.bin')
    write_file(src, 500)
    monkeypatch.setattr(filecopy, 'RETRY_DELAY', 0)

    real_copy_once = filecopy._copy_once
    calls = []

    def flaky(src_, tmp_, progress, block_size):
        calls.append(1)
        if len(calls) == 1:
            progress.done += 100
            raise OSError('network went away')
        real_copy_once(src_, tmp_, progress, block_size)

    monkeypatch.setattr(filecopy, '_copy_once', flaky)
    progress = filecopy.CopyProgress(500)
    filecopy.copy_file(src, dst, progress=progress)

    assert len(calls) == 2
    assert progress.done == 500
    assert read(dst) == read(src)


def test_failure_after_retries_cleans_up(tmp_path, monkeypatch):
    src = str(tmp_path / 'src.bin')
    dst = str(tmp_path / 'dst.bin')
    write_file(src, 10)
    monkeypatch.setattr(filecopy, 'RETRY_DELAY', 0)

    def broken(src_, tmp_, progress, block_size):
        open(tmp_, 'wb').close()
        raise OSError('disk full')

    monkeypatch.setattr(filecopy, '_copy_once', broken)
    with pytest.raises(OSError):
        filecopy.copy_file(src, dst)
    assert not os.path.exists(dst + filecopy.TEMP_SUFFIX)


def test_is_same_device(tmp_path):
    a = tmp_path / 'a'
    b = tmp_path / 'b'
    a.mkdir()
    b.mkdir()
    assert filecopy.is_same_device(str(a), str(b))


def test_copy_never_replaces_existing(tmp_path):
    src = str(tmp_path / 'src.bin')
    dst = str(tmp_path / 'dst.bin')
    write_file(src, 100)
    with open(dst, 'wb') as f:
        f.write(b'keep me')

    with pytest.raises(FileExistsError):
        filecopy.copy_file(src, dst)

    assert read(dst) == b'keep me'
    assert not os.path.exists(dst + filecopy.TEMP_SUFFIX)


def test_copy_files_records_created(tmp_path):
    pairs = []
    for name in ('a', 'b'):
        src = str(tmp_path / 'src' / name)
        write_file(src, 10)
        pairs.append((src, str(tmp_path / 'dst' / name)))
    # Second destination exists, so copying stops after the first.
    os.makedirs(tmp_path / 'dst')
    (tmp_path / 'dst' / 'b').write_bytes(b'x')

    created = []
    with pytest.raises(FileExistsError):
        filecopy.copy_files(pairs, created=created)
    assert created == [pairs[0][1]]

    filecopy.remove_files(created)
    assert not os.path.exists(pairs[0][1])
