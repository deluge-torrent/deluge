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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.

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
#	Torrents have 3 structures: 	
#		1. torrent_info - persistent data, like name, upload speed cap, etc.
#		2. core_torrent_state - transient state data from the core. This may take
#				time to calculate, so we do if efficiently
#		3. supp_torrent_state - supplementary torrent data, from Deluge


import deluge_core
import os, shutil
import pickle
import time


# Constants

TORRENTS_SUBDIR = "torrentfiles"

STATE_FILENAME  = "persistent.state"
PREFS_FILENAME  = "prefs.state"
DHT_FILENAME    = "dht.state"

CACHED_DATA_EXPIRATION = 1 # seconds, like the output of time.time()

#	"max_half_open"       : -1,
DEFAULT_PREFS = {
	"max_uploads"         : 2, # a.k.a. upload slots
	"listen_on"           : [6881,9999],
	"max_connections"     : 80,
	"use_DHT"             : True,
	"max_active_torrents" : -1,
	"auto_seed_ratio"     : -1,
	"max_download_rate"   : -1,
	"max_upload_rate"     : -1
						}

PREF_FUNCTIONS = {
	"max_uploads"         : deluge_core.set_max_uploads,
	"listen_on"           : deluge_core.set_listen_on,
	"max_connections"     : deluge_core.set_max_connections,
	"use_DHT"             : None, # not a normal pref in that is is applied only on start
	"max_active_torrents" : None, # no need for a function, applied constantly
	"auto_seed_ratio"     : None, # no need for a function, applied constantly
	"max_download_rate"   : deluge_core.set_download_rate_limit,
	"max_upload_rate"     : deluge_core.set_upload_rate_limit
						}
STATE_MESSAGES = (	"Queued",
					"Checking",
					"Connecting",
					"Downloading Metadata",
					"Downloading",
					"Finished",
					"Seeding",
					"Allocating"
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

class DuplicateTorrentError(DelugeError):
	pass

class InvalidTorrentError(DelugeError):
	pass

class InvalidUniqueIDError(DelugeError):
	pass

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
			os.mkdir(self.base_dir + "/" + TORRENTS_SUBDIR)

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

		# Unpickle the preferences, or create a new one
		self.prefs = DEFAULT_PREFS
		if not blank_slate:
			try:
				pkl_file = open(self.base_dir + "/" + PREFS_FILENAME, 'rb')
				self.prefs = pickle.load(pkl_file)
				pkl_file.close()
			except IOError:
				pass

		# Apply preferences. Note that this is before any torrents are added
		self.apply_prefs()

		# Apply DHT, if needed. Note that this is before any torrents are added
		if self.get_pref('use_DHT'):
			if not blank_slate:
				deluge_core.start_DHT(self.base_dir + "/" + DHT_FILENAME)
			else:
				deluge_core.start_DHT("")

		# Unpickle the state, or create a new one
		if not blank_slate:
			try:
				pkl_file = open(self.base_dir + "/" + STATE_FILENAME, 'rb')
				self.state = pickle.load(pkl_file)
				pkl_file.close()

				# Sync with the core: tell core about torrents, and get unique_IDs
				self.sync()

				# Apply all the file filters, right after adding the torrents
				self.apply_all_file_filters()
			except IOError:
				self.state = persistent_state()
		else:
			self.state = persistent_state()

	def quit(self):
		# Analyze data needed for pickling, etc.
		self.pre_quitting()

		# Pickle the prefs
		print "Pickling prefs..."
		output = open(self.base_dir + "/" + PREFS_FILENAME, 'wb')
		pickle.dump(self.prefs, output)
		output.close()

		# Pickle the state
		print "Pickling state..."
		output = open(self.base_dir + "/" + STATE_FILENAME, 'wb')
		pickle.dump(self.state, output)
		output.close()

		# Save fastresume data
		print "Saving fastresume data..."
		self.save_fastresume_data()

		# Stop DHT, if needed
		if self.get_pref('use_DHT'):
			print "Stopping DHT..."
			deluge_core.stop_DHT(self.base_dir + "/" + DHT_FILENAME)

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

	def get_pref(self, key):
		# If we have a value, return, else fallback on default_prefs, else raise an error
		# the fallback is useful if the source has newer prefs than the existing pref state,
		# which was created by an old version of the source
		if key in self.prefs.keys():
			return self.prefs[key]
		elif key in DEFAULT_PREFS:
			self.prefs[key] = DEFAULT_PREFS[key]
			return self.prefs[key]
		else:
			raise DelugeError("Asked for a pref that doesn't exist: " + key)

	def set_pref(self, key, value):
		# Make sure this is a valid key
		if key not in DEFAULT_PREFS.keys():
			raise DelugeError("Asked to change a pref that isn't valid: " + key)

		self.prefs[key] = value

		# Apply the pref, if applicable
		if PREF_FUNCTIONS[key] is not None:
			PREF_FUNCTIONS[key](value)

	# Torrent addition and removal functions

	def add_torrent(self, filename, save_dir, compact):
		self.add_torrent_ns(filename, save_dir, compact)
		return self.sync() # Syncing will create a new torrent in the core, and return it's ID

	def remove_torrent(self, unique_ID, data_also):
		# Save some data before we remove the torrent, needed later in this func
		temp = self.unique_IDs[unique_ID]
		temp_fileinfo = deluge_core.get_file_info(unique_ID)

		self.remove_torrent_ns(unique_ID)
		self.sync()

		# Remove .torrent and  .fastresume
		os.remove(temp.filename)
		try:
			# Must be after removal of the torrent, because that saves a new .fastresume
			os.remove(temp.filename + ".fastresume")
		except OSError:
			pass # Perhaps there never was one to begin with

		# Remove data, if asked to do so
		if data_also:
			# Must be done AFTER the torrent is removed
			# Note: can this be to the trash?
			for filedata in temp_fileinfo:
				filename = filedata['path']
				try:
					os.remove(temp.save_dir + "/" + filename)
				except OSError:
					pass # No file just means it wasn't downloaded, we can continue

	# A separate function, because people may want to call it from time to time
	def save_fastresume_data(self):
		for unique_ID in self.unique_IDs:
			deluge_core.save_fastresume(unique_ID, self.unique_IDs[unique_ID].filename)

	# State retrieval functions

	def get_state(self):
		ret = deluge_core.get_session_info()

		# Get additional data from our level
		ret['is_listening'] = deluge_core.is_listening()
		ret['port']         = deluge_core.listening_port()
		if self.get_pref('use_DHT'):
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

	# Queueing functions

	def queue_up(self, unique_ID):
		curr_index = self.get_queue_index(unique_ID)
		if curr_index > 0:
			temp = self.state.queue[curr_index - 1]
			self.state.queue[curr_index - 1] = unique_ID
			self.state.queue[curr_index]     = temp

	def queue_down(self, unique_ID):
		curr_index = self.get_queue_index(unique_ID)
		if curr_index < (len(self.state.queue) - 1):
			temp = self.state.queue[curr_index + 1]
			self.state.queue[curr_index + 1] = unique_ID
			self.state.queue[curr_index]     = temp

	def queue_bottom(self, unique_ID):
		curr_index = self.get_queue_index(unique_ID)
		if curr_index < (len(self.state.queue) - 1):
			self.state.queue.remove(curr_index)
			self.state.queue.append(unique_ID)

	def clear_completed(self):
		for unique_ID in self.unique_IDs:
			torrent_state = self.get_core_torrent_state(unique_ID)
			if torrent_state['progress'] == 100.0:
				self.remove_torrent_ns(unique_ID)

		self.sync()

	# Enforce the queue: pause/unpause as needed, based on queue and user_pausing
	# This should be called after changes to relevant parameters (user_pausing, or
	# altering max_active_torrents), or just from time to time
	# ___ALL queuing code should be in this function, and ONLY here___
	def apply_queue(self, efficient = True):
		# Handle autoseeding - downqueue as needed

		if self.auto_seed_ratio != -1:
			for unique_ID in self.unique_IDs:
				if self.get_core_torrent_state(unique_ID, efficient)['is_seed']:
					torrent_state = self.get_core_torrent_state(unique_ID, efficient)
					ratio = self.calc_ratio(unique_ID, torrent_state)
					if ratio >= self.auto_seed_ratio:
						self.queue_bottom(unique_ID)

		# Pause and resume torrents
		for index in range(len(self.state.queue)):
			unique_ID = self.state.queue[index]
			if (index < self.state.max_active_torrents or self.state_max_active_torrents == -1) \
				and self.get_core_torrent_state(unique_ID, efficient)['is_paused']               \
				and not self.is_user_paused(unique_ID):
				deluge_core.resume(unique_ID)
			elif not self.get_core_torrent_state(unique_ID, efficient)['is_paused'] and \
					(index >= self.state.max_active_torrents or self.is_user_paused(unique_ID)):
				deluge_core.pause(unique_ID)

	# Event handling

	def handle_events(self):
		# Handle them for the backend's purposes, but still send them up in case the client
		# wants to do something - show messages, for example
		ret = []

		event = deluge_core.pop_event()

		while event is not None:
#			print "EVENT: ", event

			ret.append(event)

			if event['event_type'] is self.constants['EVENT_FINISHED']:
				# If we are autoseeding, then we need to apply the queue
				if self.get_pref('auto_seed_ratio') == -1:
					self.apply_queue(efficient = False) # To work on current data
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

			event = deluge_core.pop_event()

		return ret

	# Filtering functions

	def set_file_filter(self, unique_ID, file_filter):
		assert(len(file_filter) == self.get_core_torrent_state(unique_ID, True)['num_files'])

		self.unique_IDs[unique_ID].file_filter = file_filter[:]

		deluge_core.set_filter_out(file_filter)

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

	def set_user_pause(self, unique_ID, new_value):
		self.unique_IDs[unique_ID].user_paused = new_value
		self.apply_queue()

	def is_user_paused(self, unique_ID):
		return self.unique_IDs[unique_ID].user_paused

	def get_num_torrents(self):
		return deluge_core.get_num_torrents()

	def get_unique_IDs(self):
		return self.unique_IDs.keys()


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
			self.saved_core_torrent_peer_infos[unique_ID] = cached_data(deluge_core.get_peer_info,
			                                                       unique_ID)

		return self.saved_core_torrent_peer_infos[unique_ID].get(efficiently)

	# Non-syncing functions. Used when we loop over such events, and sync manually at the end

	def add_torrent_ns(self, filename, save_dir, compact):
		# Cache torrent file
		(temp, filename_short) = os.path.split(filename)

		if filename_short in os.listdir(self.base_dir + "/" + TORRENTS_SUBDIR):
			raise DelugeError("Duplicate Torrent, it appears: " + filename_short)

		full_new_name = self.base_dir + "/" + TORRENTS_SUBDIR + "/" + filename_short

		shutil.copy(filename, full_new_name)

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

		# Add torrents to core and unique_IDs
		torrents_with_unique_ID = self.unique_IDs.values()

		for torrent in self.state.torrents:
			if torrent not in torrents_with_unique_ID:
#				print "Adding torrent to core:", torrent.filename, torrent.save_dir, torrent.compact
				unique_ID = deluge_core.add_torrent(torrent.filename,
				                                    torrent.save_dir,
				                                    torrent.compact)
#				print "Got unique ID:", unique_ID
				ret = unique_ID
				self.unique_IDs[unique_ID] = torrent
		
#		print torrents_with_unique_ID
		# Remove torrents from core, unique_IDs and queue
		to_delete = []
		for unique_ID in self.unique_IDs.keys():
#			print torrent
			if self.unique_IDs[unique_ID].delete_me:
				deluge_core.remove_torrent(unique_ID)
				to_delete.append(unique_ID)

		for unique_ID in to_delete:
			self.state.torrents.remove(self.unique_IDs[unique_ID])
			self.state.queue.remove(unique_ID)
			del self.unique_IDs[unique_ID]

		# Add torrents to queue - at the end, of course
		for unique_ID in self.unique_IDs.keys():
			if unique_ID not in self.state.queue:
				self.state.queue.append(unique_ID)

		assert(len(self.unique_IDs) == len(self.state.torrents))
		assert(len(self.unique_IDs) == len(self.state.queue))
		assert(len(self.unique_IDs) == deluge_core.get_num_torrents())

		return ret

	def get_queue_index(self, unique_ID):
		return self.state.queue.index(unique_ID)

	def apply_prefs(self):
		print "Applying preferences"
		assert(len(PREF_FUNCTIONS) == len(DEFAULT_PREFS))

		for pref in PREF_FUNCTIONS.keys():
			if PREF_FUNCTIONS[pref] is not None:
				PREF_FUNCTIONS[pref](self.get_pref(pref))

	# Calculations

	def calc_ratio(self, unique_ID, torrent_state):
		up = float(torrent_state['total_upload'] + self.unique_IDs[unique_ID].uploaded_memory)
		down = float(torrent_state["total_done"])
					
		try:
			ret = float(up/down)
		except:
			ret = -1

		return ret
