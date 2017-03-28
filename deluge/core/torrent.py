#
# torrent.py
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

"""Internal Torrent class"""

from __future__ import with_statement

import os
import time
from urllib import unquote
from urlparse import urlparse

from deluge._libtorrent import lt

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.log import LOG as log
from deluge.event import *

TORRENT_STATE = deluge.common.TORRENT_STATE

def sanitize_filepath(filepath, folder=False):
    """
    Returns a sanitized filepath to pass to libotorrent rename_file().
    The filepath will have backslashes substituted along with whitespace
    padding and duplicate slashes stripped. If `folder` is True a trailing
    slash is appended to the returned filepath.
    """
    def clean_filename(filename):
        filename = filename.strip()
        if filename.replace('.', '') == '':
            return ''
        return filename

    if '\\' in filepath or '/' in filepath:
        folderpath = filepath.replace('\\', '/').split('/')
        folderpath = [clean_filename(x) for x in folderpath]
        newfilepath = '/'.join(filter(None, folderpath))
    else:
        newfilepath = clean_filename(filepath)

    if folder is True:
        return newfilepath + '/'
    else:
        return newfilepath

class TorrentOptions(dict):
    def __init__(self):
        config = ConfigManager("core.conf").config
        options_conf_map = {
                            "max_connections": "max_connections_per_torrent",
                            "max_upload_slots": "max_upload_slots_per_torrent",
                            "max_upload_speed": "max_upload_speed_per_torrent",
                            "max_download_speed": "max_download_speed_per_torrent",
                            "prioritize_first_last_pieces": "prioritize_first_last_pieces",
                            "compact_allocation": "compact_allocation",
                            "download_location": "download_location",
                            "auto_managed": "auto_managed",
                            "stop_at_ratio": "stop_seed_at_ratio",
                            "stop_ratio": "stop_seed_ratio",
                            "remove_at_ratio": "remove_seed_at_ratio",
                            "move_completed": "move_completed",
                            "move_completed_path": "move_completed_path",
                            "add_paused": "add_paused",
                           }
        for opt_k, conf_k in options_conf_map.iteritems():
            self[opt_k] = config[conf_k]
        self["file_priorities"] = []
        self["mapped_files"] = {}


class TorrentError(object):
    def __init__(self, error_message, was_paused=False, restart_to_resume=False):
        self.error_message = error_message
        self.was_paused = was_paused
        self.restart_to_resume = restart_to_resume


class Torrent(object):
    """Torrent holds information about torrents added to the libtorrent session.
    """
    def __init__(self, handle, options, state=None, filename=None, magnet=None):
        log.debug("Creating torrent object %s", str(handle.info_hash()))
        # Get the core config
        self.config = ConfigManager("core.conf")

        self.rpcserver = component.get("RPCServer")

        # This dict holds previous status dicts returned for this torrent
        # We use this to return dicts that only contain changes from the previous
        # {session_id: status_dict, ...}
        self.prev_status = {}
        from twisted.internet.task import LoopingCall
        self.prev_status_cleanup_loop = LoopingCall(self.cleanup_prev_status)
        self.prev_status_cleanup_loop.start(10)

        # Set the libtorrent handle
        self.handle = handle
        # Set the torrent_id for this torrent
        self.torrent_id = str(handle.info_hash())

        # Let's us know if we're waiting on a lt alert
        self.waiting_on_resume_data = False

        # Keep a list of file indexes we're waiting for file_rename alerts on
        # This also includes the old_folder and new_folder to know what signal to send
        # This is so we can send one folder_renamed signal instead of multiple
        # file_renamed signals.
        # [(old_folder, new_folder, [*indexes]), ...]
        self.waiting_on_folder_rename = []

        # We store the filename just in case we need to make a copy of the torrentfile
        if not filename:
            # If no filename was provided, then just use the infohash
            filename = self.torrent_id

        self.filename = filename

        # Store the magnet uri used to add this torrent if available
        self.magnet = magnet

        # Torrent state e.g. Paused, Downloading, etc.
        self.state = None

        # Holds status info so that we don't need to keep getting it from lt
        self.status = self.handle.status()

        try:
            self.torrent_info = self.handle.get_torrent_info()
        except RuntimeError:
            self.torrent_info = None

        # Default total_uploaded to 0, this may be changed by the state
        self.total_uploaded = 0

        # Set the default options
        self.options = TorrentOptions()
        self.options.update(options)

        # We need to keep track if the torrent is finished in the state to prevent
        # some weird things on state load.
        self.is_finished = False

        # Load values from state if we have it
        if state:
            # This is for saving the total uploaded between sessions
            self.total_uploaded = state.total_uploaded
            # Set the trackers
            self.set_trackers(state.trackers)
            # Set the filename
            self.filename = state.filename
            self.is_finished = state.is_finished
        else:
            # Set trackers from libtorrent
            self.set_trackers(None)

        # Various torrent options
        self.handle.resolve_countries(True)

        # Details of torrent forced into error state (i.e. not by libtorrent).
        self.forced_error = None

        # Status message holds error info about the torrent
        self.statusmsg = "OK"

        self.set_options(self.options)

        # The torrents state
        self.update_state()

        # The tracker status
        self.tracker_status = ""

        # This gets updated when get_tracker_host is called
        self.tracker_host = None

        if state:
            self.time_added = state.time_added
        else:
            self.time_added = time.time()

        # Keep track if we're forcing a recheck of the torrent so that we can
        # repause it after its done if necessary
        self.forcing_recheck = False
        self.forcing_recheck_paused = False

    ## Options methods ##
    def set_options(self, options):
        OPTIONS_FUNCS = {
            # Functions used for setting options
            "auto_managed": self.set_auto_managed,
            "download_location": self.set_save_path,
            "file_priorities": self.set_file_priorities,
            "max_connections": self.handle.set_max_connections,
            "max_download_speed": self.set_max_download_speed,
            "max_upload_slots": self.handle.set_max_uploads,
            "max_upload_speed": self.set_max_upload_speed,
            "prioritize_first_last_pieces": self.set_prioritize_first_last
        }
        for (key, value) in options.items():
            if OPTIONS_FUNCS.has_key(key):
                OPTIONS_FUNCS[key](value)

        self.options.update(options)

    def get_options(self):
        return self.options


    def set_max_connections(self, max_connections):
        if max_connections == 0:
            max_connections = -1
        elif max_connections == 1:
            max_connections = 2
        self.options["max_connections"] = int(max_connections)
        self.handle.set_max_connections(max_connections)

    def set_max_upload_slots(self, max_slots):
        self.options["max_upload_slots"] = int(max_slots)
        self.handle.set_max_uploads(max_slots)

    def set_max_upload_speed(self, m_up_speed):
        self.options["max_upload_speed"] = m_up_speed
        if m_up_speed < 0:
            v = -1
        else:
            v = int(m_up_speed * 1024)

        self.handle.set_upload_limit(v)

    def set_max_download_speed(self, m_down_speed):
        self.options["max_download_speed"] = m_down_speed
        if m_down_speed < 0:
            v = -1
        else:
            v = int(m_down_speed * 1024)
        self.handle.set_download_limit(v)

    def set_prioritize_first_last(self, prioritize):
        if prioritize:
            if self.handle.has_metadata():
                if self.handle.get_torrent_info().num_files() == 1:
                    # We only do this if one file is in the torrent
                    self.options["prioritize_first_last_pieces"] = prioritize
                    priorities = [1] * self.handle.get_torrent_info().num_pieces()
                    priorities[0] = 7
                    priorities[-1] = 7
                    self.handle.prioritize_pieces(priorities)

    def set_auto_managed(self, auto_managed):
        self.options["auto_managed"] = auto_managed
        if not (self.handle.is_paused() and not self.handle.is_auto_managed()):
            self.handle.auto_managed(auto_managed)
            self.update_state()

    def set_stop_ratio(self, stop_ratio):
        self.options["stop_ratio"] = stop_ratio

    def set_stop_at_ratio(self, stop_at_ratio):
        self.options["stop_at_ratio"] = stop_at_ratio

    def set_remove_at_ratio(self, remove_at_ratio):
        self.options["remove_at_ratio"] = remove_at_ratio

    def set_move_completed(self, move_completed):
        self.options["move_completed"] = move_completed

    def set_move_completed_path(self, move_completed_path):
        self.options["move_completed_path"] = move_completed_path

    def set_file_priorities(self, file_priorities):
        handle_file_priorities = self.handle.file_priorities()
        # Workaround for libtorrent 1.1 changing default priorities from 1 to 4.
        if 4 in handle_file_priorities:
           handle_file_priorities = [1 if x == 4 else x for x in handle_file_priorities]

        log.debug("setting %s's file priorities: %s", self.torrent_id, file_priorities)

        if (self.handle.has_metadata() and not self.options["compact_allocation"] and
                file_priorities and len(file_priorities) == len(self.get_files())):
            self.handle.prioritize_files(file_priorities)
        else:
            log.debug("Unable to set new file priorities.")
            file_priorities = handle_file_priorities

        if 0 in self.options["file_priorities"]:
            # We have previously marked a file 'Do Not Download'
            # Check to see if we have changed any 0's to >0 and change state accordingly
            for index, priority in enumerate(self.options["file_priorities"]):
                if priority == 0 and file_priorities[index] > 0:
                    # We have a changed 'Do Not Download' to a download priority
                    self.is_finished = False
                    self.update_state()
                    break

        self.options["file_priorities"] = self.handle.file_priorities()
        if self.options["file_priorities"] != list(file_priorities):
            log.warning("File priorities were not set for this torrent")

        # Set the first/last priorities if needed
        self.set_prioritize_first_last(self.options["prioritize_first_last_pieces"])

    def set_trackers(self, trackers, reannounce=True):
        """Sets trackers"""
        if trackers == None:
            trackers = []
            for value in self.handle.trackers():
                if lt.version_major == 0 and lt.version_minor < 15:
                    tracker = {}
                    tracker["url"] = value.url
                    tracker["tier"] = value.tier
                else:
                    tracker = value
                    # These unused lt 1.1.2 tracker datetime entries need to be None for rencode.
                    tracker["min_announce"] = tracker["next_announce"] = None
                trackers.append(tracker)
            self.trackers = trackers
            self.tracker_host = None
            return

        log.debug("Setting trackers for %s: %s", self.torrent_id, trackers)
        tracker_list = []

        for idx, tracker in enumerate(trackers):
            new_entry = lt.announce_entry(tracker["url"])
            new_entry.tier = tracker["tier"]
            tracker_list.append(new_entry)
            # These unused lt 1.1.2 tracker datetime entries need to be None for rencode.
            trackers[idx]["min_announce"] = trackers[idx]["next_announce"] = None

        self.handle.replace_trackers(tracker_list)

        # Print out the trackers
        #for t in self.handle.trackers():
        #    log.debug("tier: %s tracker: %s", t["tier"], t["url"])
        # Set the tracker list in the torrent object
        self.trackers = trackers
        if len(trackers) > 0 and reannounce:
            # Force a reannounce if there is at least 1 tracker
            self.force_reannounce()

        self.tracker_host = None

    ### End Options methods ###

    def set_save_path(self, save_path):
        self.options["download_location"] = save_path

    def set_tracker_status(self, status):
        """Sets the tracker status"""
        self.tracker_host = None
        self.tracker_status = self.get_tracker_host() + ": " + status

    def update_state(self):
        """Updates the state based on what libtorrent's state for the torrent is"""
        # Set the initial state based on the lt state
        LTSTATE = deluge.common.LT_TORRENT_STATE
        status = self.handle.status()
        ltstate = status.state

        # Set self.state to the ltstate right away just incase we don't hit some of the logic below
        old_state = self.state
        self.state = LTSTATE.get(int(ltstate), str(ltstate))

        is_paused = self.handle.is_paused()
        is_auto_managed = self.handle.is_auto_managed()
        session_paused = component.get("Core").session.is_paused()

        # First we check for an error from libtorrent, and set the state to that
        # if any occurred.
        if self.forced_error:
            self.state = "Error"
            self.set_status_message("Error: " + self.forced_error.error_message)
        elif status.error:
            # This is an error'd torrent
            self.state = "Error"
            self.set_status_message(status.error)
            if is_paused:
                self.handle.auto_managed(False)
        else:
            if is_paused and is_auto_managed and not session_paused:
                self.state = "Queued"
            elif is_paused or session_paused:
                self.state = "Paused"
            elif ltstate == LTSTATE["Queued"] or ltstate == LTSTATE["Checking"] or \
                    ltstate == LTSTATE["Checking Resume Data"]:
                self.state = "Checking"
            elif ltstate == LTSTATE["Downloading"] or ltstate == LTSTATE["Downloading Metadata"]:
                self.state = "Downloading"
            elif ltstate == LTSTATE["Finished"] or ltstate == LTSTATE["Seeding"]:
                self.state = "Seeding"
            elif ltstate == LTSTATE["Allocating"]:
                self.state = "Allocating"

        if self.state != old_state:
            log.debug("Using torrent state from lt: %s, auto_managed: %s, paused: %s, session_paused: %s",
                      ltstate, is_auto_managed, is_paused, session_paused)
            log.debug("Torrent %s set from %s to %s: '%s'",
                      self.torrent_id, old_state, self.state, self.statusmsg)
            component.get("EventManager").emit(TorrentStateChangedEvent(self.torrent_id, self.state))

    def set_state(self, state):
        """Accepts state strings, ie, "Paused", "Seeding", etc."""
        if state not in TORRENT_STATE:
            log.debug("Trying to set an invalid state %s", state)
            return

        self.state = state
        return

    def set_status_message(self, message):
        self.statusmsg = message

    def force_error_state(self, message, restart_to_resume=True):
        """Forces the torrent into an error state.

        For setting an error state not covered by libtorrent.

        Args:
            message (str): The error status message.
            restart_to_resume (bool, optional): Prevent resuming clearing the error, only restarting
                session can resume.
        """
        status = self.handle.status()
        self.handle.auto_managed(False)
        self.forced_error = TorrentError(message, status.paused, restart_to_resume)
        if not status.paused:
            self.handle.pause()
        self.update_state()

    def clear_forced_error_state(self, update_state=True):
        if not self.forced_error:
            return

        if self.forced_error.restart_to_resume:
            log.error("Restart deluge to clear this torrent error")

        if not self.forced_error.was_paused and self.options["auto_managed"]:
            self.handle.auto_managed(True)
        self.forced_error = None
        self.set_status_message("OK")
        if update_state:
            self.update_state()

    def get_eta(self):
        """Returns the ETA in seconds for this torrent"""
        if self.status == None:
            status = self.handle.status()
        else:
            status = self.status

        if self.is_finished and self.options["stop_at_ratio"]:
            # We're a seed, so calculate the time to the 'stop_share_ratio'
            if not status.upload_payload_rate:
                return 0
            stop_ratio = self.options["stop_ratio"]
            return ((status.all_time_download * stop_ratio) - status.all_time_upload) / status.upload_payload_rate

        left = status.total_wanted - status.total_wanted_done

        if left <= 0 or status.download_payload_rate == 0:
            return 0

        try:
            eta = left / status.download_payload_rate
        except ZeroDivisionError:
            eta = 0

        return eta

    def get_ratio(self):
        """Returns the ratio for this torrent"""
        if self.status == None:
            status = self.handle.status()
        else:
            status = self.status

        if status.total_done > 0:
            # We use 'total_done' if the downloaded value is 0
            downloaded = status.total_done
        else:
            # Return -1.0 to signify infinity
            return -1.0

        return float(status.all_time_upload) / float(downloaded)

    def get_files(self):
        """Returns a list of files this torrent contains"""
        if self.torrent_info == None and self.handle.has_metadata():
            torrent_info = self.handle.get_torrent_info()
        else:
            torrent_info = self.torrent_info

        if not torrent_info:
            return []

        ret = []
        files = torrent_info.files()
        for index, file in enumerate(files):
            ret.append({
                'index': index,
                # Make path separators consistent across platforms
                'path': file.path.decode("utf8").replace('\\', '/'),
                'size': file.size,
                'offset': file.offset
            })
        return ret

    def get_peers(self):
        """Returns a list of peers and various information about them"""
        ret = []
        peers = self.handle.get_peer_info()

        for peer in peers:
            # We do not want to report peers that are half-connected
            if peer.flags & peer.connecting or peer.flags & peer.handshake:
                continue
            try:
                client = str(peer.client).decode("utf-8")
            except UnicodeDecodeError:
                client = str(peer.client).decode("latin-1")

            try:
                country = component.get("Core").geoip_instance.country_code_by_addr(peer.ip[0])
            except AttributeError:
                country = peer.country

            try:
                country = "".join([char if char.isalpha() else " " for char in country])
            except TypeError:
                country = ""

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
        """Returns the torrents queue position"""
        return self.handle.queue_position()

    def get_file_priorities(self):
        """Return the file priorities"""
        if not self.handle.has_metadata():
            return []

        if not self.options["file_priorities"]:
            # Ensure file_priorities option is populated.
            self.set_file_priorities([])

        return self.options["file_priorities"]

    def get_file_progress(self):
        """Returns the file progress as a list of floats.. 0.0 -> 1.0"""
        if not self.handle.has_metadata():
            return []

        file_progress = self.handle.file_progress()
        ret = []
        for i,f in enumerate(self.get_files()):
            try:
                ret.append(float(file_progress[i]) / float(f["size"]))
            except ZeroDivisionError:
                ret.append(0.0)
            except IndexError:
                return []

        return ret

    def get_tracker_host(self):
        """Returns just the hostname of the currently connected tracker
        if no tracker is connected, it uses the 1st tracker."""
        if self.tracker_host:
            return self.tracker_host

        if not self.status:
            self.status = self.handle.status()

        tracker = self.status.current_tracker
        if not tracker and self.trackers:
            tracker = self.trackers[0]["url"]

        if tracker:
            url = urlparse(tracker.replace("udp://", "http://"))
            if hasattr(url, "hostname"):
                host = (url.hostname or 'DHT')
                # Check if hostname is an IP address and just return it if that's the case
                import socket
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

    def get_status(self, keys, diff=False):
        """
        Returns the status of the torrent based on the keys provided

        :param keys: the keys to get the status on
        :type keys: list of str
        :param diff: if True, will return a diff of the changes since the last
        call to get_status based on the session_id
        :type diff: bool

        :returns: a dictionary of the status keys and their values
        :rtype: dict

        """

        # Create the full dictionary
        self.status = self.handle.status()
        if self.handle.has_metadata():
            self.torrent_info = self.handle.get_torrent_info()

        # Adjust progress to be 0-100 value
        progress = self.status.progress * 100

        # Adjust status.distributed_copies to return a non-negative value
        distributed_copies = self.status.distributed_copies
        if distributed_copies < 0:
            distributed_copies = 0.0

        # Calculate the seeds:peers ratio
        if self.status.num_incomplete == 0:
            # Use -1.0 to signify infinity
            seeds_peers_ratio = -1.0
        else:
            seeds_peers_ratio = self.status.num_complete / float(self.status.num_incomplete)

        #if you add a key here->add it to core.py STATUS_KEYS too.
        full_status = {
            "active_time": self.status.active_time,
            "all_time_download": self.status.all_time_download,
            "compact": self.options["compact_allocation"],
            "distributed_copies": distributed_copies,
            "download_payload_rate": self.status.download_payload_rate,
            "hash": self.torrent_id,
            "is_auto_managed": self.options["auto_managed"],
            "is_finished": self.is_finished,
            "max_connections": self.options["max_connections"],
            "max_download_speed": self.options["max_download_speed"],
            "max_upload_slots": self.options["max_upload_slots"],
            "max_upload_speed": self.options["max_upload_speed"],
            "message": self.statusmsg,
            "move_on_completed_path": self.options["move_completed_path"],
            "move_on_completed": self.options["move_completed"],
            "move_completed_path": self.options["move_completed_path"],
            "move_completed": self.options["move_completed"],
            "next_announce": self.status.next_announce.seconds,
            "num_peers": self.status.num_peers - self.status.num_seeds,
            "num_seeds": self.status.num_seeds,
            "paused": self.status.paused,
            "prioritize_first_last": self.options["prioritize_first_last_pieces"],
            "progress": progress,
            "remove_at_ratio": self.options["remove_at_ratio"],
            "save_path": self.options["download_location"],
            "seeding_time": self.status.seeding_time,
            "seeds_peers_ratio": seeds_peers_ratio,
            "seed_rank": self.status.seed_rank,
            "state": self.state,
            "stop_at_ratio": self.options["stop_at_ratio"],
            "stop_ratio": self.options["stop_ratio"],
            "time_added": self.time_added,
            "total_done": self.status.total_done,
            "total_payload_download": self.status.total_payload_download,
            "total_payload_upload": self.status.total_payload_upload,
            "total_peers": self.status.num_incomplete,
            "total_seeds":  self.status.num_complete,
            "total_uploaded": self.status.all_time_upload,
            "total_wanted": self.status.total_wanted,
            "tracker": self.status.current_tracker,
            "trackers": self.trackers,
            "tracker_status": self.tracker_status,
            "upload_payload_rate": self.status.upload_payload_rate
        }

        def ti_comment():
            if self.handle.has_metadata():
                try:
                    return self.torrent_info.comment().decode("utf8", "ignore")
                except UnicodeDecodeError:
                    return self.torrent_info.comment()
            return ""

        def ti_name():
            if self.handle.has_metadata():
                name = self.torrent_info.file_at(0).path.replace("\\", "/", 1).split("/", 1)[0]
                if not name:
                    name = self.torrent_info.name()
                try:
                    return name.decode("utf8", "ignore")
                except UnicodeDecodeError:
                    return name

            elif self.magnet:
                try:
                    keys = dict([k.split('=') for k in self.magnet.split('?')[-1].split('&')])
                    name = keys.get('dn')
                    if not name:
                        return self.torrent_id
                    name = unquote(name).replace('+', ' ')
                    try:
                        return name.decode("utf8", "ignore")
                    except UnicodeDecodeError:
                        return name
                except:
                    pass

            return self.torrent_id

        def ti_priv():
            if self.handle.has_metadata():
                return self.torrent_info.priv()
            return False
        def ti_total_size():
            if self.handle.has_metadata():
                return self.torrent_info.total_size()
            return 0
        def ti_num_files():
            if self.handle.has_metadata():
                return self.torrent_info.num_files()
            return 0
        def ti_num_pieces():
            if self.handle.has_metadata():
                return self.torrent_info.num_pieces()
            return 0
        def ti_piece_length():
            if self.handle.has_metadata():
                return self.torrent_info.piece_length()
            return 0

        fns = {
            "comment": ti_comment,
            "eta": self.get_eta,
            "file_priorities": self.get_file_priorities,
            "file_progress": self.get_file_progress,
            "files": self.get_files,
            "is_seed": self.handle.is_seed,
            "name": ti_name,
            "num_files": ti_num_files,
            "num_pieces": ti_num_pieces,
            "peers": self.get_peers,
            "piece_length": ti_piece_length,
            "private": ti_priv,
            "queue": self.handle.queue_position,
            "ratio": self.get_ratio,
            "total_size": ti_total_size,
            "tracker_host": self.get_tracker_host,
        }

        # Create the desired status dictionary and return it
        status_dict = {}

        if len(keys) == 0:
            status_dict = full_status
            for key in fns:
                status_dict[key] = fns[key]()
        else:
            for key in keys:
                if key in full_status:
                    status_dict[key] = full_status[key]
                elif key in fns:
                    status_dict[key] = fns[key]()

        session_id = self.rpcserver.get_session_id()
        if diff:
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

    def apply_options(self):
        """Applies the per-torrent options that are set."""
        self.handle.set_max_connections(self.max_connections)
        self.handle.set_max_uploads(self.max_upload_slots)
        self.handle.set_upload_limit(int(self.max_upload_speed * 1024))
        self.handle.set_download_limit(int(self.max_download_speed * 1024))
        self.handle.prioritize_files(self.file_priorities)
        self.handle.resolve_countries(True)

    def pause(self):
        """Pause this torrent"""
        if self.state == "Error":
            return False
        # Turn off auto-management so the torrent will not be unpaused by lt queueing
        self.handle.auto_managed(False)
        if self.handle.is_paused():
            # This torrent was probably paused due to being auto managed by lt
            # Since we turned auto_managed off, we should update the state which should
            # show it as 'Paused'.  We need to emit a torrent_paused signal because
            # the torrent_paused alert from libtorrent will not be generated.
            self.update_state()
            component.get("EventManager").emit(TorrentStateChangedEvent(self.torrent_id, "Paused"))
        else:
            try:
                self.handle.pause()
            except Exception, e:
                log.debug("Unable to pause torrent: %s", e)
                return False

        return True

    def resume(self):
        """Resumes this torrent"""

        if self.handle.is_paused() and self.handle.is_auto_managed():
            log.debug("Torrent is being auto-managed, cannot resume!")
        elif self.forced_error and self.forced_error.was_paused:
            log.debug("Skip resuming Error state torrent that was originally paused.")
        else:
            # Reset the status message just in case of resuming an Error'd torrent
            self.set_status_message("OK")

            if self.handle.is_finished():
                # If the torrent has already reached it's 'stop_seed_ratio' then do not do anything
                if self.options["stop_at_ratio"]:
                    if self.get_ratio() >= self.options["stop_ratio"]:
                        #XXX: This should just be returned in the RPC Response, no event
                        #self.signals.emit_event("torrent_resume_at_stop_ratio")
                        return

            if self.options["auto_managed"]:
                # This torrent is to be auto-managed by lt queueing
                self.handle.auto_managed(True)

            try:
                self.handle.resume()
            except:
                pass

            return True

        if self.forced_error and not self.forced_error.restart_to_resume:
            self.clear_forced_error_state()
        elif self.state == "Error" and not self.forced_error:
            self.handle.clear_error()

    def connect_peer(self, ip, port):
        """adds manual peer"""
        try:
            self.handle.connect_peer((ip, int(port)), 0)
        except Exception, e:
            log.debug("Unable to connect to peer: %s", e)
            return False
        return True

    def move_storage(self, dest):
        """Move a torrent's storage location"""
        try:
            dest = unicode(dest, "utf-8")
        except TypeError:
            # String is already unicode
            pass

        if not os.path.exists(dest):
            try:
                # Try to make the destination path if it doesn't exist
                os.makedirs(dest)
            except OSError, ex:
                log.error("Could not move storage for torrent %s since %s does "
                          "not exist and could not create the directory: %s",
                          self.torrent_id, dest, ex)
                return False

        kwargs = {}
        if deluge.common.VersionSplit(lt.version) >= deluge.common.VersionSplit("1.0.0.0"):
            kwargs['flags'] = 2  # dont_replace
        dest_bytes = dest.encode('utf-8')
        try:
            # libtorrent needs unicode object if wstrings are enabled, utf8 bytestring otherwise
            try:
                self.handle.move_storage(dest, **kwargs)
            except TypeError:
                self.handle.move_storage(dest_bytes, **kwargs)
        except Exception, e:
            log.error("Error calling libtorrent move_storage: %s" % e)
            return False

        return True

    def save_resume_data(self):
        """Signals libtorrent to build resume data for this torrent, it gets
        returned in a libtorrent alert"""
        # Don't generate fastresume data if torrent is in a Deluge Error state.
        if self.forced_error:
            log.debug("Skipped creating resume_data while in Error state")
        else:
            self.handle.save_resume_data()
            self.waiting_on_resume_data = True

    def on_metadata_received(self):
        if self.options["prioritize_first_last_pieces"]:
            self.set_prioritize_first_last(True)
        self.write_torrentfile()

    def write_torrentfile(self):
        """Writes the torrent file"""
        path = "%s/%s.torrent" % (
            os.path.join(get_config_dir(), "state"),
            self.torrent_id)
        log.debug("Writing torrent file: %s", path)
        try:
            self.torrent_info = self.handle.get_torrent_info()
            # Regenerate the file priorities
            self.set_file_priorities([])
            md = lt.bdecode(self.torrent_info.metadata())
            torrent_file = {}
            torrent_file["info"] = md
            with open(path, "wb") as _file:
                _file.write(lt.bencode(torrent_file))
        except Exception, e:
            log.warning("Unable to save torrent file: %s", e)

    def delete_torrentfile(self):
        """Deletes the .torrent file in the state"""
        path = "%s/%s.torrent" % (
            os.path.join(get_config_dir(), "state"),
            self.torrent_id)
        log.debug("Deleting torrent file: %s", path)
        try:
            os.remove(path)
        except Exception, e:
            log.warning("Unable to delete the torrent file: %s", e)

    def force_reannounce(self):
        """Force a tracker reannounce"""
        try:
            self.handle.force_reannounce()
        except Exception, e:
            log.debug("Unable to force reannounce: %s", e)
            return False

        return True

    def scrape_tracker(self):
        """Scrape the tracker"""
        try:
            self.handle.scrape_tracker()
        except Exception, e:
            log.debug("Unable to scrape tracker: %s", e)
            return False

        return True

    def force_recheck(self):
        """Forces a recheck of the torrents pieces"""
        self.forcing_recheck = True
        if self.forced_error:
            self.forcing_recheck_paused = self.forced_error.was_paused
            self.clear_forced_error_state(update_state=False)
        else:
            self.forcing_recheck_paused = self.handle.is_paused()
        # Store trackers for paused torrents to prevent unwanted announce before pausing again.
        if self.forcing_recheck_paused:
            self.set_trackers(None, reannounce=False)
            self.handle.replace_trackers([])

        try:
            self.handle.force_recheck()
            self.handle.resume()
        except Exception, e:
            log.debug("Unable to force recheck: %s", e)
            self.forcing_recheck = False
            if self.forcing_recheck_paused:
                self.set_trackers(torrent.trackers, reannounce=False)

        return self.forcing_recheck

    def rename_files(self, filenames):
        """Renames files in the torrent. 'filenames' should be a list of
        (index, filename) pairs."""
        for index, filename in filenames:
            # Make sure filename is a unicode object
            try:
                filename = unicode(filename, "utf-8")
            except TypeError:
                pass
            filename = sanitize_filepath(filename)
            # libtorrent needs unicode object if wstrings are enabled, utf8 bytestring otherwise
            try:
                self.handle.rename_file(index, filename)
            except TypeError:
                self.handle.rename_file(index, filename.encode("utf-8"))

    def rename_folder(self, folder, new_folder):
        """Renames a folder within a torrent.  This basically does a file rename
        on all of the folders children."""
        log.debug("attempting to rename folder: %s to %s", folder, new_folder)
        if len(new_folder) < 1:
            log.error("Attempting to rename a folder with an invalid folder name: %s", new_folder)
            return

        new_folder = sanitize_filepath(new_folder, folder=True)

        wait_on_folder = (folder, new_folder, [])
        for f in self.get_files():
            if f["path"].startswith(folder):
                # Keep a list of filerenames we're waiting on
                wait_on_folder[2].append(f["index"])
                new_path = f["path"].replace(folder, new_folder, 1)
                try:
                    self.handle.rename_file(f["index"], new_path)
                except TypeError:
                    self.handle.rename_file(f["index"], new_path.encode("utf-8"))
        self.waiting_on_folder_rename.append(wait_on_folder)

    def cleanup_prev_status(self):
        """
        This method gets called to check the validity of the keys in the prev_status
        dict.  If the key is no longer valid, the dict will be deleted.

        """
        for key in self.prev_status.keys():
            if not self.rpcserver.is_session_valid(key):
                del self.prev_status[key]
