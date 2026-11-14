#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import shutil
import warnings
from base64 import b64encode
from types import SimpleNamespace
from unittest import mock

import pytest
import pytest_twisted
from twisted.internet import reactor, task

from deluge import component
from deluge.bencode import bencode
from deluge.conftest import BaseTestCase
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.core.torrentmanager import (
    _torrent_info_from_bytes,
    _tracker_endpoint_has_no_error,
)
from deluge.error import AddTorrentError, InvalidTorrentError

from . import common

warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.resetwarnings()


@pytest.mark.parametrize(
    ('endpoint', 'expected'),
    [
        ({'last_error': {'value': 0}}, True),
        ({'last_error': {'value': 5}}, False),
        ({'info_hashes': [{'last_error': {'value': 0}}]}, True),
        ({'info_hashes': [{'last_error': {'value': 5}}]}, False),
        (
            {
                'info_hashes': [
                    {'last_error': {'value': 5}},
                    {'last_error': {'value': 0}},
                ]
            },
            True,
        ),
        ({'info_hashes': []}, False),
    ],
)
def test_tracker_endpoint_error_layout(endpoint, expected):
    assert _tracker_endpoint_has_no_error(endpoint) == expected


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

    async def test_full_core_status_and_state_update(self):
        """A modern state_update_alert must refresh GUI status and permit removal."""
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as source:
            torrent_id = await self.core.add_torrent_file_async(
                filename, b64encode(source.read()), {}
            )
        torrent = self.tm.torrents[torrent_id]
        native_status = torrent.handle.status()
        pending = object()
        self.tm.torrents_status_requests.append(pending)
        with mock.patch.object(self.tm, 'handle_torrents_status_callback') as callback:
            self.tm.on_alert_state_update(SimpleNamespace(status=[native_status]))
            callback.assert_called_once_with(pending)
        assert torrent.status is native_status

        # These are the bulk and per-torrent RPC requests the GTK UI needs.
        all_status = self.core.get_torrent_status(torrent_id, [])
        assert all_status['name']
        assert isinstance(all_status['active_time'], int)
        assert isinstance(all_status['creator'], str)
        status = self.core.get_torrent_status(
            torrent_id, ['name', 'peers', 'num_peers', 'num_seeds']
        )
        assert status['name']
        assert isinstance(status['peers'], list)
        assert self.tm.remove(torrent_id, False)

    def test_unsolicited_state_update_without_pending_request(self):
        """An update outside an RPC status request must not crash the handler."""
        self.tm.torrents_status_requests.clear()
        self.tm.on_alert_state_update(SimpleNamespace(status=[]))

    async def test_remove_torrent_missing_queue_entry(self):
        """Removal stays consistent if a torrent is absent from the queue."""
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as source:
            torrent_id = await self.core.add_torrent_file_async(
                filename, b64encode(source.read()), {}
            )
        self.tm.queued_torrents.discard(torrent_id)
        assert self.tm.remove(torrent_id, False)
        assert torrent_id not in self.tm.torrents

    async def test_duplicate_torrent_merges_trackers_from_modern_params(self):
        """ABI 4 no longer exposes trackers on torrent_info."""
        from deluge._libtorrent import lt

        if not hasattr(lt.add_torrent_params(), 'info_hashes'):
            pytest.skip('Modern add_torrent_params is unavailable')

        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as source:
            data = source.read()
        torrent_id = await self.core.add_torrent_file_async(
            filename, b64encode(data), {}
        )
        params = lt.load_torrent_buffer(data)
        assert not params.ti.priv()
        url = 'wss://tracker.example.com/announce'
        params.trackers = [url]
        params.tracker_tiers = [2]

        with pytest.raises(AddTorrentError, match='already in session'):
            self.tm._build_torrent_params(
                torrent_info=params.ti,
                options=self.tm._build_torrent_options({}),
                file_params=params,
            )

        assert any(
            tracker['url'] == url and tracker['tier'] == 2
            for tracker in self.tm.torrents[torrent_id].handle.trackers()
        )

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
        with open(common.get_test_data_file('test.torrent'), 'rb') as _file:
            t_info = _torrent_info_from_bytes(_file.read())
        mock_alert = mock.MagicMock()
        mock_alert.handle.info_hash = mock.MagicMock(
            return_value='ab570cdd5a17ea1b61e970bb72047de141bce173'
        )
        mock_alert.handle.torrent_file = mock.MagicMock(return_value=t_info)

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

    def test_build_torrent_params_with_resume_data(self):
        from deluge._libtorrent import lt

        with open(common.get_test_data_file('test.torrent'), 'rb') as _file:
            torrent_info = _torrent_info_from_bytes(_file.read())
        options = self.tm._build_torrent_options({'download_location': os.getcwd()})
        resume_data = lt.bencode({'test': b'resume'})
        params = mock.MagicMock()

        with mock.patch.object(
            lt, 'read_resume_data', return_value=params
        ) as read_resume_data:
            torrent_id, result = self.tm._build_torrent_params(
                torrent_info, options=options, resume_data=resume_data
            )

        assert torrent_id == str(torrent_info.info_hash())
        assert result is params
        assert params.ti is torrent_info
        assert params.save_path == os.getcwd()
        read_resume_data.assert_called_once_with(resume_data)

    def test_build_magnet_params_with_libtorrent_2_1(self):
        from deluge._libtorrent import lt

        if not hasattr(lt.add_torrent_params(), 'info_hashes'):
            pytest.skip('Requires current add_torrent_params API')

        info_hash = 'ab570cdd5a17ea1b61e970bb72047de141bce173'
        magnet = (
            f'magnet:?xt=urn:btih:{info_hash}'
            '&tr=wss%3A%2F%2Ftracker.example.com%2Fannounce'
        )
        options = self.tm._build_torrent_options({'download_location': os.getcwd()})
        torrent_id, params = self.tm._build_torrent_params(
            magnet=magnet, options=options
        )

        assert torrent_id == info_hash
        assert isinstance(params, lt.add_torrent_params)
        assert str(params.info_hashes.v1) == info_hash
        assert params.trackers == ['wss://tracker.example.com/announce']
        assert params.save_path == os.getcwd()

    def test_restore_magnet_from_native_resume_params(self):
        """Legacy resume params already carry a typed info hash."""
        from deluge._libtorrent import lt

        info_hash = 'ab570cdd5a17ea1b61e970bb72047de141bce173'
        magnet = f'magnet:?xt=urn:btih:{info_hash}&dn=restored'
        params = lt.parse_magnet_uri(magnet)
        options = self.tm._build_torrent_options({'download_location': os.getcwd()})

        with mock.patch.object(lt, 'read_resume_data', return_value=params):
            torrent_id, result = self.tm._build_torrent_params(
                magnet=magnet, options=options, resume_data=b'legacy-resume'
            )

        assert torrent_id == info_hash
        assert result is params
        if hasattr(lt.add_torrent_params(), 'info_hashes'):
            assert str(result.info_hashes.v1) == info_hash
        else:
            assert str(result.info_hash) == info_hash
        assert result.save_path == os.getcwd()

    def test_open_state(self):
        """Open a state with a UTF-8 encoded torrent filename."""
        shutil.copy(
            common.get_test_data_file('utf8_filename_torrents.state'),
            os.path.join(self.config_dir, 'state', 'torrents.state'),
        )

        state = self.tm.open_state()
        assert len(state.torrents) == 1
