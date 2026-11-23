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

from deluge import component
from deluge.bencode import bencode
from deluge.conftest import BaseTestCase
from deluge.core import torrentmanager
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

    def test_update_posts_torrent_updates(self):
        """The periodic update must refresh the status cache itself.

        Nothing else calls post_torrent_updates() when no client is polling, so
        without this the cached status would never refresh and daemon-side
        consumers such as the stop_at_ratio check would read stale values.
        """
        with mock.patch.object(self.tm.session, 'post_torrent_updates') as post:
            self.tm.update()

        post.assert_called_once_with()

    def test_on_alert_state_update_without_pending_request(self):
        """A state_update_alert with no client request queued must not raise."""
        self.tm.torrents_status_requests = []

        self.tm.on_alert_state_update(mock.Mock(status=[]))

    @pytest_twisted.inlineCallbacks
    def test_update_refreshes_a_bounded_rotating_slice(self):
        """Idle torrents are reported by state_update_alert once and never again.

        Refreshing every torrent to compensate is what pegged the reactor thread,
        so update() refreshes a fixed-size slice per tick and rotates through the
        rest on later ticks. The cost stays constant as the torrent count grows.
        """
        slice_size = torrentmanager.STATUS_REFRESH_PER_TICK
        fake_torrents = {
            f'torrent{i}': mock.Mock(options={'stop_at_ratio': False})
            for i in range(slice_size * 2)
        }

        def refreshed():
            return {
                tid
                for tid, torrent in fake_torrents.items()
                if torrent.get_lt_status.called
            }

        with mock.patch.dict(self.tm.torrents, fake_torrents, clear=True):
            with mock.patch.object(self.tm.session, 'post_torrent_updates'):
                yield self.tm.refresh_status_slice()
                first = refreshed()
                for torrent in fake_torrents.values():
                    torrent.get_lt_status.reset_mock()
                yield self.tm.refresh_status_slice()
                second = refreshed()

        assert first, 'each tick should make progress'
        assert second, 'each tick should make progress'
        assert len(first) <= slice_size, 'never more than the per-tick cap'
        assert len(second) <= slice_size, 'never more than the per-tick cap'
        assert not first & second, 'consecutive ticks should refresh different torrents'

    @pytest_twisted.inlineCallbacks
    def test_refresh_status_slice_runs_off_the_reactor(self):
        """A contended handle.status() can block for hundreds of milliseconds.

        Bounding the slice by count, then by time, both failed: a single call is
        already too expensive to make on the reactor thread at 3 Gbps. It has to
        run in a thread like the resume-data scan does.
        """
        reactor_thread = threading.get_ident()
        refresh_threads = []

        def get_lt_status():
            refresh_threads.append(threading.get_ident())

        fake_torrents = {}
        for i in range(torrentmanager.STATUS_REFRESH_PER_TICK):
            t = mock.Mock(options={'stop_at_ratio': False})
            t.get_lt_status.side_effect = get_lt_status
            fake_torrents[f'torrent{i}'] = t

        with mock.patch.dict(self.tm.torrents, fake_torrents, clear=True):
            yield self.tm.refresh_status_slice()

        assert refresh_threads, 'refresh never ran'
        assert reactor_thread not in refresh_threads, (
            'the refresh must not run on the reactor thread'
        )

    @pytest_twisted.inlineCallbacks
    def test_save_resume_data_scan_runs_off_the_reactor(self):
        """need_save_resume_data() takes libtorrent's session mutex.

        Scanning ~900 torrents for it on the reactor thread was measured blocking
        the daemon for 40-110 seconds at a time during a 3 Gbps download.
        """
        reactor_thread = threading.get_ident()
        scan_threads = []

        def need_save_resume_data():
            scan_threads.append(threading.get_ident())
            return False

        fake = mock.Mock()
        fake.handle.need_save_resume_data.side_effect = need_save_resume_data

        with mock.patch.dict(self.tm.torrents, {'faketorrent': fake}, clear=True):
            yield self.tm.save_resume_data()

        assert scan_threads, 'need_save_resume_data was never consulted'
        assert reactor_thread not in scan_threads, (
            'the scan must not run on the reactor thread'
        )

    @pytest.mark.timeout(30)
    @pytest_twisted.inlineCallbacks
    def test_save_resume_data_survives_torrent_removed_during_scan(self):
        """A torrent removed while the off-thread scan runs must not abort the save.

        save_resume_data() snapshots the torrent ids off-thread, which yields to
        the reactor for the length of the scan. A remove landing in that window
        leaves a stale id, and indexing self.torrents with it raised KeyError out
        of the coroutine driving save_resume_data_timer, stopping the LoopingCall
        for the rest of the process lifetime.
        """
        stale_id = '0' * 40
        self.tm._torrents_needing_resume_data = lambda torrent_ids: [stale_id]

        yield self.tm.save_resume_data()

    @pytest.mark.timeout(30)
    @pytest_twisted.inlineCallbacks
    def test_save_resume_data_leaves_no_stranded_waiting_entry(self):
        """A stale id must not leave an entry in waiting_on_resume_data.

        The entry is inserted before the torrent lookup, so a stale id strands a
        Deferred that no alert can ever fire. on_all_resume_data_finished gates
        on this dict being empty, so one stranded entry stops every future
        fastresume write, not just the periodic timer.
        """
        stale_id = '0' * 40
        self.tm._torrents_needing_resume_data = lambda torrent_ids: [stale_id]

        yield self.tm.save_resume_data()

        assert stale_id not in self.tm.waiting_on_resume_data

    @pytest.mark.timeout(30)
    @pytest_twisted.inlineCallbacks
    def test_save_resume_data_still_saves_live_torrents_alongside_stale_id(self):
        """Skipping a stale id must not skip torrents that are still present."""
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            filedump = _file.read()
        torrent_id = yield self.core.add_torrent_file_async(
            filename, b64encode(filedump), {}
        )
        torrent = self.tm.torrents[torrent_id]
        stale_id = '0' * 40
        self.tm._torrents_needing_resume_data = lambda ids: [stale_id, torrent_id]

        # wraps, not a bare mock: the real call must still reach libtorrent or
        # the resume alert never fires and the DeferredList never completes.
        with mock.patch.object(
            torrent, 'save_resume_data', wraps=torrent.save_resume_data
        ) as spy:
            yield self.tm.save_resume_data()

        assert spy.call_count == 1
