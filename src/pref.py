#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


# Preferences is basically a wrapper around a simple Python dictionary
# object.  However, this class provides a few extra features on top of
# the built in class that Deluge can take advantage of.

import pickle
import common
import os.path

DEFAULT_PREFS = {
    "file_manager" : common.FileManager.xdg,
    "open_folder_stock" : True,
    "open_folder_custom" : False,
    "open_folder_location": "",
    "send_info" : True,
    "auto_end_seeding" : False,
    "auto_seed_ratio" : 0,
    "close_to_tray" : False,
    "enable_files_dialog" : False,
    "queue_above_completed" : False,
    "clear_max_ratio_torrents" : False,
    "default_download_path" : os.path.expanduser("~/"),
    "default_load_path" : os.path.expanduser("~/"),
    "default_finished_path" : os.path.expanduser("~/"),
    "enable_move_completed" : False,
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
    "max_active_torrents" : 8,
    "max_connections_global" : 200,
    "max_connections_per_torrent" : -1,
    "max_download_speed" : -1,
    "max_download_speed_bps": -1,
    "max_upload_slots_global" : 15,
    "max_upload_slots_per_torrent" : -1,
    "max_upload_speed" : -1,
    "max_upload_speed_bps" : -1,
    "pref_rc4" : True,
    "prioritize_first_last_pieces" : False,
    "web_proxy_type" : common.ProxyType.none,
    "peer_proxy_type" : common.ProxyType.none,
    "dht_proxy_type" : common.ProxyType.none,
    "tracker_proxy_type" : common.ProxyType.none,
    "peer_proxy" : False,
    "tracker_proxy" : False,
    "dht_proxy" : False,
    "peer_proxy_hostname" : "",
    "peer_proxy_username" : "",
    "peer_proxy_password" : "",
    "peer_proxy_port": 8080,
    "dht_proxy_hostname" : "",
    "dht_proxy_username" : "",
    "dht_proxy_password" : "",
    "dht_proxy_port": 8080,
    "web_proxy_hostname" : "",
    "web_proxy_username" : "",
    "web_proxy_password" : "",
    "web_proxy_port": 8080,
    "tracker_proxy_hostname" : "",
    "tracker_proxy_username" : "",
    "tracker_proxy_password" : "",
    "tracker_proxy_port": 8080,
    "queue_seeds_to_bottom" : False,
    "random_port" : False,
    "show_availability" : True,
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
    "tray_downloadspeedlist" : [5.0, 10.0, 30.0, 80.0, 300.0],
    "tray_passwd" : "",
    "tray_uploadspeedlist" : [5.0, 10.0, 30.0, 80.0, 300.0],
    "use_compact_storage" : False,
    "use_full_storage" : True,
    "use_default_dir" : False,
    "use_natpmp" : False,
    "use_upnp" : False,
    "use_utpex" : True,
    "new_releases" : True,
    "window_height" : 480,
    "window_maximized" : False,
    "window_pane_position" : -1,
    "window_width" : 640,
    "window_x_pos" : 0,
    "window_y_pos" : 0,
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
    
    def get(self, key):
        try:
            value = self.mapping[key]
            return value
        except KeyError:
            return None
    
    def remove(self, key):
        self.mapping.pop(key)
    
    def clear(self):
        self.mapping.clear()
        
    def printout(self):
        for key in self.mapping.keys():
            print key, ':', self.mapping[key]
