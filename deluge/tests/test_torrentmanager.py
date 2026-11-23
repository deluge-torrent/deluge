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

    def test_open_state(self):
        """Open a state with a UTF-8 encoded torrent filename."""
        shutil.copy(
            common.get_test_data_file('utf8_filename_torrents.state'),
            os.path.join(self.config_dir, 'state', 'torrents.state'),
        )

        state = self.tm.open_state()
        assert len(state.torrents) == 1

    async def _add_test_torrent(self, name='test.torrent'):
        filename = common.get_test_data_file(name)
        with open(filename, 'rb') as _file:
            filedump = _file.read()
        return await self.core.add_torrent_file_async(filename, b64encode(filedump), {})

    def _tracker_reply(self, torrent_id):
        handle = mock.Mock(info_hash=mock.Mock(return_value=torrent_id))
        self.tm.on_alert_tracker_reply(mock.Mock(handle=handle))

    def _state_update(self, torrent_id, num_complete, num_incomplete):
        """Deliver a state_update_alert reporting these swarm counts."""
        torrent = self.tm.torrents[torrent_id]
        real_status = torrent.handle.status()
        t_status = mock.Mock(
            info_hash=torrent_id,
            num_complete=num_complete,
            num_incomplete=num_incomplete,
        )
        # The handler answers a queued status request; none is under test here.
        self.tm.torrents_status_requests.insert(0, None)
        try:
            with mock.patch.object(self.tm, 'handle_torrents_status_callback'):
                self.tm.on_alert_state_update(mock.Mock(status=[t_status]))
        finally:
            torrent.status = real_status

    async def test_tracker_reply_does_not_read_status_from_libtorrent(self):
        torrent_id = await self._add_test_torrent()
        torrent = self.tm.torrents[torrent_id]
        with mock.patch.object(torrent, 'handle', mock.Mock(wraps=torrent.handle)):
            self._tracker_reply(torrent_id)
            torrent.handle.status.assert_not_called()

    @pytest.mark.parametrize('counts', [(-1, -1), (-1, 2), (5, -1)])
    async def test_tracker_reply_without_swarm_counts_scrapes_once(self, counts):
        torrent_id = await self._add_test_torrent()
        torrent = self.tm.torrents[torrent_id]
        with mock.patch.object(torrent, 'scrape_tracker') as scrape:
            self._tracker_reply(torrent_id)
            scrape.assert_not_called()
            self._state_update(torrent_id, *counts)
            self._state_update(torrent_id, *counts)
        scrape.assert_called_once_with()

    async def test_tracker_reply_with_swarm_counts_does_not_scrape(self):
        torrent_id = await self._add_test_torrent()
        torrent = self.tm.torrents[torrent_id]
        with mock.patch.object(torrent, 'scrape_tracker') as scrape:
            self._tracker_reply(torrent_id)
            self._state_update(torrent_id, 5, 2)
        scrape.assert_not_called()

    async def test_status_update_without_tracker_reply_does_not_scrape(self):
        torrent_id = await self._add_test_torrent()
        torrent = self.tm.torrents[torrent_id]
        with mock.patch.object(torrent, 'scrape_tracker') as scrape:
            self._state_update(torrent_id, -1, -1)
        scrape.assert_not_called()
