# -*- coding: utf-8 -*-
#
# delugeplugins.py
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

import os
import sys
import imp

class PluginManager:
    def __init__(self, deluge_core, deluge_interface):
        self.plugin_dirs = []
        self.available_plugins = {}
        self.enabled_plugins = {}
        self.core = deluge_core
        self.interface = deluge_interface
    
    def add_plugin_dir(self, directory):
        self.plugin_dirs.append(directory)
        sys.path.append(directory)
        
    # Scans all defined plugin dirs for Deluge plugins.  The resulting
    # module object is store with the defined name.
    def scan_for_plugins(self):
        for folder in self.plugin_dirs:
            print "Scanning plugin dir",folder
            for modname in os.listdir(folder):
                path = folder+'/'+modname
                if '__init__.py' in os.listdir(path):
                    # Import the found module. Note that the last
                    # parameter is important otherwise only the base
                    # modules (ie. 'plugins') is imported.  This appears
                    # to be by design.
                    mod = __import__(modname, globals(), locals(), [''])
                    if 'deluge_init' in dir(mod):
                        if modname != "TorrentPieces":
                            print "Initialising plugin",modname
                            mod.deluge_init(path)
                            self.available_plugins[mod.plugin_name] = mod
    
    def get_available_plugins(self):
        return self.available_plugins.keys()
    
    def get_plugin(self, name):
        return self.available_plugins[name]
    
    def enable_plugin(self, name):
        plugin = self.available_plugins[name]
        self.enabled_plugins[name] = plugin.enable(self.core, self.interface)

    def get_enabled_plugins(self):
        return self.enabled_plugins.keys()

    def disable_plugin(self, name):
        plugin = self.enabled_plugins[name]
        if 'unload' in dir(plugin):
            plugin.unload()
        del self.enabled_plugins[name]
        
    def configurable_plugin(self, name):
        if name in self.enabled_plugins:
            return 'configure' in dir(self.enabled_plugins[name])
        else:
            return False

    def configure_plugin(self, name, window):
        self.enabled_plugins[name].configure(window)

    def get_plugin_tray_messages(self):
        tray_message = ""
        for name in self.enabled_plugins.keys():
            plugin = self.enabled_plugins[name]
            if hasattr(plugin, 'get_tray_message'):
                plugin_tray_message = plugin.get_tray_message()
                if plugin_tray_message:
                    tray_message += '\n' + plugin_tray_message
                
        return tray_message

    def update_active_plugins(self):
        for name in self.enabled_plugins.keys():
            plugin = self.enabled_plugins[name]
            if 'update' in dir(plugin):
                plugin.update()
                
        # We have to return False here to stop calling this function by timer
        # over and over again, from interface.torrent_clicked() for example.
        return False

    def shutdown_all_plugins(self):
        for name in self.enabled_plugins.keys():
            self.disable_plugin(name)
        self.enabled_plugins.clear()
    

## Few lines of code to test functionality
if __name__ == "__main__":
    p = PluginManager()
    p.add_plugin_dir("plugins/")
    p.scan_for_plugins()
    for x in p.plugins:
        print x
        for y in p.plugins[x]:
            print "\t", y
