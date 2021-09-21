# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""TorrentManager handles Torrent objects"""
from __future__ import unicode_literals

import datetime
import logging
import operator
import os
import time
from collections import namedtuple
from tempfile import gettempdir

import six.moves.cPickle as pickle  # noqa: N813
from twisted.internet import defer, error, reactor, threads
from twisted.internet.defer import Deferred, DeferredList
from twisted.internet.task import LoopingCall

import deluge.component as component
from deluge._libtorrent import LT_VERSION, lt
from deluge.common import (
    PY2,
    VersionSplit,
    archive_files,
    decode_bytes,
    get_magnet_info,
    is_magnet,
)
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.core.torrent import Torrent, TorrentOptions, sanitize_filepath
from deluge.error import AddTorrentError, InvalidTorrentError
from deluge.event import (
    ExternalIPEvent,
    PreTorrentRemovedEvent,
    SessionStartedEvent,
    TorrentAddedEvent,
    TorrentFileCompletedEvent,
    TorrentFileRenamedEvent,
    TorrentFinishedEvent,
    TorrentRemovedEvent,
    TorrentResumedEvent,
)

log = logging.getLogger(__name__)

LT_DEFAULT_ADD_TORRENT_FLAGS = (
    lt.add_torrent_params_flags_t.flag_paused
    | lt.add_torrent_params_flags_t.flag_auto_managed
    | lt.add_torrent_params_flags_t.flag_update_subscribe
    | lt.add_torrent_params_flags_t.flag_apply_ip_filter
)


class TorrentState:  # pylint: disable=old-style-class
    """Create a torrent state.

    Note:
        This must be old style class to avoid breaking torrent.state file.

    """

    def __init__(
        self,
        torrent_id=None,
        filename=None,
        trackers=None,
        storage_mode='sparse',
        paused=False,
        save_path=None,
        max_connections=-1,
        max_upload_slots=-1,
        max_upload_speed=-1.0,
        max_download_speed=-1.0,
        prioritize_first_last=False,
        sequential_download=False,
        file_priorities=None,
        queue=None,
        auto_managed=True,
        is_finished=False,
        stop_ratio=2.00,
        stop_at_ratio=False,
        remove_at_ratio=False,
        move_completed=False,
        move_completed_path=None,
        magnet=None,
        owner=None,
        shared=False,
        super_seeding=False,
        name=None,
    ):
        # Build the class attribute list from args
        for key, value in locals().items():
            if key == 'self':
                continue
            setattr(self, key, value)

    def __eq__(self, other):
        return isinstance(other, TorrentState) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class TorrentManagerState:  # pylint: disable=old-style-class
    """TorrentManagerState holds a list of TorrentState objects.

    Note:
        This must be old style class to avoid breaking torrent.state file.

    """

    def __init__(self):
        self.torrents = []

    def __eq__(self, other):
        return (
            isinstance(other, TorrentManagerState) and self.torrents == other.torrents
        )

    def __ne__(self, other):
        return not self == other


class TorrentManager(component.Component):
    """TorrentManager contains a list of torrents in the current libtorrent session.

    This object is also responsible for saving the state of the session for use on restart.

    """

    callLater = reactor.callLater  # noqa: N815

    def __init__(self):
        component.Component.__init__(
            self,
            'TorrentManager',
            interval=5,
            depend=['CorePluginManager', 'AlertManager'],
        )
        log.debug('TorrentManager init...')
        # Set the libtorrent session
        self.session = component.get('Core').session
        # Set the alertmanager
        self.alerts = component.get('AlertManager')
        # Get the core config
        self.config = ConfigManager('core.conf')

        # Make sure the state folder has been created
        self.state_dir = os.path.join(get_config_dir(), 'state')
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
        self.temp_file = os.path.join(self.state_dir, '.safe_state_check')

        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
        self.queued_torrents = set()
        self.is_saving_state = False
        self.save_resume_data_file_lock = defer.DeferredLock()
        self.torrents_loading = {}
        self.prefetching_metadata = {}

        # This is a map of torrent_ids to Deferreds used to track needed resume data.
        # The Deferreds will be completed when resume data has been saved.
        self.waiting_on_resume_data = {}

        # Keep track of torrents finished but moving storage
        self.waiting_on_finish_moving = []

        # Keeps track of resume data
        self.resume_data = {}

        self.torrents_status_requests = []
        self.status_dict = {}
        self.last_state_update_alert_ts = 0

        # Keep the previous saved state
        self.prev_saved_state = None

        # Register set functions
        set_config_keys = [
            'max_connections_per_torrent',
            'max_upload_slots_per_torrent',
            'max_upload_speed_per_torrent',
            'max_download_speed_per_torrent',
        ]

        for config_key in set_config_keys:
            on_set_func = getattr(self, ''.join(['on_set_', config_key]))
            self.config.register_set_function(config_key, on_set_func)

        # Register alert functions
        alert_handles = [
            'external_ip_alert',
            'performance_alert',
            'add_torrent_alert',
            'metadata_received_alert',
            'torrent_finished_alert',
            'torrent_paused_alert',
            'torrent_checked_alert',
            'torrent_resumed_alert',
            'tracker_reply_alert',
            'tracker_announce_alert',
            'tracker_warning_alert',
            'tracker_error_alert',
            'file_renamed_alert',
            'file_error_alert',
            'file_completed_alert',
            'storage_moved_alert',
            'storage_moved_failed_alert',
            'state_update_alert',
            'state_changed_alert',
            'save_resume_data_alert',
            'save_resume_data_failed_alert',
            'fastresume_rejected_alert',
        ]

        for alert_handle in alert_handles:
            on_alert_func = getattr(
                self, ''.join(['on_alert_', alert_handle.replace('_alert', '')])
            )
            self.alerts.register_handler(alert_handle, on_alert_func)

        # Define timers
        self.save_state_timer = LoopingCall(self.save_state)
        self.save_resume_data_timer = LoopingCall(self.save_resume_data)
        self.prev_status_cleanup_loop = LoopingCall(self.cleanup_torrents_prev_status)

    def start(self):
        # Check for old temp file to verify safe shutdown
        if os.path.isfile(self.temp_file):
            self.archive_state('Bad shutdown detected so archiving state files')
            os.remove(self.temp_file)

        with open(self.temp_file, 'a'):
            os.utime(self.temp_file, None)

        # Try to load the state from file
        self.load_state()

        # Save the state periodically
        self.save_state_timer.start(200, False)
        self.save_resume_data_timer.start(190, False)
        self.prev_status_cleanup_loop.start(10)

    @defer.inlineCallbacks
    def stop(self):
        # Stop timers
        if self.save_state_timer.running:
            self.save_state_timer.stop()

        if self.save_resume_data_timer.running:
            self.save_resume_data_timer.stop()

        if self.prev_status_cleanup_loop.running:
            self.prev_status_cleanup_loop.stop()

        # Save state on shutdown
        yield self.save_state()

        self.session.pause()

        result = yield self.save_resume_data(flush_disk_cache=True)
        # Remove the temp_file to signify successfully saved state
        if result and os.path.isfile(self.temp_file):
            os.remove(self.temp_file)

    def update(self):
        for torrent_id, torrent in self.torrents.items():
            # XXX: Should the state check be those that _can_ be stopped at ratio
            if torrent.options['stop_at_ratio'] and torrent.state not in (
                'Checking',
                'Allocating',
                'Paused',
                'Queued',
            ):
                # If the global setting is set, but the per-torrent isn't...
                # Just skip to the next torrent.
                # This is so that a user can turn-off the stop at ratio option on a per-torrent basis
                if not torrent.options['stop_at_ratio']:
                    continue
                if (
                    torrent.get_ratio() >= torrent.options['stop_ratio']
                    and torrent.is_finished
                ):
                    if torrent.options['remove_at_ratio']:
                        self.remove(torrent_id)
                        break
                    if not torrent.handle.status().paused:
                        torrent.pause()

    def __getitem__(self, torrent_id):
        """Return the Torrent with torrent_id.

        Args:
            torrent_id (str): The torrent_id.

        Returns:
            Torrent: A torrent object.

        """
        return self.torrents[torrent_id]

    def get_torrent_list(self):
        """Creates a list of torrent_ids, owned by current user and any marked shared.

        Returns:
            list: A list of torrent_ids.

        """
        torrent_ids = list(self.torrents)
        if component.get('RPCServer').get_session_auth_level() == AUTH_LEVEL_ADMIN:
            return torrent_ids

        current_user = component.get('RPCServer').get_session_user()
        for torrent_id in torrent_ids[:]:
            torrent_status = self.torrents[torrent_id].get_status(['owner', 'shared'])
            if torrent_status['owner'] != current_user and not torrent_status['shared']:
                torrent_ids.pop(torrent_ids.index(torrent_id))
        return torrent_ids

    def get_torrent_info_from_file(self, filepath):
        """Retrieves torrent_info from the file specified.

        Args:
            filepath (str): The filepath to extract torrent info from.

        Returns:
            lt.torrent_info: A libtorrent torrent_info dict or None if invalid file or data.

        """
        # Get the torrent data from the torrent file
        if log.isEnabledFor(logging.DEBUG):
            log.debug('Attempting to extract torrent_info from %s', filepath)
        try:
            torrent_info = lt.torrent_info(filepath)
        except RuntimeError as ex:
            log.warning('Unable to open torrent file %s: %s', filepath, ex)
        else:
            return torrent_info

    def prefetch_metadata(self, magnet, timeout):
        """Download the metadata for a magnet URI.

        Args:
            magnet (str): A magnet URI to download the metadata for.
            timeout (int): Number of seconds to wait before canceling.

        Returns:
            Deferred: A tuple of (torrent_id (str), metadata (dict))

        """

        torrent_id = get_magnet_info(magnet)['info_hash']
        if torrent_id in self.prefetching_metadata:
            return self.prefetching_metadata[torrent_id].defer

        add_torrent_params = {}
        add_torrent_params['save_path'] = gettempdir()
        add_torrent_params['url'] = magnet.strip().encode('utf8')
        add_torrent_params['flags'] = (
            (
                LT_DEFAULT_ADD_TORRENT_FLAGS
                | lt.add_torrent_params_flags_t.flag_duplicate_is_error
                | lt.add_torrent_params_flags_t.flag_upload_mode
            )
            ^ lt.add_torrent_params_flags_t.flag_auto_managed
            ^ lt.add_torrent_params_flags_t.flag_paused
        )

        torrent_handle = self.session.add_torrent(add_torrent_params)

        d = Deferred()
        # Cancel the defer if timeout reached.
        defer_timeout = self.callLater(timeout, d.cancel)
        d.addBoth(self.on_prefetch_metadata, torrent_id, defer_timeout)
        Prefetch = namedtuple('Prefetch', 'defer handle')
        self.prefetching_metadata[torrent_id] = Prefetch(defer=d, handle=torrent_handle)
        return d

    def on_prefetch_metadata(self, torrent_info, torrent_id, defer_timeout):
        # Cancel reactor.callLater.
        try:
            defer_timeout.cancel()
        except error.AlreadyCalled:
            pass

        log.debug('remove prefetch magnet from session')
        try:
            torrent_handle = self.prefetching_metadata.pop(torrent_id).handle
        except KeyError:
            pass
        else:
            self.session.remove_torrent(torrent_handle, 1)

        metadata = None
        if isinstance(torrent_info, lt.torrent_info):
            log.debug('prefetch metadata received')
            metadata = lt.bdecode(torrent_info.metadata())

        return torrent_id, metadata

    def _build_torrent_options(self, options):
        """Load default options and update if needed."""
        _options = TorrentOptions()
        if options:
            _options.update(options)
        options = _options

        if not options['owner']:
            options['owner'] = component.get('RPCServer').get_session_user()
        if not component.get('AuthManager').has_account(options['owner']):
            options['owner'] = 'localclient'

        return options

    def _build_torrent_params(
        self, torrent_info=None, magnet=None, options=None, resume_data=None
    ):
        """Create the add_torrent_params dict for adding torrent to libtorrent."""
        add_torrent_params = {}
        if torrent_info:
            add_torrent_params['ti'] = torrent_info
            name = torrent_info.name()
            if not name:
                name = (
                    torrent_info.file_at(0).path.replace('\\', '/', 1).split('/', 1)[0]
                )
            add_torrent_params['name'] = name
            torrent_id = str(torrent_info.info_hash())
        elif magnet:
            magnet_info = get_magnet_info(magnet)
            if magnet_info:
                add_torrent_params['url'] = magnet.strip().encode('utf8')
                add_torrent_params['name'] = magnet_info['name']
                torrent_id = magnet_info['info_hash']
                # Workaround lt 1.2 bug for magnet resume data with no metadata
                if resume_data and VersionSplit(LT_VERSION) >= VersionSplit('1.2.10.0'):
                    add_torrent_params['info_hash'] = bytes(
                        bytearray.fromhex(torrent_id)
                    )
            else:
                raise AddTorrentError(
                    'Unable to add magnet, invalid magnet info: %s' % magnet
                )

        # Check for existing torrent in session.
        if torrent_id in self.get_torrent_list():
            # Attempt merge trackers before returning.
            self.torrents[torrent_id].merge_trackers(torrent_info)
            raise AddTorrentError('Torrent already in session (%s).' % torrent_id)
        elif torrent_id in self.torrents_loading:
            raise AddTorrentError('Torrent already being added (%s).' % torrent_id)
        elif torrent_id in self.prefetching_metadata:
            # Cancel and remove metadata fetching torrent.
            self.prefetching_metadata[torrent_id].defer.cancel()

        # Check for renamed files and if so, rename them in the torrent_info before adding.
        if options['mapped_files'] and torrent_info:
            for index, fname in options['mapped_files'].items():
                fname = sanitize_filepath(decode_bytes(fname))
                if log.isEnabledFor(logging.DEBUG):
                    log.debug('renaming file index %s to %s', index, fname)
                try:
                    torrent_info.rename_file(index, fname.encode('utf8'))
                except TypeError:
                    torrent_info.rename_file(index, fname)
            add_torrent_params['ti'] = torrent_info

        if log.isEnabledFor(logging.DEBUG):
            log.debug('options: %s', options)

        # Fill in the rest of the add_torrent_params dictionary.
        add_torrent_params['save_path'] = options['download_location'].encode('utf8')
        if options['name']:
            add_torrent_params['name'] = options['name']
        if options['pre_allocate_storage']:
            add_torrent_params['storage_mode'] = lt.storage_mode_t.storage_mode_allocate
        if resume_data:
            add_torrent_params['resume_data'] = resume_data

        # Set flags: enable duplicate_is_error & override_resume_data, disable auto_managed.
        add_torrent_params['flags'] = (
            LT_DEFAULT_ADD_TORRENT_FLAGS
            | lt.add_torrent_params_flags_t.flag_duplicate_is_error
            | lt.add_torrent_params_flags_t.flag_override_resume_data
        ) ^ lt.add_torrent_params_flags_t.flag_auto_managed
        if options['seed_mode']:
            add_torrent_params['flags'] |= lt.add_torrent_params_flags_t.flag_seed_mode
        if options['super_seeding']:
            add_torrent_params[
                'flags'
            ] |= lt.add_torrent_params_flags_t.flag_super_seeding

        return torrent_id, add_torrent_params

    def add(
        self,
        torrent_info=None,
        state=None,
        options=None,
        save_state=True,
        filedump=None,
        filename=None,
        magnet=None,
        resume_data=None,
    ):
        """Adds a torrent to the torrent manager.

        Args:
            torrent_info (lt.torrent_info, optional): A libtorrent torrent_info object.
            state (TorrentState, optional): The torrent state.
            options (dict, optional): The options to apply to the torrent on adding.
            save_state (bool, optional): If True save the session state after adding torrent, defaults to True.
            filedump (str, optional): bencoded filedump of a torrent file.
            filename (str, optional): The filename of the torrent file.
            magnet (str, optional): The magnet URI.
            resume_data (lt.entry, optional): libtorrent fast resume data.

        Returns:
            str: If successful the torrent_id of the added torrent, None if adding the torrent failed.

        Emits:
            TorrentAddedEvent: Torrent with torrent_id added to session.

        """
        if not torrent_info and not filedump and not magnet:
            raise AddTorrentError(
                'You must specify a valid torrent_info, torrent state or magnet.'
            )

        if filedump:
            try:
                torrent_info = lt.torrent_info(lt.bdecode(filedump))
            except RuntimeError as ex:
                raise AddTorrentError(
                    'Unable to add torrent, decoding filedump failed: %s' % ex
                )

        options = self._build_torrent_options(options)
        __, add_torrent_params = self._build_torrent_params(
            torrent_info, magnet, options, resume_data
        )

        # We need to pause the AlertManager momentarily to prevent alerts
        # for this torrent being generated before a Torrent object is created.
        component.pause('AlertManager')

        try:
            handle = self.session.add_torrent(add_torrent_params)
            if not handle.is_valid():
                raise InvalidTorrentError('Torrent handle is invalid!')
        except (RuntimeError, InvalidTorrentError) as ex:
            component.resume('AlertManager')
            raise AddTorrentError('Unable to add torrent to session: %s' % ex)

        torrent = self._add_torrent_obj(
            handle, options, state, filename, magnet, resume_data, filedump, save_state
        )
        return torrent.torrent_id

    def add_async(
        self,
        torrent_info=None,
        state=None,
        options=None,
        save_state=True,
        filedump=None,
        filename=None,
        magnet=None,
        resume_data=None,
    ):
        """Adds a torrent to the torrent manager using libtorrent async add torrent method.

        Args:
            torrent_info (lt.torrent_info, optional): A libtorrent torrent_info object.
            state (TorrentState, optional): The torrent state.
            options (dict, optional): The options to apply to the torrent on adding.
            save_state (bool, optional): If True save the session state after adding torrent, defaults to True.
            filedump (str, optional): bencoded filedump of a torrent file.
            filename (str, optional): The filename of the torrent file.
            magnet (str, optional): The magnet URI.
            resume_data (lt.entry, optional): libtorrent fast resume data.

        Returns:
            Deferred: If successful the torrent_id of the added torrent, None if adding the torrent failed.

        Emits:
            TorrentAddedEvent: Torrent with torrent_id added to session.

        """
        if not torrent_info and not filedump and not magnet:
            raise AddTorrentError(
                'You must specify a valid torrent_info, torrent state or magnet.'
            )

        if filedump:
            try:
                torrent_info = lt.torrent_info(lt.bdecode(filedump))
            except RuntimeError as ex:
                raise AddTorrentError(
                    'Unable to add torrent, decoding filedump failed: %s' % ex
                )

        options = self._build_torrent_options(options)
        torrent_id, add_torrent_params = self._build_torrent_params(
            torrent_info, magnet, options, resume_data
        )

        d = Deferred()
        self.torrents_loading[torrent_id] = (
            d,
            options,
            state,
            filename,
            magnet,
            resume_data,
            filedump,
            save_state,
        )
        try:
            self.session.async_add_torrent(add_torrent_params)
        except RuntimeError as ex:
            raise AddTorrentError('Unable to add torrent to session: %s' % ex)
        return d

    def _add_torrent_obj(
        self,
        handle,
        options,
        state,
        filename,
        magnet,
        resume_data,
        filedump,
        save_state,
    ):
        # For magnets added with metadata, filename is used so set as magnet.
        if not magnet and is_magnet(filename):
            magnet = filename
            filename = None

        # Create a Torrent object and add to the dictionary.
        torrent = Torrent(handle, options, state, filename, magnet)
        self.torrents[torrent.torrent_id] = torrent

        # Resume AlertManager if paused for adding torrent to libtorrent.
        component.resume('AlertManager')

        # Store the original resume_data, in case of errors.
        if resume_data:
            self.resume_data[torrent.torrent_id] = resume_data

        # Add to queued torrents set.
        self.queued_torrents.add(torrent.torrent_id)
        if self.config['queue_new_to_top']:
            self.queue_top(torrent.torrent_id)

        # Resume the torrent if needed.
        if not options['add_paused']:
            torrent.resume()

        # Emit torrent_added signal.
        from_state = state is not None
        component.get('EventManager').emit(
            TorrentAddedEvent(torrent.torrent_id, from_state)
        )

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Torrent added: %s', str(handle.info_hash()))
        if log.isEnabledFor(logging.INFO):
            name_and_owner = torrent.get_status(['name', 'owner'])
            log.info(
                'Torrent %s from user "%s" %s',
                name_and_owner['name'],
                name_and_owner['owner'],
                from_state and 'loaded' or 'added',
            )

        # Write the .torrent file to the state directory.
        if filedump:
            torrent.write_torrentfile(filedump)

        # Save the session state.
        if save_state:
            self.save_state()

        return torrent

    def add_async_callback(
        self,
        handle,
        d,
        options,
        state,
        filename,
        magnet,
        resume_data,
        filedump,
        save_state,
    ):
        torrent = self._add_torrent_obj(
            handle, options, state, filename, magnet, resume_data, filedump, save_state
        )

        d.callback(torrent.torrent_id)

    def remove(self, torrent_id, remove_data=False, save_state=True):
        """Remove a torrent from the session.

        Args:
            torrent_id (str): The torrent ID to remove.
            remove_data (bool, optional): If True, remove the downloaded data, defaults to False.
            save_state (bool, optional): If True, save the session state after removal, defaults to True.

        Returns:
            bool: True if removed successfully, False if not.

        Emits:
            PreTorrentRemovedEvent: Torrent is about to be removed from session.
            TorrentRemovedEvent: Torrent with torrent_id removed from session.

        Raises:
            InvalidTorrentError: If the torrent_id is not in the session.

        """
        try:
            torrent = self.torrents[torrent_id]
        except KeyError:
            raise InvalidTorrentError('torrent_id %s not in session.' % torrent_id)

        torrent_name = torrent.get_status(['name'])['name']

        # Emit the signal to the clients
        component.get('EventManager').emit(PreTorrentRemovedEvent(torrent_id))

        try:
            self.session.remove_torrent(torrent.handle, 1 if remove_data else 0)
        except RuntimeError as ex:
            log.warning('Error removing torrent: %s', ex)
            return False

        # Remove fastresume data if it is exists
        self.resume_data.pop(torrent_id, None)

        # Remove the .torrent file in the state and copy location, if user requested.
        delete_copies = (
            self.config['copy_torrent_file'] and self.config['del_copy_torrent_file']
        )
        torrent.delete_torrentfile(delete_copies)

        # Remove from set if it wasn't finished
        if not torrent.is_finished:
            try:
                self.queued_torrents.remove(torrent_id)
            except KeyError:
                log.debug('%s is not in queued torrents set.', torrent_id)
                raise InvalidTorrentError(
                    '%s is not in queued torrents set.' % torrent_id
                )

        # Remove the torrent from deluge's session
        del self.torrents[torrent_id]

        if save_state:
            self.save_state()

        # Emit the signal to the clients
        component.get('EventManager').emit(TorrentRemovedEvent(torrent_id))
        log.info(
            'Torrent %s removed by user: %s',
            torrent_name,
            component.get('RPCServer').get_session_user(),
        )
        return True

    def fixup_state(self, state):
        """Fixup an old state by adding missing TorrentState options and assigning default values.

        Args:
            state (TorrentManagerState): A torrentmanager state containing torrent details.

        Returns:
            TorrentManagerState: A fixedup TorrentManager state.

        """
        if state.torrents:
            t_state_tmp = TorrentState()
            if dir(state.torrents[0]) != dir(t_state_tmp):
                self.archive_state('Migration of TorrentState required.')
                try:
                    for attr in set(dir(t_state_tmp)) - set(dir(state.torrents[0])):
                        for t_state in state.torrents:
                            setattr(t_state, attr, getattr(t_state_tmp, attr, None))
                except AttributeError as ex:
                    log.error(
                        'Unable to update state file to a compatible version: %s', ex
                    )
        return state

    def open_state(self):
        """Open the torrents.state file containing a TorrentManager state with session torrents.

        Returns:
            TorrentManagerState: The TorrentManager state.

        """
        torrents_state = os.path.join(self.state_dir, 'torrents.state')
        state = None
        for filepath in (torrents_state, torrents_state + '.bak'):
            log.info('Loading torrent state: %s', filepath)
            if not os.path.isfile(filepath):
                continue

            try:
                with open(filepath, 'rb') as _file:
                    if PY2:
                        state = pickle.load(_file)
                    else:
                        state = pickle.load(_file, encoding='utf8')
            except (IOError, EOFError, pickle.UnpicklingError) as ex:
                message = 'Unable to load {}: {}'.format(filepath, ex)
                log.error(message)
                if not filepath.endswith('.bak'):
                    self.archive_state(message)
            else:
                log.info('Successfully loaded %s', filepath)
                break

        return state if state else TorrentManagerState()

    def load_state(self):
        """Load all the torrents from TorrentManager state into session.

        Emits:
            SessionStartedEvent: Emitted after all torrents are added to the session.

        """
        start = datetime.datetime.now()
        state = self.open_state()
        state = self.fixup_state(state)

        # Reorder the state.torrents list to add torrents in the correct queue order.
        state.torrents.sort(
            key=operator.attrgetter('queue'), reverse=self.config['queue_new_to_top']
        )
        resume_data = self.load_resume_data_file()

        deferreds = []
        for t_state in state.torrents:
            # Populate the options dict from state
            options = TorrentOptions()
            for option in options:
                try:
                    options[option] = getattr(t_state, option)
                except AttributeError:
                    pass
            # Manually update unmatched attributes
            options['download_location'] = t_state.save_path
            options['pre_allocate_storage'] = t_state.storage_mode == 'allocate'
            options['prioritize_first_last_pieces'] = t_state.prioritize_first_last
            options['add_paused'] = t_state.paused

            magnet = t_state.magnet
            torrent_info = self.get_torrent_info_from_file(
                os.path.join(self.state_dir, t_state.torrent_id + '.torrent')
            )

            try:
                d = self.add_async(
                    torrent_info=torrent_info,
                    state=t_state,
                    options=options,
                    save_state=False,
                    magnet=magnet,
                    resume_data=resume_data.get(t_state.torrent_id),
                )
            except AddTorrentError as ex:
                log.warning(
                    'Error when adding torrent "%s" to session: %s',
                    t_state.torrent_id,
                    ex,
                )
            else:
                deferreds.append(d)

        deferred_list = DeferredList(deferreds, consumeErrors=False)

        def on_complete(result):
            log.info(
                'Finished loading %d torrents in %s',
                len(state.torrents),
                str(datetime.datetime.now() - start),
            )
            component.get('EventManager').emit(SessionStartedEvent())

        deferred_list.addCallback(on_complete)

    def create_state(self):
        """Create a state of all the torrents in TorrentManager.

        Returns:
            TorrentManagerState: The TorrentManager state.

        """
        state = TorrentManagerState()
        # Create the state for each Torrent and append to the list
        for torrent in self.torrents.values():
            if self.session.is_paused():
                paused = torrent.handle.is_paused()
            elif torrent.forced_error:
                paused = torrent.forced_error.was_paused
            elif torrent.state == 'Paused':
                paused = True
            else:
                paused = False

            torrent_state = TorrentState(
                torrent.torrent_id,
                torrent.filename,
                torrent.trackers,
                torrent.get_status(['storage_mode'])['storage_mode'],
                paused,
                torrent.options['download_location'],
                torrent.options['max_connections'],
                torrent.options['max_upload_slots'],
                torrent.options['max_upload_speed'],
                torrent.options['max_download_speed'],
                torrent.options['prioritize_first_last_pieces'],
                torrent.options['sequential_download'],
                torrent.options['file_priorities'],
                torrent.get_queue_position(),
                torrent.options['auto_managed'],
                torrent.is_finished,
                torrent.options['stop_ratio'],
                torrent.options['stop_at_ratio'],
                torrent.options['remove_at_ratio'],
                torrent.options['move_completed'],
                torrent.options['move_completed_path'],
                torrent.magnet,
                torrent.options['owner'],
                torrent.options['shared'],
                torrent.options['super_seeding'],
                torrent.options['name'],
            )
            state.torrents.append(torrent_state)
        return state

    def save_state(self):
        """Run the save state task in a separate thread to avoid blocking main thread.

        Note:
            If a save task is already running, this call is ignored.

        """
        if self.is_saving_state:
            return defer.succeed(None)
        self.is_saving_state = True
        d = threads.deferToThread(self._save_state)

        def on_state_saved(arg):
            self.is_saving_state = False
            if self.save_state_timer.running:
                self.save_state_timer.reset()

        d.addBoth(on_state_saved)
        return d

    def _save_state(self):
        """Save the state of the TorrentManager to the torrents.state file."""
        state = self.create_state()

        # If the state hasn't changed, no need to save it
        if self.prev_saved_state == state:
            return

        filename = 'torrents.state'
        filepath = os.path.join(self.state_dir, filename)
        filepath_bak = filepath + '.bak'
        filepath_tmp = filepath + '.tmp'

        try:
            log.debug('Creating the temporary file: %s', filepath_tmp)
            with open(filepath_tmp, 'wb', 0) as _file:
                pickle.dump(state, _file, protocol=2)
                _file.flush()
                os.fsync(_file.fileno())
        except (OSError, pickle.PicklingError) as ex:
            log.error('Unable to save %s: %s', filename, ex)
            return

        try:
            log.debug('Creating backup of %s at: %s', filename, filepath_bak)
            if os.path.isfile(filepath_bak):
                os.remove(filepath_bak)
            if os.path.isfile(filepath):
                os.rename(filepath, filepath_bak)
        except OSError as ex:
            log.error('Unable to backup %s to %s: %s', filepath, filepath_bak, ex)
            return

        try:
            log.debug('Saving %s to: %s', filename, filepath)
            os.rename(filepath_tmp, filepath)
            self.prev_saved_state = state
        except OSError as ex:
            log.error('Failed to set new state file %s: %s', filepath, ex)
            if os.path.isfile(filepath_bak):
                log.info('Restoring backup of state from: %s', filepath_bak)
                os.rename(filepath_bak, filepath)

    def save_resume_data(self, torrent_ids=None, flush_disk_cache=False):
        """Saves torrents resume data.

        Args:
            torrent_ids (list of str): A list of torrents to save the resume data for, defaults
                to None which saves all torrents resume data.
            flush_disk_cache (bool, optional): If True flushes the disk cache which avoids potential
                issue with file timestamps, defaults to False. This is only needed when stopping the session.

        Returns:
            t.i.d.DeferredList: A list of twisted Deferred callbacks to be invoked when save is complete.

        """
        if torrent_ids is None:
            torrent_ids = (
                tid
                for tid, t in self.torrents.items()
                if t.handle.need_save_resume_data()
            )

        def on_torrent_resume_save(dummy_result, torrent_id):
            """Received torrent resume_data alert so remove from waiting list"""
            self.waiting_on_resume_data.pop(torrent_id, None)

        deferreds = []
        for torrent_id in torrent_ids:
            d = self.waiting_on_resume_data.get(torrent_id)
            if not d:
                d = Deferred().addBoth(on_torrent_resume_save, torrent_id)
                self.waiting_on_resume_data[torrent_id] = d
            deferreds.append(d)
            self.torrents[torrent_id].save_resume_data(flush_disk_cache)

        def on_all_resume_data_finished(dummy_result):
            """Saves resume data file when no more torrents waiting for resume data.

            Returns:
                bool: True if fastresume file is saved.

                This return value determines removal of `self.temp_file` in `self.stop()`.

            """
            # Use flush_disk_cache as a marker for shutdown so fastresume is
            # saved even if torrents are waiting.
            if not self.waiting_on_resume_data or flush_disk_cache:
                return self.save_resume_data_file(queue_task=flush_disk_cache)

        return DeferredList(deferreds).addBoth(on_all_resume_data_finished)

    def load_resume_data_file(self):
        """Load the resume data from file for all torrents.

        Returns:
            dict: A dict of torrents and their resume_data.

        """
        filename = 'torrents.fastresume'
        filepath = os.path.join(self.state_dir, filename)
        filepath_bak = filepath + '.bak'
        old_data_filepath = os.path.join(get_config_dir(), filename)

        for _filepath in (filepath, filepath_bak, old_data_filepath):
            log.info('Opening %s for load: %s', filename, _filepath)
            try:
                with open(_filepath, 'rb') as _file:
                    resume_data = lt.bdecode(_file.read())
            except (IOError, EOFError, RuntimeError) as ex:
                if self.torrents:
                    log.warning('Unable to load %s: %s', _filepath, ex)
                resume_data = None
            else:
                # lt.bdecode returns the dict keys as bytes so decode them.
                resume_data = {k.decode(): v for k, v in resume_data.items()}
                log.info('Successfully loaded %s: %s', filename, _filepath)
                break

        # If the libtorrent bdecode doesn't happen properly, it will return None
        # so we need to make sure we return a {}
        if resume_data is None:
            return {}
        else:
            return resume_data

    def save_resume_data_file(self, queue_task=False):
        """Save resume data to file in a separate thread to avoid blocking main thread.

        Args:
            queue_task (bool): If True and a save task is already running then queue
                this save task to run next. Default is to not queue save tasks.

        Returns:
            Deferred: Fires with arg, True if save task was successful, False if
                not and None if task was not performed.

        """
        if not queue_task and self.save_resume_data_file_lock.locked:
            return defer.succeed(None)

        def on_lock_aquired():
            d = threads.deferToThread(self._save_resume_data_file)

            def on_resume_data_file_saved(arg):
                if self.save_resume_data_timer.running:
                    self.save_resume_data_timer.reset()
                return arg

            d.addBoth(on_resume_data_file_saved)
            return d

        return self.save_resume_data_file_lock.run(on_lock_aquired)

    def _save_resume_data_file(self):
        """Saves the resume data file with the contents of self.resume_data"""
        if not self.resume_data:
            return True

        filename = 'torrents.fastresume'
        filepath = os.path.join(self.state_dir, filename)
        filepath_bak = filepath + '.bak'
        filepath_tmp = filepath + '.tmp'

        try:
            log.debug('Creating the temporary file: %s', filepath_tmp)
            with open(filepath_tmp, 'wb', 0) as _file:
                _file.write(lt.bencode(self.resume_data))
                _file.flush()
                os.fsync(_file.fileno())
        except (OSError, EOFError) as ex:
            log.error('Unable to save %s: %s', filename, ex)
            return False

        try:
            log.debug('Creating backup of %s at: %s', filename, filepath_bak)
            if os.path.isfile(filepath_bak):
                os.remove(filepath_bak)
            if os.path.isfile(filepath):
                os.rename(filepath, filepath_bak)
        except OSError as ex:
            log.error('Unable to backup %s to %s: %s', filepath, filepath_bak, ex)
            return False

        try:
            log.debug('Saving %s to: %s', filename, filepath)
            os.rename(filepath_tmp, filepath)
        except OSError as ex:
            log.error('Failed to set new file %s: %s', filepath, ex)
            if os.path.isfile(filepath_bak):
                log.info('Restoring backup from: %s', filepath_bak)
                os.rename(filepath_bak, filepath)
        else:
            # Sync the rename operations for the directory
            if hasattr(os, 'O_DIRECTORY'):
                dirfd = os.open(os.path.dirname(filepath), os.O_DIRECTORY)
                os.fsync(dirfd)
                os.close(dirfd)
            return True

    def archive_state(self, message):
        log.warning(message)
        arc_filepaths = []
        for filename in ('torrents.fastresume', 'torrents.state'):
            filepath = os.path.join(self.state_dir, filename)
            arc_filepaths.extend([filepath, filepath + '.bak'])

        archive_files('state', arc_filepaths, message=message)

    def get_queue_position(self, torrent_id):
        """Get queue position of torrent"""
        return self.torrents[torrent_id].get_queue_position()

    def queue_top(self, torrent_id):
        """Queue torrent to top"""
        if self.torrents[torrent_id].get_queue_position() == 0:
            return False

        self.torrents[torrent_id].handle.queue_position_top()
        return True

    def queue_up(self, torrent_id):
        """Queue torrent up one position"""
        if self.torrents[torrent_id].get_queue_position() == 0:
            return False

        self.torrents[torrent_id].handle.queue_position_up()
        return True

    def queue_down(self, torrent_id):
        """Queue torrent down one position"""
        if self.torrents[torrent_id].get_queue_position() == (
            len(self.queued_torrents) - 1
        ):
            return False

        self.torrents[torrent_id].handle.queue_position_down()
        return True

    def queue_bottom(self, torrent_id):
        """Queue torrent to bottom"""
        if self.torrents[torrent_id].get_queue_position() == (
            len(self.queued_torrents) - 1
        ):
            return False

        self.torrents[torrent_id].handle.queue_position_bottom()
        return True

    def cleanup_torrents_prev_status(self):
        """Run cleanup_prev_status for each registered torrent"""
        for torrent in self.torrents.values():
            torrent.cleanup_prev_status()

    def on_set_max_connections_per_torrent(self, key, value):
        """Sets the per-torrent connection limit"""
        log.debug('max_connections_per_torrent set to %s...', value)
        for key in self.torrents:
            self.torrents[key].set_max_connections(value)

    def on_set_max_upload_slots_per_torrent(self, key, value):
        """Sets the per-torrent upload slot limit"""
        log.debug('max_upload_slots_per_torrent set to %s...', value)
        for key in self.torrents:
            self.torrents[key].set_max_upload_slots(value)

    def on_set_max_upload_speed_per_torrent(self, key, value):
        """Sets the per-torrent upload speed limit"""
        log.debug('max_upload_speed_per_torrent set to %s...', value)
        for key in self.torrents:
            self.torrents[key].set_max_upload_speed(value)

    def on_set_max_download_speed_per_torrent(self, key, value):
        """Sets the per-torrent download speed limit"""
        log.debug('max_download_speed_per_torrent set to %s...', value)
        for key in self.torrents:
            self.torrents[key].set_max_download_speed(value)

    # --- Alert handlers ---
    def on_alert_add_torrent(self, alert):
        """Alert handler for libtorrent add_torrent_alert"""
        if not alert.handle.is_valid():
            log.warning('Torrent handle is invalid: %s', alert.error.message())
            return

        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError as ex:
            log.warning('Failed to get torrent id from handle: %s', ex)
            return

        try:
            add_async_params = self.torrents_loading.pop(torrent_id)
        except KeyError as ex:
            log.warning('Torrent id not in torrents loading list: %s', ex)
            return

        self.add_async_callback(alert.handle, *add_async_params)

    def on_alert_torrent_finished(self, alert):
        """Alert handler for libtorrent torrent_finished_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        # If total_download is 0, do not move, it's likely the torrent wasn't downloaded, but just added.
        # Get fresh data from libtorrent, the cache isn't always up to date
        total_download = torrent.get_status(['total_payload_download'], update=True)[
            'total_payload_download'
        ]

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Finished %s ', torrent_id)
            log.debug(
                'Torrent settings: is_finished: %s, total_download: %s, move_completed: %s, move_path: %s',
                torrent.is_finished,
                total_download,
                torrent.options['move_completed'],
                torrent.options['move_completed_path'],
            )

        torrent.update_state()
        if not torrent.is_finished and total_download:
            # Move completed download to completed folder if needed
            if (
                torrent.options['move_completed']
                and torrent.options['download_location']
                != torrent.options['move_completed_path']
            ):
                self.waiting_on_finish_moving.append(torrent_id)
                torrent.move_storage(torrent.options['move_completed_path'])
            else:
                torrent.is_finished = True
                component.get('EventManager').emit(TorrentFinishedEvent(torrent_id))
        else:
            torrent.is_finished = True

        # Torrent is no longer part of the queue
        try:
            self.queued_torrents.remove(torrent_id)
        except KeyError:
            # Sometimes libtorrent fires a TorrentFinishedEvent twice
            if log.isEnabledFor(logging.DEBUG):
                log.debug('%s is not in queued torrents set.', torrent_id)

        # Only save resume data if it was actually downloaded something. Helps
        # on startup with big queues with lots of seeding torrents. Libtorrent
        # emits alert_torrent_finished for them, but there seems like nothing
        # worth really to save in resume data, we just read it up in
        # self.load_state().
        if total_download:
            self.save_resume_data((torrent_id,))

    def on_alert_torrent_paused(self, alert):
        """Alert handler for libtorrent torrent_paused_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return
        torrent.update_state()
        # Write the fastresume file if we are not waiting on a bulk write
        if torrent_id not in self.waiting_on_resume_data:
            self.save_resume_data((torrent_id,))

    def on_alert_torrent_checked(self, alert):
        """Alert handler for libtorrent torrent_checked_alert"""
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return

        # Check to see if we're forcing a recheck and set it back to paused if necessary.
        if torrent.forcing_recheck:
            torrent.forcing_recheck = False
            if torrent.forcing_recheck_paused:
                torrent.handle.pause()

        torrent.update_state()

    def on_alert_tracker_reply(self, alert):
        """Alert handler for libtorrent tracker_reply_alert"""
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return

        # Set the tracker status for the torrent
        torrent.set_tracker_status('Announce OK')

        # Check for peer information from the tracker, if none then send a scrape request.
        if (
            alert.handle.status().num_complete == -1
            or alert.handle.status().num_incomplete == -1
        ):
            torrent.scrape_tracker()

    def on_alert_tracker_announce(self, alert):
        """Alert handler for libtorrent tracker_announce_alert"""
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return

        # Set the tracker status for the torrent
        torrent.set_tracker_status('Announce Sent')

    def on_alert_tracker_warning(self, alert):
        """Alert handler for libtorrent tracker_warning_alert"""
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return
        # Set the tracker status for the torrent
        torrent.set_tracker_status('Warning: %s' % decode_bytes(alert.message()))

    def on_alert_tracker_error(self, alert):
        """Alert handler for libtorrent tracker_error_alert"""
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return

        error_message = decode_bytes(alert.error_message())
        if not error_message:
            error_message = decode_bytes(alert.error.message())
        log.debug(
            'Tracker Error Alert: %s [%s]', decode_bytes(alert.message()), error_message
        )
        if VersionSplit(LT_VERSION) >= VersionSplit('1.2.0.0'):
            # libtorrent 1.2 added endpoint struct to each tracker. to prevent false updates
            # we will need to verify that at least one endpoint to the errored tracker is working
            for tracker in torrent.handle.trackers():
                if tracker['url'] == alert.url:
                    if any(
                        endpoint['last_error']['value'] == 0
                        for endpoint in tracker['endpoints']
                    ):
                        torrent.set_tracker_status('Announce OK')
                    else:
                        torrent.set_tracker_status('Error: ' + error_message)
                    break
        else:
            # preserve old functionality for libtorrent < 1.2
            torrent.set_tracker_status('Error: ' + error_message)

    def on_alert_storage_moved(self, alert):
        """Alert handler for libtorrent storage_moved_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        torrent.set_download_location(os.path.normpath(alert.storage_path()))
        torrent.set_move_completed(False)
        torrent.update_state()

        if torrent_id in self.waiting_on_finish_moving:
            self.waiting_on_finish_moving.remove(torrent_id)
            torrent.is_finished = True
            component.get('EventManager').emit(TorrentFinishedEvent(torrent_id))

    def on_alert_storage_moved_failed(self, alert):
        """Alert handler for libtorrent storage_moved_failed_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        log.warning('on_alert_storage_moved_failed: %s', decode_bytes(alert.message()))
        # Set an Error message and pause the torrent
        alert_msg = decode_bytes(alert.message()).split(':', 1)[1].strip()
        torrent.force_error_state('Failed to move download folder: %s' % alert_msg)

        if torrent_id in self.waiting_on_finish_moving:
            self.waiting_on_finish_moving.remove(torrent_id)
            torrent.is_finished = True
            component.get('EventManager').emit(TorrentFinishedEvent(torrent_id))

    def on_alert_torrent_resumed(self, alert):
        """Alert handler for libtorrent torrent_resumed_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return
        torrent.update_state()
        component.get('EventManager').emit(TorrentResumedEvent(torrent_id))

    def on_alert_state_changed(self, alert):
        """Alert handler for libtorrent state_changed_alert.

        Emits:
            TorrentStateChangedEvent: The state has changed.

        """
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        torrent.update_state()
        # Torrent may need to download data after checking.
        if torrent.state in ('Checking', 'Downloading'):
            torrent.is_finished = False
            self.queued_torrents.add(torrent_id)

    def on_alert_save_resume_data(self, alert):
        """Alert handler for libtorrent save_resume_data_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError:
            return
        if torrent_id in self.torrents:
            # libtorrent add_torrent expects bencoded resume_data.
            self.resume_data[torrent_id] = lt.bencode(alert.resume_data)

        if torrent_id in self.waiting_on_resume_data:
            self.waiting_on_resume_data[torrent_id].callback(None)

    def on_alert_save_resume_data_failed(self, alert):
        """Alert handler for libtorrent save_resume_data_failed_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError:
            return

        if torrent_id in self.waiting_on_resume_data:
            self.waiting_on_resume_data[torrent_id].errback(
                Exception(decode_bytes(alert.message()))
            )

    def on_alert_fastresume_rejected(self, alert):
        """Alert handler for libtorrent fastresume_rejected_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        alert_msg = decode_bytes(alert.message())
        log.error('on_alert_fastresume_rejected: %s', alert_msg)
        if alert.error.value() == 134:
            if not os.path.isdir(torrent.options['download_location']):
                error_msg = 'Unable to locate Download Folder!'
            else:
                error_msg = 'Missing or invalid torrent data!'
        else:
            error_msg = (
                'Problem with resume data: %s' % alert_msg.split(':', 1)[1].strip()
            )
        torrent.force_error_state(error_msg, restart_to_resume=True)

    def on_alert_file_renamed(self, alert):
        """Alert handler for libtorrent file_renamed_alert.

        Emits:
            TorrentFileRenamedEvent: Files in the torrent have been renamed.

        """
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        new_name = decode_bytes(alert.new_name())
        log.debug('index: %s name: %s', alert.index, new_name)

        # We need to see if this file index is in a waiting_on_folder dict
        for wait_on_folder in torrent.waiting_on_folder_rename:
            if alert.index in wait_on_folder:
                wait_on_folder[alert.index].callback(None)
                break
        else:
            # This is just a regular file rename so send the signal
            component.get('EventManager').emit(
                TorrentFileRenamedEvent(torrent_id, alert.index, new_name)
            )
            self.save_resume_data((torrent_id,))

    def on_alert_metadata_received(self, alert):
        """Alert handler for libtorrent metadata_received_alert"""
        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError:
            return

        try:
            torrent = self.torrents[torrent_id]
        except KeyError:
            pass
        else:
            return torrent.on_metadata_received()

        # Try callback to prefetch_metadata method.
        try:
            d = self.prefetching_metadata[torrent_id].defer
        except KeyError:
            pass
        else:
            torrent_info = alert.handle.get_torrent_info()
            return d.callback(torrent_info)

    def on_alert_file_error(self, alert):
        """Alert handler for libtorrent file_error_alert"""
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return
        torrent.update_state()

    def on_alert_file_completed(self, alert):
        """Alert handler for libtorrent file_completed_alert

        Emits:
            TorrentFileCompletedEvent: When an individual file completes downloading.

        """
        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError:
            return
        if torrent_id in self.torrents:
            component.get('EventManager').emit(
                TorrentFileCompletedEvent(torrent_id, alert.index)
            )

    def on_alert_state_update(self, alert):
        """Alert handler for libtorrent state_update_alert

        Result of a session.post_torrent_updates() call and contains the torrent status
        of all torrents that changed since last time this was posted.

        """
        self.last_state_update_alert_ts = time.time()

        for t_status in alert.status:
            try:
                torrent_id = str(t_status.info_hash)
            except RuntimeError:
                continue
            if torrent_id in self.torrents:
                self.torrents[torrent_id].update_status(t_status)

        self.handle_torrents_status_callback(self.torrents_status_requests.pop())

    def on_alert_external_ip(self, alert):
        """Alert handler for libtorrent external_ip_alert

        Note:
            The alert.message IPv4 address format is:
                'external IP received: 0.0.0.0'
            and IPv6 address format is:
                'external IP received: 0:0:0:0:0:0:0:0'
        """

        external_ip = decode_bytes(alert.message()).split(' ')[-1]
        log.info('on_alert_external_ip: %s', external_ip)
        component.get('EventManager').emit(ExternalIPEvent(external_ip))

    def on_alert_performance(self, alert):
        """Alert handler for libtorrent performance_alert"""
        log.warning(
            'on_alert_performance: %s, %s',
            decode_bytes(alert.message()),
            alert.warning_code,
        )
        if alert.warning_code == lt.performance_warning_t.send_buffer_watermark_too_low:
            max_send_buffer_watermark = 3 * 1024 * 1024  # 3MiB
            settings = self.session.get_settings()
            send_buffer_watermark = settings['send_buffer_watermark']

            # If send buffer is too small, try increasing its size by 512KiB (up to max_send_buffer_watermark)
            if send_buffer_watermark < max_send_buffer_watermark:
                value = send_buffer_watermark + (500 * 1024)
                log.info(
                    'Increasing send_buffer_watermark from %s to %s Bytes',
                    send_buffer_watermark,
                    value,
                )
                component.get('Core').apply_session_setting(
                    'send_buffer_watermark', value
                )
            else:
                log.warning(
                    'send_buffer_watermark reached maximum value: %s Bytes',
                    max_send_buffer_watermark,
                )

    def separate_keys(self, keys, torrent_ids):
        """Separates the input keys into torrent class keys and plugins keys"""
        if self.torrents:
            for torrent_id in torrent_ids:
                if torrent_id in self.torrents:
                    status_keys = list(self.torrents[torrent_id].status_funcs)
                    leftover_keys = list(set(keys) - set(status_keys))
                    torrent_keys = list(set(keys) - set(leftover_keys))
                    return torrent_keys, leftover_keys
        return [], []

    def handle_torrents_status_callback(self, status_request):
        """Build the status dictionary with torrent values"""
        d, torrent_ids, keys, diff = status_request
        status_dict = {}.fromkeys(torrent_ids)
        torrent_keys, plugin_keys = self.separate_keys(keys, torrent_ids)

        # Get the torrent status for each torrent_id
        for torrent_id in torrent_ids:
            if torrent_id not in self.torrents:
                # The torrent_id does not exist in the dict.
                # Could be the clients cache (sessionproxy) isn't up to speed.
                del status_dict[torrent_id]
            else:
                status_dict[torrent_id] = self.torrents[torrent_id].get_status(
                    torrent_keys, diff, all_keys=not keys
                )
        self.status_dict = status_dict
        d.callback((status_dict, plugin_keys))

    def torrents_status_update(self, torrent_ids, keys, diff=False):
        """Returns status dict for the supplied torrent_ids async.

        Note:
            If torrent states was updated recently post_torrent_updates is not called and
            instead cached state is used.

        Args:
            torrent_ids (list of str): The torrent IDs to get the status of.
            keys (list of str): The keys to get the status on.
            diff (bool, optional): If True, will return a diff of the changes since the
                last call to get_status based on the session_id, defaults to False.

        Returns:
            dict: A status dictionary for the requested torrents.

        """
        d = Deferred()
        now = time.time()
        # If last update was recent, use cached data instead of request updates from libtorrent
        if (now - self.last_state_update_alert_ts) < 1.5:
            reactor.callLater(
                0, self.handle_torrents_status_callback, (d, torrent_ids, keys, diff)
            )
        else:
            # Ask libtorrent for status update
            self.torrents_status_requests.insert(0, (d, torrent_ids, keys, diff))
            self.session.post_torrent_updates()
        return d
