#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import tempfile

from deluge import maketorrent


def check_torrent(filename):
    # Test loading with libtorrent to make sure it's valid
    from deluge._libtorrent import lt

    lt.torrent_info(filename)

    # Test loading with our internal TorrentInfo class
    from deluge.ui.common import TorrentInfo

    TorrentInfo(filename)


class TestMakeTorrent:
    def test_save_multifile(self):
        # Create a temporary folder for torrent creation
        tmp_path = tempfile.mkdtemp()
        with open(os.path.join(tmp_path, 'file_A'), 'wb') as _file:
            _file.write(b'a' * (312 * 1024))
        with open(os.path.join(tmp_path, 'file_B'), 'wb') as _file:
            _file.write(b'b' * (2354 * 1024))
        with open(os.path.join(tmp_path, 'file_C'), 'wb') as _file:
            _file.write(b'c' * (11 * 1024))

        t = maketorrent.TorrentMetadata()
        t.data_path = tmp_path
        tmp_fd, tmp_file = tempfile.mkstemp('.torrent')
        t.save(tmp_file)

        check_torrent(tmp_file)

        os.remove(os.path.join(tmp_path, 'file_A'))
        os.remove(os.path.join(tmp_path, 'file_B'))
        os.remove(os.path.join(tmp_path, 'file_C'))
        os.rmdir(tmp_path)
        os.close(tmp_fd)
        os.remove(tmp_file)

    def test_save_singlefile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_data = tmp_dir + '/data'
            with open(tmp_data, 'wb') as _file:
                _file.write(b'a' * (2314 * 1024))
            t = maketorrent.TorrentMetadata()
            t.data_path = tmp_data
            tmp_file = tmp_dir + '/.torrent'
            t.save(tmp_file)

            check_torrent(tmp_file)

    def test_save_multifile_padded(self):
        # Create a temporary folder for torrent creation
        tmp_path = tempfile.mkdtemp()
        with open(os.path.join(tmp_path, 'file_A'), 'wb') as _file:
            _file.write(b'a' * (312 * 1024))
        with open(os.path.join(tmp_path, 'file_B'), 'wb') as _file:
            _file.write(b'b' * (2354 * 1024))
        with open(os.path.join(tmp_path, 'file_C'), 'wb') as _file:
            _file.write(b'c' * (11 * 1024))

        t = maketorrent.TorrentMetadata()
        t.data_path = tmp_path
        t.pad_files = True
        tmp_fd, tmp_file = tempfile.mkstemp('.torrent')
        t.save(tmp_file)

        check_torrent(tmp_file)

        os.remove(os.path.join(tmp_path, 'file_A'))
        os.remove(os.path.join(tmp_path, 'file_B'))
        os.remove(os.path.join(tmp_path, 'file_C'))
        os.rmdir(tmp_path)
        os.close(tmp_fd)
        os.remove(tmp_file)
