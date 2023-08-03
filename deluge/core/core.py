#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import glob
import logging
import os
import shutil
import tempfile
from base64 import b64decode, b64encode
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.request import URLError, urlopen

from twisted.internet import defer, reactor, task, threads
from twisted.web.client import Agent, readBody

import deluge.common
import deluge.component as component
from deluge import metafile, path_chooser_common
from deluge._libtorrent import LT_VERSION, lt
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.core.alertmanager import AlertManager
from deluge.core.authmanager import (
    AUTH_LEVEL_ADMIN,
    AUTH_LEVEL_NONE,
    AUTH_LEVELS_MAPPING,
    AUTH_LEVELS_MAPPING_REVERSE,
    AuthManager,
)
from deluge.core.eventmanager import EventManager
from deluge.core.filtermanager import FilterManager
from deluge.core.pluginmanager import PluginManager
from deluge.core.preferencesmanager import PreferencesManager
from deluge.core.rpcserver import export
from deluge.core.torrentmanager import TorrentManager
from deluge.decorators import deprecated, maybe_coroutine
from deluge.error import (
    AddTorrentError,
    DelugeError,
    InvalidPathError,
    InvalidTorrentError,
)
from deluge.event import (
    NewVersionAvailableEvent,
    SessionPausedEvent,
    SessionResumedEvent,
    TorrentQueueChangedEvent,
)
from deluge.httpdownloader import download_file

log = logging.getLogger(__name__)

DEPR_SESSION_STATUS_KEYS = {
    # 'active_requests': None, # In dht_stats_alert, if required.
    'allowed_upload_slots': 'ses.num_unchoke_slots',
    # 'dht_global_nodes': None,
    'dht_node_cache': 'dht.dht_node_cache',
    'dht_nodes': 'dht.dht_nodes',
    'dht_torrents': 'dht.dht_torrents',
    # 'dht_total_allocations': None,
    'down_bandwidth_bytes_queue': 'net.limiter_down_bytes',
    'down_bandwidth_queue': 'net.limiter_down_queue',
    'has_incoming_connections': 'net.has_incoming_connections',
    'num_peers': 'peer.num_peers_connected',
    'num_unchoked': 'peer.num_peers_up_unchoked',
    # 'optimistic_unchoke_counter': None, # lt.settings_pack
    'total_dht_download': 'dht.dht_bytes_in',
    'total_dht_upload': 'dht.dht_bytes_out',
    'total_download': 'net.recv_bytes',
    'total_failed_bytes': 'net.recv_failed_bytes',
    'total_ip_overhead_download': 'net.recv_ip_overhead_bytes',
    'total_ip_overhead_upload': 'net.sent_ip_overhead_bytes',
    'total_payload_download': 'net.recv_payload_bytes',
    'total_payload_upload': 'net.sent_payload_bytes',
    'total_redundant_bytes': 'net.recv_redundant_bytes',
    'total_tracker_download': 'net.recv_tracker_bytes',
    'total_tracker_upload': 'net.sent_tracker_bytes',
    'total_upload': 'net.sent_bytes',
    # 'unchoke_counter': None, # lt.settings_pack
    'up_bandwidth_bytes_queue': 'net.limiter_up_bytes',
    'up_bandwidth_queue': 'net.limiter_up_queue',
    # 'utp_stats': None
}

# Session status rate keys associated with session status counters.
SESSION_RATES_MAPPING = {
    'dht_download_rate': 'dht.dht_bytes_in',
    'dht_upload_rate': 'dht.dht_bytes_out',
    'ip_overhead_download_rate': 'net.recv_ip_overhead_bytes',
    'ip_overhead_upload_rate': 'net.sent_ip_overhead_bytes',
    'payload_download_rate': 'net.recv_payload_bytes',
    'payload_upload_rate': 'net.sent_payload_bytes',
    'tracker_download_rate': 'net.recv_tracker_bytes',
    'tracker_upload_rate': 'net.sent_tracker_bytes',
    'download_rate': 'net.recv_bytes',
    'upload_rate': 'net.sent_bytes',
}

DELUGE_VER = deluge.common.get_version()


class Core(component.Component):
    def __init__(
        self, listen_interface=None, outgoing_interface=None, read_only_config_keys=None
    ):
        component.Component.__init__(self, 'Core')

        # Start the libtorrent session.
        user_agent = f'Deluge/{DELUGE_VER} libtorrent/{LT_VERSION}'
        peer_id = self._create_peer_id(DELUGE_VER)
        log.debug('Starting session (peer_id: %s, user_agent: %s)', peer_id, user_agent)
        settings_pack = {
            'peer_fingerprint': peer_id,
            'user_agent': user_agent,
            'ignore_resume_timestamps': True,
        }
        self.session = lt.session(settings_pack, flags=0)

        # Load the settings, if available.
        self._load_session_state()

        # Enable libtorrent extensions
        # Allows peers to download the metadata from the swarm directly
        self.session.add_extension('ut_metadata')
        # Ban peers that sends bad data
        self.session.add_extension('smart_ban')

        # Create the components
        self.eventmanager = EventManager()
        self.preferencesmanager = PreferencesManager()
        self.alertmanager = AlertManager()
        self.pluginmanager = PluginManager(self)
        self.torrentmanager = TorrentManager()
        self.filtermanager = FilterManager(self)
        self.authmanager = AuthManager()

        # New release check information
        self.new_release = None

        # External IP Address from libtorrent
        self.external_ip = None
        self.eventmanager.register_event_handler(
            'ExternalIPEvent', self._on_external_ip_event
        )

        # GeoIP instance with db loaded
        self.geoip_instance = None

        # These keys will be dropped from the set_config() RPC and are
        # configurable from the command-line.
        self.read_only_config_keys = read_only_config_keys
        log.debug('read_only_config_keys: %s', read_only_config_keys)

        # Get the core config
        self.config = ConfigManager('core.conf')
        self.config.save()

        # If there was an interface value from the command line, use it, but
        # store the one in the config so we can restore it on shutdown
        self._old_listen_interface = None
        if listen_interface:
            if deluge.common.is_interface(listen_interface):
                self._old_listen_interface = self.config['listen_interface']
                self.config['listen_interface'] = listen_interface
            else:
                log.error(
                    'Invalid listen interface (must be IP Address or Interface Name): %s',
                    listen_interface,
                )

        self._old_outgoing_interface = None
        if outgoing_interface:
            if deluge.common.is_interface(outgoing_interface):
                self._old_outgoing_interface = self.config['outgoing_interface']
                self.config['outgoing_interface'] = outgoing_interface
            else:
                log.error(
                    'Invalid outgoing interface (must be IP Address or Interface Name): %s',
                    outgoing_interface,
                )

        # New release check information
        self.__new_release = None

        # Session status timer
        self.session_status = {k.name: 0 for k in lt.session_stats_metrics()}
        self._session_prev_bytes = {k: 0 for k in SESSION_RATES_MAPPING}
        # Initiate other session status keys.
        self.session_status.update(self._session_prev_bytes)
        hit_ratio_keys = ['write_hit_ratio', 'read_hit_ratio']
        self.session_status.update({k: 0.0 for k in hit_ratio_keys})

        self.session_status_timer_interval = 0.5
        self.session_status_timer = task.LoopingCall(self.session.post_session_stats)
        self.alertmanager.register_handler(
            'session_stats', self._on_alert_session_stats
        )
        self.session_rates_timer_interval = 2
        self.session_rates_timer = task.LoopingCall(self._update_session_rates)

    def start(self):
        """Starts the core"""
        self.session_status_timer.start(self.session_status_timer_interval)
        self.session_rates_timer.start(self.session_rates_timer_interval, now=False)

    def stop(self):
        log.debug('Core stopping...')

        if self.session_status_timer.running:
            self.session_status_timer.stop()

        if self.session_rates_timer.running:
            self.session_rates_timer.stop()

        # Save the libtorrent session state
        self._save_session_state()

        # We stored a copy of the old interface value
        if self._old_listen_interface is not None:
            self.config['listen_interface'] = self._old_listen_interface

        if self._old_outgoing_interface is not None:
            self.config['outgoing_interface'] = self._old_outgoing_interface

        # Make sure the config file has been saved
        self.config.save()

    def shutdown(self):
        pass

    def apply_session_setting(self, key, value):
        self.apply_session_settings({key: value})

    def apply_session_settings(self, settings):
        """Apply libtorrent session settings.

        Args:
            settings: A dict of lt session settings to apply.
        """
        self.session.apply_settings(settings)

    @staticmethod
    def _create_peer_id(version: str) -> str:
        """Create a peer_id fingerprint.

        This creates the peer_id and modifies the release char to identify
        pre-release and development version. Using ``D`` for dev, daily or
        nightly builds, ``a, b, r`` for pre-releases and ``s`` for
        stable releases.

        Examples:
            ``--<client><client><major><minor><micro><release>--``
            ``--DE200D--`` (development version of 2.0.0)
            ``--DE200s--`` (stable release of v2.0.0)
            ``--DE201b--`` (beta pre-release of v2.0.1)

        Args:
            version: The version string in PEP440 dotted notation.

        Returns:
            The formatted peer_id with Deluge prefix e.g. '--DE200s--'
        """
        split = deluge.common.VersionSplit(version)
        # Fill list with zeros to length of 4 and use lt to create fingerprint.
        version_list = split.version + [0] * (4 - len(split.version))
        peer_id = lt.generate_fingerprint('DE', *version_list)

        def substitute_chr(string, idx, char):
            """Fast substitute single char in string."""
            return string[:idx] + char + string[idx + 1 :]

        if split.dev:
            release_chr = 'D'
        elif split.suffix:
            # a (alpha), b (beta) or r (release candidate).
            release_chr = split.suffix[0].lower()
        else:
            release_chr = 's'
        peer_id = substitute_chr(peer_id, 6, release_chr)

        return peer_id

    def _save_session_state(self):
        """Saves the libtorrent session state"""
        filename = 'session.state'
        filepath = get_config_dir(filename)
        filepath_bak = filepath + '.bak'
        filepath_tmp = filepath + '.tmp'

        try:
            if os.path.isfile(filepath):
                log.debug('Creating backup of %s at: %s', filename, filepath_bak)
                shutil.copy2(filepath, filepath_bak)
        except OSError as ex:
            log.error('Unable to backup %s to %s: %s', filepath, filepath_bak, ex)
        else:
            log.info('Saving the %s at: %s', filename, filepath)
            try:
                with open(filepath_tmp, 'wb') as _file:
                    _file.write(lt.bencode(self.session.save_state()))
                    _file.flush()
                    os.fsync(_file.fileno())
                shutil.move(filepath_tmp, filepath)
            except (OSError, EOFError) as ex:
                log.error('Unable to save %s: %s', filename, ex)
                if os.path.isfile(filepath_bak):
                    log.info('Restoring backup of %s from: %s', filename, filepath_bak)
                    shutil.move(filepath_bak, filepath)

    def _load_session_state(self) -> dict:
        """Loads the libtorrent session state

        Returns:
            A libtorrent sesion state, empty dict if unable to load it.
        """
        filename = 'session.state'
        filepath = get_config_dir(filename)
        filepath_bak = filepath + '.bak'

        for _filepath in (filepath, filepath_bak):
            log.debug('Opening %s for load: %s', filename, _filepath)
            try:
                with open(_filepath, 'rb') as _file:
                    state = lt.bdecode(_file.read())
            except (OSError, EOFError, RuntimeError) as ex:
                log.warning('Unable to load %s: %s', _filepath, ex)
            else:
                log.info('Successfully loaded %s: %s', filename, _filepath)
                self.session.load_state(state)

    def _on_alert_session_stats(self, alert):
        """The handler for libtorrent session stats alert"""
        self.session_status.update(alert.values)
        self._update_session_cache_hit_ratio()

    def _update_session_cache_hit_ratio(self):
        """Calculates the cache read/write hit ratios for session_status."""
        blocks_written = self.session_status['disk.num_blocks_written']
        blocks_read = self.session_status['disk.num_blocks_read']

        if blocks_written:
            self.session_status['write_hit_ratio'] = (
                blocks_written - self.session_status['disk.num_write_ops']
            ) / blocks_written
        else:
            self.session_status['write_hit_ratio'] = 0.0

        if blocks_read:
            self.session_status['read_hit_ratio'] = (
                blocks_read - self.session_status['disk.num_read_ops']
            ) / blocks_read
        else:
            self.session_status['read_hit_ratio'] = 0.0

    def _update_session_rates(self):
        """Calculate session status rates.

        Uses polling interval and counter difference for session_status rates.
        """
        for rate_key, prev_bytes in list(self._session_prev_bytes.items()):
            new_bytes = self.session_status[SESSION_RATES_MAPPING[rate_key]]
            self.session_status[rate_key] = (
                new_bytes - prev_bytes
            ) / self.session_rates_timer_interval
            # Store current value for next update.
            self._session_prev_bytes[rate_key] = new_bytes

    def get_new_release(self):
        log.debug('get_new_release')
        try:
            self.new_release = (
                urlopen('http://download.deluge-torrent.org/version-2.0')
                .read()
                .decode()
                .strip()
            )
        except URLError as ex:
            log.debug('Unable to get release info from website: %s', ex)
        else:
            self.check_new_release()

    def check_new_release(self):
        if self.new_release:
            log.debug('new_release: %s', self.new_release)
            if deluge.common.VersionSplit(
                self.new_release
            ) > deluge.common.VersionSplit(deluge.common.get_version()):
                component.get('EventManager').emit(
                    NewVersionAvailableEvent(self.new_release)
                )
                return self.new_release
        return False

    # Exported Methods
    @export
    def add_torrent_file_async(
        self, filename: str, filedump: str, options: dict, save_state: bool = True
    ) -> 'defer.Deferred[Optional[str]]':
        """Adds a torrent file to the session asynchronously.

        Args:
            filename: The filename of the torrent.
            filedump: A base64 encoded string of torrent file contents.
            options: The options to apply to the torrent upon adding.
            save_state: If the state should be saved after adding the file.

        Returns:
            The torrent ID or None.
        """
        try:
            filedump = b64decode(filedump)
        except TypeError as ex:
            log.error('There was an error decoding the filedump string: %s', ex)

        try:
            d = self.torrentmanager.add_async(
                filedump=filedump,
                options=options,
                filename=filename,
                save_state=save_state,
            )
        except RuntimeError as ex:
            log.error('There was an error adding the torrent file %s: %s', filename, ex)
            raise
        else:
            return d

    @export
    @maybe_coroutine
    async def prefetch_magnet_metadata(
        self, magnet: str, timeout: int = 30
    ) -> Tuple[str, bytes]:
        """Download magnet metadata without adding to Deluge session.

        Used by UIs to get magnet files for selection before adding to session.

        The metadata is bencoded and for transfer base64 encoded.

        Args:
            magnet: The magnet URI.
            timeout: Number of seconds to wait before canceling request.

        Returns:
            A tuple of (torrent_id, metadata) for the magnet.

        """
        return await self.torrentmanager.prefetch_metadata(magnet, timeout)

    @export
    def add_torrent_file(
        self, filename: str, filedump: Union[str, bytes], options: dict
    ) -> Optional[str]:
        """Adds a torrent file to the session.

        Args:
            filename: The filename of the torrent.
            filedump: A base64 encoded string of the torrent file contents.
            options: The options to apply to the torrent upon adding.

        Returns:
            The torrent_id or None.
        """
        try:
            filedump = b64decode(filedump)
        except Exception as ex:
            log.error('There was an error decoding the filedump string: %s', ex)

        try:
            return self.torrentmanager.add(
                filedump=filedump, options=options, filename=filename
            )
        except RuntimeError as ex:
            log.error('There was an error adding the torrent file %s: %s', filename, ex)
            raise

    @export
    def add_torrent_files(
        self, torrent_files: List[Tuple[str, Union[str, bytes], dict]]
    ) -> 'defer.Deferred[List[AddTorrentError]]':
        """Adds multiple torrent files to the session asynchronously.

        Args:
            torrent_files: Torrent files as tuple of
                ``(filename, filedump, options)``.

        Returns:
            A list of errors (if there were any)
        """

        @maybe_coroutine
        async def add_torrents():
            errors = []
            last_index = len(torrent_files) - 1
            for idx, torrent in enumerate(torrent_files):
                try:
                    await self.add_torrent_file_async(
                        torrent[0], torrent[1], torrent[2], save_state=idx == last_index
                    )
                except AddTorrentError as ex:
                    log.warning('Error when adding torrent: %s', ex)
                    errors.append(ex)
            defer.returnValue(errors)

        return task.deferLater(reactor, 0, add_torrents)

    @export
    @maybe_coroutine
    async def add_torrent_url(
        self, url: str, options: dict, headers: dict = None
    ) -> 'defer.Deferred[Optional[str]]':
        """Adds a torrent from a URL. Deluge will attempt to fetch the torrent
        from the URL prior to adding it to the session.

        Args:
            url: the URL pointing to the torrent file
            options: the options to apply to the torrent on add
            headers: any optional headers to send

        Returns:
            a Deferred which returns the torrent_id as a str or None
        """
        log.info('Attempting to add URL %s', url)

        tmp_fd, tmp_file = tempfile.mkstemp(prefix='deluge_url.', suffix='.torrent')
        try:
            filename = await download_file(
                url, tmp_file, headers=headers, force_filename=True
            )
        except Exception:
            log.error('Failed to add torrent from URL %s', url)
            raise
        else:
            with open(filename, 'rb') as _file:
                data = _file.read()
            return self.add_torrent_file(filename, b64encode(data), options)
        finally:
            try:
                os.close(tmp_fd)
                os.remove(tmp_file)
            except OSError as ex:
                log.warning(f'Unable to delete temp file {tmp_file}: , {ex}')

    @export
    def add_torrent_magnet(self, uri: str, options: dict) -> str:
        """Adds a torrent from a magnet link.

        Args:
            uri: the magnet link
            options: the options to apply to the torrent on add

        Returns:
            the torrent_id
        """
        log.debug('Attempting to add by magnet URI: %s', uri)

        return self.torrentmanager.add(magnet=uri, options=options)

    @export
    def remove_torrent(self, torrent_id: str, remove_data: bool) -> bool:
        """Removes a single torrent from the session.

        Args:
            torrent_id: The torrent ID to remove.
            remove_data: If True, also remove the downloaded data.

        Returns:
            True if removed successfully.

        Raises:
             InvalidTorrentError: If the torrent ID does not exist in the session.
        """
        log.debug('Removing torrent %s from the core.', torrent_id)
        return self.torrentmanager.remove(torrent_id, remove_data)

    @export
    def remove_torrents(
        self, torrent_ids: List[str], remove_data: bool
    ) -> 'defer.Deferred[List[Tuple[str, str]]]':
        """Remove multiple torrents from the session.

        Args:
            torrent_ids: The torrent IDs to remove.
            remove_data: If True, also remove the downloaded data.

        Returns:
            An empty list if no errors occurred otherwise the list contains
            tuples of strings, a torrent ID and an error message. For example:

            [('<torrent_id>', 'Error removing torrent')]
        """
        log.info('Removing %d torrents from core.', len(torrent_ids))

        def do_remove_torrents():
            errors = []
            for torrent_id in torrent_ids:
                try:
                    self.torrentmanager.remove(
                        torrent_id, remove_data=remove_data, save_state=False
                    )
                except InvalidTorrentError as ex:
                    errors.append((torrent_id, str(ex)))
            # Save the session state
            self.torrentmanager.save_state()
            if errors:
                log.warning(
                    'Failed to remove %d of %d torrents.', len(errors), len(torrent_ids)
                )
            return errors

        return task.deferLater(reactor, 0, do_remove_torrents)

    @export
    def get_session_status(self, keys: List[str]) -> Dict[str, Union[int, float]]:
        """Gets the session status values for 'keys', these keys are taking
        from libtorrent's session status.

        See: http://www.rasterbar.com/products/libtorrent/manual.html#status

        Args:
            keys: the keys for which we want values

        Returns:
            a dictionary of {key: value, ...}
        """
        if not keys:
            return self.session_status

        status = {}
        for key in keys:
            try:
                status[key] = self.session_status[key]
            except KeyError:
                if key in DEPR_SESSION_STATUS_KEYS:
                    new_key = DEPR_SESSION_STATUS_KEYS[key]
                    log.debug(
                        'Deprecated session status key %s, please use %s', key, new_key
                    )
                    status[key] = self.session_status[new_key]
                else:
                    log.debug('Session status key not valid: %s', key)
        return status

    @export
    def force_reannounce(self, torrent_ids: List[str]) -> None:
        log.debug('Forcing reannouncment to: %s', torrent_ids)
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].force_reannounce()

    @export
    def pause_torrent(self, torrent_id: str) -> None:
        """Pauses a torrent"""
        log.debug('Pausing: %s', torrent_id)
        if not isinstance(torrent_id, str):
            self.pause_torrents(torrent_id)
        else:
            self.torrentmanager[torrent_id].pause()

    @export
    def pause_torrents(self, torrent_ids: List[str] = None) -> None:
        """Pauses a list of torrents"""
        if not torrent_ids:
            torrent_ids = self.torrentmanager.get_torrent_list()
        for torrent_id in torrent_ids:
            self.pause_torrent(torrent_id)

    @export
    def connect_peer(self, torrent_id: str, ip: str, port: int):
        log.debug('adding peer %s to %s', ip, torrent_id)
        if not self.torrentmanager[torrent_id].connect_peer(ip, port):
            log.warning('Error adding peer %s:%s to %s', ip, port, torrent_id)

    @export
    def move_storage(self, torrent_ids: List[str], dest: str):
        log.debug('Moving storage %s to %s', torrent_ids, dest)
        for torrent_id in torrent_ids:
            if not self.torrentmanager[torrent_id].move_storage(dest):
                log.warning('Error moving torrent %s to %s', torrent_id, dest)

    @export
    def pause_session(self) -> None:
        """Pause the entire session"""
        if not self.session.is_paused():
            self.session.pause()
            component.get('EventManager').emit(SessionPausedEvent())

    @export
    def resume_session(self) -> None:
        """Resume the entire session"""
        if self.session.is_paused():
            self.session.resume()
            for torrent_id in self.torrentmanager.torrents:
                self.torrentmanager[torrent_id].update_state()
            component.get('EventManager').emit(SessionResumedEvent())

    @export
    def is_session_paused(self) -> bool:
        """Returns the activity of the session"""
        return self.session.is_paused()

    @export
    def resume_torrent(self, torrent_id: str) -> None:
        """Resumes a torrent"""
        log.debug('Resuming: %s', torrent_id)
        if not isinstance(torrent_id, str):
            self.resume_torrents(torrent_id)
        else:
            self.torrentmanager[torrent_id].resume()

    @export
    def resume_torrents(self, torrent_ids: List[str] = None) -> None:
        """Resumes a list of torrents"""
        if not torrent_ids:
            torrent_ids = self.torrentmanager.get_torrent_list()
        for torrent_id in torrent_ids:
            self.resume_torrent(torrent_id)

    def create_torrent_status(
        self,
        torrent_id,
        torrent_keys,
        plugin_keys,
        diff=False,
        update=False,
        all_keys=False,
    ):
        try:
            status = self.torrentmanager[torrent_id].get_status(
                torrent_keys, diff, update=update, all_keys=all_keys
            )
        except KeyError:
            import traceback

            traceback.print_exc()
            # Torrent was probably removed meanwhile
            return {}

        # Ask the plugin manager to fill in the plugin keys
        if len(plugin_keys) > 0 or all_keys:
            status.update(self.pluginmanager.get_status(torrent_id, plugin_keys))
        return status

    @export
    def get_torrent_status(
        self, torrent_id: str, keys: List[str], diff: bool = False
    ) -> dict:
        torrent_keys, plugin_keys = self.torrentmanager.separate_keys(
            keys, [torrent_id]
        )
        return self.create_torrent_status(
            torrent_id,
            torrent_keys,
            plugin_keys,
            diff=diff,
            update=True,
            all_keys=not keys,
        )

    @export
    @maybe_coroutine
    async def get_torrents_status(
        self, filter_dict: dict, keys: List[str], diff: bool = False
    ) -> dict:
        """returns all torrents , optionally filtered by filter_dict."""
        all_keys = not keys
        torrent_ids = self.filtermanager.filter_torrent_ids(filter_dict)
        status_dict, plugin_keys = await self.torrentmanager.torrents_status_update(
            torrent_ids, keys, diff=diff
        )
        # Ask the plugin manager to fill in the plugin keys
        if len(plugin_keys) > 0 or all_keys:
            for key in status_dict:
                status_dict[key].update(self.pluginmanager.get_status(key, plugin_keys))
        return status_dict

    @export
    def get_filter_tree(
        self, show_zero_hits: bool = True, hide_cat: List[str] = None
    ) -> Dict:
        """returns {field: [(value,count)] }
        for use in sidebar(s)
        """
        return self.filtermanager.get_filter_tree(show_zero_hits, hide_cat)

    @export
    def get_session_state(self) -> List[str]:
        """Returns a list of torrent_ids in the session."""
        # Get the torrent list from the TorrentManager
        return self.torrentmanager.get_torrent_list()

    @export
    def get_config(self) -> dict:
        """Get all the preferences as a dictionary"""
        return self.config.config

    @export
    def get_config_value(self, key: str) -> Any:
        """Get the config value for key"""
        return self.config.get(key)

    @export
    def get_config_values(self, keys: List[str]) -> Dict[str, Any]:
        """Get the config values for the entered keys"""
        return {key: self.config.get(key) for key in keys}

    @export
    def set_config(self, config: Dict[str, Any]):
        """Set the config with values from dictionary"""
        # Load all the values into the configuration
        for key in config:
            if self.read_only_config_keys and key in self.read_only_config_keys:
                continue
            self.config[key] = config[key]

    @export
    def get_listen_port(self) -> int:
        """Returns the active listen port"""
        return self.session.listen_port()

    @export
    def get_proxy(self) -> Dict[str, Any]:
        """Returns the proxy settings

        Returns:
            Proxy settings.

        Notes:
            Proxy type names:
                0: None, 1: Socks4, 2: Socks5, 3: Socks5 w Auth, 4: HTTP, 5: HTTP w Auth, 6: I2P
        """

        settings = self.session.get_settings()
        proxy_type = settings['proxy_type']
        proxy_hostname = (
            settings['i2p_hostname'] if proxy_type == 6 else settings['proxy_hostname']
        )
        proxy_port = settings['i2p_port'] if proxy_type == 6 else settings['proxy_port']
        proxy_dict = {
            'type': proxy_type,
            'hostname': proxy_hostname,
            'username': settings['proxy_username'],
            'password': settings['proxy_password'],
            'port': proxy_port,
            'proxy_hostnames': settings['proxy_hostnames'],
            'proxy_peer_connections': settings['proxy_peer_connections'],
            'proxy_tracker_connections': settings['proxy_tracker_connections'],
        }

        return proxy_dict

    @export
    def get_available_plugins(self) -> List[str]:
        """Returns a list of plugins available in the core"""
        return self.pluginmanager.get_available_plugins()

    @export
    def get_enabled_plugins(self) -> List[str]:
        """Returns a list of enabled plugins in the core"""
        return self.pluginmanager.get_enabled_plugins()

    @export
    def enable_plugin(self, plugin: str) -> 'defer.Deferred[bool]':
        return self.pluginmanager.enable_plugin(plugin)

    @export
    def disable_plugin(self, plugin: str) -> 'defer.Deferred[bool]':
        return self.pluginmanager.disable_plugin(plugin)

    @export
    def force_recheck(self, torrent_ids: List[str]) -> None:
        """Forces a data recheck on torrent_ids"""
        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].force_recheck()

    @export
    def set_torrent_options(
        self, torrent_ids: List[str], options: Dict[str, Any]
    ) -> None:
        """Sets the torrent options for torrent_ids

        Args:
            torrent_ids: A list of torrent_ids to set the options for.
            options: A dict of torrent options to set. See
                ``torrent.TorrentOptions`` class for valid keys.
        """
        if 'owner' in options and not self.authmanager.has_account(options['owner']):
            raise DelugeError('Username "%s" is not known.' % options['owner'])

        if isinstance(torrent_ids, str):
            torrent_ids = [torrent_ids]

        for torrent_id in torrent_ids:
            self.torrentmanager[torrent_id].set_options(options)

    @export
    def set_torrent_trackers(
        self, torrent_id: str, trackers: List[Dict[str, Any]]
    ) -> None:
        """Sets a torrents tracker list. trackers will be ``[{"url", "tier"}]``"""
        return self.torrentmanager[torrent_id].set_trackers(trackers)

    @export
    def get_magnet_uri(self, torrent_id: str) -> str:
        return self.torrentmanager[torrent_id].get_magnet_uri()

    @deprecated
    @export
    def set_torrent_max_connections(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'max_connections'"""
        self.set_torrent_options([torrent_id], {'max_connections': value})

    @deprecated
    @export
    def set_torrent_max_upload_slots(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'max_upload_slots'"""
        self.set_torrent_options([torrent_id], {'max_upload_slots': value})

    @deprecated
    @export
    def set_torrent_max_upload_speed(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'max_upload_speed'"""
        self.set_torrent_options([torrent_id], {'max_upload_speed': value})

    @deprecated
    @export
    def set_torrent_max_download_speed(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'max_download_speed'"""
        self.set_torrent_options([torrent_id], {'max_download_speed': value})

    @deprecated
    @export
    def set_torrent_file_priorities(self, torrent_id, priorities):
        """Deprecated: Use set_torrent_options with 'file_priorities'"""
        self.set_torrent_options([torrent_id], {'file_priorities': priorities})

    @deprecated
    @export
    def set_torrent_prioritize_first_last(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'prioritize_first_last'"""
        self.set_torrent_options([torrent_id], {'prioritize_first_last_pieces': value})

    @deprecated
    @export
    def set_torrent_auto_managed(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'auto_managed'"""
        self.set_torrent_options([torrent_id], {'auto_managed': value})

    @deprecated
    @export
    def set_torrent_stop_at_ratio(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'stop_at_ratio'"""
        self.set_torrent_options([torrent_id], {'stop_at_ratio': value})

    @deprecated
    @export
    def set_torrent_stop_ratio(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'stop_ratio'"""
        self.set_torrent_options([torrent_id], {'stop_ratio': value})

    @deprecated
    @export
    def set_torrent_remove_at_ratio(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'remove_at_ratio'"""
        self.set_torrent_options([torrent_id], {'remove_at_ratio': value})

    @deprecated
    @export
    def set_torrent_move_completed(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'move_completed'"""
        self.set_torrent_options([torrent_id], {'move_completed': value})

    @deprecated
    @export
    def set_torrent_move_completed_path(self, torrent_id, value):
        """Deprecated: Use set_torrent_options with 'move_completed_path'"""
        self.set_torrent_options([torrent_id], {'move_completed_path': value})

    @export
    def get_path_size(self, path):
        """Returns the size of the file or folder 'path' and -1 if the path is
        inaccessible (non-existent or insufficient privileges)"""
        return deluge.common.get_path_size(path)

    @export
    def create_torrent(
        self,
        path,
        tracker,
        piece_length,
        comment=None,
        target=None,
        webseeds=None,
        private=False,
        created_by=None,
        trackers=None,
        add_to_session=False,
        torrent_format=metafile.TorrentFormat.V1,
    ):
        if isinstance(torrent_format, str):
            torrent_format = metafile.TorrentFormat(torrent_format)

        log.debug('creating torrent..')
        return threads.deferToThread(
            self._create_torrent_thread,
            path,
            tracker,
            piece_length,
            comment=comment,
            target=target,
            webseeds=webseeds,
            private=private,
            created_by=created_by,
            trackers=trackers,
            add_to_session=add_to_session,
            torrent_format=torrent_format,
        )

    def _create_torrent_thread(
        self,
        path,
        tracker,
        piece_length,
        comment,
        target,
        webseeds,
        private,
        created_by,
        trackers,
        add_to_session,
        torrent_format,
    ):
        from deluge import metafile

        filecontent = metafile.make_meta_file_content(
            path,
            tracker,
            piece_length,
            comment=comment,
            webseeds=webseeds,
            private=private,
            created_by=created_by,
            trackers=trackers,
            torrent_format=torrent_format,
        )

        write_file = False
        if target or not add_to_session:
            write_file = True

        if not target:
            target = metafile.default_meta_file_path(path)
        filename = os.path.split(target)[-1]

        if write_file:
            with open(target, 'wb') as _file:
                _file.write(filecontent)

        filedump = b64encode(filecontent)
        log.debug('torrent created!')
        if add_to_session:
            options = {}
            options['download_location'] = os.path.split(path)[0]
            self.add_torrent_file(filename, filedump, options)
        return filename, filedump

    @export
    def upload_plugin(self, filename: str, filedump: Union[str, bytes]) -> None:
        """This method is used to upload new plugins to the daemon.  It is used
        when connecting to the daemon remotely and installing a new plugin on
        the client side. ``plugin_data`` is a ``xmlrpc.Binary`` object of the file data,
        i.e. ``plugin_file.read()``"""

        try:
            filedump = b64decode(filedump)
        except TypeError as ex:
            log.error('There was an error decoding the filedump string!')
            log.exception(ex)
            return

        with open(os.path.join(get_config_dir(), 'plugins', filename), 'wb') as _file:
            _file.write(filedump)
        component.get('CorePluginManager').scan_for_plugins()

    @export
    def rescan_plugins(self) -> None:
        """Re-scans the plugin folders for new plugins"""
        component.get('CorePluginManager').scan_for_plugins()

    @export
    def rename_files(
        self, torrent_id: str, filenames: List[Tuple[int, str]]
    ) -> defer.Deferred:
        """Rename files in ``torrent_id``.  Since this is an asynchronous operation by
        libtorrent, watch for the TorrentFileRenamedEvent to know when the
        files have been renamed.

        Args:
            torrent_id: the torrent_id to rename files
            filenames: a list of index, filename pairs

        Raises:
            InvalidTorrentError: if torrent_id is invalid
        """
        if torrent_id not in self.torrentmanager.torrents:
            raise InvalidTorrentError('torrent_id is not in session')

        def rename():
            self.torrentmanager[torrent_id].rename_files(filenames)

        return task.deferLater(reactor, 0, rename)

    @export
    def rename_folder(
        self, torrent_id: str, folder: str, new_folder: str
    ) -> defer.Deferred:
        """Renames the 'folder' to 'new_folder' in 'torrent_id'.  Watch for the
        TorrentFolderRenamedEvent which is emitted when the folder has been
        renamed successfully.

        Args:
            torrent_id: the torrent to rename folder in
            folder: the folder to rename
            new_folder: the new folder name

        Raises:
            InvalidTorrentError: if the torrent_id is invalid
        """
        if torrent_id not in self.torrentmanager.torrents:
            raise InvalidTorrentError('torrent_id is not in session')

        return self.torrentmanager[torrent_id].rename_folder(folder, new_folder)

    @export
    def queue_top(self, torrent_ids: List[str]) -> None:
        log.debug('Attempting to queue %s to top', torrent_ids)
        # torrent_ids must be sorted in reverse before moving to preserve order
        for torrent_id in sorted(
            torrent_ids, key=self.torrentmanager.get_queue_position, reverse=True
        ):
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_top(torrent_id):
                    component.get('EventManager').emit(TorrentQueueChangedEvent())
            except KeyError:
                log.warning('torrent_id: %s does not exist in the queue', torrent_id)

    @export
    def queue_up(self, torrent_ids: List[str]) -> None:
        log.debug('Attempting to queue %s to up', torrent_ids)
        torrents = (
            (self.torrentmanager.get_queue_position(torrent_id), torrent_id)
            for torrent_id in torrent_ids
        )
        torrent_moved = True
        prev_queue_position = None
        # torrent_ids must be sorted before moving.
        for queue_position, torrent_id in sorted(torrents):
            # Move the torrent if and only if there is space (by not moving it we preserve the order)
            if torrent_moved or queue_position - prev_queue_position > 1:
                try:
                    torrent_moved = self.torrentmanager.queue_up(torrent_id)
                except KeyError:
                    log.warning(
                        'torrent_id: %s does not exist in the queue', torrent_id
                    )
            # If the torrent moved, then we should emit a signal
            if torrent_moved:
                component.get('EventManager').emit(TorrentQueueChangedEvent())
            else:
                prev_queue_position = queue_position

    @export
    def queue_down(self, torrent_ids: List[str]) -> None:
        log.debug('Attempting to queue %s to down', torrent_ids)
        torrents = (
            (self.torrentmanager.get_queue_position(torrent_id), torrent_id)
            for torrent_id in torrent_ids
        )
        torrent_moved = True
        prev_queue_position = None
        # torrent_ids must be sorted before moving.
        for queue_position, torrent_id in sorted(torrents, reverse=True):
            # Move the torrent if and only if there is space (by not moving it we preserve the order)
            if torrent_moved or prev_queue_position - queue_position > 1:
                try:
                    torrent_moved = self.torrentmanager.queue_down(torrent_id)
                except KeyError:
                    log.warning(
                        'torrent_id: %s does not exist in the queue', torrent_id
                    )
            # If the torrent moved, then we should emit a signal
            if torrent_moved:
                component.get('EventManager').emit(TorrentQueueChangedEvent())
            else:
                prev_queue_position = queue_position

    @export
    def queue_bottom(self, torrent_ids: List[str]) -> None:
        log.debug('Attempting to queue %s to bottom', torrent_ids)
        # torrent_ids must be sorted before moving to preserve order
        for torrent_id in sorted(
            torrent_ids, key=self.torrentmanager.get_queue_position
        ):
            try:
                # If the queue method returns True, then we should emit a signal
                if self.torrentmanager.queue_bottom(torrent_id):
                    component.get('EventManager').emit(TorrentQueueChangedEvent())
            except KeyError:
                log.warning('torrent_id: %s does not exist in the queue', torrent_id)

    @export
    def glob(self, path: str) -> List[str]:
        return glob.glob(path)

    @export
    def test_listen_port(self) -> 'defer.Deferred[Optional[bool]]':
        """Checks if the active port is open

        Returns:
            True if the port is open, False if not
        """
        port = self.get_listen_port()
        url = 'https://deluge-torrent.org/test_port.php?port=%s' % port
        agent = Agent(reactor, connectTimeout=30)
        d = agent.request(b'GET', url.encode())

        def on_get_page(body):
            return bool(int(body))

        def on_error(failure):
            log.warning('Error testing listen port: %s', failure)

        d.addCallback(readBody).addCallback(on_get_page)
        d.addErrback(on_error)

        return d

    @export
    def get_free_space(self, path: str = None) -> int:
        """Returns the number of free bytes at path

        Args:
            path: the path to check free space at, if None, use the default download location

        Returns:
            the number of free bytes at path

        Raises:
            InvalidPathError: if the path is invalid
        """
        if not path:
            path = self.config['download_location']
        try:
            return deluge.common.free_space(path)
        except InvalidPathError:
            return -1

    def _on_external_ip_event(self, external_ip):
        self.external_ip = external_ip

    @export
    def get_external_ip(self) -> str:
        """Returns the external IP address received from libtorrent."""
        return self.external_ip

    @export
    def get_libtorrent_version(self) -> str:
        """Returns the libtorrent version.

        Returns:
            the version
        """
        return LT_VERSION

    @export
    def get_completion_paths(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Returns the available path completions for the input value."""
        return path_chooser_common.get_completion_paths(args)

    @export(AUTH_LEVEL_ADMIN)
    def get_known_accounts(self) -> List[Dict[str, Any]]:
        return self.authmanager.get_known_accounts()

    @export(AUTH_LEVEL_NONE)
    def get_auth_levels_mappings(self) -> Tuple[Dict[str, int], Dict[int, str]]:
        return (AUTH_LEVELS_MAPPING, AUTH_LEVELS_MAPPING_REVERSE)

    @export(AUTH_LEVEL_ADMIN)
    def create_account(self, username: str, password: str, authlevel: str) -> bool:
        return self.authmanager.create_account(username, password, authlevel)

    @export(AUTH_LEVEL_ADMIN)
    def update_account(self, username: str, password: str, authlevel: str) -> bool:
        return self.authmanager.update_account(username, password, authlevel)

    @export(AUTH_LEVEL_ADMIN)
    def remove_account(self, username: str) -> bool:
        return self.authmanager.remove_account(username)
