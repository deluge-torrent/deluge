#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import shutil
import threading
import warnings
from base64 import b64encode
from unittest import mock

import pytest
import pytest_twisted
from twisted.internet import reactor, task
from twisted.python import threadable

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

    async def _add_test_torrent(self, name='test.torrent'):
        filename = common.get_test_data_file(name)
        with open(filename, 'rb') as _file:
            filedump = _file.read()
        return await self.core.add_torrent_file_async(filename, b64encode(filedump), {})

    async def test_status_request_runs_slow_keys_off_reactor(self):
        torrent_id = await self._add_test_torrent()
        calls = []

        def get_peers():
            calls.append(threadable.isInIOThread())
            return ['peer']

        self.tm[torrent_id].status_funcs['peers'] = get_peers
        self.tm.session.post_torrent_updates = mock.Mock()
        self.tm.last_state_update_alert_ts = 0

        d = self.tm.torrents_status_update([torrent_id], ['peers', 'name'])
        self.tm.on_alert_state_update(mock.Mock(status=[]))
        status = await d

        assert status[torrent_id]['peers'] == ['peer']
        assert status[torrent_id]['name'] == self.tm[torrent_id].get_name()
        assert calls == [False]

    async def test_status_request_leaves_out_torrent_whose_fetch_failed(self):
        torrent_id = await self._add_test_torrent()

        def get_peers():
            raise ValueError('boom')

        self.tm[torrent_id].status_funcs['peers'] = get_peers
        self.tm.session.post_torrent_updates = mock.Mock()
        self.tm.last_state_update_alert_ts = 0

        other_id = await self._add_test_torrent('test_torrent.file.torrent')

        with mock.patch('deluge.core.torrentmanager.log') as log:
            d = self.tm.torrents_status_update(
                [torrent_id, other_id], ['peers', 'name']
            )
            self.tm.on_alert_state_update(mock.Mock(status=[]))
            assert list(await d) == [other_id]

        assert 'boom' in log.warning.call_args[0][-1]

    async def test_status_request_diffs_every_torrent_after_its_fetches(self):
        moving_id = await self._add_test_torrent()
        other_id = await self._add_test_torrent('test_torrent.file.torrent')
        release = threading.Event()

        def get_progress():
            release.wait(5)
            return 50.0

        self.tm[moving_id].state = 'Moving'
        self.tm[moving_id].status_funcs['progress'] = get_progress
        self.tm.session.post_torrent_updates = mock.Mock()
        self.tm.last_state_update_alert_ts = 0
        self.rpcserver.factory.session_id = 1

        d = self.tm.torrents_status_update(
            [moving_id, other_id], ['progress'], diff=True
        )
        self.tm.on_alert_state_update(mock.Mock(status=[]))
        # Diffed now, a torrent with nothing slow to fetch would reach the
        # client after a newer diff of it sent by a quicker request.
        assert self.tm[other_id].prev_status == {}
        release.set()
        status = await d.addTimeout(5, reactor)

        assert set(status) == {moving_id, other_id}
        assert 1 in self.tm[other_id].prev_status

    async def test_status_request_diffs_against_requesting_session(self):
        torrent_id = await self._add_test_torrent()
        self.tm.session.post_torrent_updates = mock.Mock()
        self.tm.last_state_update_alert_ts = 0
        self.rpcserver.factory.session_id = 1

        d = self.tm.torrents_status_update([torrent_id], ['name'], diff=True)
        # Another session's call is dispatched before the alert arrives.
        self.rpcserver.factory.session_id = 2
        self.tm.on_alert_state_update(mock.Mock(status=[]))
        await d

        assert list(self.tm[torrent_id].prev_status) == [1]

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
