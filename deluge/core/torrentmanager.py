# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""TorrentManager handles Torrent objects"""

import cPickle
import datetime
import logging
import operator
import os
import shutil
import time

from twisted.internet import defer, reactor, threads
from twisted.internet.defer import Deferred, DeferredList
from twisted.internet.task import LoopingCall

import deluge.component as component
from deluge._libtorrent import lt
from deluge.common import decode_string, get_magnet_info, utf8_encoded
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.core.torrent import Torrent, TorrentOptions, sanitize_filepath
from deluge.error import AddTorrentError, InvalidTorrentError
from deluge.event import (PreTorrentRemovedEvent, SessionStartedEvent, TorrentAddedEvent, TorrentFileCompletedEvent,
                          TorrentFileRenamedEvent, TorrentFinishedEvent, TorrentRemovedEvent, TorrentResumedEvent)

log = logging.getLogger(__name__)


class TorrentState:
    """Create a torrent state"""
    def __init__(self,
                 torrent_id=None,
                 filename=None,
                 trackers=None,
                 storage_mode="sparse",
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
                 priority=0,
                 name=None
                 ):
        # Build the class atrribute list from args
        for key, value in locals().items():
            if key == "self":
                continue
            setattr(self, key, value)


class TorrentManagerState:
    """TorrentManagerState holds a list of TorrentState objects"""
    def __init__(self):
        self.torrents = []


class TorrentManager(component.Component):
    """TorrentManager contains a list of torrents in the current libtorrent session.

    This object is also responsible for saving the state of the session for use on restart.

    """

    def __init__(self):
        component.Component.__init__(self, "TorrentManager", interval=5,
                                     depend=["CorePluginManager", "AlertManager"])
        log.debug("TorrentManager init...")
        # Set the libtorrent session
        self.session = component.get("Core").session
        # Set the alertmanager
        self.alerts = component.get("AlertManager")
        # Get the core config
        self.config = ConfigManager("core.conf")

        # Make sure the state folder has been created
        self.state_dir = os.path.join(get_config_dir(), "state")
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
        self.temp_file = os.path.join(self.state_dir, ".safe_state_check")

        # Create the torrents dict { torrent_id: Torrent }
        self.torrents = {}
        self.queued_torrents = set()
        self.is_saving_state = False
        self.torrents_loading = {}

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

        # Register set functions
        self.config.register_set_function("max_connections_per_torrent",
                                          self.on_set_max_connections_per_torrent)
        self.config.register_set_function("max_upload_slots_per_torrent",
                                          self.on_set_max_upload_slots_per_torrent)
        self.config.register_set_function("max_upload_speed_per_torrent",
                                          self.on_set_max_upload_speed_per_torrent)
        self.config.register_set_function("max_download_speed_per_torrent",
                                          self.on_set_max_download_speed_per_torrent)

        # Register alert functions
        self.alerts.register_handler("torrent_finished_alert", self.on_alert_torrent_finished)
        self.alerts.register_handler("torrent_paused_alert", self.on_alert_torrent_paused)
        self.alerts.register_handler("torrent_checked_alert", self.on_alert_torrent_checked)
        self.alerts.register_handler("tracker_reply_alert", self.on_alert_tracker_reply)
        self.alerts.register_handler("tracker_announce_alert", self.on_alert_tracker_announce)
        self.alerts.register_handler("tracker_warning_alert", self.on_alert_tracker_warning)
        self.alerts.register_handler("tracker_error_alert", self.on_alert_tracker_error)
        self.alerts.register_handler("storage_moved_alert", self.on_alert_storage_moved)
        self.alerts.register_handler("storage_moved_failed_alert", self.on_alert_storage_moved_failed)
        self.alerts.register_handler("torrent_resumed_alert", self.on_alert_torrent_resumed)
        self.alerts.register_handler("state_changed_alert", self.on_alert_state_changed)
        self.alerts.register_handler("save_resume_data_alert", self.on_alert_save_resume_data)
        self.alerts.register_handler("save_resume_data_failed_alert", self.on_alert_save_resume_data_failed)
        self.alerts.register_handler("file_renamed_alert", self.on_alert_file_renamed)
        self.alerts.register_handler("metadata_received_alert", self.on_alert_metadata_received)
        self.alerts.register_handler("file_error_alert", self.on_alert_file_error)
        self.alerts.register_handler("file_completed_alert", self.on_alert_file_completed)
        self.alerts.register_handler("state_update_alert", self.on_alert_state_update)
        self.alerts.register_handler("external_ip_alert", self.on_alert_external_ip)
        self.alerts.register_handler("performance_alert", self.on_alert_performance)
        self.alerts.register_handler("fastresume_rejected_alert", self.on_alert_fastresume_rejected)
        self.alerts.register_handler("add_torrent_alert", self.on_add_torrent_alert)

        # Define timers
        self.save_state_timer = LoopingCall(self.save_state)
        self.save_resume_data_timer = LoopingCall(self.save_resume_data)
        self.prev_status_cleanup_loop = LoopingCall(self.cleanup_torrents_prev_status)

    def start(self):
        # Check for old temp file to verify safe shutdown
        if os.path.isfile(self.temp_file):
            def archive_file(filename):
                """Archives the file in 'archive' sub-directory with timestamp appended"""
                filepath = os.path.join(self.state_dir, filename)
                filepath_bak = filepath + ".bak"
                archive_dir = os.path.join(get_config_dir(), "archive")
                if not os.path.exists(archive_dir):
                    os.makedirs(archive_dir)

                for _filepath in (filepath, filepath_bak):
                    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(':', '-')
                    archive_filepath = os.path.join(archive_dir, filename + "-" + timestamp)
                    try:
                        shutil.copy2(_filepath, archive_filepath)
                    except IOError:
                        log.error("Unable to archive: %s", filename)
                    else:
                        log.info("Archive of %s successful: %s", filename, archive_filepath)

            log.warning("Potential bad shutdown of Deluge detected, archiving torrent state files...")
            archive_file("torrents.state")
            archive_file("torrents.fastresume")
        else:
            with file(self.temp_file, 'a'):
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
            if torrent.options["stop_at_ratio"] and torrent.state not in (
                    "Checking", "Allocating", "Paused", "Queued"):
                # If the global setting is set, but the per-torrent isn't...
                # Just skip to the next torrent.
                # This is so that a user can turn-off the stop at ratio option on a per-torrent basis
                if not torrent.options["stop_at_ratio"]:
                    continue
                if torrent.get_ratio() >= torrent.options["stop_ratio"] and torrent.is_finished:
                    if torrent.options["remove_at_ratio"]:
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
        torrent_ids = self.torrents.keys()
        if component.get("RPCServer").get_session_auth_level() == AUTH_LEVEL_ADMIN:
            return torrent_ids

        current_user = component.get("RPCServer").get_session_user()
        for torrent_id in torrent_ids[:]:
            torrent_status = self.torrents[torrent_id].get_status(["owner", "shared"])
            if torrent_status["owner"] != current_user and not torrent_status["shared"]:
                torrent_ids.pop(torrent_ids.index(torrent_id))
        return torrent_ids

    def get_torrent_info_from_file(self, filepath):
        """Retrieves torrent_info from the file specified.

        Args:
            filepath (str): The filepath to extract torrent info from.

        Returns:
            lt.torrent_info : A libtorrent torrent_info dict or None if invalid file or data.
        """
        # Get the torrent data from the torrent file
        if log.isEnabledFor(logging.DEBUG):
            log.debug("Attempting to extract torrent_info from %s", filepath)
        try:
            torrent_info = lt.torrent_info(filepath)
        except RuntimeError as ex:
            log.warning("Unable to open torrent file %s: %s", filepath, ex)
        else:
            return torrent_info

    def add(self, torrent_info=None, state=None, options=None, save_state=True,
            filedump=None, filename=None, magnet=None, resume_data=None):
        """Adds a torrent to the torrent manager.

        Args:
            torrent_info (lt.torrent_info, optional): A libtorrent torrent_info object.
            state (TorrentState, optional): The torrent state.
            options (dict, optional): The options to apply to the torrent on adding.
            save_state (bool, optional): If True save the session state after adding torrent, defaults to True.
            filedump (str, optional): bencoded filedump of a torrent file.
            filename (str, optional): The filename of the torrent file.
            magnet (str, optional): The magnet uri.
            resume_data (lt.entry, optional): libtorrent fast resume data.

        Returns:
            str: If successful the torrent_id of the added torrent, None if adding the torrent failed.

        Emits:
            TorrentAddedEvent: Torrent with torrent_id added to session.

        """
        if not torrent_info and not filedump and not magnet:
            raise AddTorrentError("You must specify a valid torrent_info, torrent state or magnet.")

        if filedump:
            try:
                torrent_info = lt.torrent_info(lt.bdecode(filedump))
            except RuntimeError as ex:
                raise AddTorrentError("Unable to add torrent, decoding filedump failed: %s" % ex)

        add_torrent_params = {}
        if torrent_info:
            add_torrent_params["ti"] = torrent_info
            name = torrent_info.name()
            if not name:
                name = torrent_info.file_at(0).path.replace("\\", "/", 1).split("/", 1)[0]
            add_torrent_params["name"] = name
            torrent_id = str(torrent_info.info_hash())
        elif magnet:
            magnet = utf8_encoded(magnet)
            magnet_info = get_magnet_info(magnet)
            if magnet_info:
                add_torrent_params["url"] = magnet
                add_torrent_params["name"] = magnet_info["name"]
                torrent_id = magnet_info["info_hash"]
            else:
                raise AddTorrentError("Unable to add magnet, invalid magnet info: %s" % magnet)

        # Check for existing torrent in session.
        if torrent_id in self.get_torrent_list():
            # Attempt merge trackers before returning.
            self.torrents[torrent_id].merge_trackers(torrent_info)
            raise AddTorrentError("Torrent already in session (%s)." % torrent_id)
        elif torrent_id in self.torrents_loading:
            raise AddTorrentError("Torrent already being added (%s)." % torrent_id)

        # Load default options and update if needed.
        _options = TorrentOptions()
        if options:
            _options.update(options)
        options = _options

        # Check for renamed files and if so, rename them in the torrent_info before adding.
        if options["mapped_files"] and torrent_info:
            for index, fname in options["mapped_files"].items():
                fname = sanitize_filepath(decode_string(fname))
                log.debug("renaming file index %s to %s", index, fname)
                try:
                    torrent_info.rename_file(index, fname)
                except TypeError:
                    torrent_info.rename_file(index, utf8_encoded(fname))
            add_torrent_params["ti"] = torrent_info

        if not options["owner"]:
            options["owner"] = component.get("RPCServer").get_session_user()
        if not component.get("AuthManager").has_account(options["owner"]):
            options["owner"] = "localclient"

        if log.isEnabledFor(logging.DEBUG):
            log.debug("options: %s", options)

        # Fill in the rest of the add_torrent_params dictionary.
        add_torrent_params["save_path"] = utf8_encoded(options["download_location"])
        if options["name"]:
            add_torrent_params["name"] = options["name"]
        if options["pre_allocate_storage"]:
            add_torrent_params["storage_mode"] = lt.storage_mode_t.storage_mode_allocate
        if resume_data:
            add_torrent_params["resume_data"] = resume_data

        default_flags = (lt.add_torrent_params_flags_t.flag_paused |
                         lt.add_torrent_params_flags_t.flag_auto_managed |
                         lt.add_torrent_params_flags_t.flag_update_subscribe |
                         lt.add_torrent_params_flags_t.flag_apply_ip_filter)
        # Set flags: enable duplicate_is_error & override_resume_data, disable auto_managed.
        add_torrent_params["flags"] = ((default_flags |
                                        lt.add_torrent_params_flags_t.flag_duplicate_is_error |
                                        lt.add_torrent_params_flags_t.flag_override_resume_data) ^
                                       lt.add_torrent_params_flags_t.flag_auto_managed)
        if options["seed_mode"]:
            add_torrent_params["flags"] |= lt.add_torrent_params_flags_t.flag_seed_mode

        d = Deferred()
        try:
            self.torrents_loading[torrent_id] = (d, options, state, filename, magnet, resume_data, filedump, save_state)
            self.session.async_add_torrent(add_torrent_params)
        except RuntimeError as ex:
            raise AddTorrentError("Unable to add torrent to session: %s" % ex)
        return d

    def on_add_torrent_alert(self, alert):
        """Alert handler for libtorrent add_torrent_alert"""
        if not alert.handle.is_valid():
            log.warn("Torrent handle is invalid!")
            return

        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError as ex:
            log.warn("Failed to get torrent id from handle: %s", ex)
            return

        d, options, state, filename, magnet, resume_data, filedump, save_state = self.torrents_loading.pop(torrent_id)

        # Create a Torrent object and add to the dictionary.
        torrent = Torrent(alert.handle, options, state, filename, magnet)
        self.torrents[torrent.torrent_id] = torrent

        # Store the orignal resume_data, in case of errors.
        if resume_data:
            self.resume_data[torrent.torrent_id] = resume_data

        # Add to queued torrents set.
        self.queued_torrents.add(torrent.torrent_id)
        if self.config["queue_new_to_top"]:
            self.queue_top(torrent.torrent_id)

        # Resume the torrent if needed.
        if not options["add_paused"]:
            torrent.resume()

        # Emit torrent_added signal.
        from_state = state is not None
        component.get("EventManager").emit(TorrentAddedEvent(torrent.torrent_id, from_state))

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Torrent added: %s", str(alert.handle.info_hash()))
        if log.isEnabledFor(logging.INFO):
            name_and_owner = torrent.get_status(["name", "owner"])
            log.info("Torrent %s from user \"%s\" %s",
                     name_and_owner["name"],
                     name_and_owner["owner"],
                     from_state and "loaded" or "added")

        # Write the .torrent file to the state directory.
        if filedump:
            torrent.write_torrentfile(filedump)

        # Save the session state.
        if save_state:
            self.save_state()

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
            raise InvalidTorrentError("torrent_id '%s' not in session." % torrent_id)

        torrent_name = torrent.get_status(["name"])["name"]

        # Emit the signal to the clients
        component.get("EventManager").emit(PreTorrentRemovedEvent(torrent_id))

        try:
            self.session.remove_torrent(torrent.handle, 1 if remove_data else 0)
        except RuntimeError as ex:
            log.warning("Error removing torrent: %s", ex)
            return False

        # Remove fastresume data if it is exists
        self.resume_data.pop(torrent_id, None)

        # Remove the .torrent file in the state and copy location, if user requested.
        delete_copies = self.config["copy_torrent_file"] and self.config["del_copy_torrent_file"]
        torrent.delete_torrentfile(delete_copies)

        # Remove from set if it wasn't finished
        if not torrent.is_finished:
            try:
                self.queued_torrents.remove(torrent_id)
            except KeyError:
                log.debug("%s isn't in queued torrents set?", torrent_id)
                raise InvalidTorrentError("%s isn't in queued torrents set?" % torrent_id)

        # Remove the torrent from deluge's session
        del self.torrents[torrent_id]

        if save_state:
            self.save_state()

        # Emit the signal to the clients
        component.get("EventManager").emit(TorrentRemovedEvent(torrent_id))
        log.info("Torrent %s removed by user: %s", torrent_name, component.get("RPCServer").get_session_user())
        return True

    def fixup_state(self, state):
        """ Fixup an old state by adding missing TorrentState options and assigning default values.

        Args:
            state (TorrentManagerState): A torrentmanager state containing torrent details.

        Returns:
            TorrentManagerState: A fixedup TorrentManager state.

        """
        if state.torrents:
            t_state_tmp = TorrentState()
            if dir(state.torrents[0]) != dir(t_state_tmp):
                try:
                    for attr in set(dir(t_state_tmp)) - set(dir(state.torrents[0])):
                        for t_state in state.torrents:
                            if attr == "storage_mode" and getattr(t_state, "compact", None):
                                setattr(t_state, attr, "compact")
                            else:
                                setattr(t_state, attr, getattr(t_state_tmp, attr, None))
                except AttributeError as ex:
                    log.error("Unable to update state file to a compatible version: %s", ex)
        return state

    def open_state(self):
        """Open the torrents.state file containing a TorrentManager state with session torrents.

        Returns:
            TorrentManagerState: The TorrentManager state.

        """
        torrents_state = os.path.join(self.state_dir, "torrents.state")
        for filepath in (torrents_state, torrents_state + ".bak"):
            log.info("Loading torrent state: %s", filepath)
            try:
                with open(filepath, "rb") as _file:
                    state = cPickle.load(_file)
            except (IOError, EOFError, cPickle.UnpicklingError) as ex:
                log.warning("Unable to load %s: %s", filepath, ex)
                state = None
            else:
                log.info("Successfully loaded %s", filepath)
                break

        if state is None:
            state = TorrentManagerState()
        return state

    def load_state(self):
        """Load all the torrents from TorrentManager state into session

        Emits:
            SessionStartedEvent: Emitted after all torrents are added to the session.

        """
        start = datetime.datetime.now()
        state = self.open_state()
        state = self.fixup_state(state)

        # Reorder the state.torrents list to add torrents in the correct queue order.
        state.torrents.sort(key=operator.attrgetter("queue"), reverse=self.config["queue_new_to_top"])
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
            options["download_location"] = t_state.save_path
            options["pre_allocate_storage"] = t_state.storage_mode == "allocate"
            options["prioritize_first_last_pieces"] = t_state.prioritize_first_last
            options["add_paused"] = t_state.paused

            magnet = t_state.magnet
            torrent_info = self.get_torrent_info_from_file(
                os.path.join(self.state_dir, t_state.torrent_id + ".torrent"))
            if torrent_info:
                magnet = None

            d = self.add(torrent_info=torrent_info, state=t_state, options=options, save_state=False,
                         magnet=magnet, resume_data=resume_data.get(t_state.torrent_id))
            deferreds.append(d)

        deferred_list = DeferredList(deferreds, consumeErrors=False)

        def on_complete(result):
            log.info("Finished loading %d torrents in %s", len(state.torrents), str(datetime.datetime.now() - start))
            component.get("EventManager").emit(SessionStartedEvent())
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
            elif torrent.state == "Paused":
                paused = True
            else:
                paused = False

            torrent_state = TorrentState(
                torrent.torrent_id,
                torrent.filename,
                torrent.trackers,
                torrent.get_status(["storage_mode"])["storage_mode"],
                paused,
                torrent.options["download_location"],
                torrent.options["max_connections"],
                torrent.options["max_upload_slots"],
                torrent.options["max_upload_speed"],
                torrent.options["max_download_speed"],
                torrent.options["prioritize_first_last_pieces"],
                torrent.options["sequential_download"],
                torrent.options["file_priorities"],
                torrent.get_queue_position(),
                torrent.options["auto_managed"],
                torrent.is_finished,
                torrent.options["stop_ratio"],
                torrent.options["stop_at_ratio"],
                torrent.options["remove_at_ratio"],
                torrent.options["move_completed"],
                torrent.options["move_completed_path"],
                torrent.magnet,
                torrent.options["owner"],
                torrent.options["shared"],
                torrent.options["super_seeding"],
                torrent.options["priority"],
                torrent.options["name"]
            )
            state.torrents.append(torrent_state)
        return state

    def save_state(self):
        """
        Run the save state task in a separate thread to avoid blocking main thread.

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
        if not state.torrents:
            log.debug("Skipping saving state with no torrents loaded")
            return

        filename = "torrents.state"
        filepath = os.path.join(self.state_dir, filename)
        filepath_bak = filepath + ".bak"
        filepath_tmp = filepath + ".tmp"

        try:
            log.debug("Creating the temporary file: %s", filepath_tmp)
            with open(filepath_tmp, "wb", 0) as _file:
                cPickle.dump(state, _file)
                _file.flush()
                os.fsync(_file.fileno())
        except (OSError, cPickle.PicklingError) as ex:
            log.error("Unable to save %s: %s", filename, ex)
            return

        try:
            log.debug("Creating backup of %s at: %s", filename, filepath_bak)
            if os.path.isfile(filepath_bak):
                os.remove(filepath_bak)
            if os.path.isfile(filepath):
                os.rename(filepath, filepath_bak)
        except OSError as ex:
            log.error("Unable to backup %s to %s: %s", filepath, filepath_bak, ex)
            return

        try:
            log.debug("Saving %s to: %s", filename, filepath)
            os.rename(filepath_tmp, filepath)
        except OSError as ex:
            log.error("Failed to set new state file %s: %s", filepath, ex)
            if os.path.isfile(filepath_bak):
                log.info("Restoring backup of state from: %s", filepath_bak)
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
            torrent_ids = (t[0] for t in self.torrents.iteritems() if t[1].handle.need_save_resume_data())

        def on_torrent_resume_save(dummy_result, torrent_id):
            """Recieved torrent resume_data alert so remove from waiting list"""
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
            """Saves resume data file when no more torrents waiting for resume data

            Returns:
                bool: True if fastresume file is saved.

                Used by remove_temp_file callback in stop.

            """
            # Use flush_disk_cache as a marker for shutdown so fastresume is
            # saved even if torrents are waiting.
            if not self.waiting_on_resume_data or flush_disk_cache:
                return self.save_resume_data_file()

        return DeferredList(deferreds).addBoth(on_all_resume_data_finished)

    def load_resume_data_file(self):
        """Load the resume data from file for all torrents

        Returns:
            dict: A dict of torrents and their resume_data

        """
        filename = "torrents.fastresume"
        filepath = os.path.join(self.state_dir, filename)
        filepath_bak = filepath + ".bak"
        old_data_filepath = os.path.join(get_config_dir(), filename)

        for _filepath in (filepath, filepath_bak, old_data_filepath):
            log.info("Opening %s for load: %s", filename, _filepath)
            try:
                with open(_filepath, "rb") as _file:
                    resume_data = lt.bdecode(_file.read())
            except (IOError, EOFError, RuntimeError) as ex:
                if self.torrents:
                    log.warning("Unable to load %s: %s", _filepath, ex)
                resume_data = None
            else:
                log.info("Successfully loaded %s: %s", filename, _filepath)
                break
        # If the libtorrent bdecode doesn't happen properly, it will return None
        # so we need to make sure we return a {}
        if resume_data is None:
            return {}
        else:
            return resume_data

    def save_resume_data_file(self):
        """Saves the resume data file with the contents of self.resume_data"""
        if not self.resume_data:
            return True

        filename = "torrents.fastresume"
        filepath = os.path.join(self.state_dir, filename)
        filepath_bak = filepath + ".bak"
        filepath_tmp = filepath + ".tmp"

        try:
            log.debug("Creating the temporary file: %s", filepath_tmp)
            with open(filepath_tmp, "wb", 0) as _file:
                _file.write(lt.bencode(self.resume_data))
                _file.flush()
                os.fsync(_file.fileno())
        except (OSError, EOFError) as ex:
            log.error("Unable to save %s: %s", filename, ex)
            return False

        try:
            log.debug("Creating backup of %s at: %s", filename, filepath_bak)
            if os.path.isfile(filepath_bak):
                os.remove(filepath_bak)
            if os.path.isfile(filepath):
                os.rename(filepath, filepath_bak)
        except OSError as ex:
            log.error("Unable to backup %s to %s: %s", filepath, filepath_bak, ex)
            return False

        try:
            log.debug("Saving %s to: %s", filename, filepath)
            os.rename(filepath_tmp, filepath)
        except OSError as ex:
            log.error("Failed to set new file %s: %s", filepath, ex)
            if os.path.isfile(filepath_bak):
                log.info("Restoring backup from: %s", filepath_bak)
                os.rename(filepath_bak, filepath)
        else:
            # Sync the rename operations for the directory
            if hasattr(os, 'O_DIRECTORY'):
                dirfd = os.open(os.path.dirname(filepath), os.O_DIRECTORY)
                os.fsync(dirfd)
                os.close(dirfd)
            return True

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
        if self.torrents[torrent_id].get_queue_position() == (len(self.queued_torrents) - 1):
            return False

        self.torrents[torrent_id].handle.queue_position_down()
        return True

    def queue_bottom(self, torrent_id):
        """Queue torrent to bottom"""
        if self.torrents[torrent_id].get_queue_position() == (len(self.queued_torrents) - 1):
            return False

        self.torrents[torrent_id].handle.queue_position_bottom()
        return True

    def cleanup_torrents_prev_status(self):
        """Run cleanup_prev_status for each registered torrent"""
        for torrent in self.torrents.iteritems():
            torrent[1].cleanup_prev_status()

    def on_set_max_connections_per_torrent(self, key, value):
        """Sets the per-torrent connection limit"""
        log.debug("max_connections_per_torrent set to %s...", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_connections(value)

    def on_set_max_upload_slots_per_torrent(self, key, value):
        """Sets the per-torrent upload slot limit"""
        log.debug("max_upload_slots_per_torrent set to %s...", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_upload_slots(value)

    def on_set_max_upload_speed_per_torrent(self, key, value):
        """Sets the per-torrent upload speed limit"""
        log.debug("max_upload_speed_per_torrent set to %s...", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_upload_speed(value)

    def on_set_max_download_speed_per_torrent(self, key, value):
        """Sets the per-torrent download speed limit"""
        log.debug("max_download_speed_per_torrent set to %s...", value)
        for key in self.torrents.keys():
            self.torrents[key].set_max_download_speed(value)

    # --- Alert handlers ---
    def on_alert_torrent_finished(self, alert):
        """Alert handler for libtorrent torrent_finished_alert"""
        log.debug("on_alert_torrent_finished")
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return
        log.debug("Finished %s ", torrent_id)

        # If total_download is 0, do not move, it's likely the torrent wasn't downloaded, but just added.
        # Get fresh data from libtorrent, the cache isn't always up to date
        total_download = torrent.get_status(["total_payload_download"], update=True)["total_payload_download"]

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Torrent settings: is_finished: %s, total_download: %s, move_completed: %s, move_path: %s",
                      torrent.is_finished, total_download, torrent.options["move_completed"],
                      torrent.options["move_completed_path"])

        torrent.update_state()
        if not torrent.is_finished and total_download:
            # Move completed download to completed folder if needed
            if torrent.options["move_completed"] and \
                    torrent.options["download_location"] != torrent.options["move_completed_path"]:
                self.waiting_on_finish_moving.append(torrent_id)
                torrent.move_storage(torrent.options["move_completed_path"])
            else:
                torrent.is_finished = True
                component.get("EventManager").emit(TorrentFinishedEvent(torrent_id))
        else:
            torrent.is_finished = True

        # Torrent is no longer part of the queue
        try:
            self.queued_torrents.remove(torrent_id)
        except KeyError:
            # Sometimes libtorrent fires a TorrentFinishedEvent twice
            if log.isEnabledFor(logging.DEBUG):
                log.debug("%s isn't in queued torrents set?", torrent_id)

        # Only save resume data if it was actually downloaded something. Helps
        # on startup with big queues with lots of seeding torrents. Libtorrent
        # emits alert_torrent_finished for them, but there seems like nothing
        # worth really to save in resume data, we just read it up in
        # self.load_state().
        if total_download:
            self.save_resume_data((torrent_id, ))

    def on_alert_torrent_paused(self, alert):
        """Alert handler for libtorrent torrent_paused_alert"""
        if log.isEnabledFor(logging.DEBUG):
            log.debug("on_alert_torrent_paused")
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
        if log.isEnabledFor(logging.DEBUG):
            log.debug("on_alert_torrent_checked")
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
        if log.isEnabledFor(logging.DEBUG):
            log.debug("on_alert_tracker_reply: %s", decode_string(alert.message()))
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return

        # Set the tracker status for the torrent
        torrent.set_tracker_status("Announce OK")

        # Check for peer information from the tracker, if none then send a scrape request.
        if alert.handle.status().num_complete == -1 or alert.handle.status().num_incomplete == -1:
            torrent.scrape_tracker()

    def on_alert_tracker_announce(self, alert):
        """Alert handler for libtorrent tracker_announce_alert"""
        if log.isEnabledFor(logging.DEBUG):
            log.debug("on_alert_tracker_announce")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return

        # Set the tracker status for the torrent
        torrent.set_tracker_status("Announce Sent")

    def on_alert_tracker_warning(self, alert):
        """Alert handler for libtorrent tracker_warning_alert"""
        log.debug("on_alert_tracker_warning")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return
        # Set the tracker status for the torrent
        torrent.set_tracker_status("Warning: %s" % decode_string(alert.message()))

    def on_alert_tracker_error(self, alert):
        """Alert handler for libtorrent tracker_error_alert"""
        error_message = decode_string(alert.msg)
        # If alert.msg is empty then it's a '-1' code so fallback to a.e.message. Note that alert.msg
        # cannot be replaced by a.e.message because the code is included in the string (for non-'-1').
        if not error_message:
            error_message = decode_string(alert.error.message())
        log.debug("Tracker Error Alert: %s [%s]", decode_string(alert.message()), error_message)
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return

        torrent.set_tracker_status("Error: " + error_message)

    def on_alert_storage_moved(self, alert):
        """Alert handler for libtorrent storage_moved_alert"""
        log.debug("on_alert_storage_moved")
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return
        torrent.set_download_location(os.path.normpath(alert.handle.save_path()))
        torrent.set_move_completed(False)
        torrent.moving_storage = False
        torrent.update_state()

        if torrent_id in self.waiting_on_finish_moving:
            self.waiting_on_finish_moving.remove(torrent_id)
            torrent.is_finished = True
            component.get("EventManager").emit(TorrentFinishedEvent(torrent_id))

    def on_alert_storage_moved_failed(self, alert):
        """Alert handler for libtorrent storage_moved_failed_alert"""
        log.warning("on_alert_storage_moved_failed: %s", decode_string(alert.message()))
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return
        # Set an Error message and pause the torrent
        alert_msg = decode_string(alert.message()).split(':', 1)[1].strip()
        torrent.moving_storage = False
        torrent.force_error_state("Failed to move download folder: %s" % alert_msg)

        if torrent_id in self.waiting_on_finish_moving:
            self.waiting_on_finish_moving.remove(torrent_id)
            torrent.is_finished = True
            component.get("EventManager").emit(TorrentFinishedEvent(torrent_id))

    def on_alert_torrent_resumed(self, alert):
        """Alert handler for libtorrent torrent_resumed_alert"""
        log.debug("on_alert_torrent_resumed")
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return
        torrent.update_state()
        component.get("EventManager").emit(TorrentResumedEvent(torrent_id))

    def on_alert_state_changed(self, alert):
        """Alert handler for libtorrent state_changed_alert
        Emits a TorrentStateChangedEvent if state has changed
        """
        if log.isEnabledFor(logging.DEBUG):
            log.debug("on_alert_state_changed")
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
        if log.isEnabledFor(logging.DEBUG):
            log.debug("on_alert_save_resume_data")
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
        log.debug("on_alert_save_resume_data_failed: %s", decode_string(alert.message()))
        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError:
            return

        if torrent_id in self.waiting_on_resume_data:
            self.waiting_on_resume_data[torrent_id].errback(Exception(decode_string(alert.message())))

    def on_alert_fastresume_rejected(self, alert):
        """Alert handler for libtorrent fastresume_rejected_alert"""
        alert_msg = decode_string(alert.message())
        log.error("on_alert_fastresume_rejected: %s", alert_msg)
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        if alert.error.value() == 134:
            if not os.path.isdir(torrent.options["download_location"]):
                error_msg = "Unable to locate Download Folder!"
            else:
                error_msg = "Missing or invalid torrent data!"
        else:
            error_msg = "Problem with resume data: %s" % alert_msg.split(":", 1)[1].strip()
        torrent.force_error_state(error_msg, restart_to_resume=True)

    def on_alert_file_renamed(self, alert):
        """Alert handler for libtorrent file_renamed_alert
        Emits a TorrentFileCompletedEvent for renamed files
        """
        log.debug("on_alert_file_renamed")
        log.debug("index: %s name: %s", alert.index, decode_string(alert.name))
        try:
            torrent_id = str(alert.handle.info_hash())
            torrent = self.torrents[torrent_id]
        except (RuntimeError, KeyError):
            return

        # We need to see if this file index is in a waiting_on_folder dict
        for wait_on_folder in torrent.waiting_on_folder_rename:
            if alert.index in wait_on_folder:
                wait_on_folder[alert.index].callback(None)
                break
        else:
            # This is just a regular file rename so send the signal
            component.get("EventManager").emit(TorrentFileRenamedEvent(torrent_id, alert.index, alert.name))
            self.save_resume_data((torrent_id,))

    def on_alert_metadata_received(self, alert):
        """Alert handler for libtorrent metadata_received_alert"""
        log.debug("on_alert_metadata_received")
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return
        torrent.on_metadata_received()

    def on_alert_file_error(self, alert):
        """Alert handler for libtorrent file_error_alert"""
        log.debug("on_alert_file_error: %s", decode_string(alert.message()))
        try:
            torrent = self.torrents[str(alert.handle.info_hash())]
        except (RuntimeError, KeyError):
            return
        torrent.update_state()

    def on_alert_file_completed(self, alert):
        """Alert handler for libtorrent file_completed_alert

        Emits a TorrentFileCompletedEvent when an individual file completes downloading

        """
        log.debug("file_completed_alert: %s", decode_string(alert.message()))
        try:
            torrent_id = str(alert.handle.info_hash())
        except RuntimeError:
            return
        if torrent_id in self.torrents:
            component.get("EventManager").emit(TorrentFileCompletedEvent(torrent_id, alert.index))

    def on_alert_state_update(self, alert):
        """Alert handler for libtorrent state_update_alert

        Result of a session.post_torrent_updates() call and contains the torrent status
        of all torrents that changed since last time this was posted.

        """
        log.debug("on_status_notification: %s", decode_string(alert.message()))
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
        """Alert handler for libtorrent external_ip_alert"""
        log.info("on_alert_external_ip: %s", decode_string(alert.message()))

    def on_alert_performance(self, alert):
        """Alert handler for libtorrent performance_alert"""
        log.warning("on_alert_performance: %s, %s", decode_string(alert.message()), alert.warning_code)
        if alert.warning_code == lt.performance_warning_t.send_buffer_watermark_too_low:
            max_send_buffer_watermark = 3 * 1024 * 1024  # 3MiB
            settings = self.session.get_settings()
            send_buffer_watermark = settings["send_buffer_watermark"]

            # If send buffer is too small, try increasing its size by 512KiB (up to max_send_buffer_watermark)
            if send_buffer_watermark < max_send_buffer_watermark:
                value = send_buffer_watermark + (500 * 1024)
                log.info("Increasing send_buffer_watermark from %s to %s Bytes", send_buffer_watermark, value)
                settings["send_buffer_watermark"] = value
                self.session.set_settings(settings)
            else:
                log.warning("send_buffer_watermark reached maximum value: %s Bytes", max_send_buffer_watermark)

    def separate_keys(self, keys, torrent_ids):
        """Separates the input keys into torrent class keys and plugins keys"""
        if self.torrents:
            for torrent_id in torrent_ids:
                if torrent_id in self.torrents:
                    status_keys = self.torrents[torrent_id].status_funcs.keys()
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
                status_dict[torrent_id] = self.torrents[torrent_id].get_status(torrent_keys, diff, all_keys=not keys)
        self.status_dict = status_dict
        d.callback((status_dict, plugin_keys))

    def torrents_status_update(self, torrent_ids, keys, diff=False):
        """Returns status dict for the supplied torrent_ids async

        Note:
            If torrent states was updated recently post_torrent_updates is not called and
            instead cached state is used.

        Args:
            torrent_ids (list of str): The torrent IDs to get the status of.
            keys (list of str): The keys to get the status on.
            diff (bool, optional): If True, will return a diff of the changes since the last call to get_status
                based on the session_id, defaults to False

        Returns:
            dict: A status dictionary for the requested torrents.

        """
        d = Deferred()
        now = time.time()
        # If last update was recent, use cached data instead of request updates from libtorrent
        if (now - self.last_state_update_alert_ts) < 1.5:
            reactor.callLater(0, self.handle_torrents_status_callback, (d, torrent_ids, keys, diff))
        else:
            # Ask libtorrent for status update
            self.torrents_status_requests.insert(0, (d, torrent_ids, keys, diff))
            self.session.post_torrent_updates()
        return d
