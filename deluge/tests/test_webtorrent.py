"""WSS tracker integration for Deluge's WebTorrent-enabled libtorrent session."""

import hashlib
import tempfile
import threading
from base64 import b64encode
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
import pytest_twisted
from twisted.internet import defer, reactor, task

import deluge.component as component
from deluge.conftest import BaseTestCase
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.tests.webtorrent_tracker import RelayWssTracker


@pytest.mark.internet
class TestWebTorrent(BaseTestCase):
    def set_up(self):
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.core.config.config['lsd'] = False
        return component.start()

    def tear_down(self):
        def cleanup(result):
            del self.rpcserver
            del self.core
            return result

        return component.shutdown().addCallback(cleanup)

    def test_current_metadata_writer_preserves_info_hash_and_wss_tracker(self):
        """Saving received metadata must preserve its original hash and tracker."""
        from deluge._libtorrent import lt
        from deluge.core.torrent import Torrent
        from deluge.tests import common

        params = lt.load_torrent_buffer(
            Path(common.get_test_data_file('test.torrent')).read_bytes()
        )
        info_hash = str(params.ti.info_hash())
        tracker = 'wss://tracker.example.com/announce'
        fake_handle = SimpleNamespace(
            trackers=lambda: [{'url': tracker, 'tier': 0}],
            url_seeds=lambda: [],
        )
        torrent = SimpleNamespace(
            torrent_id=info_hash,
            torrent_info=params.ti,
            handle=fake_handle,
            config={'copy_torrent_file': False},
        )
        state = Path(self.config_dir) / 'state'
        state.mkdir(exist_ok=True)
        Torrent.write_torrentfile(torrent)

        saved = lt.load_torrent_buffer((state / f'{info_hash}.torrent').read_bytes())
        assert str(saved.ti.info_hash()) == info_hash
        assert saved.trackers == [tracker]

    @pytest.mark.parametrize('async_add', [False, True])
    @pytest_twisted.inlineCallbacks
    def test_torrent_file_add_preserves_wss_trackers(self, async_add):
        """Torrent-file imports retain the WSS trackers from their announce list."""
        from deluge._libtorrent import lt

        with tempfile.TemporaryDirectory() as directory:
            payload = b'webtorrent tracker retention'
            creator = lt.create_torrent(
                [lt.create_file_entry('tracker-retention.bin', len(payload))],
                16384,
                lt.create_torrent.v1_only,
            )
            creator.set_hash(0, hashlib.sha1(payload).digest())
            tracker_url = 'wss://127.0.0.1:1/announce'
            creator.add_tracker(tracker_url)
            filedump = b64encode(lt.bencode(creator.generate()))
            options = {
                'download_location': directory,
                'add_paused': True,
                'auto_managed': False,
            }

            if async_add:
                torrent_id = yield self.core.add_torrent_file_async(
                    'tracker-retention.torrent', filedump, options
                )
            else:
                torrent_id = self.core.add_torrent_file(
                    'tracker-retention.torrent', filedump, options
                )

            try:
                manager = self.core.torrentmanager
                handle = manager.torrents[torrent_id].handle
                assert tracker_url in [entry['url'] for entry in handle.trackers()]

                # On restart, loading torrent_info alone drops its trackers
                # in ABI 4. Ensure the original torrent bytes are reloaded.
                state = manager.create_state()
                with (
                    mock.patch.object(manager, 'open_state', return_value=state),
                    mock.patch.object(
                        manager, 'load_resume_data_file', return_value={}
                    ),
                    mock.patch.object(
                        manager, 'add_async', return_value=defer.succeed(torrent_id)
                    ) as add_async,
                ):
                    manager.load_state()
                restored = add_async.call_args.kwargs['filedump']
                assert tracker_url in lt.load_torrent_buffer(restored).trackers
            finally:
                self.core.remove_torrent(torrent_id, remove_data=False)

    def test_webtorrent_stun_preference(self):
        prefs = component.get('PreferencesManager')
        key = 'webtorrent_stun_server'
        initial = self.core.session.get_settings()
        assert key in initial

        value = 'stun.example.com:3478'
        try:
            prefs.do_config_set_func(key, value)
            assert self.core.session.get_settings()[key] == value
        finally:
            prefs.do_config_set_func(key, initial[key])

    @pytest_twisted.inlineCallbacks
    def test_wss_rtc_peer_visible_between_two_leechers(self):
        """Two incomplete RTC clients must expose their connected peers."""
        from deluge._libtorrent import lt

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed_dir = root / 'seed'
            download_dir = root / 'download'
            seed_dir.mkdir()
            download_dir.mkdir()
            filename = 'rtc-peers.bin'
            payload = bytes(range(256)) * 64
            # Neither client starts with the file. Both are genuine
            # leechers requesting pieces, avoiding an instantaneous transfer.
            tracker = RelayWssTracker(directory)
            tracker.start()
            seeder = None
            torrent_id = None
            try:
                tracker_url = f'wss://127.0.0.1:{tracker.port}/announce'
                creator = lt.create_torrent(
                    [lt.create_file_entry(filename, len(payload))],
                    16384,
                    lt.create_torrent.v1_only,
                )
                creator.set_hash(0, hashlib.sha1(payload).digest())
                creator.add_tracker(tracker_url)
                torrent_bytes = lt.bencode(creator.generate())

                settings = {
                    'enable_dht': False,
                    'enable_lsd': False,
                    'enable_upnp': False,
                    'enable_natpmp': False,
                    'validate_https_trackers': False,
                    'webtorrent_stun_server': '',
                }
                self.core.apply_session_settings(settings)
                seeder = lt.session({**settings, 'listen_interfaces': '127.0.0.1:0'})
                seed_params = lt.load_torrent_buffer(torrent_bytes)
                seed_params.save_path = str(seed_dir)
                seed_params.flags &= ~lt.torrent_flags.paused
                seed_params.flags &= ~lt.torrent_flags.auto_managed
                seed_handle = seeder.add_torrent(seed_params)
                assert not seed_handle.status().is_seeding

                # Both peers want the file but neither currently has pieces.
                # The real WSS/RTC connection can be inspected without racing
                # a completed loopback transfer or inserting fabricated peers.
                torrent_id = yield self.core.add_torrent_file_async(
                    'rtc-peers.torrent',
                    b64encode(torrent_bytes),
                    {
                        'download_location': str(download_dir),
                        'add_paused': True,
                        'auto_managed': False,
                    },
                )
                handle = self.core.torrentmanager.torrents[torrent_id].handle
                assert handle.get_file_priorities()[0] > 0
                self.core.resume_torrent(torrent_id)
                handle.force_reannounce()

                deadline = reactor.seconds() + 90
                next_announce = reactor.seconds() + 12
                max_native_peers = 0
                max_aggregate_peers = 0
                visible_peers = []
                while reactor.seconds() < deadline:
                    native_peers = handle.get_peer_info()
                    status = self.core.get_torrent_status(torrent_id, ['peers'])
                    max_native_peers = max(max_native_peers, len(native_peers))
                    max_aggregate_peers = max(
                        max_aggregate_peers, handle.status().num_peers
                    )
                    visible_peers = status['peers']
                    if visible_peers:
                        break
                    if reactor.seconds() >= next_announce:
                        handle.force_reannounce()
                        next_announce = reactor.seconds() + 12
                    yield task.deferLater(reactor, 0.1, lambda: None)

                assert visible_peers, (
                    'Live WSS/RTC leecher was not exposed through Deluge Peers API '
                    f'(native_peers={max_native_peers}, '
                    f'aggregate_peers={max_aggregate_peers}, '
                    f'offers={tracker.offers_relayed}, '
                    f'answers={tracker.answers_relayed})'
                )
                assert visible_peers[0]['ip']
                assert isinstance(visible_peers[0]['client'], str)
                assert handle.status().total_payload_download == 0
            finally:
                if torrent_id is not None:
                    self.core.remove_torrent(torrent_id, remove_data=False)
                if seeder is not None:
                    seeder.pause()
                tracker.stop()

    @pytest_twisted.inlineCallbacks
    def test_wss_discovers_rtc_peer_and_transfers_verified_pieces(self):
        """Download payload from a WSS-discovered RTC seeder into Deluge."""
        from deluge._libtorrent import lt

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed_dir = root / 'seed'
            download_dir = root / 'download'
            seed_dir.mkdir()
            download_dir.mkdir()
            filename = 'rtc-payload.bin'
            payload = bytes(range(256)) * 192
            (seed_dir / filename).write_bytes(payload)

            tracker = RelayWssTracker(directory)
            tracker.start()
            seeder = None
            try:
                tracker_url = f'wss://127.0.0.1:{tracker.port}/announce'
                piece_size = 16384
                creator = lt.create_torrent(
                    [lt.create_file_entry(filename, len(payload))],
                    piece_size,
                    lt.create_torrent.v1_only,
                )
                for index in range(creator.num_pieces()):
                    start = index * piece_size
                    creator.set_hash(
                        index,
                        hashlib.sha1(payload[start : start + piece_size]).digest(),
                    )
                creator.add_tracker(tracker_url)
                torrent_bytes = lt.bencode(creator.generate())

                settings = {
                    'enable_dht': False,
                    'enable_lsd': False,
                    'enable_upnp': False,
                    'enable_natpmp': False,
                    'validate_https_trackers': False,
                    'webtorrent_stun_server': '',
                }
                self.core.apply_session_settings(settings)

                seeder = lt.session(
                    {
                        **settings,
                        'listen_interfaces': '127.0.0.1:0',
                    }
                )
                seed_params = lt.load_torrent_buffer(torrent_bytes)
                seed_params.save_path = str(seed_dir)
                seed_params.flags &= ~lt.torrent_flags.paused
                seed_params.flags &= ~lt.torrent_flags.auto_managed
                seed_handle = seeder.add_torrent(seed_params)

                deadline = reactor.seconds() + 15
                while (
                    not seed_handle.status().is_seeding and reactor.seconds() < deadline
                ):
                    yield task.deferLater(reactor, 0.2, lambda: None)
                assert seed_handle.status().is_seeding, (
                    'RTC seeder did not hash its file'
                )

                # This exercises both RTC metadata exchange and piece
                # transfer, with WSS as the only peer discovery mechanism.
                magnet = (
                    f'magnet:?xt=urn:btih:{seed_params.ti.info_hash()}'
                    f'&tr=wss%3A%2F%2F127.0.0.1%3A{tracker.port}%2Fannounce'
                )
                torrent_id = yield self.core.add_torrent_magnet(
                    magnet,
                    {
                        'download_location': str(download_dir),
                        'add_paused': True,
                        'auto_managed': False,
                    },
                )
                assert torrent_id
                download_handle = self.core.torrentmanager.torrents[torrent_id].handle
                assert any(
                    entry['url'] == tracker_url for entry in download_handle.trackers()
                ), 'Deluge did not retain the WSS tracker from the torrent file'
                # Exercise the real Deluge RPC-facing pause status. A magnet
                # added paused must not transfer metadata or payload until
                # explicitly resumed, even when the WSS seeder is available.
                paused_status = self.core.get_torrent_status(
                    torrent_id,
                    ['paused', 'num_peers', 'num_seeds', 'total_payload_download'],
                )
                assert paused_status['paused'], paused_status
                paused_downloaded = paused_status['total_payload_download']
                yield task.deferLater(reactor, 1.0, lambda: None)
                paused_again = self.core.get_torrent_status(
                    torrent_id, ['paused', 'total_payload_download']
                )
                assert paused_again['paused'], paused_again
                assert paused_again['total_payload_download'] == paused_downloaded, (
                    'Payload was transferred while the torrent was paused'
                )

                self.core.resume_torrent(torrent_id)
                download_handle.force_reannounce()

                deadline = reactor.seconds() + 90
                next_announce = reactor.seconds() + 12
                while reactor.seconds() < deadline:
                    if download_handle.status().is_seeding:
                        break
                    if reactor.seconds() >= next_announce:
                        # RTC negotiations can fail transiently on CI runners;
                        # reannounce to exercise fresh offers without allowing
                        # any fallback transport or weakening payload checks.
                        download_handle.force_reannounce()
                        next_announce = reactor.seconds() + 12
                    yield task.deferLater(reactor, 0.2, lambda: None)

                target = download_dir / filename
                assert tracker.offers_relayed > 0, (
                    'No offer crossed the WSS tracker '
                    f'(answers={tracker.answers_relayed}, '
                    f'seeder={seed_handle.status().is_seeding}, '
                    f'download_status={download_handle.status().state}, '
                    f'download_paused={bool(download_handle.status().flags & lt.torrent_flags.paused)}, '
                    f'download_error={download_handle.status().errc.message()}, '
                    f'trackers={download_handle.trackers()})'
                )
                assert tracker.answers_relayed > 0, 'No answer crossed the WSS tracker'
                assert download_handle.status().is_seeding, (
                    'No completed RTC payload transfer '
                    f'(offers={tracker.offers_relayed}, '
                    f'answers={tracker.answers_relayed}, '
                    f'progress={download_handle.status().progress}, '
                    f'download_peers={download_handle.status().num_peers}, '
                    f'seed_peers={seed_handle.status().num_peers}, '
                    f'download_state={download_handle.status().state}, '
                    f'download_error={download_handle.status().errc.message()})'
                )
                # A torrent can reach the seeding state while its disk writes
                # are still cached. Verify on-disk bytes only after libtorrent
                # confirms that the cache was flushed.
                cache_flushed = threading.Event()

                def on_cache_flushed(alert):
                    if alert.handle == download_handle:
                        cache_flushed.set()

                self.core.alertmanager.register_handler(
                    'cache_flushed_alert', on_cache_flushed
                )
                try:
                    download_handle.flush_cache()
                    flush_deadline = reactor.seconds() + 30
                    while (
                        not cache_flushed.is_set()
                        and reactor.seconds() < flush_deadline
                    ):
                        yield task.deferLater(reactor, 0.1, lambda: None)
                    assert cache_flushed.is_set(), (
                        'Timed out waiting for native cache_flushed_alert'
                    )
                finally:
                    self.core.alertmanager.deregister_handler(on_cache_flushed)

                assert target.read_bytes() == payload, (
                    'The RTC payload on disk differs after cache_flushed_alert'
                )
                # Peer visibility is asserted in the separate real-connection
                # test above; this transfer can complete between UI polls.

                # Verify the status shape consumed by the Files and Peers
                # tabs, not only the raw native torrent_handle state.
                deluge_status = self.core.get_torrent_status(
                    torrent_id,
                    [
                        'files',
                        'file_progress',
                        'file_priorities',
                        'num_files',
                        'num_peers',
                        'num_seeds',
                        'peers',
                        'progress',
                        'paused',
                    ],
                )
                assert deluge_status['num_files'] == 1, deluge_status
                assert len(deluge_status['files']) == 1, deluge_status
                assert deluge_status['files'][0]['path'].endswith(filename), (
                    deluge_status
                )
                assert len(deluge_status['file_progress']) == 1, deluge_status
                assert deluge_status['file_progress'][0] == 1.0, deluge_status
                assert not deluge_status['paused'], deluge_status
                assert deluge_status['progress'] == 100, deluge_status
                assert isinstance(deluge_status['peers'], list), deluge_status
                assert deluge_status['num_peers'] >= 0
                assert deluge_status['num_seeds'] >= 0

                saved = Path(self.config_dir) / 'state' / f'{torrent_id}.torrent'
                assert saved.is_file(), (
                    'Received metadata was not saved as a torrent file'
                )
                saved_params = lt.load_torrent_buffer(saved.read_bytes())
                assert str(saved_params.ti.info_hash()) == torrent_id
                assert tracker_url in saved_params.trackers
            finally:
                if seeder is not None:
                    seeder.pause()
                tracker.stop()
