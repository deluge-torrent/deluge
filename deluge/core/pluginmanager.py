#
# pluginmanager.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
# 	Boston, MA    02110-1301, USA.
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

"""PluginManager for Core"""

import os.path

import pkg_resources

from deluge.log import LOG as log

class PluginManager:
    """PluginManager handles the loading of plugins and provides plugins with
    functions to access parts of the core."""
    
    def __init__(self):
        # Set up the hooks dictionary
        self.hooks = {
            "post_torrent_add": [],
            "post_torrent_remove": []
        }
        
        self.status_fields = {}
        
        # This will load any .eggs in the plugins folder inside the main
        # deluge egg.. Need to scan the local plugin folder too.
        
        plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
        
        pkg_resources.working_set.add_entry(plugin_dir)
        pkg_env = pkg_resources.Environment([plugin_dir])
        
        self.plugins = {}
        for name in pkg_env:
            egg = pkg_env[name][0]
            egg.activate()
            for name in egg.get_entry_map("deluge.plugin.core"):
                entry_point = egg.get_entry_info("deluge.plugin.core", name)
                cls = entry_point.load()
                instance = cls(self)
                self.plugins[name] = instance
                log.info("Load plugin %s", name)
           
    def __getitem__(self, key):
        return self.plugins[key]
        
    def register_status_field(self, field, function):
        """Register a new status field.  This can be used in the same way the
        client requests other status information from core."""
        self.status_fields[field] = function
    
    def get_status(self, torrent_id, fields):
        """Return the value of status fields for the selected torrent_id."""
        status = {}
        for field in fields:
            try:
                status[field] = self.status_fields[field](torrent_id)
            except KeyError:
                log.warning("Status field %s is not registered with the\
                                                                PluginManager.")
        return status
        
    def register_hook(self, hook, function):
        """Register a hook function with the plugin manager"""
        try:
            self.hooks[hook].append(function)
        except KeyError:
            log.warning("Plugin attempting to register invalid hook.")
          
    def run_post_torrent_add(self, torrent_id):
        """This hook is run after a torrent has been added to the session."""
        log.debug("run_post_torrent_add")
        for function in self.hooks["post_torrent_add"]:
            function(torrent_id)
            
    def run_post_torrent_remove(self, torrent_id):
        """This hook is run after a torrent has been removed from the session.
        """
        log.debug("run_post_torrent_remove")
        for function in self.hooks["post_torrent_remove"]:
            function(torrent_id)
   
