#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import shutil
import warnings
from base64 import b64encode
from unittest import mock

import pytest
import pytest_twisted
from twisted.internet import reactor, task

from deluge import component
from deluge.bencode import bencode
from deluge.conftest import BaseTestCase
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.error import InvalidTorrentError

from . import common

warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.resetwarnings()


class TestTorrentmanager(BaseTestCase):
    def set_up(self):
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.clock = task.Clock()
        self.tm = self.core.torrentmanager
        self.tm.callLater = self.clock.callLater
        self.tm.clock = self.clock
        return component.start()

    def tear_down(self):
        def on_shutdown(result):
            del self.rpcserver
            del self.core

        return component.shutdown().addCallback(on_shutdown)

    @pytest_twisted.inlineCallbacks
    def test_remove_torrent(self):
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = _file.read()
        torrent_id = yield self.core.add_torrent_file_async(
            filename, b64encode(filedump), {}
        )
        assert self.tm.remove(torrent_id, False)

    @pytest_twisted.inlineCallbacks
    def test_remove_magnet(self):
        """Test remove magnet before received metadata and delete_copies is True"""
        magnet = 'magnet:?xt=urn:btih:ab570cdd5a17ea1b61e970bb72047de141bce173'
        options = {}
        self.core.config.config['copy_torrent_file'] = True
        self.core.config.config['del_copy_torrent_file'] = True
        torrent_id = yield self.core.add_torrent_magnet(magnet, options)
        assert self.tm.remove(torrent_id, False)

    async def test_prefetch_metadata(self):
        from deluge._libtorrent import lt

        with open(common.get_test_data_file('test.torrent'), 'rb') as _file:
            t_info = lt.torrent_info(lt.bdecode(_file.read()))
        mock_alert = mock.MagicMock()
        mock_alert.handle.info_hash = mock.MagicMock(
            return_value='ab570cdd5a17ea1b61e970bb72047de141bce173'
        )
        mock_alert.handle.get_torrent_info = mock.MagicMock(return_value=t_info)

        magnet = 'magnet:?xt=urn:btih:ab570cdd5a17ea1b61e970bb72047de141bce173'
        d = self.tm.prefetch_metadata(magnet, 30)
        # Make sure to use calllater, because the above prefetch call won't
        # actually start running until we await it.
        reactor.callLater(0, self.tm.on_alert_metadata_received, mock_alert)

        expected = (
            'ab570cdd5a17ea1b61e970bb72047de141bce173',
            b64encode(
                bencode(
                    {
                        b'piece length': 32768,
                        b'sha1': (
                            b'2\xce\xb6\xa8"\xd7\xf0\xd4\xbf\xdc^K\xba\x1bh'
                            b'\x9d\xc5\xb7\xac\xdd'
                        ),
                        b'name': b'azcvsupdater_2.6.2.jar',
                        b'private': 0,
                        b'pieces': (
                            b"\xdb\x04B\x05\xc3'\xdab\xb8su97\xa9u"
                            b'\xca<w\\\x1ef\xd4\x9b\x16\xa9}\xc0\x9f:\xfd'
                            b'\x97qv\x83\xa2"\xef\x9d7\x0by!\rl\xe5v\xb7'
                            b'\x18{\xf7/"P\xe9\x8d\x01D\x9e8\xbd\x16\xe3'
                            b'\xfb-\x9d\xaa\xbcM\x11\xba\x92\xfc\x13F\xf0'
                            b'\x1c\x86x+\xc8\xd0S\xa9\x90`\xa1\xe4\x82\xe8'
                            b'\xfc\x08\xf7\xe3\xe5\xf6\x85\x1c%\xe7%\n\xed'
                            b'\xc0\x1f\xa1;\x9a\xea\xcf\x90\x0c/F>\xdf\xdagA'
                            b'\xc42|\xda\x82\xf5\xa6b\xa1\xb8#\x80wI\xd8f'
                            b'\xf8\xbd\xacW\xab\xc3s\xe0\xbbw\xf2K\xbe\xee'
                            b'\xa8rG\xe1W\xe8\xb7\xc2i\xf3\xd8\xaf\x9d\xdc'
                            b'\xd0#\xf4\xc1\x12u\xcd\x0bE?:\xe8\x9c\x1cu'
                            b'\xabb(oj\r^\xd5\xd5A\x83\x88\x9a\xa1J\x1c?'
                            b'\xa1\xd6\x8c\x83\x9e&'
                        ),
                        b'length': 307949,
                        b'name.utf-8': b'azcvsupdater_2.6.2.jar',
                        b'ed2k': b'>p\xefl\xfa]\x95K\x1b^\xc2\\;;e\xb7',
                    }
                )
            ),
        )
        assert expected == await d

    async def test_prefetch_metadata_timeout(self):
        magnet = 'magnet:?xt=urn:btih:deadbeefdeadbeefdeadbeefdeadbeefdeadbeef'
        timeout = 30
        d = self.tm.prefetch_metadata(magnet, timeout)
        # Prefetch won't start running until awaited so use callLater to ensure
        # clock advance runs after timeout registered and coroutine started.
        reactor.callLater(0, self.clock.advance, timeout + 1)
        result = await d
        expected = ('deadbeefdeadbeefdeadbeefdeadbeefdeadbeef', b'')
        assert result == expected

    @pytest.mark.todo
    def test_remove_torrent_false(self):
        """Test when remove_torrent returns False"""
        common.todo_test(self)

    def test_remove_invalid_torrent(self):
        with pytest.raises(InvalidTorrentError):
            self.tm.remove('torrentidthatdoesntexist')

    @pytest_twisted.inlineCallbacks
    def test_remove_torrent_missing_from_queued_set(self):
        """An unfinished torrent absent from queued_torrents must still be removed.

        By this point session.remove_torrent() has already destroyed the
        libtorrent handle, so abandoning the removal leaves a Torrent whose
        every later status read raises RuntimeError for the life of the daemon.

        on_alert_torrent_finished reaches this state on its own: when a
        move_completed path is set it queues the move and leaves is_finished
        False, while still dropping the id from queued_torrents.
        """
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = _file.read()
        torrent_id = yield self.core.add_torrent_file_async(
            filename, b64encode(filedump), {}
        )
        self.tm.queued_torrents.discard(torrent_id)
        assert not self.tm.torrents[torrent_id].is_finished

        assert self.tm.remove(torrent_id, False)
        assert torrent_id not in self.tm.torrents

    @pytest_twisted.inlineCallbacks
    def test_remove_torrent_with_dead_handle(self):
        """A torrent whose handle libtorrent already dropped must be removable.

        remove_torrent() raises on an invalid handle, so returning False here
        left the only existing zombies unremovable short of a daemon restart.
        """
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = _file.read()
        torrent_id = yield self.core.add_torrent_file_async(
            filename, b64encode(filedump), {}
        )
        torrent = self.tm.torrents[torrent_id]

        # Kill the handle behind TorrentManager's back, as an aborted remove does.
        self.tm.session.remove_torrent(torrent.handle, 0)
        for _ in range(100):
            if not torrent.handle.is_valid():
                break
            yield task.deferLater(reactor, 0.05)
        assert not torrent.handle.is_valid(), 'libtorrent never dropped the handle'
        # A real zombie has outlived the 5s status cache, so reads hit the handle.
        torrent._status_last_update = 0

        assert self.tm.remove(torrent_id, False)
        assert torrent_id not in self.tm.torrents

    def test_open_state(self):
        """Open a state with a UTF-8 encoded torrent filename."""
        shutil.copy(
            common.get_test_data_file('utf8_filename_torrents.state'),
            os.path.join(self.config_dir, 'state', 'torrents.state'),
        )

        state = self.tm.open_state()
        assert len(state.torrents) == 1
