#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import tempfile

import pytest

from deluge import metafile
from deluge._libtorrent import LT_VERSION
from deluge.common import VersionSplit

from . import common


def check_torrent(filename):
    # Test loading with libtorrent to make sure it's valid
    from deluge._libtorrent import lt

    lt.torrent_info(filename)

    # Test loading with our internal TorrentInfo class
    from deluge.ui.common import TorrentInfo

    TorrentInfo(filename)


class TestMetafile:
    def test_save_multifile(self):
        # Create a temporary folder for torrent creation
        tmp_path = tempfile.mkdtemp()
        with open(os.path.join(tmp_path, 'file_A'), 'wb') as tmp_file:
            tmp_file.write(b'a' * (312 * 1024))
        with open(os.path.join(tmp_path, 'file_B'), 'wb') as tmp_file:
            tmp_file.write(b'b' * (2354 * 1024))
        with open(os.path.join(tmp_path, 'file_C'), 'wb') as tmp_file:
            tmp_file.write(b'c' * (11 * 1024))

        tmp_fd, tmp_file = tempfile.mkstemp('.torrent')
        metafile.make_meta_file(tmp_path, '', 32768, target=tmp_file)

        check_torrent(tmp_file)

        os.remove(os.path.join(tmp_path, 'file_A'))
        os.remove(os.path.join(tmp_path, 'file_B'))
        os.remove(os.path.join(tmp_path, 'file_C'))
        os.rmdir(tmp_path)
        os.close(tmp_fd)
        os.remove(tmp_file)

    def test_save_singlefile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_data = tmp_dir + '/testdata'
            with open(tmp_data, 'wb') as tmp_file:
                tmp_file.write(b'a' * (2314 * 1024))

            tmp_torrent = tmp_dir + '/.torrent'
            metafile.make_meta_file(tmp_data, '', 32768, target=tmp_torrent)

            check_torrent(tmp_torrent)

    @pytest.mark.parametrize(
        'path',
        [
            common.get_test_data_file('deluge.png'),
            common.get_test_data_file('unicode_filenames.torrent'),
            os.path.dirname(common.get_test_data_file('deluge.png')),
        ],
    )
    @pytest.mark.parametrize(
        'torrent_format',
        [
            metafile.TorrentFormat.V1,
            metafile.TorrentFormat.V2,
            metafile.TorrentFormat.HYBRID,
        ],
    )
    @pytest.mark.parametrize('piece_length', [2**14, 2**15, 2**16])
    @pytest.mark.parametrize('private', [True, False])
    def test_create_info(self, path, torrent_format, piece_length, private):
        our_info, our_piece_layers = metafile.makeinfo(
            path,
            piece_length,
            metafile.dummy,
            private=private,
            torrent_format=torrent_format,
        )
        lt_info, lt_piece_layers = metafile.makeinfo_lt(
            path,
            piece_length,
            private=private,
            torrent_format=torrent_format,
        )

        if (
            torrent_format == metafile.TorrentFormat.HYBRID
            and os.path.isdir(path)
            and VersionSplit(LT_VERSION) <= VersionSplit('2.0.7.0')
        ):
            # Libtorrent didn't correctly follow the standard until version 2.0.7 included
            # https://github.com/arvidn/libtorrent/commit/74d82a0cd7c2e9e3c4294901d7eb65e247050df4
            # If last file is a padding, ignore that file and the last piece.
            if our_info[b'files'][-1][b'path'][0] == b'.pad':
                our_info[b'files'] = our_info[b'files'][:-1]
                our_info[b'pieces'] = our_info[b'pieces'][:-32]
                lt_info[b'pieces'] = lt_info[b'pieces'][:-32]

        assert our_info == lt_info
        assert our_piece_layers == lt_piece_layers
