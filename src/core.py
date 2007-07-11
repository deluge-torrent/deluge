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

import deluge_core
import os
import os.path
import shutil
import statvfs
import pickle
import time
import gettext
import pref

# Constants

TORRENTS_SUBDIR = "torrentfiles"

STATE_FILENAME  = "persistent.state"
PREFS_FILENAME  = "prefs.state"
DHT_FILENAME    = "dht.state"

CACHED_DATA_EXPIRATION = 1 # seconds, like the output of time.time()

PREF_FUNCTIONS = {
    "max_uploads"         : deluge_core.set_max_uploads,
    "listen_on"           : deluge_core.set_listen_on,
    "max_connections"     : deluge_core.set_max_connections,
    "max_active_torrents" : None, # no need for a function, applied constantly
    "auto_seed_ratio"     : None, # no need for a function, applied constantly
    "max_download_speed_bps"   : deluge_core.set_download_rate_limit,
    "max_upload_speed_bps"     : deluge_core.set_upload_rate_limit,
    "enable_dht"          : None, # not a normal pref in that is is applied only on start 
    "use_upnp"        : deluge_core.use_upnp,
    "use_natpmp"        : deluge_core.use_natpmp,
    "use_utpex"        : deluge_core.use_utpex,
}

def N_(self):
        return self

STATE_MESSAGES = (    N_("Queued"),
                    N_("Checking"),
                    N_("Connecting"),
                    N_("Downloading Metadata"),
                    N_("Downloading"),
                    N_("Finished"),
                    N_("Seeding"),
                    N_("Allocating")
                     )
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
        return _("%d %d bytes needed")%(self.free_space, self.needed_space)

# A cached data item

class cached_data:
    def __init__(self, get_method, key):
        self.get_method = get_method
        self.key        = key

        self.timestamp = -1

    def get(self, efficiently=True):
        if self.timestamp == -1 or time.time() > self.timestamp + CACHED_DATA_EXPIRATION or \
           not efficiently:
            self.data = self.get_method(self.key)
            self.timestamp = time.time()

        return self.data

        
# Persistent information for a single torrent

class torrent_info:
    def __init__(self, filename, save_dir, compact):
        self.filename  = filename
        self.save_dir  = save_dir
        self.compact   = compact

        self.user_paused     = False # start out unpaused
        self.uploaded_memory = 0

        self.delete_me = False # set this to true, to delete it on next sync


# The persistent state of the torrent system. Everything in this will be pickled

class persistent_state:
    def __init__(self):
        # Torrents
        self.torrents = []

        # Prepare queue (queue is pickled, just like everything else)
        self.queue = [] # queue[x] is the unique_ID of the x-th queue position. Simple.


# The manager for the torrent system

class Manager:
    # blank_slate mode ignores the two pickle files and DHT state file, i.e. you start
    # completely fresh. When quitting, the old files will be overwritten
    def __init__(self, client_ID, version, user_agent, base_dir, blank_slate=False):
        self.base_dir = base_dir

        # Ensure directories exist
        if not TORRENTS_SUBDIR in os.listdir(self.base_dir):
            os.mkdir(os.path.join(self.base_dir, TORRENTS_SUBDIR))

        # Pre-initialize the core's data structures
        deluge_core.pre_init(DelugeError,
                          InvalidEncodingError,
                          FilesystemError,
                          DuplicateTorrentError,
                          InvalidTorrentError)

        # Start up the core
        assert(len(version) == 4)
        deluge_core.init(client_ID,
                             int(version[0]),
                             int(version[1]),
                             int(version[2]),
                             int(version[3]),
                             user_agent)

        self.constants = deluge_core.constants()

        # Unique IDs are NOT in the state, since they are temporary for each session
        self.unique_IDs = {} # unique_ID -> a torrent_info object, i.e. persistent data

        # Saved torrent core_states. We do not poll the core in a costly manner, necessarily
        self.saved_core_torrent_states = {} # unique_ID -> torrent_state

        # supplementary torrent states
        self.supp_torrent_states = {} # unique_ID->dict of data

        # Saved torrent core_states. We do not poll the core in a costly manner, necessarily
        self.saved_core_torrent_peer_infos = {} # unique_ID -> torrent_state
        
        # Saved torrent core_states. We do not poll the core in a costly manner, necessarily
        self.saved_core_torrent_file_infos = {} # unique_ID -> torrent_state
        
        # Keeps track of DHT running state
        self.dht_running = False

        # Load the preferences
        self.config = pref.Preferences(os.path.join(self.base_dir, PREFS_FILENAME))
        
        # Apply preferences. Note that this is before any torrents are added
        self.apply_prefs()

        PREF_FUNCTIONS["enable_dht"] = self.set_DHT 

        # Unpickle the state, or create a new one
        if not blank_slate:
            try:
                pkl_file = open(os.path.join(self.base_dir, STATE_FILENAME), 'rb')
                self.state = pickle.load(pkl_file)
                pkl_file.close()

                # Sync with the core: tell core about torrents, and get unique_IDs
                self.sync()

                # Apply all the file filters, right after adding the torrents
                self.apply_all_file_filters()

                # Apply the queue at this time, after all is loaded and ready
                self.apply_queue()
            except IOError:
                self.state = persistent_state()
        else:
            self.state = persistent_state()



    def quit(self):
        # Analyze data needed for pickling, etc.
        self.pre_quitting()

        # Pickle the prefs
        print "Saving prefs..."
        self.config.save()

        # Pickle the state
        print "Pickling state..."
        output = open(os.path.join(self.base_dir, STATE_FILENAME), 'wb')
        pickle.dump(self.state, output)
        output.close()

        # Stop DHT, if needed
        self.set_DHT(False)

        # Save fastresume data
        print "Saving fastresume data..."
        self.save_fastresume_data()

        # Shutdown torrent core
        print "Quitting the core..."
        deluge_core.quit()

    def pre_quitting(self):
        # Save the uploaded data from this session to the existing upload memory
        for unique_ID in self.unique_IDs.keys():
            self.unique_IDs[unique_ID].uploaded_memory = \
                    self.unique_IDs[unique_ID].uploaded_memory + \
                    self.get_core_torrent_state(unique_ID, False)['total_upload'] # Purposefully ineffi.

    # Preference management functions

    def get_config(self):
        # This returns the preference object
        return self.config
        
    def get_pref(self, key):
        # Get the value from the preferences object
        return self.config.get(key)

    def set_pref(self, key, value):
        # Make sure this is a valid key
        if key not in pref.DEFAULT_PREFS.keys():
            raise DelugeError("Asked to change a pref that isn't valid: " + key)

        self.config.set(key, value)

        # Apply the pref, if applicable
        if PREF_FUNCTIONS[key] is not None:
            PREF_FUNCTIONS[key](value)
        
    # Torrent addition and removal functions

    def add_torrent(self, filename, save_dir, compact):
        self.add_torrent_ns(filename, save_dir, compact)
        return self.sync() # Syncing will create a new torrent in the core, and return it's ID

    def remove_torrent(self, unique_ID, data_also, torrent_also):
        temp = self.unique_IDs[unique_ID]
        temp_fileinfo = deluge_core.get_file_info(unique_ID)

        self.remove_torrent_ns(unique_ID)
        self.sync()

        # Remove .torrent file if asked to do so
        if torrent_also:
            os.remove(temp.filename)
            
        # Remove data, if asked to do so
        if data_also:
            # Must be done AFTER the torrent is removed
            # Note: can this be to the trash?
            for filedata in temp_fileinfo:
                filename = filedata['path']
                if filename.find(os.sep) != -1:
                    # This is a file inside a directory inside the torrent. We can delete the
                    # directory itself, save time
                    try:
                        shutil.rmtree(os.path.dirname(os.path.join(temp.save_dir, filename)))
                    except OSError: # Perhaps it wasn't downloaded
                        pass
                # Perhaps this is just a file, try to remove it
                try:
                    os.remove(os.path.join(temp.save_dir, filename))
                except OSError:
                    pass # No file just means it wasn't downloaded, we can continue

    # A function to try and reload a torrent from a previous session. This is
    # used in the event that Deluge crashes and a blank state is loaded.
    def add_old_torrent(self, filename, save_dir, compact):
        if not filename in os.listdir(os.path.join(self.base_dir, TORRENTS_SUBDIR)):
            raise InvalidTorrentError(_("File was not found") + ": " + filename)

        full_new_name = os.path.join(self.base_dir, TORRENTS_SUBDIR, filename)

        # Create torrent object
        new_torrent = torrent_info(full_new_name, save_dir, compact)
        self.state.torrents.append(new_torrent)
        
        return self.sync()

    # A separate function, because people may want to call it from time to time
    def save_fastresume_data(self, uid=None):
        if uid == None:
            for unique_ID in self.unique_IDs:
                deluge_core.save_fastresume(unique_ID, self.unique_IDs[unique_ID].filename)
        else:
            deluge_core.save_fastresume(uid, self.unique_IDs[uid].filename)

    # Load all NEW torrents in a directory. The GUI can call this every minute or so,
    # if one wants a directory to be 'watched' (personally, I think it should only be
    # done on user command).os.path.join(
    def autoload_directory(self, directory, save_dir, compact):
        for filename in os.listdir(directory):
            if filename[-len(".torrent"):].lower() == ".torrent":
                try:
                    self.add_torrent_ns(self, filename, save_dir, compact)
                except DuplicateTorrentError:
                    pass

        self.sync()

    # State retrieval functions

    def get_state(self):
        ret = deluge_core.get_session_info()

        # Get additional data from our level
        ret['is_listening'] = deluge_core.is_listening()
        ret['port']         = deluge_core.listening_port()
        if self.dht_running == True:
            ret['DHT_nodes'] = deluge_core.get_DHT_info()

        return ret

    # This is the EXTERNAL function, for the GUI. It returns the core_state + supp_state
    def get_torrent_state(self, unique_ID):
        # Check to see if unique_ID exists:
        if self.state.queue.count(unique_ID) == 0:
            raise InvalidUniqueIDError("Asked for a torrent that doesn't exist")
         
        ret = self.get_core_torrent_state(unique_ID, True).copy()

        # Add the deluge-level things to the deluge_core data
        if self.get_supp_torrent_state(unique_ID) is not None:
            ret.update(self.get_supp_torrent_state(unique_ID))

        # Get queue position
        ret['queue_pos'] = self.state.queue.index(unique_ID)

        return ret

    def get_torrent_peer_info(self, unique_ID):
        # Perhaps at some time we may add info here
        return self.get_core_torrent_peer_info(unique_ID)
    
    def get_torrent_file_info(self, unique_ID):
        return self.get_core_torrent_file_info(unique_ID)

    # Queueing functions

    def queue_top(self, unique_ID, enforce_queue=True):
        self.state.queue.insert(0,self.state.queue.pop(self.get_queue_index(unique_ID)))

    def queue_up(self, unique_ID, enforce_queue=True):
        curr_index = self.get_queue_index(unique_ID)
        if curr_index > 0:
            temp = self.state.queue[curr_index - 1]
            self.state.queue[curr_index - 1] = unique_ID
            self.state.queue[curr_index]     = temp
            if enforce_queue:
                self.apply_queue()

    def queue_down(self, unique_ID, enforce_queue=True):
        curr_index = self.get_queue_index(unique_ID)
        if curr_index < (len(self.state.queue) - 1):
            temp = self.state.queue[curr_index + 1]
            self.state.queue[curr_index + 1] = unique_ID
            self.state.queue[curr_index]     = temp
            if enforce_queue:
                self.apply_queue()

    def queue_bottom(self, unique_ID, enforce_queue=True):
        curr_index = self.get_queue_index(unique_ID)
        if curr_index < (len(self.state.queue) - 1):
            self.state.queue.remove(unique_ID)
            self.state.queue.append(unique_ID)
            if enforce_queue:
                self.apply_queue()

    def clear_completed(self):
        for unique_ID in self.unique_IDs:
            torrent_state = self.get_core_torrent_state(unique_ID)
            if torrent_state['progress'] == 1.0:
                self.remove_torrent_ns(unique_ID)

        self.sync()
        self.apply_queue()

    # Enforce the queue: pause/unpause as needed, based on queue and user_pausing
    # This should be called after changes to relevant parameters (user_pausing, or
    # altering max_active_torrents), or just from time to time
    # ___ALL queuing code should be in this function, and ONLY here___
    def apply_queue(self, efficient = True):
        # Handle autoseeding - downqueue as needed
        if self.get_pref('auto_seed_ratio') > 0 and self.get_pref('auto_end_seeding'):
            for unique_ID in self.unique_IDs:
                if self.get_core_torrent_state(unique_ID, efficient)['is_seed']:
                    torrent_state = self.get_core_torrent_state(unique_ID, efficient)
                    ratio = self.calc_ratio(unique_ID, torrent_state)
                    if ratio >= self.get_pref('auto_seed_ratio'):
                        self.queue_bottom(unique_ID, enforce_queue=False) # don't recurse!
                        self.set_user_pause(unique_ID, True, enforce_queue=False)

        # Pause and resume torrents
        for index in range(len(self.state.queue)):
            unique_ID = self.state.queue[index]
            if (index < self.get_pref('max_active_torrents') or self.get_pref('max_active_torrents') == -1) \
                and self.get_core_torrent_state(unique_ID, efficient)['is_paused']               \
                and not self.is_user_paused(unique_ID):
                
                # This torrent is a seed so skip all the free space checking
                if self.get_core_torrent_state(unique_ID, efficient)['is_seed']:
                    deluge_core.resume(unique_ID)
                    continue
                    
                # Before we resume, we should check if the torrent is using Full Allocation 
                # and if there is enough space on to finish this file.
                if self.unique_IDs[unique_ID].compact == False:
                    torrent_state = self.get_core_torrent_state(unique_ID, efficient)
                    avail = self.calc_free_space(self.unique_IDs[unique_ID].save_dir)
                    total_needed = torrent_state["total_size"] - torrent_state["total_done"]
                    if total_needed < avail:
                        # We have enough free space, so lets resume this torrent
                        deluge_core.resume(unique_ID)
                    else:
                        print "Not enough free space to resume this torrent!"
                else: #We're using compact allocation so lets just resume
                    deluge_core.resume(unique_ID)

            elif (not self.get_core_torrent_state(unique_ID, efficient)['is_paused']) and \
                  ( (index >= self.get_pref('max_active_torrents') and \
                    self.get_pref('max_active_torrents') != -1        ) or \
                self.is_user_paused(unique_ID)):
                deluge_core.pause(unique_ID)

    # Event handling

    def handle_events(self):
        # Handle them for the backend's purposes, but still send them up in case the client
        # wants to do something - show messages, for example
        def pop_event():
            try:
                return deluge_core.pop_event()
            except:
                pass
            else:
                return deluge_core.pop_event()
                
        ret = []
        try:
            event = deluge_core.pop_event()
        except:
            pass
        else:
            while event is not None:
    #            print "EVENT: ", event

                ret.append(event)
                try:
                    if event['unique_ID'] not in self.unique_IDs:
                        event = pop_event()
                        continue
                except KeyError:
                    event = pop_event()
                    continue
                    
                if event['event_type'] is self.constants['EVENT_FINISHED']:
                    # Queue seeding torrent to bottom if needed
                    if(self.get_pref('enable_move_completed')):
                        deluge_core.move_storage(event['unique_ID'], self.get_pref('default_finished_path'))
                        self.unique_IDs[event['unique_ID']].save_dir = self.get_pref('default_finished_path')
                    if self.get_pref('queue_seeds_to_bottom'):
                        self.queue_bottom(event['unique_ID'])
                    # If we are autoseeding, then we need to apply the queue
                    if self.get_pref('auto_seed_ratio') == -1:
                        self.apply_queue(efficient = False) # To work on current data
                    #save fast resume once torrent finshes so as to not recheck seed if client crashes
                    self.save_fastresume_data(event['unique_ID'])
                elif event['event_type'] is self.constants['EVENT_TRACKER']:
                    unique_ID = event['unique_ID']
                    status    = event['tracker_status']
                    message   = event['message']
                    tracker   = message[message.find('"')+1:message.rfind('"')]

                    self.set_supp_torrent_state_val(unique_ID,            
                                                    "tracker_status",
                                                    (tracker, status))

                    old_state = self.get_supp_torrent_state(unique_ID)
                    try:
                        new = old_state['tracker_messages']
                    except KeyError:
                        new = {}

                    new[tracker] = message

                    self.set_supp_torrent_state_val(unique_ID,
                                                    "tracker_messages",
                                                    new)

                event = pop_event()

        return ret

    # Filtering functions

    def set_file_filter(self, unique_ID, file_filter):
        assert(len(file_filter) == self.get_core_torrent_state(unique_ID, True)['num_files'])

        self.unique_IDs[unique_ID].file_filter = file_filter[:]

        deluge_core.set_filter_out(unique_ID, file_filter)

    def get_file_filter(self, unique_ID):
        try:
            return self.unique_IDs[unique_ID].file_filter[:]
        except AttributeError:
            return None

    # Called when a session starts, to apply existing filters
    def apply_all_file_filters(self):
        for unique_ID in self.unique_IDs.keys():
            try:
                self.set_file_filter(unique_ID, self.unique_IDs[unique_ID].file_filter)
            except AttributeError:
                pass

    # Advanced statistics - these may be SLOW. The client should call these only
    # when needed, and perhaps only once in a long while (they are mostly just
    # approximations anyhow

    def calc_availability(self, unique_ID):
        return deluge_stats.calc_availability(self.get_core_torrent_peer_info(unique_ID))

    def calc_swarm_speed(self, unique_ID):
        pieces_per_sec = deluge_stats.calc_swarm_speed(self.get_core_torrent_peer_info(unique_ID))
        piece_length   = self.get_core_torrent_state(unique_ID, efficiently=True)

        return pieces_per_sec * piece_length

    # Miscellaneous minor functions

    def set_user_pause(self, unique_ID, new_value, enforce_queue=True):
        self.unique_IDs[unique_ID].user_paused = new_value
        if enforce_queue:
            self.apply_queue()

    def set_ratio(self, unique_ID, num):
        deluge_core.set_ratio(unique_ID, float(num))

    def is_user_paused(self, unique_ID):
        return self.unique_IDs[unique_ID].user_paused

    def get_num_torrents(self):
        return deluge_core.get_num_torrents()

    def get_unique_IDs(self):
        return self.unique_IDs.keys()

    def update_tracker(self, unique_ID):
        deluge_core.reannounce(unique_ID)


    ####################
    # Internal functions
    ####################

    # Efficient: use a saved state, if it hasn't expired yet
    def get_core_torrent_state(self, unique_ID, efficiently=True):
        if unique_ID not in self.saved_core_torrent_states.keys():
            self.saved_core_torrent_states[unique_ID] = cached_data(deluge_core.get_torrent_state,
                                                               unique_ID)

        return self.saved_core_torrent_states[unique_ID].get(efficiently)

    def get_supp_torrent_state(self, unique_ID):
        try:
            return self.supp_torrent_states[unique_ID]
        except KeyError:
            return None

    def set_supp_torrent_state_val(self, unique_ID, key, val):
        try:
            if self.supp_torrent_states[unique_ID] is None:
                self.supp_torrent_states[unique_ID] = {}
        except KeyError:
            self.supp_torrent_states[unique_ID] = {}

        self.supp_torrent_states[unique_ID][key] = val

    def get_core_torrent_peer_info(self, unique_ID, efficiently=True):
        if unique_ID not in self.saved_core_torrent_peer_infos.keys():
            self.saved_core_torrent_peer_infos[unique_ID] = cached_data(deluge_core.get_peer_info, unique_ID)

        return self.saved_core_torrent_peer_infos[unique_ID].get(efficiently)
    
    def get_core_torrent_file_info(self, unique_ID, efficiently=True):
        if unique_ID not in self.saved_core_torrent_file_infos.keys():
            self.saved_core_torrent_file_infos[unique_ID] = cached_data(deluge_core.get_file_info, unique_ID)
        
        return self.saved_core_torrent_file_infos[unique_ID].get(efficiently)

    # Functions for checking if enough space is available
    
    def calc_free_space(self, directory):
        dir_stats = os.statvfs(directory)
        block_size = dir_stats[statvfs.F_BSIZE]
        avail_blocks = dir_stats[statvfs.F_BAVAIL]
        return long(block_size * avail_blocks)

    # Non-syncing functions. Used when we loop over such events, and sync manually at the end

    def add_torrent_ns(self, filename, save_dir, compact):
        # Cache torrent file
        (temp, filename_short) = os.path.split(filename)

        # if filename_short in os.listdir(self.base_dir + "/" + TORRENTS_SUBDIR):
        #     raise DuplicateTorrentError("Duplicate Torrent, it appears: " + filename_short)

        full_new_name = os.path.join(self.base_dir, TORRENTS_SUBDIR, filename_short)

        try:
            shutil.copy(filename, full_new_name)
        except Exception, e:
            if str(e).find('are the same file'):
                pass
            else:
                raise

        # Create torrent object
        new_torrent = torrent_info(full_new_name, save_dir, compact)
        self.state.torrents.append(new_torrent)

    def remove_torrent_ns(self, unique_ID):
        self.unique_IDs[unique_ID].delete_me = True
        

    # Sync the state.torrents and unique_IDs lists with the core
    # ___ALL syncing code with the core is here, and ONLY here___
    # Also all self-syncing is done here (various lists)

    ##
    ## I had to make some changes here to get things to work properly
    ## Some of these changes may be hack-ish, so look at them and make
    ## sure nothing is wrong.
    ##
    def sync(self):
        ret = None # We return new added unique ID(s), or None
        no_space = False

        # Add torrents to core and unique_IDs
        torrents_with_unique_ID = self.unique_IDs.values()

        for torrent in self.state.torrents:
            if not os.path.exists(torrent.filename):
                print "Missing file: %s" % torrent.filename
                self.state.torrents.remove(torrent)
                continue
            if torrent not in torrents_with_unique_ID:
#                print "Adding torrent to core:", torrent.filename, torrent.save_dir, torrent.compact
                try:
                    unique_ID = deluge_core.add_torrent(torrent.filename,
                                                    torrent.save_dir,
                                                    torrent.compact)
                except DelugeError, e:
                    print "Error:", e
                    self.state.torrents.remove(torrent)
                    raise e
#                print "Got unique ID:", unique_ID

                ret = unique_ID
                self.unique_IDs[unique_ID] = torrent

        
#        print torrents_with_unique_ID
        # Remove torrents from core, unique_IDs and queue
        to_delete = []
        for unique_ID in self.unique_IDs.keys():
#            print torrent
            if self.unique_IDs[unique_ID].delete_me:
                deluge_core.remove_torrent(unique_ID)
                to_delete.append(unique_ID)

        for unique_ID in to_delete:
            self.state.torrents.remove(self.unique_IDs[unique_ID])
            self.state.queue.remove(unique_ID)
            # Remove .fastresume
            try:
                # Must be after removal of the torrent, because that saves a new .fastresume
                os.remove(self.unique_IDs[unique_ID].filename + ".fastresume")
            except OSError:
                pass # Perhaps there never was one to begin with
            del self.unique_IDs[unique_ID]
            
        # Add torrents to queue - at the end, of course
        for unique_ID in self.unique_IDs.keys():
            if unique_ID not in self.state.queue:
                self.state.queue.append(unique_ID)
        # run through queue, remove those that no longer exists
        to_delete = []
        for queue_item in self.state.queue:
            if queue_item not in self.unique_IDs.keys():
                to_delete.append(queue_item)
        for del_item in to_delete:
            self.state.queue.remove(del_item)

        assert(len(self.unique_IDs) == len(self.state.torrents))

        assert(len(self.unique_IDs) == len(self.state.queue))
        assert(len(self.unique_IDs) == deluge_core.get_num_torrents())
        
        #if no_space:
            #self.apply_queue()
        # Pickle the state so if we experience a crash, the latest state is available
        print "Pickling state..."
        output = open(os.path.join(self.base_dir, STATE_FILENAME), 'wb')
        pickle.dump(self.state, output)
        output.close()

        return ret

    def get_queue_index(self, unique_ID):
        return self.state.queue.index(unique_ID)


    def apply_prefs(self):
        print "Applying preferences"

        for pref in PREF_FUNCTIONS.keys():
            if PREF_FUNCTIONS[pref] is not None:
                PREF_FUNCTIONS[pref](self.get_pref(pref))


    def set_DHT(self, start=False):
        if start == True and self.dht_running != True:
            print "Starting DHT..."
            deluge_core.start_DHT(os.path.join(self.base_dir, DHT_FILENAME))
            self.dht_running = True
        elif start == False and self.dht_running == True:
            print "Stopping DHT..."
            deluge_core.stop_DHT(os.path.join(self.base_dir, DHT_FILENAME))
            self.dht_running = False

    # Calculations

    def calc_ratio(self, unique_ID, torrent_state):
        up = float((torrent_state['total_payload_upload'] / 1024) + (self.unique_IDs[unique_ID].uploaded_memory / 1024))
        down = float(torrent_state["total_done"] / 1024)
        try:
            ret = float(up/down)
        except:
            ret = 0
        return ret
    

    def create_torrent(self, filename, source_directory, trackers, comments=None,
                    piece_size=32, author="Deluge"):
        return deluge_core.create_torrent(filename, source_directory, trackers, comments, piece_size, author)

    # Creates/resets the IP filter list
    def reset_ip_filter(self):
        return deluge_core.reset_IP_filter()

    # Adds an IP range (as two dotted quad strings) to the filter 
    def add_range_to_ip_filter(self, start, end):
        return deluge_core.add_range_to_IP_filter(start, end)

    def proxy_settings(self, server, login, paswd, portnum, proxytype, peerproxy, trackerproxy, dhtproxy):
        if self.dht_running == False:
            dhtproxy = False
        return deluge_core.proxy_settings(server, login, paswd, portnum, proxytype, peerproxy, trackerproxy, dhtproxy)

    def pe_settings(self, out_enc_policy, in_enc_policy, allowed_enc_level, prefer_rc4):
        return deluge_core.pe_settings(out_enc_policy, in_enc_policy, allowed_enc_level, prefer_rc4)

    def get_trackers(self, unique_ID):
        return deluge_core.get_trackers(unique_ID)

    def replace_trackers(self, unique_ID, trackers):
        return deluge_core.replace_trackers(unique_ID, trackers)

