# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""Internal Torrent class

Attributes:
    LT_TORRENT_STATE_MAP (dict): Maps the torrent state from libtorrent to Deluge state.

"""

from __future__ import division

import logging
import os
import socket
from itertools import izip
from urlparse import urlparse

from twisted.internet.defer import Deferred, DeferredList

import deluge.component as component
from deluge._libtorrent import lt
from deluge.common import decode_string, utf8_encoded
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.event import TorrentFolderRenamedEvent, TorrentStateChangedEvent

log = logging.getLogger(__name__)

LT_TORRENT_STATE_MAP = {
    "queued_for_checking": "Checking",
    "checking_files": "Checking",
    "downloading_metadata": "Downloading",
    "downloading": "Downloading",
    "finished": "Seeding",
    "seeding": "Seeding",
    "allocating": "Allocating",
    "checking_resume_data": "Checking"
}


def sanitize_filepath(filepath, folder=False):
    """Returns a sanitized filepath to pass to libtorrent rename_file().

    The filepath will have backslashes substituted along with whitespace
    padding and duplicate slashes stripped.

    Args:
        folder (bool): A trailing slash is appended to the returned filepath.
    """
    def clean_filename(filename):
        """Strips whitespace and discards dotted filenames"""
        filename = filename.strip()
        if filename.replace(".", "") == "":
            return ""
        return filename

    if "\\" in filepath or "/" in filepath:
        folderpath = filepath.replace("\\", "/").split("/")
        folderpath = [clean_filename(x) for x in folderpath]
        newfilepath = "/".join([path for path in folderpath if path])
    else:
        newfilepath = clean_filename(filepath)

    if folder is True:
        newfilepath += "/"

    return newfilepath


def convert_lt_files(files):
    """Indexes and decodes files from libtorrent get_files().

    Args:
        files (list): The libtorrent torrent files.

    Returns:
        list of dict: The files.

        The format for the file dict::

            {
                "index": int,
                "path": str,
                "size": int,
                "offset": int
            }
    """
    filelist = []
    for index, _file in enumerate(files):
        filelist.append({
            "index": index,
            "path": _file.path.decode("utf8").replace("\\", "/"),
            "size": _file.size,
            "offset": _file.offset
        })

    return filelist


class TorrentOptions(dict):
    """TorrentOptions create a dict of the torrent options.

    Attributes:
        max_connections (int): Sets maximum number of connections this torrent will open.
            This must be at least 2. The default is unlimited (-1).
        max_upload_slots (int): Sets the maximum number of peers that are
            unchoked at the same time on this torrent. This defaults to infinite (-1).
        max_upload_speed (float): Will limit the upload bandwidth used by this torrent to the limit
            you set. The default is unlimited (-1) but will not exceed global limit.
        max_download_speed (float): Will limit the download bandwidth used by this torrent to the
            limit you set.The default is unlimited (-1) but will not exceed global limit.
        prioritize_first_last_pieces (bool): Prioritize the first and last pieces in the torrent.
        sequential_download (bool): Download the pieces of the torrent in order.
        pre_allocate_storage (bool): When adding the torrent should all files be pre-allocated.
        download_location (str): The path for the torrent data to be stored while downloading.
        auto_managed (bool): Set torrent to auto managed mode, i.e. will be started or queued automatically.
        stop_at_ratio (bool): Stop the torrent when it has reached stop_ratio.
        stop_ratio (float): The seeding ratio to stop (or remove) the torrent at.
        remove_at_ratio (bool): Remove the torrent when it has reached the stop_ratio.
        move_completed (bool): Move the torrent when downloading has finished.
        move_completed_path (str): The path to move torrent to when downloading has finished.
        add_paused (bool): Add the torrrent in a paused state.
        shared (bool): Enable the torrent to be seen by other Deluge users.
        super_seeding (bool): Enable super seeding/initial seeding.
        priority (int): Torrent bandwidth priority with a range [0..255], 0 is lowest and default priority.
        file_priorities (list of int): The priority for files in torrent, range is [0..7] however
            only [0, 1, 5, 7] are normally used and correspond to [Do Not Download, Normal, High, Highest]
        mapped_files (dict): A mapping of the renamed filenames in 'index:filename' pairs.
        owner (str): The user this torrent belongs to.
        name (str): The display name of the torrent.
        seed_mode (bool): Assume that all files are present for this torrent (Only used when adding a torent).
    """
    def __init__(self):
        super(TorrentOptions, self).__init__()
        config = ConfigManager("core.conf").config
        options_conf_map = {
            "max_connections": "max_connections_per_torrent",
            "max_upload_slots": "max_upload_slots_per_torrent",
            "max_upload_speed": "max_upload_speed_per_torrent",
            "max_download_speed": "max_download_speed_per_torrent",
            "prioritize_first_last_pieces": "prioritize_first_last_pieces",
            "sequential_download": "sequential_download",
            "pre_allocate_storage": "pre_allocate_storage",
            "download_location": "download_location",
            "auto_managed": "auto_managed",
            "stop_at_ratio": "stop_seed_at_ratio",
            "stop_ratio": "stop_seed_ratio",
            "remove_at_ratio": "remove_seed_at_ratio",
            "move_completed": "move_completed",
            "move_completed_path": "move_completed_path",
            "add_paused": "add_paused",
            "shared": "shared",
            "super_seeding": "super_seeding",
            "priority": "priority",
        }
        for opt_k, conf_k in options_conf_map.iteritems():
            self[opt_k] = config[conf_k]
        self["file_priorities"] = []
        self["mapped_files"] = {}
        self["owner"] = ""
        self["name"] = ""
        self["seed_mode"] = False


class Torrent(object):
    """Torrent holds information about torrents added to the libtorrent session.

    Args:
        handle: The libtorrent torrent handle.
        options (dict): The torrent options.
        state (TorrentState): The torrent state.
        filename (str): The filename of the torrent file.
        magnet (str): The magnet uri.

    Attributes:
        torrent_id (str): The torrent_id for this torrent
        handle: Holds the libtorrent torrent handle
        magnet (str): The magnet uri used to add this torrent (if available).
        status: Holds status info so that we don"t need to keep getting it from libtorrent.
        torrent_info: store the torrent info.
        has_metadata (bool): True if the metadata for the torrent is available, False otherwise.
        status_funcs (dict): The function mappings to get torrent status
        prev_status (dict): Previous status dicts returned for this torrent. We use this to return
            dicts that only contain changes from the previous.
            {session_id: status_dict, ...}
        waiting_on_folder_rename (list of dict): A list of Deferreds for file indexes we're waiting for file_rename
            alerts on. This is so we can send one folder_renamed signal instead of multiple file_renamed signals.
            [{index: Deferred, ...}, ...]
        options (dict): The torrent options.
        filename (str): The filename of the torrent file in case it is required.
        is_finished (bool): Keep track if torrent is finished to prevent some weird things on state load.
        statusmsg (str): Status message holds error info about the torrent
        state (str): The torrent's state
        trackers (list of dict): The torrent's trackers
        tracker_status (str): Status message of currently connected tracker
        tracker_host (str): Hostname of the currently connected tracker
        forcing_recheck (bool): Keep track if we're forcing a recheck of the torrent
        forcing_recheck_paused (bool): Keep track if we're forcing a recheck of the torrent so that
            we can re-pause it after its done if necessary
    """
    def __init__(self, handle, options, state=None, filename=None, magnet=None):
        self.torrent_id = str(handle.info_hash())
        if log.isEnabledFor(logging.DEBUG):
            log.debug("Creating torrent object %s", self.torrent_id)

        # Get the core config
        self.config = ConfigManager("core.conf")
        self.rpcserver = component.get("RPCServer")

        self.handle = handle
        self.handle.resolve_countries(True)

        self.magnet = magnet
        self.status = self.handle.status()

        try:
            self.torrent_info = self.handle.get_torrent_info()
        except RuntimeError:
            self.torrent_info = None

        self.has_metadata = self.status.has_metadata

        self.options = TorrentOptions()
        self.options.update(options)

        # Load values from state if we have it
        if state:
            self.set_trackers(state.trackers)
            self.filename = state.filename
            self.is_finished = state.is_finished
            last_sess_prepend = "[Error from Previous Session] "
            if state.error_statusmsg and not state.error_statusmsg.startswith(last_sess_prepend):
                self.error_statusmsg = last_sess_prepend + state.error_statusmsg
            else:
                self.error_statusmsg = state.error_statusmsg
        else:
            self.trackers = [tracker for tracker in self.handle.trackers()]
            self.is_finished = False
            # Use infohash as fallback.
            if not filename:
                self.filename = self.torrent_id
            else:
                self.filename = filename
            self.error_statusmsg = None

        self.statusmsg = "OK"
        self.state = None
        self.moving_storage = False
        self.moving_storage_dest_path = None
        self.tracker_status = ""
        self.tracker_host = None
        self.forcing_recheck = False
        self.forcing_recheck_paused = False
        self.status_funcs = None
        self.prev_status = {}
        self.waiting_on_folder_rename = []

        self.update_status(self.handle.status())
        self._create_status_funcs()
        self.set_options(self.options)

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Torrent object created.")

    def on_metadata_received(self):
        """Process the metadata received alert for this torrent"""
        self.has_metadata = True
        self.torrent_info = self.handle.get_torrent_info()
        if self.options["prioritize_first_last_pieces"]:
            self.set_prioritize_first_last_pieces(True)
        self.write_torrentfile()

    # --- Options methods ---
    def set_options(self, options):
        """Set the torrent options.

        Args:
            options (dict): Torrent options, see TorrentOptions class for valid keys.
        """
        # set_prioritize_first_last is called by set_file_priorities so only run if not in options
        skip_func = []
        if "file_priorities" in options:
            self.options["prioritize_first_last_pieces"] = options["prioritize_first_last_pieces"]
            skip_func.append("prioritize_first_last_pieces")

        for key, value in options.items():
            if key in self.options:
                options_set_func = getattr(self, "set_" + key, None)
                if options_set_func and key not in skip_func:
                    options_set_func(value)
                else:
                    # Update config options that do not have funcs
                    self.options[key] = value

    def get_options(self):
        """Get the torrent options.

        Returns:
            dict: the torrent options.
        """
        return self.options

    def set_max_connections(self, max_connections):
        """Sets maximum number of connections this torrent will open.

        Args:
            max_connections (int): Maximum number of connections
        """
        self.options["max_connections"] = int(max_connections)
        self.handle.set_max_connections(max_connections)

    def set_max_upload_slots(self, max_slots):
        """Sets maximum number of upload slots for this torrent.

        Args:
            max_slots (int): Maximum upload slots
        """
        self.options["max_upload_slots"] = int(max_slots)
        self.handle.set_max_uploads(max_slots)

    def set_max_upload_speed(self, m_up_speed):
        """Sets maximum upload speed for this torrent.

        Args:
            m_up_speed (float): Maximum upload speed in KiB/s.
        """
        self.options["max_upload_speed"] = m_up_speed
        if m_up_speed < 0:
            value = -1
        else:
            value = int(m_up_speed * 1024)
        self.handle.set_upload_limit(value)

    def set_max_download_speed(self, m_down_speed):
        """Sets maximum download speed for this torrent.

        Args:
            m_up_speed (float): Maximum download speed in KiB/s.
        """
        self.options["max_download_speed"] = m_down_speed
        if m_down_speed < 0:
            value = -1
        else:
            value = int(m_down_speed * 1024)
        self.handle.set_download_limit(value)

    def set_prioritize_first_last(self, prioritize):
        """Deprecated due to mismatch between option and func name."""
        self.set_prioritize_first_last_pieces(prioritize)

    def set_prioritize_first_last_pieces(self, prioritize):
        """Prioritize the first and last pieces in the torrent.

        Args:
            prioritize (bool): Prioritize the first and last pieces.

        Returns:
            tuple of lists: The prioritized pieces and the torrent piece priorities.
        """
        self.options["prioritize_first_last_pieces"] = prioritize
        if not prioritize:
            # If we are turning off this option, call set_file_priorities to
            # reset all the piece priorities
            self.set_file_priorities(self.options["file_priorities"])
            return
        if not self.has_metadata:
            return
        if self.get_status(["storage_mode"])["storage_mode"] == "compact":
            log.debug("Setting first/last priority with compact allocation does not work!")
            return
        # A list of priorities for each piece in the torrent
        priorities = self.handle.piece_priorities()
        prioritized_pieces = []
        t_info = self.torrent_info
        for i in range(t_info.num_files()):
            _file = t_info.file_at(i)
            two_percent_bytes = int(0.02 * _file.size)
            # Get the pieces for the byte offsets
            first_start = t_info.map_file(i, 0, 0).piece
            first_end = t_info.map_file(i, two_percent_bytes, 0).piece
            last_start = t_info.map_file(i, _file.size - two_percent_bytes, 0).piece
            last_end = t_info.map_file(i, max(_file.size - 1, 0), 0).piece

            first_end += 1
            last_end += 1
            prioritized_pieces.append((first_start, first_end))
            prioritized_pieces.append((last_start, last_end))

            # Set the pieces in our first and last ranges to priority 7
            # if they are not marked as do not download
            priorities[first_start:first_end] = [p and 7 for p in priorities[first_start:first_end]]
            priorities[last_start:last_end] = [p and 7 for p in priorities[last_start:last_end]]
        # Setting the priorites for all the pieces of this torrent
        self.handle.prioritize_pieces(priorities)
        return prioritized_pieces, priorities

    def set_sequential_download(self, set_sequencial):
        """Sets whether to download the pieces of the torrent in order.

        Args:
            set_sequencial (bool): Enable sequencial downloading.
        """
        if self.get_status(["storage_mode"])["storage_mode"] != "compact":
            self.options["sequential_download"] = set_sequencial
            self.handle.set_sequential_download(set_sequencial)
        else:
            self.options["sequential_download"] = False

    def set_auto_managed(self, auto_managed):
        """Set auto managed mode, i.e. will be started or queued automatically.

        Args:
            auto_managed (bool): Enable auto managed.
        """
        self.options["auto_managed"] = auto_managed
        if not (self.status.paused and not self.status.auto_managed):
            self.handle.auto_managed(auto_managed)
            self.update_state()

    def set_super_seeding(self, super_seeding):
        """Set super seeding/initial seeding.

        Args:
            super_seeding (bool): Enable super seeding.
        """
        if self.status.is_seeding:
            self.options["super_seeding"] = super_seeding
            self.handle.super_seeding(super_seeding)
        else:
            self.options["super_seeding"] = False

    def set_stop_ratio(self, stop_ratio):
        """The seeding ratio to stop (or remove) the torrent at.

        Args:
            stop_ratio (float): The seeding ratio.
        """
        self.options["stop_ratio"] = stop_ratio

    def set_stop_at_ratio(self, stop_at_ratio):
        """Stop the torrent when it has reached stop_ratio.

        Args:
            stop_at_ratio (bool): Stop the torrent.
        """
        self.options["stop_at_ratio"] = stop_at_ratio

    def set_remove_at_ratio(self, remove_at_ratio):
        """Remove the torrent when it has reached the stop_ratio.

        Args:
            remove_at_ratio (bool): Remove the torrent.
        """
        self.options["remove_at_ratio"] = remove_at_ratio

    def set_move_completed(self, move_completed):
        """Set whether to move the torrent when downloading has finished.

        Args:
            move_completed (bool): Move the torrent.

        """
        self.options["move_completed"] = move_completed

    def set_move_completed_path(self, move_completed_path):
        """Set the path to move torrent to when downloading has finished.

        Args:
            move_completed_path (str): The move path.
        """
        self.options["move_completed_path"] = move_completed_path

    def set_file_priorities(self, file_priorities):
        """Sets the file priotities.

        Args:
            file_priorities (list of int): List of file priorities
        """
        if not self.has_metadata:
            return
        if len(file_priorities) != self.torrent_info.num_files():
            log.debug("file_priorities len != num_files")
            self.options["file_priorities"] = self.handle.file_priorities()
            return

        if self.get_status(["storage_mode"])["storage_mode"] == "compact":
            log.warning("Setting file priority with compact allocation does not work!")
            self.options["file_priorities"] = self.handle.file_priorities()
            return

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Setting %s's file priorities: %s", self.torrent_id, file_priorities)

        self.handle.prioritize_files(file_priorities)

        if 0 in self.options["file_priorities"]:
            # We have previously marked a file 'Do Not Download'
            # Check to see if we have changed any 0's to >0 and change state accordingly
            for index, priority in enumerate(self.options["file_priorities"]):
                if priority == 0 and file_priorities[index] > 0:
                    # We have a changed 'Do Not Download' to a download priority
                    self.is_finished = False
                    self.update_state()
                    break

        # In case values in file_priorities were faulty (old state?)
        # we make sure the stored options are in sync
        self.options["file_priorities"] = self.handle.file_priorities()

        # Set the first/last priorities if needed
        if self.options["prioritize_first_last_pieces"]:
            self.set_prioritize_first_last_pieces(self.options["prioritize_first_last_pieces"])

    def set_save_path(self, download_location):
        """Deprecated, use set_download_location."""
        self.set_download_location(download_location)

    def set_download_location(self, download_location):
        """The location for downloading torrent data."""
        self.options["download_location"] = download_location

    def set_priority(self, priority):
        """Sets the bandwidth priority of this torrent.

        Bandwidth is not distributed strictly in order of priority, but the priority is used as a weight.
        Accepted priority range is [0..255] where 0 is lowest (and default) priority.

        priority (int): the torrent priority

        Raises:
            ValueError: If value of priority is not in range [0..255]
        """
        if 0 <= priority <= 255:
            self.options["priority"] = priority
            return self.handle.set_priority(priority)
        else:
            raise ValueError("Torrent priority, %s, is invalid, should be [0..255]", priority)

    def set_owner(self, account):
        """Sets the owner of this torrent.

        Only a user with admin level auth can change this value.
        """
        if self.rpcserver.get_session_auth_level() == AUTH_LEVEL_ADMIN:
            self.options["owner"] = account

    # End Options methods #

    def set_trackers(self, trackers):
        """Sets the trackers for this torrent.

        Args:
            trackers (list of dicts): A list of trackers.
        """
        if trackers is None:
            self.trackers = [tracker for tracker in self.handle.trackers()]
            self.tracker_host = None
            return

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Setting trackers for %s: %s", self.torrent_id, trackers)

        tracker_list = []

        for tracker in trackers:
            new_entry = lt.announce_entry(str(tracker["url"]))
            new_entry.tier = tracker["tier"]
            tracker_list.append(new_entry)
        self.handle.replace_trackers(tracker_list)

        # Print out the trackers
        if log.isEnabledFor(logging.DEBUG):
            log.debug("Trackers set for %s:", self.torrent_id)
            for tracker in self.handle.trackers():
                log.debug(" [tier %s]: %s", tracker["tier"], tracker["url"])
        # Set the tracker list in the torrent object
        self.trackers = trackers
        if len(trackers) > 0:
            # Force a re-announce if there is at least 1 tracker
            self.force_reannounce()
        self.tracker_host = None

    def set_tracker_status(self, status):
        """Sets the tracker status.

        Args:
            status (str): The tracker status.
        """
        self.tracker_status = status

    def update_state(self):
        """Updates the state, based on libtorrent's torrent state"""
        status = self.handle.status()
        session_is_paused = component.get("Core").session.is_paused()

        if status.error or self.error_statusmsg:
            self.state = "Error"
            # This will be reverted upon resuming.
            self.handle.auto_managed(False)
            if not status.paused:
                self.handle.pause()

            if status.error:
                self.set_error_statusmsg(decode_string(status.error))
                log.debug("Error state from lt: %s", self.error_statusmsg)
            else:
                # As this is not a libtorrent Error we should emit a state changed event
                component.get("EventManager").emit(TorrentStateChangedEvent(self.torrent_id, "Error"))
                log.debug("Error state forced by Deluge, error_statusmsg: %s", self.error_statusmsg)
            self.set_status_message(self.error_statusmsg)
        elif self.moving_storage:
            self.state = "Moving"
        elif not session_is_paused and status.paused and status.auto_managed:
            self.state = "Queued"
        elif session_is_paused or status.paused:
            self.state = "Paused"
        else:
            self.state = LT_TORRENT_STATE_MAP.get(str(status.state), str(status.state))

        if log.isEnabledFor(logging.DEBUG):
            log.debug("State from lt was: %s | Session is paused: %s", status.state, session_is_paused)
            log.debug("Torrent state set to '%s' (%s)", self.state, self.torrent_id)

    def set_status_message(self, message):
        """Sets the torrent status message.

        Args:
            message (str): The status message.

        """
        self.statusmsg = message

    def set_error_statusmsg(self, message):
        """Sets the torrent error status message.

        Note:
            This will force a torrent into an error state. It is used for
            setting those errors that are not covered by libtorrent.

        Args:
            message (str): The error status message.

        """
        self.error_statusmsg = message

    def get_eta(self):
        """Get the ETA for this torrent.

        Returns:
            int: The ETA in seconds.

        """
        status = self.status
        eta = 0
        if self.is_finished and self.options["stop_at_ratio"] and status.upload_payload_rate:
            # We're a seed, so calculate the time to the 'stop_share_ratio'
            eta = ((status.all_time_download * self.options["stop_ratio"]) -
                   status.all_time_upload) // status.upload_payload_rate
        elif status.download_payload_rate:
            left = status.total_wanted - status.total_wanted_done
            if left > 0:
                eta = left // status.download_payload_rate

        return eta

    def get_ratio(self):
        """Get the ratio of upload/download for this torrent.

        Returns:
            float: The ratio or -1.0 (for infinity).

        """
        if self.status.total_done > 0:
            return self.status.all_time_upload / self.status.total_done
        else:
            return -1.0

    def get_files(self):
        """Get the files this torrent contains.

        Returns:
            list of dict: The files.

        """
        if not self.has_metadata:
            return []

        files = self.torrent_info.files()
        return convert_lt_files(files)

    def get_orig_files(self):
        """Get the original filenames of files in this torrent.

        Returns:
            list of dict: The files with original filenames.

        """
        if not self.has_metadata:
            return []

        files = self.torrent_info.orig_files()
        return convert_lt_files(files)

    def get_peers(self):
        """Get the peers for this torrent.

        A list of peers and various information about them.

        Returns:
            list of dict: The peers.

            The format for the peer dict::

                {
                    "client": str,
                    "country": str,
                    "down_speed": int,
                    "ip": str,
                    "progress": float,
                    "seed": bool,
                    "up_speed": int
                }
        """
        ret = []
        peers = self.handle.get_peer_info()

        for peer in peers:
            # We do not want to report peers that are half-connected
            if peer.flags & peer.connecting or peer.flags & peer.handshake:
                continue

            client = decode_string(str(peer.client))
            # Make country a proper string
            country = str()
            for char in peer.country:
                if not char.isalpha():
                    country += " "
                else:
                    country += char

            ret.append({
                "client": client,
                "country": country,
                "down_speed": peer.payload_down_speed,
                "ip": "%s:%s" % (peer.ip[0], peer.ip[1]),
                "progress": peer.progress,
                "seed": peer.flags & peer.seed,
                "up_speed": peer.payload_up_speed,
            })

        return ret

    def get_queue_position(self):
        """Get the torrents queue position

        Returns:
            int: queue position
        """
        return self.handle.queue_position()

    def get_file_progress(self):
        """Calculates the file progress as a percentage.

        Returns:
            list of floats: The file progress (0.0 -> 1.0)
        """
        if not self.has_metadata:
            return 0.0
        return [progress / _file.size if _file.size else 0.0 for progress, _file in
                izip(self.handle.file_progress(), self.torrent_info.files())]

    def get_tracker_host(self):
        """Get the hostname of the currently connected tracker.

        If no tracker is connected, it uses the 1st tracker.

        Returns:
            str: The tracker host
        """
        if self.tracker_host:
            return self.tracker_host

        tracker = self.status.current_tracker
        if not tracker and self.trackers:
            tracker = self.trackers[0]["url"]

        if tracker:
            url = urlparse(tracker.replace("udp://", "http://"))
            if hasattr(url, "hostname"):
                host = (url.hostname or "DHT")
                # Check if hostname is an IP address and just return it if that's the case
                try:
                    socket.inet_aton(host)
                except socket.error:
                    pass
                else:
                    # This is an IP address because an exception wasn't raised
                    return url.hostname

                parts = host.split(".")
                if len(parts) > 2:
                    if parts[-2] in ("co", "com", "net", "org") or parts[-1] in ("uk"):
                        host = ".".join(parts[-3:])
                    else:
                        host = ".".join(parts[-2:])
                self.tracker_host = host
                return host
        return ""

    def get_magnet_uri(self):
        """Returns a magnet uri for this torrent"""
        return lt.make_magnet_uri(self.handle)

    def get_name(self):
        """The name of the torrent (distinct from the filenames).

        Note:
            Can be manually set in options through `name` key. If the key is
            reset to empty string "" it will return the original torrent name.

        Returns:
            str: the name of the torrent.

        """
        if not self.options["name"]:
            handle_name = self.handle.name()
            if handle_name:
                name = decode_string(handle_name)
            else:
                name = self.torrent_id
        else:
            name = self.options["name"]

        return name

    def get_progress(self):
        """The progress of this torrent's current task.

        Returns:
            float: The progress percentage (0 to 100).

        """

        def get_size(files, path):
            """Returns total size of 'files' currently located in 'path'"""
            files = [os.path.join(path, f) for f in files]
            return sum(os.stat(f).st_size for f in files if os.path.exists(f))

        if self.state == "Error":
            progress = 100.0
        elif self.moving_storage:
            # Check if torrent has downloaded any data yet.
            if self.status.total_done:
                torrent_files = [f["path"] for f in self.get_files()]
                dest_path_size = get_size(torrent_files, self.moving_storage_dest_path)
                progress = dest_path_size / self.status.total_done * 100
            else:
                progress = 100.0
        else:
            progress = self.status.progress * 100

        return progress

    def get_status(self, keys, diff=False, update=False, all_keys=False):
        """Returns the status of the torrent based on the keys provided

        Args:
            keys (list of str): the keys to get the status on
            diff (bool): Will return a diff of the changes since the last
                call to get_status based on the session_id
            update (bool): If True the status will be updated from libtorrent
                if False, the cached values will be returned

        Returns:
            dict: a dictionary of the status keys and their values
        """
        if update:
            self.update_status(self.handle.status())

        if all_keys:
            keys = self.status_funcs.keys()

        status_dict = {}

        for key in keys:
            status_dict[key] = self.status_funcs[key]()

        if diff:
            session_id = self.rpcserver.get_session_id()
            if session_id in self.prev_status:
                # We have a previous status dict, so lets make a diff
                status_diff = {}
                for key, value in status_dict.items():
                    if key in self.prev_status[session_id]:
                        if value != self.prev_status[session_id][key]:
                            status_diff[key] = value
                    else:
                        status_diff[key] = value

                self.prev_status[session_id] = status_dict
                return status_diff

            self.prev_status[session_id] = status_dict
            return status_dict

        return status_dict

    def update_status(self, status):
        """Updates the cached status.

        Args:
            status (libtorrent.torrent_status): a libtorrent torrent status
        """
        self.status = status

    def _create_status_funcs(self):
        """Creates the functions for getting torrent status"""
        self.status_funcs = {
            "active_time": lambda: self.status.active_time,
            "all_time_download": lambda: self.status.all_time_download,
            "storage_mode": lambda: self.status.storage_mode.name.split("_")[2],  # sparse, allocate or compact
            "distributed_copies": lambda: max(0.0, self.status.distributed_copies),
            "download_payload_rate": lambda: self.status.download_payload_rate,
            "file_priorities": lambda: self.options["file_priorities"],
            "hash": lambda: self.torrent_id,
            "is_auto_managed": lambda: self.options["auto_managed"],
            "is_finished": lambda: self.is_finished,
            "max_connections": lambda: self.options["max_connections"],
            "max_download_speed": lambda: self.options["max_download_speed"],
            "max_upload_slots": lambda: self.options["max_upload_slots"],
            "max_upload_speed": lambda: self.options["max_upload_speed"],
            "message": lambda: self.statusmsg,
            "move_on_completed_path": lambda: self.options["move_completed_path"],  # Depr, use move_completed_path
            "move_on_completed": lambda: self.options["move_completed"],  # Deprecated, use move_completed
            "move_completed_path": lambda: self.options["move_completed_path"],
            "move_completed": lambda: self.options["move_completed"],
            "next_announce": lambda: self.status.next_announce.seconds,
            "num_peers": lambda: self.status.num_peers - self.status.num_seeds,
            "num_seeds": lambda: self.status.num_seeds,
            "owner": lambda: self.options["owner"],
            "paused": lambda: self.status.paused,
            "prioritize_first_last": lambda: self.options["prioritize_first_last_pieces"],
            "sequential_download": lambda: self.options["sequential_download"],
            "progress": self.get_progress,
            "shared": lambda: self.options["shared"],
            "remove_at_ratio": lambda: self.options["remove_at_ratio"],
            "save_path": lambda: self.options["download_location"],  # Deprecated, use download_location
            "download_location": lambda: self.options["download_location"],
            "seeding_time": lambda: self.status.seeding_time,
            "seeds_peers_ratio": lambda: -1.0 if self.status.num_incomplete == 0 else
            self.status.num_complete / self.status.num_incomplete,  # Use -1.0 to signify infinity
            "seed_rank": lambda: self.status.seed_rank,
            "state": lambda: self.state,
            "stop_at_ratio": lambda: self.options["stop_at_ratio"],
            "stop_ratio": lambda: self.options["stop_ratio"],
            "time_added": lambda: self.status.added_time,
            "total_done": lambda: self.status.total_done,
            "total_payload_download": lambda: self.status.total_payload_download,
            "total_payload_upload": lambda: self.status.total_payload_upload,
            "total_peers": lambda: self.status.num_incomplete,
            "total_seeds": lambda: self.status.num_complete,
            "total_uploaded": lambda: self.status.all_time_upload,
            "total_wanted": lambda: self.status.total_wanted,
            "total_remaining": lambda: self.status.total_wanted - self.status.total_wanted_done,
            "tracker": lambda: self.status.current_tracker,
            "tracker_host": self.get_tracker_host,
            "trackers": lambda: self.trackers,
            "tracker_status": lambda: self.tracker_status,
            "upload_payload_rate": lambda: self.status.upload_payload_rate,
            "comment": lambda: decode_string(self.torrent_info.comment()) if self.has_metadata else "",
            "num_files": lambda: self.torrent_info.num_files() if self.has_metadata else 0,
            "num_pieces": lambda: self.torrent_info.num_pieces() if self.has_metadata else 0,
            "piece_length": lambda: self.torrent_info.piece_length() if self.has_metadata else 0,
            "private": lambda: self.torrent_info.priv() if self.has_metadata else False,
            "total_size": lambda: self.torrent_info.total_size() if self.has_metadata else 0,
            "eta": self.get_eta,
            "file_progress": self.get_file_progress,
            "files": self.get_files,
            "orig_files": self.get_orig_files,
            "is_seed": lambda: self.status.is_seeding,
            "peers": self.get_peers,
            "queue": lambda: self.status.queue_position,
            "ratio": self.get_ratio,
            "completed_time": lambda: self.status.completed_time,
            "last_seen_complete": lambda: self.status.last_seen_complete,
            "name": self.get_name,
            "pieces": self._get_pieces_info,
            "seed_mode": lambda: self.status.seed_mode,
            "super_seeding": lambda: self.status.super_seeding,
            "time_since_download": lambda: self.status.time_since_download,
            "time_since_upload": lambda: self.status.time_since_upload,
            "priority": lambda: self.status.priority,
        }

    def pause(self):
        """Pause this torrent.

        Returns:
            bool: True is successful, otherwise False.

        """
        # Turn off auto-management so the torrent will not be unpaused by lt queueing
        self.handle.auto_managed(False)
        if self.status.paused:
            # This torrent was probably paused due to being auto managed by lt
            # Since we turned auto_managed off, we should update the state which should
            # show it as 'Paused'.  We need to emit a torrent_paused signal because
            # the torrent_paused alert from libtorrent will not be generated.
            self.update_state()
            component.get("EventManager").emit(TorrentStateChangedEvent(self.torrent_id, "Paused"))
        else:
            try:
                self.handle.pause()
            except RuntimeError as ex:
                log.debug("Unable to pause torrent: %s", ex)
                return False
        return True

    def resume(self):
        """Resumes this torrent."""
        if self.status.paused and self.status.auto_managed:
            log.debug("Torrent is being auto-managed, cannot resume!")
            return

        # Reset the status message just in case of resuming an Error'd torrent
        self.set_status_message("OK")
        self.set_error_statusmsg(None)

        if self.status.is_finished:
            # If the torrent has already reached it's 'stop_seed_ratio' then do not do anything
            if self.options["stop_at_ratio"]:
                if self.get_ratio() >= self.options["stop_ratio"]:
                    # XXX: This should just be returned in the RPC Response, no event
                    return

        if self.options["auto_managed"]:
            # This torrent is to be auto-managed by lt queueing
            self.handle.auto_managed(True)

        try:
            self.handle.resume()
        except RuntimeError as ex:
            log.debug("Unable to resume torrent: %s", ex)

    def connect_peer(self, peer_ip, peer_port):
        """Manually add a peer to the torrent

        Args:
            peer_ip (str) : Peer IP Address
            peer_port (int): Peer Port

        Returns:
            bool: True is successful, otherwise False
        """
        try:
            self.handle.connect_peer((peer_ip, int(peer_port)), 0)
        except RuntimeError as ex:
            log.debug("Unable to connect to peer: %s", ex)
            return False
        return True

    def move_storage(self, dest):
        """Move a torrent's storage location

        Args:
            dest (str): The destination folder for the torrent data

        Returns:
            bool: True if successful, otherwise False

        """
        dest = decode_string(dest)

        if not os.path.exists(dest):
            try:
                os.makedirs(dest)
            except IOError as ex:
                log.error("Could not move storage for torrent %s since %s does "
                          "not exist and could not create the directory: %s",
                          self.torrent_id, dest, ex)
                return False

        try:
            # libtorrent needs unicode object if wstrings are enabled, utf8 bytestring otherwise
            try:
                self.handle.move_storage(dest)
            except TypeError:
                self.handle.move_storage(utf8_encoded(dest))
        except RuntimeError as ex:
            log.error("Error calling libtorrent move_storage: %s", ex)
            return False
        self.moving_storage = True
        self.moving_storage_dest_path = dest
        self.update_state()
        return True

    def save_resume_data(self, flush_disk_cache=False):
        """Signals libtorrent to build resume data for this torrent.

        Args:
            flush_disk_cache (bool): Avoids potential issue with file timestamps
                and is only needed when stopping the session.

        Returns:
            None: The response with resume data is returned in a libtorrent save_resume_data_alert.

        """
        flags = lt.save_resume_flags_t.flush_disk_cache if flush_disk_cache else 0
        self.handle.save_resume_data(flags)

    def write_torrentfile(self, filename=None, filedump=None):
        """Writes the torrent file to the state dir and optional 'copy of' dir.

        Args:
            filename (str, optional): The filename of the torrent file.
            filedump (str, optional): bencoded filedump of a torrent file.

        """

        def write_file(filepath, filedump):
            log.debug("Writing torrent file to: %s", filepath)
            try:
                with open(filepath, "wb") as save_file:
                    save_file.write(filedump)
            except IOError as ex:
                log.error("Unable to save torrent file to: %s", ex)

        filepath = os.path.join(get_config_dir(), "state", self.torrent_id + ".torrent")
        # Regenerate the file priorities
        self.set_file_priorities([])
        if filedump is None:
            metadata = lt.bdecode(self.torrent_info.metadata())
            torrent_file = {"info": metadata}
            filedump = lt.bencode(torrent_file)
        write_file(filepath, filedump)

        # If the user has requested a copy of the torrent be saved elsewhere we need to do that.
        if self.config["copy_torrent_file"]:
            if filename is None:
                filename = self.get_name() + ".torrent"
            filepath = os.path.join(self.config["torrentfiles_location"], filename)
            write_file(filepath, filedump)

    def delete_torrentfile(self):
        """Deletes the .torrent file in the state directory in config"""
        path = os.path.join(get_config_dir(), "state", self.torrent_id + ".torrent")
        log.debug("Deleting torrent file: %s", path)
        try:
            os.remove(path)
        except OSError as ex:
            log.warning("Unable to delete the torrent file: %s", ex)

    def force_reannounce(self):
        """Force a tracker reannounce"""
        try:
            self.handle.force_reannounce()
        except RuntimeError as ex:
            log.debug("Unable to force reannounce: %s", ex)
            return False
        return True

    def scrape_tracker(self):
        """Scrape the tracker

         A scrape request queries the tracker for statistics such as total
         number of incomplete peers, complete peers, number of downloads etc.
        """
        try:
            self.handle.scrape_tracker()
        except RuntimeError as ex:
            log.debug("Unable to scrape tracker: %s", ex)
            return False
        return True

    def force_recheck(self):
        """Forces a recheck of the torrent's pieces"""
        paused = self.status.paused
        try:
            self.handle.force_recheck()
            self.handle.resume()
        except RuntimeError as ex:
            log.debug("Unable to force recheck: %s", ex)
            return False
        self.forcing_recheck = True
        self.forcing_recheck_paused = paused
        return True

    def rename_files(self, filenames):
        """Renames files in the torrent.

        Args:
            filenames (list): A list of (index, filename) pairs.
        """
        for index, filename in filenames:
            # Make sure filename is a unicode object
            filename = sanitize_filepath(decode_string(filename))
            # libtorrent needs unicode object if wstrings are enabled, utf8 bytestring otherwise
            try:
                self.handle.rename_file(index, filename)
            except TypeError:
                self.handle.rename_file(index, utf8_encoded(filename))

    def rename_folder(self, folder, new_folder):
        """Renames a folder within a torrent.

        This basically does a file rename on all of the folders children.

        Args:
            folder (str): The orignal folder name
            new_folder (str): The new folder name

        Returns:
            twisted.internet.defer.Deferred: A deferred which fires when the rename is complete
        """
        log.debug("Attempting to rename folder: %s to %s", folder, new_folder)
        if len(new_folder) < 1:
            log.error("Attempting to rename a folder with an invalid folder name: %s", new_folder)
            return

        new_folder = sanitize_filepath(new_folder, folder=True)

        def on_file_rename_complete(dummy_result, wait_dict, index):
            """File rename complete"""
            wait_dict.pop(index, None)

        wait_on_folder = {}
        self.waiting_on_folder_rename.append(wait_on_folder)
        for _file in self.get_files():
            if _file["path"].startswith(folder):
                # Keep track of filerenames we're waiting on
                wait_on_folder[_file["index"]] = Deferred().addBoth(
                    on_file_rename_complete, wait_on_folder, _file["index"]
                )
                new_path = _file["path"].replace(folder, new_folder, 1)
                try:
                    self.handle.rename_file(_file["index"], new_path)
                except TypeError:
                    self.handle.rename_file(_file["index"], utf8_encoded(new_path))

        def on_folder_rename_complete(dummy_result, torrent, folder, new_folder):
            """Folder rename complete"""
            component.get("EventManager").emit(TorrentFolderRenamedEvent(torrent.torrent_id, folder, new_folder))
            # Empty folders are removed after libtorrent folder renames
            self.remove_empty_folders(folder)
            torrent.waiting_on_folder_rename = [_dir for _dir in torrent.waiting_on_folder_rename if _dir]
            component.get("TorrentManager").save_resume_data((self.torrent_id,))

        d = DeferredList(wait_on_folder.values())
        d.addBoth(on_folder_rename_complete, self, folder, new_folder)
        return d

    def remove_empty_folders(self, folder):
        """Recursively removes folders but only if they are empty.

        This cleans up after libtorrent folder renames.

        Args:
            folder (str): The folder to recursively check
        """
        # Removes leading slashes that can cause join to ignore download_location
        download_location = self.options["download_location"]
        folder_full_path = os.path.normpath(os.path.join(download_location, folder.lstrip("\\/")))

        try:
            if not os.listdir(folder_full_path):
                os.removedirs(folder_full_path)
                log.debug("Removed Empty Folder %s", folder_full_path)
            else:
                for root, dirs, dummy_files in os.walk(folder_full_path, topdown=False):
                    for name in dirs:
                        try:
                            os.removedirs(os.path.join(root, name))
                            log.debug("Removed Empty Folder %s", os.path.join(root, name))
                        except OSError as ex:
                            log.debug(ex)

        except OSError as ex:
            log.debug("Cannot Remove Folder: %s", ex)

    def cleanup_prev_status(self):
        """Checks the validity of the keys in the prev_status dict.

        If the key is no longer valid, the dict will be deleted.
        """
        for key in self.prev_status.keys():
            if not self.rpcserver.is_session_valid(key):
                del self.prev_status[key]

    def _get_pieces_info(self):
        """Get the pieces for this torrent."""
        if not self.has_metadata or self.status.is_seeding:
            pieces = None
        else:
            pieces = []
            for piece, avail_piece in izip(self.status.pieces, self.handle.piece_availability()):
                if piece:
                    pieces.append(3)  # Completed.
                elif avail_piece:
                    pieces.append(1)  # Available, just not downloaded nor being downloaded.
                else:
                    pieces.append(0)  # Missing, no known peer with piece, or not asked for yet.

            for peer_info in self.handle.get_peer_info():
                if peer_info.downloading_piece_index >= 0:
                    pieces[peer_info.downloading_piece_index] = 2  # Being downloaded from peer.

        return pieces
