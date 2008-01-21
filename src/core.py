# -*- coding: utf-8 -*-
# core.py
#
# Copyright (C) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

# Deluge Library, previously known as python-libtorrent:
#
#   Deluge is a Python library for torrenting, that includes
#   Deluge, which is Python code, and Deluge_core, which is also a Python
#   module, but written in C++, and includes the libtorrent torrent library. Only
#   Deluge should be visible, and only it should be imported, in the client.
#   Deluge_core contains mainly libtorrent-interfacing code, and a few other things
#   that make most sense to write at that level. Deluge contains all other
#   torrent-system management: queueing, configuration management, persistent
#   list of torrents, etc.
#

# Documentation:
#    Torrents have 3 structures:     
#        1. torrent_info - persistent data, like name, upload speed cap, etc.
#        2. core_torrent_state - transient state data from the core. This may take
#                time to calculate, so we do if efficiently
#        3. supp_torrent_state - supplementary torrent data, from Deluge

import cPickle as pickle
import os
import re
import shutil
import platform
import common
import time

import deluge_core
import pref

# Constants

TORRENTS_SUBDIR = "torrentfiles"

STATE_FILENAME = "persistent.state"
PREFS_FILENAME = "prefs.state"
DHT_FILENAME = "dht.state"

PREF_FUNCTIONS = {
    "listen_on" : deluge_core.set_listen_on,
    "max_half_open" : deluge_core.set_max_half_open,
    "connection_speed" : deluge_core.connection_speed,
    "max_connections_global" : deluge_core.set_max_connections_global,
    "max_active_torrents" : None, # no need for a function, applied constantly
    "max_upload_slots_global" : deluge_core.set_max_upload_slots_global,
    "auto_seed_ratio" : None, # no need for a function, applied constantly
    "max_download_speed_bps" : deluge_core.set_download_rate_limit,
    "max_upload_speed_bps" : deluge_core.set_upload_rate_limit,
    "enable_dht" : None, # not a normal pref in that is is applied only on start
    "use_upnp" : deluge_core.use_upnp,
    "use_lsd" : deluge_core.use_lsd,
    "use_natpmp" : deluge_core.use_natpmp,
    "use_utpex" : deluge_core.use_utpex,
}

STATE_MESSAGES = (_("Queued"),
                  _("Checking"),
                  _("Connecting"),
                  _("Downloading Metadata"),
                  _("Downloading"),
                  _("Finished"),
                  _("Seeding"),
                  _("Allocating"))

# Priorities
PRIORITY_DONT_DOWNLOAD = 0
PRIORITY_NORMAL = 1
PRIORITY_HIGH = 2
PRIORITY_HIGHEST = 5

PRIORITY_DICT = {PRIORITY_DONT_DOWNLOAD: _("Don't download"),
                 PRIORITY_NORMAL: _("Normal"),
                 PRIORITY_HIGH: _("High"),
                 PRIORITY_HIGHEST: _("Highest")}

# Exceptions

class DelugeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class InvalidEncodingError(DelugeError):
    pass

class FilesystemError(DelugeError):
    pass

# Note: this may be raised both from deluge-core.cpp and deluge.py, for
# different reasons, both related to duplicate torrents
class DuplicateTorrentError(DelugeError):
    pass

class InvalidTorrentError(DelugeError):
    pass

class InvalidUniqueIDError(DelugeError):
    pass

class InsufficientFreeSpaceError(DelugeError):
    def __init__(self, free_space, needed_space):
        self.free_space = free_space
        self.needed_space = needed_space
    def __str__(self):
        return "%d %d" % self.free_space, self.needed_space + _("bytes needed")

# A cached data item

class cached_data:
    CACHED_DATA_EXPIRATION = 1
    
    def __init__(self, get_method):
        self._get_method = get_method
        self._cache = {}
        self._expire_info = {}

    def get(self, key, cached=True):
        now = time.time()
        exp = self._expire_info.get(key)
        if not exp or now > exp + self.CACHED_DATA_EXPIRATION or not cached:
            self._cache[key] = self._get_method(key)
            self._expire_info[key] = now

        return self._cache[key]
        
# Persistent information for a single torrent

class torrent_info:
    def __init__(self, filename, save_dir, compact, user_paused=False):
        self.filename = filename
        self.save_dir = save_dir
        self.compact = compact
        self.user_paused = user_paused
        self.uploaded_memory = 0
        self.initial_uploaded_memory = 0
        self.upload_rate_limit = 0
        self.download_rate_limit = 0
        self.webseed_urls = []
        self.desired_ratio = 1.0
        self.trackers = ""
        self.trackers_changed = 0

        self.delete_me = False # set this to true, to delete it on next sync
        self.del_data = False # set this to true, to delete data on next sync

# The persistent state of the torrent system. Everything in this will be pickled

class persistent_state:
    def __init__(self):
        # Torrents is a dict with instance of torrent_info -> unique_ID 
        self.torrents = {}

        # Prepare queue (queue is pickled, just like everything else)
        # queue[x] is the unique_ID of the x-th queue position. Simple.
        self.queue = []

# The manager for the torrent system

class Manager:
    # blank_slate mode ignores the two pickle files and DHT state file, i.e. you start
    # completely fresh. When quitting, the old files will be overwritten
    def __init__(self, client_ID, version, user_agent, base_dir, blank_slate=False):
        self.base_dir = base_dir
        # Keeps track of DHT running state
        self.dht_running = False

        # Load the preferences
        self.config = pref.Preferences(os.path.join(self.base_dir, PREFS_FILENAME))
        
        TORRENTS_SUBDIR = self.config.get("default_torrent_path")

        # Ensure directories exist
        if not os.path.exists(TORRENTS_SUBDIR):
            os.mkdir(TORRENTS_SUBDIR)

        # Pre-initialize the core's data structures
        deluge_core.pre_init(DelugeError,
                          InvalidEncodingError,
                          SystemError,
                          FilesystemError,
                          DuplicateTorrentError,
                          InvalidTorrentError)

        # Start up the core
        deluge_core.init(client_ID,
                             int(version[0]),
                             int(version[1]),
                             int(version[2]),
                             int(version[3]),
                             user_agent)

        self.constants = deluge_core.constants()

        # Unique IDs are NOT in the state, since they are temporary for each session
        self.unique_IDs = {} # unique_ID -> a torrent_info object, i.e. persistent data

        # Cached torrent core_states. We do not poll the core in a costly 
        # manner.
        self.cached_core_torrent_states = \
            cached_data(deluge_core.get_torrent_state)

        # supplementary torrent states
        self.supp_torrent_states = {} # unique_ID->dict of data

        # Cached torrent core_states. We do not poll the core in a costly 
        # manner.
        self.cached_core_torrent_peer_infos = \
            cached_data(deluge_core.get_peer_info)
        
        # Cached torrent core_states. We do not poll the core in a costly 
        # manner.
        self.cached_core_torrent_file_infos = \
            cached_data(deluge_core.get_file_info)

        # Apply preferences. Note that this is before any torrents are added
        self.apply_prefs()
        
        # Event callbacks for use with plugins
        self.event_callbacks = {}

        # unique_ids removed by core
        self.removed_unique_ids = {}

        # unique_ids with files just removed by user
        self.update_files_removed = {}

        PREF_FUNCTIONS["enable_dht"] = self.set_DHT 

        # Unpickle the state, or create a new one
        self.state = persistent_state()
        if not blank_slate:
            try:
                pkl_file = open(os.path.join(self.base_dir, STATE_FILENAME), 
                                'rb')
                state = pickle.load(pkl_file)
                pkl_file.close()
                
                if isinstance(state.torrents, list):
                    # One time convert of old torrents list to dict
                    state.torrents = dict((x, None) for x in 
                                                   state.torrents)
                # Add torrents to core and unique_IDs
                for torrent in state.torrents:
                    if not os.path.exists(torrent.filename):
                        print "Missing file: %s" % torrent.filename
                        continue
                    if torrent not in self.unique_IDs.values():
                        try:
                            unique_ID = deluge_core.add_torrent(torrent.filename,
                                                                torrent.save_dir,
                                                                torrent.compact)
                        except Exception, e:
                            print "Unable to add torrent: ", e

                        self.unique_IDs[unique_ID] = torrent
                        self.state.torrents[torrent] = unique_ID
                        
                        # Apply per torrent prefs after torrent added to core
                        self.apply_prefs_per_torrent(unique_ID)
                        #remove fastresume for non-seed
                        try:
                            torrent_state = self.get_core_torrent_state(unique_ID)
                        except:
                            pass
                        else:
                            if not torrent_state['is_seed']:
                                try:
                                    os.remove(self.unique_IDs[unique_ID].filename + ".fastresume")
                                except:
                                    pass

                # Sync with the core: tell core about torrents, and get 
                # unique_IDs
                self.sync()

                # Apply the queue at this time, after all is loaded and ready
                self.apply_queue()
            except:
                pass

    def quit(self):
        # Pickle the state
        self.pickle_state()

        # Stop DHT, if needed
        self.set_DHT(False)

        #close upnp
        deluge_core.use_upnp(0)

        if self.config.get("use_compact_storage"):
            for unique_ID in self.unique_IDs.keys():
                self.pause(unique_ID)

        # Save fastresume data
        print "Saving fastresume data..."
        self.save_fastresume_data()

        # save upload memory
        print "Saving uploaded memory..."
        self.save_upmem()

        # Shutdown torrent core
        print "Quitting the core..."
        deluge_core.quit()

        #kill dbus on windows
        import platform
        if platform.system() == "Windows":
            import os
            os.popen4('tskill.exe dbus-daemon-deluge')
        elif platform.system() == "Microsoft":
            import os
            os.popen4('taskkill.exe /IM dbus-daemon-deluge.exe /F')

    def pickle_state(self):
        # Pickle the state so if we experience a crash, the latest state is 
        # available
        print "Pickling state..."
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        output = open(os.path.join(self.base_dir, STATE_FILENAME), 'wb')
        pickle.dump(self.state, output)
        output.close()

    def save_upmem(self):
        # Save the uploaded data from this session to the existing upload memory
        for unique_ID in self.unique_IDs.keys():
            # self.get_core_torrent_state purposefully not cached.
            try:
                self.unique_IDs[unique_ID].uploaded_memory = \
                self.unique_IDs[unique_ID].initial_uploaded_memory + \
                self.get_core_torrent_state(unique_ID, False)['total_upload']
            except AttributeError:
                self.unique_IDs[unique_ID].initial_uploaded_memory = 0

    # Preference management functions

    def get_config(self):
        # This returns the preference object
        return self.config
        
    def get_pref(self, key):
        # Get the value from the preferences object
        return self.config.get(key)
    
    # Get file piece range
    def get_file_piece_range(self, unique_id):
        try:
            return deluge_core.get_file_piece_range(unique_id)
        except Exception, e:
            print "Unable to get file piece range:", e
    
    # Check if piece is finished
    def has_piece(self, unique_id, piece_index):
        try:
            return deluge_core.has_piece(unique_id, piece_index)
        except Exception, e:
            print "Unable to get has piece:", e
    
    # Dump torrent info without adding
    def dump_torrent_file_info(self, torrent):
        try:
            ret = deluge_core.dump_file_info(torrent)
        except SystemError:
            print "invalid file"
        else:
            return ret

    # Dump trackers from torrent file
    def dump_trackers(self, torrent):
        try:
            return deluge_core.dump_trackers(torrent)
        except Exception, e:
            print "Unable to dump trackers:", e
    
    # Torrent addition and removal functions

    def add_torrent(self, filename, save_dir, compact, user_paused=False):
        self.add_torrent_ns(filename, save_dir, compact, user_paused)
        return self.sync() # Syncing will create a new torrent in the core, and return it's ID
    
    # When duplicate torrent error, use to find duplicate when merging tracker lists
    def test_duplicate(self, torrent, unique_id):
        try:
            return deluge_core.test_duplicate(torrent, unique_id)
        except Exception, e:
            print "Unable to test duplicate:", e

    def remove_torrent(self, unique_ID, data_also, torrent_also):
        temp = self.unique_IDs[unique_ID]
        try:
            temp_fileinfo = deluge_core.get_file_info(unique_ID)
        except Exception, e:
            print "Unable to get file info:", e
        self.remove_torrent_ns(unique_ID, data_also)
        self.sync()

        # Remove .torrent file if asked to do so
        if torrent_also:
            os.remove(temp.filename)

    # A function to try and reload a torrent from a previous session. This is
    # used in the event that Deluge crashes and a blank state is loaded.
    def add_old_torrent(self, filename, save_dir, compact):
        if not filename in os.listdir(self.config.get("default_torrent_path")):
            #raise InvalidTorrentError(_("File was not found") + ": " + filename)
            print "File not found: ", filename
            return

        full_new_name = os.path.join(self.config.get("default_torrent_path"), filename)

        # Create torrent object
        new_torrent = torrent_info(full_new_name, save_dir, compact)
        self.state.torrents[new_torrent] = None
        
        return self.sync()

    # A separate function, because people may want to call it from time to time
    def save_fastresume_data(self, uid=None):
        if uid == None:
            for unique_ID in self.unique_IDs:
                try:
                    os.remove(self.unique_IDs[unique_ID].filename + ".fastresume")
                except:
                    pass
                try:
                    deluge_core.save_fastresume(unique_ID, self.unique_IDs[unique_ID].filename)
                except Exception, e:
                    print "Unable to save fastresume: ", e
        else:
            try:
                os.remove(self.unique_IDs[uid].filename + ".fastresume")
            except:
                pass
            try:
                deluge_core.save_fastresume(uid, self.unique_IDs[uid].filename)
            except Exception, e:
                print "Unable to save fastresume: ", e

    # State retrieval functions

    def get_state(self):
        ret = deluge_core.get_session_info()

        # Get additional data from our level
        ret['is_listening'] = deluge_core.is_listening()
        ret['port'] = deluge_core.listening_port()
        if self.dht_running == True:
            ret['DHT_nodes'] = deluge_core.get_DHT_info()

        return ret

    # This is the EXTERNAL function, for the GUI. It returns the core_state + supp_state
    def get_torrent_state(self, unique_ID):
        # Check to see if unique_ID exists:
        if unique_ID not in self.unique_IDs:
            print "Asked for a torrent that doesn't exist"
            return
        try:
            ret = self.get_core_torrent_state(unique_ID).copy()

            # Add the deluge-level things to the deluge_core data
            ret.update(self.get_supp_torrent_state(unique_ID))

            # Get queue position
            torrent = self.unique_IDs[unique_ID]
            ret['queue_pos'] = self.state.queue.index(torrent) + 1
            return ret
        except:
            return None

    def get_torrent_peer_info(self, unique_ID):
        # Perhaps at some time we may add info here
        return self.get_core_torrent_peer_info(unique_ID)
    
    def get_torrent_file_info(self, unique_ID):
        return self.get_core_torrent_file_info(unique_ID)

    def get_piece_info(self, unique_ID, piece_index):
        try:
            return deluge_core.get_piece_info(unique_ID, piece_index)
        except Exception, e:
            print "Unable to get piece info:", e

    def get_all_piece_info(self, unique_ID):
        try:
            return deluge_core.get_all_piece_info(unique_ID)
        except Exception, e:
            print "Unable to get all piece info:", e
    
    def get_torrent_unique_id(self, torrent):
        return self.state.torrents[torrent]

    # Queueing functions

    def queue_top(self, unique_ID):
        torrent = self.unique_IDs[unique_ID]
        self.state.queue.insert(0,
            self.state.queue.pop(self.get_queue_index(torrent)))
        self.apply_queue()
        self.pickle_state()

    def queue_up(self, unique_ID):
        torrent = self.unique_IDs[unique_ID]
        curr_index = self.get_queue_index(torrent)
        if curr_index > 0:
            temp = self.state.queue[curr_index - 1]
            self.state.queue[curr_index - 1] = torrent
            self.state.queue[curr_index] = temp
            self.apply_queue()
            self.pickle_state()

    def queue_down(self, unique_ID):
        torrent = self.unique_IDs[unique_ID]
        curr_index = self.get_queue_index(torrent)
        if curr_index < (len(self.state.queue) - 1):
            temp = self.state.queue[curr_index + 1]
            self.state.queue[curr_index + 1] = torrent
            self.state.queue[curr_index] = temp
            self.apply_queue()
            self.pickle_state()

    def queue_bottom(self, unique_ID, enforce_queue=True):
        torrent = self.unique_IDs[unique_ID]
        curr_index = self.get_queue_index(torrent)
        if curr_index < (len(self.state.queue) - 1):
            self.state.queue.remove(torrent)
            self.state.queue.append(torrent)
            if enforce_queue:
                self.apply_queue()
            self.pickle_state()

    def clear_completed(self):
        for unique_ID in self.unique_IDs:
            torrent_state = self.get_core_torrent_state(unique_ID)
            if torrent_state['progress'] == 1.0:
                self.remove_torrent_ns(unique_ID, False)
                self.removed_unique_ids[unique_ID] = 1

        self.sync()
        self.apply_queue()

    # Enforce the queue: pause/unpause as needed, based on queue and user_pausing
    # This should be called after changes to relevant parameters (user_pausing, or
    # altering max_active_torrents), or just from time to time
    # ___ALL queuing code should be in this function, and ONLY here___
    def apply_queue(self):
        # Counter for currently active torrent in the queue. Paused in core
        # but having self.is_user_paused(unique_ID) == False is 
        # also considered active.
        active_torrent_cnt = 0

        # Pause and resume torrents
        for torrent in self.state.queue:
            unique_ID = self.state.torrents[torrent]
            # Get not cached torrent state so we don't pause/resume torrents
            # more than 1 time - if cached torrent_state['is_paused'] can be
            # still paused after we already paused it.
            torrent_state = self.get_core_torrent_state(unique_ID, False)
            
            if not torrent_state['is_paused'] or \
               (torrent_state['is_paused'] and not \
                self.is_user_paused(unique_ID)):
                active_torrent_cnt += 1 
            
            if (active_torrent_cnt <= self.get_pref('max_active_torrents') or \
                self.get_pref('max_active_torrents') == -1) and \
               torrent_state['is_paused'] and not \
               self.is_user_paused(unique_ID):
                # This torrent is a seed so skip all the free space checking
                if torrent_state['is_seed']:
                    self.resume(unique_ID)
                    continue
                    
                # Before we resume, we should check if the torrent is using Full Allocation 
                # and if there is enough space on to finish this file.
                if not self.unique_IDs[unique_ID].compact:
                    avail = self.calc_free_space(directory = self.unique_IDs\
                        [unique_ID].save_dir)
                    total_needed = torrent_state["total_wanted"] - torrent_state["total_wanted_done"]
                    if total_needed < avail:
                        # We have enough free space, so lets resume this torrent
                        self.resume(unique_ID)
                    else:
                        self.pause(unique_ID)
                        self.unique_IDs[unique_ID].user_paused = True
                        nice_need = common.fsize(total_needed)
                        nice_free = common.fsize(avail)
                        import gtk
                        import dialogs
                        gtk.gdk.threads_enter()
                        dialogs.show_popup_warning(None, _("There is not enough \
free disk space to complete your download.") + "\n" + "This torrents will be \
paused" + "\n" + _("Space Needed:") + " " + nice_need + "\n" + _("Available \
Space:") + " " + nice_free)
                        gtk.gdk.threads_leave()
                        print "Not enough free space to resume this torrent!"
                else: #We're using compact allocation so lets just resume
                    self.resume(unique_ID)
            elif not torrent_state['is_paused'] and \
                 ((active_torrent_cnt > self.get_pref('max_active_torrents') and \
                   self.get_pref('max_active_torrents') != -1) or \
                  self.is_user_paused(unique_ID)):
                self.pause(unique_ID)

        # Handle autoseeding - downqueue as needed
        if not self.get_pref('clear_max_ratio_torrents') \
            and self.get_pref('auto_seed_ratio') > 0 \
            and self.get_pref('auto_end_seeding'):

            for unique_ID in self.unique_IDs:
                torrent_state = self.get_core_torrent_state(unique_ID)
                if (torrent_state["total_wanted"] - torrent_state["total_wanted_done"] == 0) and not torrent_state['is_paused']:
                    ratio = self.calc_ratio(unique_ID, torrent_state)
                    if ratio >= self.get_pref('auto_seed_ratio'):
                        self.queue_bottom(unique_ID, enforce_queue=False) # don't recurse!
                        self.set_user_pause(unique_ID, True, enforce_queue=False)
        
        if self.get_pref('clear_max_ratio_torrents'):
            for unique_ID in self.unique_IDs.keys():
                torrent_state = self.get_core_torrent_state(unique_ID)
                if (torrent_state["total_wanted"] - torrent_state["total_wanted_done"] == 0):
                    ratio = self.calc_ratio(unique_ID, torrent_state)
                    if ratio >= self.get_pref('auto_seed_ratio'):
                        self.removed_unique_ids[unique_ID] = 1
                        self.remove_torrent(unique_ID, False, True)
    # Event handling

    def connect_event(self, event_type, callback):
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    def disconnect_event(self, event_type, callback):
        if event_type in self.event_callbacks and \
           callback in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(callback)

    def handle_events(self):
        # Handle them for the backend's purposes, but still send them up in case the client
        # wants to do something - show messages, for example
        def pop_event():
            try:
                event = deluge_core.pop_event()
            except:
                return None
            else:
                return event
                
        ret = []
        while True:
            event = pop_event()
            if event is None:
                break

#            print "EVENT: ", event

            ret.append(event)

            if 'unique_ID' in event and \
               event['unique_ID'] not in self.unique_IDs:
                continue

            if event['event_type'] in self.event_callbacks:
                for callback in self.event_callbacks[event['event_type']]:
                    callback(event)

            if event['event_type'] is self.constants['EVENT_FINISHED']: 
                if event['message'] == "torrent has finished downloading":

                    # Queue seeding torrent to bottom if needed
                    if self.get_pref('queue_seeds_to_bottom'):
                        self.queue_bottom(event['unique_ID'])
                    
                # save fast resume once torrent finishes so as to not recheck
                # seed if client crashes
                self.save_fastresume_data(event['unique_ID'])

            elif event['event_type'] is self.constants['EVENT_FILE_ERROR']:
                import gtk
                import dialogs
                gtk.gdk.threads_enter()
                dialogs.show_popup_warning(None, event['message'])
                gtk.gdk.threads_leave()

            elif event['event_type'] is self.constants['EVENT_TRACKER_ANNOUNCE']:
                self.set_supp_torrent_state_val(event['unique_ID'], 
                                                "tracker_status",
                                                _("Announce sent"))
            elif event['event_type'] is self.constants['EVENT_TRACKER_REPLY']:
                self.set_supp_torrent_state_val(event['unique_ID'], 
                                                "tracker_status",
                                                _("Announce OK"))
            elif event['event_type'] is self.constants['EVENT_TRACKER_ALERT']:
                match = re.search('tracker:\s*".*"\s*(.*)', event["message"])
                message = match and match.groups()[0] or ""
                try:
                    tracker_status = "%s: %s (%s=%s, %s=%s)" % \
                        (_("Alert"), message, 
                         _("HTTP code"), event["status_code"], 
                         _("times in a row"), event["times_in_row"])
                        
                    self.set_supp_torrent_state_val(event['unique_ID'], 
                                                "tracker_status",
                                                tracker_status)
                except Exception, e:
                    print "There was a problem displaying a tracker alert. Most\
likely the tracker did not responsd in utf-8.", e

            elif event['event_type'] is self.constants['EVENT_TRACKER_WARNING']:
                # Probably will need proper formatting later, not tested yet
                tracker_status = '%s: %s' % (_("Warning"), event["message"])
                
                self.set_supp_torrent_state_val(event['unique_ID'], 
                                                "tracker_status",
                                                tracker_status)

        return ret

    # Priorities functions
    def clear_update_files_removed(self):
        self.update_files_removed = {}

    def prioritize_files(self, unique_ID, priorities, update_files_removed=False):
        assert(len(priorities) == \
                   self.get_core_torrent_state(unique_ID)['num_files'])
        self.unique_IDs[unique_ID].priorities = priorities[:]
        try:
            deluge_core.prioritize_files(unique_ID, priorities)
        except Exception, e:
            print "Unable to prioritize files:", e
            
        if update_files_removed:
            self.update_files_removed[unique_ID] = 1
        
        if self.get_pref('prioritize_first_last_pieces'):
            self.prioritize_first_last_pieces(unique_ID)

    def get_priorities(self, unique_ID):
        try:
            return self.unique_IDs[unique_ID].priorities[:]
        except AttributeError:
            # return normal priority for all files by default
            
            num_files = self.get_core_torrent_state(unique_ID)['num_files']
            return [PRIORITY_NORMAL] * num_files

    def prioritize_first_last_pieces(self, unique_ID):
        """Try to prioritize first and last pieces of each file in torrent
        
        Currently it tries to prioritize 1% in the beginning and in the end
        of each file in the torrent
        
        """
        try:
            deluge_core.prioritize_first_last_pieces(unique_ID, 
            self.unique_IDs[unique_ID].priorities)
        except Exception, e:
            print "Unable to prioritize first and last pieces:", e

    # Advanced statistics - these may be SLOW. The client should call these only
    # when needed, and perhaps only once in a long while (they are mostly just
    # approximations anyhow

    def calc_swarm_speed(self, unique_ID):
        pieces_per_sec = deluge_stats.calc_swarm_speed(self.get_core_torrent_peer_info(unique_ID))
        piece_length = self.get_core_torrent_state(unique_ID)

        return pieces_per_sec * piece_length

    # Miscellaneous minor functions

    def set_user_pause(self, unique_ID, new_value, enforce_queue=True):
        if self.config.get("max_active_torrents") == 0:
            self.config.set("max_active_torrents", \
                self.config.get("max_active_torrents_tmp"))
            self.apply_prefs()
        try:
            self.unique_IDs[unique_ID].user_paused = new_value
            if enforce_queue:
                self.apply_queue()
            self.pickle_state()
        except:
            print "pause failed\n"

    def set_ratio(self, unique_ID, num):
        try:
            deluge_core.set_ratio(unique_ID, float(num))
        except Exception, e:
            print "Unable to set ratio: ", e

    def is_user_paused(self, unique_ID):
        return self.unique_IDs[unique_ID].user_paused

    def get_num_torrents(self):
        return deluge_core.get_num_torrents()

    def get_queue(self):
        return self.state.queue

    def update_tracker(self, unique_ID):
        try:
            deluge_core.reannounce(unique_ID)
        except Exception, e:
            print "Unable to reannounce: ", e

    def scrape_tracker(self, unique_ID):
        try:
            deluge_core.scrape_tracker(unique_ID)
        except Exception, e:
            print "Unable to scrape tracker ", e

    def pause(self, unique_ID):
        try:
            state = self.get_torrent_state(unique_ID)
            if not state["is_paused"]:
                deluge_core.pause(unique_ID)
        except:
            print "pause failed\n"

    def resume(self, unique_ID):
        state = self.get_torrent_state(unique_ID)
        if state["is_paused"]:
            try:
                deluge_core.resume(unique_ID)
                # We have to re-apply per torrent settings after resume. This has to
                # be done until ticket #118 in libtorrent is fixed.
                self.apply_prefs_per_torrent(unique_ID)
            except:
                print "pause failed\n"

    def pause_all(self):
        if self.config.get('max_active_torrents') != 0:
            self.config.set('max_active_torrents_tmp', \
                self.config.get('max_active_torrents'))
            self.config.set('max_active_torrents', 0)
            self.apply_prefs()

    def resume_all(self):
        if self.config.get('max_active_torrents') == 0:
            self.config.set('max_active_torrents', \
                self.config.get('max_active_torrents_tmp'))
            self.apply_prefs()

    def move_storage(self, unique_ID, directory):
        try:
            deluge_core.move_storage(unique_ID, directory)
        except Exception, e:
            print "Unable to move storage: ", e

    ####################
    # Internal functions
    ####################

    def get_core_torrent_state(self, unique_ID, cached=True):
        return self.cached_core_torrent_states.get(unique_ID, cached)

    def get_supp_torrent_state(self, unique_ID):
        return self.supp_torrent_states.get(unique_ID, {})

    def set_supp_torrent_state_val(self, unique_ID, key, val):
        if unique_ID not in self.supp_torrent_states:
            self.supp_torrent_states[unique_ID] = {}

        self.supp_torrent_states[unique_ID][key] = val

    def get_core_torrent_peer_info(self, unique_ID):
        return self.cached_core_torrent_peer_infos.get(unique_ID)
    
    def get_core_torrent_file_info(self, unique_ID):
        return self.cached_core_torrent_file_infos.get(unique_ID)

    # Functions for checking if enough space is available

    def calc_free_space(self, directory):
        if not common.windows_check(): 
            import statvfs
            try:
                dir_stats = os.statvfs(directory)
            except:
                return 0
            block_size = dir_stats[statvfs.F_BSIZE]
            avail_blocks = dir_stats[statvfs.F_BAVAIL]
            return long(block_size * avail_blocks)
        else:
            import string
            import win32file
            sectorsPerCluster, bytesPerSector, numFreeClusters, \
                totalNumClusters_Not_Used = win32file.GetDiskFreeSpace(\
                    directory[0] + ":\\")
            sectorsPerCluster = long(sectorsPerCluster)
            bytesPerSector = long(bytesPerSector)
            numFreeClusters = long(numFreeClusters)
            return long(numFreeClusters * sectorsPerCluster * bytesPerSector)

    # Non-syncing functions. Used when we loop over such events, and sync manually at the end

    def add_torrent_ns(self, filename, save_dir, compact, user_paused):
        # Cache torrent file
        (temp, filename_short) = os.path.split(filename)

        # if filename_short in os.listdir(self.base_dir + "/" + TORRENTS_SUBDIR):
        #     raise DuplicateTorrentError("Duplicate Torrent, it appears: " + filename_short)

        full_new_name = os.path.join(self.config.get("default_torrent_path"), filename_short)

        try:
            shutil.copy(filename, full_new_name)
        except Exception, e:
            if str(e).find('are the same file'):
                pass
            else:
                raise

        # Create torrent object
        new_torrent = torrent_info(full_new_name, save_dir, compact, user_paused)
        self.state.torrents[new_torrent] = None

    def remove_torrent_ns(self, unique_ID, data_also):
        self.unique_IDs[unique_ID].delete_me = True
        self.unique_IDs[unique_ID].del_data = data_also        

    # Sync the state.torrents and unique_IDs lists with the core
    # ___ALL syncing code with the core is here, and ONLY here___
    # Also all self-syncing is done here (various lists)

    ##
    ## I had to make some changes here to get things to work properly
    ## Some of these changes may be hack-ish, so look at them and make
    ## sure nothing is wrong.
    ##
    def sync(self, called_on_start=False):
        ret = None # We return new added unique ID(s), or None
        no_space = False

        to_remove = []
        # Add torrents to core and unique_IDs
        for torrent in self.state.torrents:
            if not os.path.exists(torrent.filename):
                print "Missing file: %s" % torrent.filename
                to_remove.append(torrent)
                continue
            if torrent not in self.unique_IDs.values():
                try:
                    unique_ID = deluge_core.add_torrent(torrent.filename,
                                                        torrent.save_dir,
                                                        torrent.compact)
                except Exception, e:
                    print "Unable to add torrent: ", e
                    to_remove.append(torrent)
                    continue
                    
                ret = unique_ID
                self.unique_IDs[unique_ID] = torrent
                self.state.torrents[torrent] = unique_ID
                
                # Apply per torrent prefs after torrent added to core
                self.apply_prefs_per_torrent(unique_ID)
                #remove fastresume for non-seed
                try:
                    torrent_state = self.get_core_torrent_state(unique_ID)
                except:
                    pass
                else:
                    if not torrent_state['is_seed']:
                        try:
                            os.remove(self.unique_IDs[unique_ID].filename + ".fastresume")
                        except:
                            pass
        
        # Remove torrents from self.state because they were not added to the
        # libtorrent session.
        for torrent in to_remove:
            del self.state.torrents[torrent]

        # Remove torrents from core, unique_IDs and queue
        to_delete = []
        for unique_ID in self.unique_IDs.keys():
#            print torrent
            if self.unique_IDs[unique_ID].delete_me:
                deluge_core.remove_torrent(unique_ID, \
                    self.unique_IDs[unique_ID].del_data)
                to_delete.append(unique_ID)

        for unique_ID in to_delete:
            del self.state.torrents[self.unique_IDs[unique_ID]]
            self.state.queue.remove(self.unique_IDs[unique_ID])
            # Remove .fastresume
            try:
                # Must be after removal of the torrent, because that saves a new .fastresume
                os.remove(self.unique_IDs[unique_ID].filename + ".fastresume")
            except OSError:
                pass # Perhaps there never was one to begin with
            del self.unique_IDs[unique_ID]
            
        # Add torrents to queue - at the end, of course
        for torrent in self.unique_IDs.values():
            if torrent not in self.state.queue:
                if self.get_pref('queue_above_completed') and \
                   len(self.state.queue) > 0 and not called_on_start:
                    for index, torrent_tmp in enumerate(self.state.queue):
                        unique_ID = self.state.torrents[torrent_tmp]
                        torrent_state = self.get_core_torrent_state(unique_ID)
                        if torrent_state['progress'] == 1.0:
                            break
                    if torrent_state['progress'] == 1.0:
                        self.state.queue.insert(index, torrent)
                    else:
                        self.state.queue.append(torrent)
                else:
                    self.state.queue.append(torrent)

        # run through queue, remove those that no longer exists
        to_delete = []
        for torrent in self.state.queue:
            if torrent not in self.state.torrents:
                to_delete.append(torrent)
                
        for torrent in to_delete:
            self.state.queue.remove(torrent)

        assert(len(self.unique_IDs) == len(self.state.torrents))

        assert(len(self.unique_IDs) == len(self.state.queue))
        assert(len(self.unique_IDs) == deluge_core.get_num_torrents())
        
        #if no_space:
            #self.apply_queue()

        self.pickle_state()

        return ret

    def get_queue_index(self, torrent):
        return self.state.queue.index(torrent)

    def apply_prefs(self):
        print "Applying preferences"

        for pref in PREF_FUNCTIONS:
            if PREF_FUNCTIONS[pref] is not None:
                if (PREF_FUNCTIONS[pref] == PREF_FUNCTIONS["listen_on"]):
                    if not self.get_pref("random_port"):
                        PREF_FUNCTIONS[pref](self.get_pref(pref))
                    else:
                        if deluge_core.listening_port() != 0:
                            if self.get_pref("listen_on")[0] <= deluge_core.listening_port() <= self.get_pref("listen_on")[1]:
                                import random
                                randrange = lambda: random.randrange(49152, 65535)
                                ports = [randrange(), randrange()]
                                ports.sort()
                                deluge_core.set_listen_on(ports)
                            
                        else:
                            import random
                            randrange = lambda: random.randrange(49152, 65535)
                            ports = [randrange(), randrange()]
                            ports.sort()
                            deluge_core.set_listen_on(ports)
                else:
                    PREF_FUNCTIONS[pref](self.get_pref(pref))
                                                
        # We need to reapply priorities to files and per torrent options after
        # preferences were changed.
        for unique_ID in self.unique_IDs:
            self.prioritize_files(unique_ID, self.get_priorities(unique_ID))
            self.apply_prefs_per_torrent(unique_ID)

    def apply_prefs_per_torrent(self, unique_ID):
        self.set_max_connections_per_torrent(unique_ID, 
            self.get_pref("max_connections_per_torrent"))
        self.set_max_upload_slots_per_torrent(unique_ID, 
            self.get_pref("max_upload_slots_per_torrent"))

    def set_DHT(self, start=False):
        if start and not self.dht_running:
            print "Starting DHT..."
            deluge_core.start_DHT(os.path.join(self.base_dir, DHT_FILENAME))
            self.dht_running = True
        elif not start and self.dht_running:
            print "Stopping DHT..."
            deluge_core.stop_DHT(os.path.join(self.base_dir, DHT_FILENAME))
            self.dht_running = False

    # Calculations

    def calc_ratio(self, unique_ID, torrent_state):
        try:
            up = float((self.unique_IDs[unique_ID].initial_uploaded_memory + self.get_core_torrent_state(unique_ID, False)['total_upload']) / 1024)
        except AttributeError:
            up = float((self.unique_IDs[unique_ID].uploaded_memory + self.get_core_torrent_state(unique_ID, False)['total_upload']) / 1024)
        down = float(torrent_state["total_done"] / 1024)
        try:
            ret = up/down
        except:
            ret = 0.0
            
        return ret    

    def create_torrent(self, filename, source_directory, trackers, comments=None,
                    piece_size=32, author="Deluge", private=False, webseeds=None):
        return deluge_core.create_torrent(filename, source_directory, trackers, comments, piece_size, author, private, webseeds)

    # Creates/resets the IP filter list
    def reset_ip_filter(self):
        return deluge_core.reset_IP_filter()

    # Adds an IP range (as two dotted quad strings) to the filter 
    def add_range_to_ip_filter(self, start, end):
        return deluge_core.add_range_to_IP_filter(start, end)

    def set_ip_filter(self):
        return deluge_core.set_IP_filter()

    def proxy_settings(self, server, login, paswd, portnum, proxytype, proxy):
        return deluge_core.proxy_settings(server, login, paswd, portnum, proxytype, proxy)

    def pe_settings(self, out_enc_policy, in_enc_policy, allowed_enc_level, prefer_rc4):
        return deluge_core.pe_settings(out_enc_policy, in_enc_policy, allowed_enc_level, prefer_rc4)

    def get_trackers(self, unique_ID):
        if self.unique_IDs[unique_ID].trackers:
            return self.unique_IDs[unique_ID].trackers
        else:
            return deluge_core.get_trackers(unique_ID)

    def replace_trackers(self, unique_ID, trackerslist):
        try:
            self.unique_IDs[unique_ID].trackers = trackerslist
            self.unique_IDs[unique_ID].trackers_changed = 1
            return deluge_core.replace_trackers(unique_ID, trackerslist)
        except:
            pass

    def set_priv(self, unique_ID, on_off):
        return deluge_core.set_priv(unique_ID, on_off)

    def set_max_connections_per_torrent(self, unique_ID, max_connections):
        return deluge_core.set_max_connections_per_torrent(unique_ID, 
                   max_connections)
    
    def set_max_upload_slots_per_torrent(self, unique_ID, max_upload_slots):
        return deluge_core.set_max_upload_slots_per_torrent(unique_ID, 
                   max_upload_slots)

    def set_per_upload_rate_limit(self, unique_ID, speed):
        return deluge_core.set_per_upload_rate_limit(unique_ID, speed)

    def set_per_download_rate_limit(self, unique_ID, speed):
        return deluge_core.set_per_download_rate_limit(unique_ID, speed)

    def get_per_upload_rate_limit(self, unique_ID):
        return deluge_core.get_per_upload_rate_limit(unique_ID)

    def get_per_download_rate_limit(self, unique_ID):
        return deluge_core.get_per_download_rate_limit(unique_ID)

    def add_url_seed(self, unique_ID, address):
        return deluge_core.add_url_seed(unique_ID, address)

    def get_torrent_path(self, unique_ID):
        torrent_path = self.unique_IDs[unique_ID].save_dir
        torrent_state = self.get_torrent_state(unique_ID)
        if torrent_state["num_files"] > 1:
            file = self.get_torrent_file_info(unique_ID)[0]
            torrent_path = os.path.join(torrent_path,
                                        file["path"].split("/", 1)[0])
        return torrent_path

    def rename_file(self, unique_ID, filename, filesize):
        return deluge_core.remap_files(unique_ID, filename, filesize)
