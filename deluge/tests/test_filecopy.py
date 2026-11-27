#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import hashlib
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


def make_pieces(data, piece_length):
    return [
        hashlib.sha1(data[i : i + piece_length]).digest()
        for i in range(0, len(data), piece_length)
    ]


def test_verify_pieces_matches_with_pad_files(tmp_path):
    a = os.urandom(300)
    b = os.urandom(70)
    (tmp_path / 'a').write_bytes(a)
    (tmp_path / 'b').write_bytes(b)
    # Pad files align b to a piece boundary and fill the last piece.
    entries = [
        (str(tmp_path / 'a'), 300),
        (None, 84),
        (str(tmp_path / 'b'), 70),
        (None, 58),
    ]
    data = a + bytes(84) + b + bytes(58)
    progress = filecopy.CopyProgress(370)

    bad = filecopy.verify_pieces(entries, 128, make_pieces(data, 128), progress, 64)

    assert bad is None
    assert progress.done == 370


def test_verify_pieces_finds_corrupt_piece(tmp_path):
    data = bytearray(os.urandom(1000))
    hashes = make_pieces(bytes(data), 256)
    data[600] ^= 0xFF
    (tmp_path / 'f').write_bytes(bytes(data))

    bad = filecopy.verify_pieces([(str(tmp_path / 'f'), 1000)], 256, hashes)

    assert bad == 2


def test_verify_pieces_rejects_wrong_size(tmp_path):
    data = os.urandom(500)
    (tmp_path / 'f').write_bytes(data + b'extra')
    with pytest.raises(OSError):
        filecopy.verify_pieces(
            [(str(tmp_path / 'f'), 500)], 256, make_pieces(data, 256)
        )


def test_verify_pieces_missing_file(tmp_path):
    with pytest.raises(OSError):
        filecopy.verify_pieces([(str(tmp_path / 'nope'), 10)], 16, [b'x' * 20])


def test_verify_pieces_cancel(tmp_path):
    data = os.urandom(100)
    (tmp_path / 'f').write_bytes(data)
    progress = filecopy.CopyProgress(100)
    progress.cancel()
    with pytest.raises(filecopy.CopyCancelled):
        filecopy.verify_pieces(
            [(str(tmp_path / 'f'), 100)], 64, make_pieces(data, 64), progress
        )
