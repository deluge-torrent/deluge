#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import itertools
import os
import time
from base64 import b64encode
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import mock

import pytest
from twisted.internet import defer, reactor
from twisted.internet.task import deferLater

import deluge.component as component
import deluge.core.torrent
import deluge.tests.common as common
from deluge._libtorrent import lt
from deluge.common import VersionSplit, utf8_encode_structure
from deluge.conftest import BaseTestCase
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.core.torrent import (
    Torrent,
    _time_since_torrent_activity,
    _torrent_duration,
    _torrent_status_flag,
)
from deluge.core.torrentmanager import (
    TorrentManager,
    TorrentState,
    _torrent_info_from_bytes,
)

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock import AsyncMock


class TestTorrent(BaseTestCase):
    def test_libtorrent_status_legacy_and_modern_activity(self):
        modern = SimpleNamespace(
            active_duration=timedelta(seconds=42),
            seeding_duration=timedelta(seconds=12),
            last_download=datetime.now() - timedelta(seconds=10),
            last_upload=None,
        )
        assert _torrent_duration(modern, 'active_time', 'active_duration') == 42
        elapsed = _time_since_torrent_activity(
            modern, 'time_since_download', 'last_download'
        )
        assert 9 <= elapsed <= 12
        assert (
            _time_since_torrent_activity(modern, 'time_since_upload', 'last_upload')
            == -1
        )

        legacy = SimpleNamespace(active_time=17, time_since_download=8)
        assert _torrent_duration(legacy, 'active_time', 'active_duration') == 17
        assert (
            _time_since_torrent_activity(legacy, 'time_since_download', 'last_download')
            == 8
        )

    def test_full_torrent_status_with_native_binding(self):
        """GTK Details and Status require every status key to be queryable."""
        handle = self.session.add_torrent(self.get_torrent_atp('test.torrent'))
        torrent = Torrent(handle, {})
        status = torrent.get_status([], update=True, all_keys=True)
        assert 'name' in status
        assert isinstance(status['active_time'], int)
        assert isinstance(status['seeding_time'], int)
        assert isinstance(status['finished_time'], int)
        assert isinstance(status['time_since_transfer'], int)
        assert isinstance(status['time_since_download'], int)
        assert isinstance(status['time_since_upload'], int)
        assert isinstance(status['super_seeding'], bool)
        assert isinstance(status['seed_mode'], bool)
        assert isinstance(status['creator'], str)
        assert isinstance(status['comment'], str)

    def test_peer_endpoints_with_current_and_legacy_bindings(self):
        """The Peers tab must work without the removed peer_info.ip field."""
        fields = {
            'client': b'test peer',
            'flags': 0,
            'connecting': 1,
            'handshake': 2,
            'seed': 4,
            'payload_down_speed': 1024,
            'payload_up_speed': 512,
            'progress': 0.5,
        }
        modern = SimpleNamespace(
            **fields, remote_endpoint=lambda: ('2001:db8::1', 51413)
        )
        legacy = SimpleNamespace(**fields, ip=('192.0.2.5', 6881))
        connecting = SimpleNamespace(
            **{**fields, 'flags': 1},
            remote_endpoint=lambda: ('192.0.2.6', 6882),
        )
        torrent = SimpleNamespace(
            handle=SimpleNamespace(get_peer_info=lambda: [modern, legacy, connecting])
        )

        with mock.patch.object(deluge.core.torrent.component, 'get') as get:
            get.return_value.geoip_instance.country_code_by_addr.return_value = 'AU'
            peers = Torrent.get_peers(torrent)

        assert [peer['ip'] for peer in peers] == [
            '2001:db8::1:51413',
            '192.0.2.5:6881',
        ]
        assert peers[0]['client'] == 'test peer'
        assert peers[0]['country'] == 'AU'
        assert peers[0]['down_speed'] == 1024
        assert peers[0]['up_speed'] == 512
        assert peers[0]['progress'] == 0.5

    def test_file_progress_uses_indexed_storage(self):
        """ABI 2/3 file_storage does not expose __iter__ in Python."""
        storage = SimpleNamespace(
            num_files=lambda: 3,
            file_size=lambda index: [0, 16, 32][index],
        )
        torrent = SimpleNamespace(
            has_metadata=True,
            torrent_info=SimpleNamespace(layout=lambda: storage),
            handle=SimpleNamespace(file_progress=lambda: [0, 4, 16]),
        )
        assert Torrent.get_file_progress(torrent) == [0.0, 0.25, 0.5]

    def test_file_progress_handles_native_progress_failure(self):
        """A libtorrent file_progress error must not break the Files tab."""
        storage = SimpleNamespace(
            num_files=lambda: 2,
            file_size=lambda index: [16, 32][index],
        )

        def fail_progress():
            raise RuntimeError('file_progress unavailable')

        torrent = SimpleNamespace(
            has_metadata=True,
            torrent_info=SimpleNamespace(layout=lambda: storage),
            handle=SimpleNamespace(file_progress=fail_progress),
        )
        assert Torrent.get_file_progress(torrent) == [0.0, 0.0]

    def test_manual_pause_sets_native_paused_flag(self):
        """A user pause command must stop the libtorrent torrent itself."""
        atp = self.get_torrent_atp('test.torrent')
        handle = self.session.add_torrent(atp)
        torrent = Torrent(handle, {'auto_managed': False})
        torrent.resume()
        torrent.pause()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if handle.status().flags & lt.torrent_flags.paused:
                break
            time.sleep(0.1)
        else:
            pytest.fail('Deluge manual pause did not pause the libtorrent handle')

    def test_torrent_status_flags(self):
        status = SimpleNamespace(
            flags=lt.torrent_flags.paused | lt.torrent_flags.auto_managed
        )
        assert _torrent_status_flag(status, lt.torrent_flags.paused, 'paused')
        assert _torrent_status_flag(
            status, lt.torrent_flags.auto_managed, 'auto_managed'
        )

        legacy_status = SimpleNamespace(paused=True, auto_managed=False)
        assert _torrent_status_flag(legacy_status, lt.torrent_flags.paused, 'paused')
        assert not _torrent_status_flag(
            legacy_status, lt.torrent_flags.auto_managed, 'auto_managed'
        )

    def setup_config(self):
        core_config = deluge.config.Config(
            'core.conf',
            defaults=deluge.core.preferencesmanager.DEFAULT_PREFS,
            config_dir=self.config_dir,
        )
        core_config.save()

    def set_up(self):
        self.setup_config()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.core.config.config['new_release_check'] = False
        self.session = self.core.session
        self.torrent = None
        return component.start()

    def tear_down(self):
        def on_shutdown(result):
            del self.rpcserver
            del self.core

        return component.shutdown().addCallback(on_shutdown)

    def print_priority_list(self, priorities):
        tmp = ''
        for i, p in enumerate(priorities):
            if i % 100 == 0:
                print(tmp)
                tmp = ''
            tmp += '%s' % p
        print(tmp)

    def assert_state(self, torrent, state):
        """Assert torrent state matches expected state"""
        torrent.update_state()
        assert torrent.state == state

    def assert_state_wait(self, torrent, expected, timeout=1, interval=0.2):
        """Assert state but retry with timeout e.g. Allow for async lt alerts"""
        start = time.time()

        while time.time() - start < timeout:
            torrent.update_state()
            time.sleep(interval)
            if torrent.state == expected:
                break
        else:
            assert torrent.state == expected

    def get_torrent_atp(self, filename):
        filename = common.get_test_data_file(filename)
        with open(filename, 'rb') as _file:
            info = _torrent_info_from_bytes(_file.read())
        atp = {
            'ti': info,
            'save_path': os.getcwd(),
            'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            'flags': (
                lt.torrent_flags.auto_managed
                | lt.torrent_flags.duplicate_is_error & ~lt.torrent_flags.paused
            ),
        }
        return atp

    async def test_set_file_priorities(self):
        if getattr(lt, 'file_prio_alert', None):
            # Libtorrent 2.0.3 and later has a file_prio_alert
            prios_set = defer.Deferred()
            prios_set.addTimeout(1.5, reactor)
            component.get('AlertManager').register_handler(
                'file_prio_alert', lambda a: prios_set.callback(True)
            )
        else:
            # On older libtorrent, we just wait a while
            prios_set = deferLater(reactor, 0.8)

        atp = self.get_torrent_atp('dir_with_6_files.torrent')
        handle = self.session.add_torrent(atp)
        torrent = Torrent(handle, {})

        result = torrent.get_file_priorities()
        assert all(x == 4 for x in result)

        new_priorities = [3, 1, 2, 0, 5, 6, 7]
        torrent.set_file_priorities(new_priorities)
        assert torrent.get_file_priorities() == new_priorities

        # Test with handle.piece_priorities as handle.file_priorities async
        # updates and will return old value. Also need to remove a priority
        # value as one file is much smaller than piece size so doesn't show.
        await prios_set  # Delay to wait for alert from lt
        piece_prio = handle.get_piece_priorities()
        result = all(p in piece_prio for p in [3, 2, 0, 5, 6, 7])
        assert result

    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    def test_set_prioritize_first_last_pieces(self):
        piece_indexes = [
            0,
            1,
            50,
            51,
            52,
            110,
            111,
            112,
            113,
            200,
            201,
            202,
            212,
            213,
            214,
            215,
            216,
            217,
            457,
            458,
            459,
            460,
            461,
            462,
        ]
        self.run_test_set_prioritize_first_last_pieces(
            'dir_with_6_files.torrent', piece_indexes
        )

    def run_test_set_prioritize_first_last_pieces(
        self, torrent_file, prioritized_piece_indexes
    ):
        atp = self.get_torrent_atp(torrent_file)
        handle = self.session.add_torrent(atp)

        self.torrent = Torrent(handle, {})
        priorities_original = handle.get_piece_priorities()
        self.torrent.set_prioritize_first_last_pieces(True)
        priorities = handle.get_piece_priorities()

        # The length of the list of new priorites is the same as the original
        assert len(priorities_original) == len(priorities)

        # Test the priority of all the pieces against the calculated indexes.
        for idx, priority in enumerate(priorities):
            if idx in prioritized_piece_indexes:
                assert priorities[idx] == 7
            else:
                assert priorities[idx] == 4

        # self.print_priority_list(priorities)

    def test_set_prioritize_first_last_pieces_false(self):
        atp = self.get_torrent_atp('dir_with_6_files.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        # First set some pieces prioritized
        self.torrent.set_prioritize_first_last_pieces(True)
        # Reset pirorities
        self.torrent.set_prioritize_first_last_pieces(False)
        priorities = handle.get_piece_priorities()

        # Test the priority of the prioritized pieces
        for i in priorities:
            assert priorities[i] == 4

        # self.print_priority_list(priorities)

    def test_torrent_error_data_missing(self):
        if VersionSplit(lt.__version__) > VersionSplit('2.0.7.0'):
            pytest.xfail('Test not working as expected after lt 2.0.7')
        options = {'seed_mode': True}
        filename = common.get_test_data_file('test_torrent.file.torrent')
        with open(filename, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = self.core.add_torrent_file(filename, filedump, options)
        torrent = self.core.torrentmanager.torrents[torrent_id]

        # The initial seed-mode check runs asynchronously in libtorrent.
        self.assert_state_wait(torrent, 'Downloading', timeout=10)

        # Force an error by reading (non-existant) piece from disk
        torrent.handle.read_piece(0)
        self.assert_state_wait(torrent, 'Error')

    def test_torrent_error_resume_original_state(self):
        if VersionSplit(lt.__version__) > VersionSplit('2.0.7.0'):
            pytest.xfail('Test not working as expected after lt 2.0.7')
        options = {'seed_mode': True, 'add_paused': True}
        filename = common.get_test_data_file('test_torrent.file.torrent')
        with open(filename, 'rb') as _file:
            filedump = b64encode(_file.read())
        torrent_id = self.core.add_torrent_file(filename, filedump, options)
        torrent = self.core.torrentmanager.torrents[torrent_id]

        orig_state = 'Paused'
        self.assert_state(torrent, orig_state)

        # Force an error by reading (non-existant) piece from disk
        torrent.handle.read_piece(0)
        self.assert_state_wait(torrent, 'Error')

        # Clear error and verify returned to original state
        torrent.force_recheck()

    def test_torrent_error_resume_data_unaltered(self):
        if VersionSplit(lt.__version__) >= VersionSplit('1.2.0.0'):
            pytest.xfail('Test not working as expected on lt 1.2 or greater')

        resume_data = {
            'active_time': 13399,
            'num_incomplete': 16777215,
            'announce_to_lsd': 1,
            'seed_mode': 0,
            'pieces': '\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01',
            'paused': 0,
            'seeding_time': 13399,
            'last_scrape': 13399,
            'info-hash': '-\xc5\xd0\xe7\x1af\xfeid\x9ad\r9\xcb\x00\xa2YpIs',
            'max_uploads': 16777215,
            'max_connections': 16777215,
            'num_downloaders': 16777215,
            'total_downloaded': 0,
            'file-format': 'libtorrent resume file',
            'peers6': '',
            'added_time': 1411826665,
            'banned_peers6': '',
            'file_priority': [1],
            'last_seen_complete': 0,
            'total_uploaded': 0,
            'piece_priority': '\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01',
            'file-version': 1,
            'announce_to_dht': 1,
            'auto_managed': 1,
            'upload_rate_limit': 0,
            'completed_time': 1411826665,
            'allocation': 'sparse',
            'blocks per piece': 2,
            'download_rate_limit': 0,
            'libtorrent-version': '0.16.17.0',
            'banned_peers': '',
            'num_seeds': 16777215,
            'sequential_download': 0,
            'announce_to_trackers': 1,
            'peers': '\n\x00\x02\x0f=\xc6SC\x17]\xd8}\x7f\x00\x00\x01=\xc6',
            'finished_time': 13399,
            'last_upload': 13399,
            'trackers': [[]],
            'super_seeding': 0,
            'file sizes': [[512000, 1411826586]],
            'last_download': 13399,
        }
        torrent_state = TorrentState(
            torrent_id='2dc5d0e71a66fe69649a640d39cb00a259704973',
            filename='test_torrent.file.torrent',
            name='',
            save_path='/home/ubuntu/Downloads',
            file_priorities=[1],
            is_finished=True,
        )

        filename = common.get_test_data_file('test_torrent.file.torrent')
        with open(filename, 'rb') as _file:
            filedump = _file.read()
        resume_data = utf8_encode_structure(resume_data)
        torrent_id = self.core.torrentmanager.add(
            state=torrent_state, filedump=filedump, resume_data=lt.bencode(resume_data)
        )
        torrent = self.core.torrentmanager.torrents[torrent_id]

        def assert_resume_data():
            self.assert_state(torrent, 'Error')
            tm_resume_data = lt.bdecode(
                self.core.torrentmanager.resume_data[torrent.torrent_id]
            )
            assert tm_resume_data == resume_data

        return deferLater(reactor, 0.5, assert_resume_data)

    def test_get_eta_seeding(self):
        atp = self.get_torrent_atp('test_torrent.file.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        assert self.torrent.get_eta() == 0
        self.torrent.status = mock.MagicMock()

        self.torrent.status.upload_payload_rate = 5000
        self.torrent.status.download_payload_rate = 0
        self.torrent.status.all_time_download = 10000
        self.torrent.status.all_time_upload = 500
        self.torrent.is_finished = True
        self.torrent.options = {'stop_at_ratio': False}
        # Test finished and uploading but no stop_at_ratio set.
        assert self.torrent.get_eta() == 0

        self.torrent.options = {'stop_at_ratio': True, 'stop_ratio': 1.5}
        result = self.torrent.get_eta()
        assert result == 2
        assert isinstance(result, int)

    def test_get_eta_downloading(self):
        atp = self.get_torrent_atp('test_torrent.file.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        assert self.torrent.get_eta() == 0

        self.torrent.status = mock.MagicMock()
        self.torrent.status.download_payload_rate = 50
        self.torrent.status.total_wanted = 10000
        self.torrent.status.total_wanted_done = 5000

        result = self.torrent.get_eta()
        assert result == 100
        assert isinstance(result, int)

    def test_get_name_with_empty_file_view(self):
        """A delayed metadata file listing must not break status or removal."""
        torrent = mock.MagicMock()
        torrent.options = {'name': ''}
        torrent.has_metadata = True
        torrent.get_files.return_value = []
        torrent.torrent_id = 'abc123'
        assert Torrent.get_name(torrent) == 'abc123'

    def test_magnet_uri_preserves_hash_and_wss_tracker(self):
        """The ABI 4 make_magnet_uri API requires add_torrent_params."""
        from urllib.parse import unquote

        handle = self.session.add_torrent(self.get_torrent_atp('test.torrent'))
        torrent = Torrent(handle, {})
        tracker_url = 'wss://tracker.example.com/announce'
        handle.add_tracker({'url': tracker_url, 'tier': 1})

        magnet = unquote(torrent.get_magnet_uri())
        assert torrent.torrent_id in magnet
        assert tracker_url in magnet

    def test_get_name_unicode(self):
        """Test retrieving a unicode torrent name from libtorrent."""
        atp = self.get_torrent_atp('unicode_file.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        assert self.torrent.get_name() == 'সুকুমার রায়.txt'

    def test_get_files_normalizes_windows_renamed_paths(self):
        """The native renamed-file view can return Windows separators."""
        paths = (
            'Tears of Steel\\poster.jpg',
            'Tears of Steel\\Tears of Steel.de.srt',
        )
        storage = SimpleNamespace(
            num_files=lambda: len(paths),
            file_path=lambda index: paths[index],
            file_size=lambda index: 100,
            file_offset=lambda index: index * 100,
        )
        renamed_files = SimpleNamespace(file_path=lambda files, index: paths[index])
        torrent = SimpleNamespace(
            has_metadata=True,
            torrent_info=SimpleNamespace(layout=lambda: storage),
            handle=SimpleNamespace(get_renamed_files=lambda: renamed_files),
            options={'mapped_files': {}},
        )

        assert [item['path'] for item in Torrent.get_files(torrent)] == [
            'Tears of Steel/poster.jpg',
            'Tears of Steel/Tears of Steel.de.srt',
        ]

    def test_get_files_with_mapped_names(self):
        atp = self.get_torrent_atp('dir_with_6_files.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {'mapped_files': {0: 'renamed_file'}})

        assert self.torrent.get_files()[0]['path'] == 'renamed_file'
        assert self.torrent.get_orig_files()[0]['path'] != 'renamed_file'

    def test_rename_unicode(self):
        """Test renaming file/folders with unicode filenames."""
        atp = self.get_torrent_atp('unicode_filenames.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        # Ignore TorrentManager method call
        TorrentManager.save_resume_data = AsyncMock()

        result = self.torrent.rename_folder('unicode_filenames', 'Горбачёв')
        assert isinstance(result, defer.DeferredList)

        result = self.torrent.rename_files([[0, 'new_рбачёв']])
        assert result is None

    def test_connect_peer_port(self):
        """Test to ensure port is int for libtorrent"""
        atp = self.get_torrent_atp('test_torrent.file.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        assert not self.torrent.connect_peer('127.0.0.1', 'text')
        assert self.torrent.connect_peer('127.0.0.1', '1234')

    def test_status_cache(self):
        atp = self.get_torrent_atp('test_torrent.file.torrent')
        handle = self.session.add_torrent(atp)
        mock_time = mock.Mock(return_value=time.time())
        with mock.patch('time.time', mock_time):
            torrent = Torrent(handle, {})
            counter = itertools.count()
            handle.status = mock.Mock(side_effect=counter.__next__)
            first_status = torrent.get_lt_status()
            assert first_status == 0, 'sanity check'
            assert first_status == torrent.status, 'cached status should be used'
            assert torrent.get_lt_status() == 1, 'status should update'
            assert torrent.status == 1
            # Advance time and verify cache expires and updates
            mock_time.return_value += 10
            assert torrent.status == 2
