# pref.py
#
# Copyright (C) Zach Tibbitts 2006 <zach@collegegeek.org>
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


# Preferences is basically a wrapper around a simple Python dictionary
# object.  However, this class provides a few extra features on top of
# the built in class that Deluge can take advantage of.

import pickle
import common

DEFAULT_PREFS = {
	"auto_end_seeding" : False,
	"auto_seed_ratio" : -1,
	"close_to_tray" : False,
	"default_download_path" : "",
	"dht_connections" : 80,
	"enable_dht" : True,
	"enable_system_tray" : True,
	"enabled_plugins" : "",
	"encin_state" : common.EncState.enabled,
	"encout_state" : common.EncState.enabled,
	"enclevel_type" : common.EncLevel.both,
	"end_seed_ratio" : 0.0,
	"gui_update_interval" : 1.0,
	"listen_on" : [6881,6889],
	"lock_tray" : False,
	"max_active_torrents" : -1,
	"max_connections" : 80,
	"max_download_rate" : -1.0,
	"max_download_rate_bps": -1.0,
	"max_number_downloads" : -1.0,
	"max_number_torrents" : -1.0,
	"max_number_uploads" : -1.0,
	"max_upload_rate" : -1.0,
	"max_upload_rate_bps" : -1.0,
	"max_uploads" : 2,
	"pref_rc4" : True,
	"queue_seeds_to_bottom" : False,
	"show_dl" : True,
	"show_eta" : True,
	"show_infopane" : True,
	"show_peers" : True,
	"show_seeders" : True,
	"show_share" : True,
	"show_size" : True,
	"show_status" : True,
	"show_toolbar" : True,
	"show_ul" : True,
	"tray_passwd" : "",
	"use_compact_storage" : False,
	"use_default_dir" : False,
	"window_height" : 480,
	"window_maximized" : False,
	"window_pane_position" : -1,
	"window_width" : 640,
	"window_x_pos" : 0,
	"window_y_pos" : 0
}
class Preferences:
	def __init__(self, filename=None, global_defaults=True, defaults=None):
		self.mapping = {}
		if defaults is not None:
			for key in defaults.keys():
				self.mapping.setdefault(key, defaults[key])
		
		if global_defaults is True:
			self.mapping = DEFAULT_PREFS
				
		self.config_file = filename
		if self.config_file is not None:
			self.load(self.config_file)
	
	# Allows you to access an item in a Preferences objecy by calling
	# instance[key] rather than instance.get(key).  However, this will
	# return the value as the type it is currently in memory, so it is
	# advisable to use get() if you need the value converted.
	def __getitem__(self, key):
		return self.mapping[key]
	
	def __setitem__(self, key, value):
		self.mapping[key] = value
	
	def __delitem__(self, key):
		del self.mapping[key]
	
	def __len__(self):
		return len(self.mapping)
	
	def has_key(self, key): return self.mapping.has_key(key)
	def items(self): return self.mapping.items()
	def keys(self): return self.mapping.keys()
	def values(self): return self.mapping.values()
	
	def save(self, filename=None):
		if filename is None:
			filename = self.config_file
		try:
			pkl_file = open(filename, 'wb')
			pickle.dump(self.mapping, pkl_file)
			pkl_file.close()
		except IOError:
			pass

	def load(self, filename=None):
		if filename is None:
			filename = self.config_file
		try:
			pkl_file = open(filename, 'rb')
			self.dump = pickle.load(pkl_file)
			self.mapping.update(self.dump)
			pkl_file.close()
		except IOError:
			pass
		except EOFError:
			pkl_file.close()
			pass
	
	def set(self, key, value):
		self.mapping[key] = value
	
	def get(self, key, kind=None, default=None):
		if not key in self.mapping.keys():
			if default is not None:
				self.mapping[key] = default
				return default
			else:
				raise KeyError
		result = self.mapping[key]
		if kind == None:
			pass
		elif kind == bool:
			if isinstance(result, str):
				result = not (result.lower() == "false")
			elif isinstance(result, int):
				result = not (result == 0)
			else:
				result = False
		elif kind == int:
			try:
				result = int(result)
			except ValueError:
				result = int(float(result))
		elif kind == float:
			result = float(result)		
		elif kind == str:
			result = str(result)
		else:
			pass
		
		return result
	
	def remove(self, key):
		self.mapping.pop(key)
	
	def clear(self):
		self.mapping.clear()
		
	def printout(self):
		for key in self.mapping.keys():
			print key, ':', self.mapping[key]
		
