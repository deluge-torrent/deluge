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

import os.path

import pkg_resources

from deluge.log import LOG as log

class PluginManager:
    def __init__(self, gtkui):
        
        self._gtkui = gtkui
        
        # This will load any .eggs in the plugins folder inside the main
        # deluge egg.. Need to scan the local plugin folder too.
        
        plugin_dir = os.path.join(os.path.dirname(__file__), "../..", "plugins")
        
        pkg_resources.working_set.add_entry(plugin_dir)
        pkg_env = pkg_resources.Environment([plugin_dir])
        
        self.plugins = {}
        for name in pkg_env:
           egg = pkg_env[name][0]
           egg.activate()
           modules = []
           for name in egg.get_entry_map("deluge.plugin.ui.gtk"):
              entry_point = egg.get_entry_info("deluge.plugin.ui.gtk", name)
              cls = entry_point.load()
              instance = cls(self)
              self.plugins[name] = instance
              log.info("Loaded plugin %s", name)
           
    def __getitem__(self, key):
        return self.plugins[key]
        
    def get_torrentview(self):
        """Returns a reference to the torrentview component"""
        return self._gtkui.mainwindow.torrentview

    def get_toolbar(self):
        """Returns a reference to the toolbar component"""
        return self._gtkui.mainwindow.toolbar
     
    def get_menubar(self):
        """Returns a reference to the menubar component"""
        return self._gtkui.mainwindow.menubar
    
    def get_torrentmenu(self):
        """Returns a reference to the torrentmenu component"""
        return self._gtkui.mainwindow.menubar.torrentmenu
        
    def get_selected_torrents(self):
        """Returns a list of the selected torrent_ids"""
        return self._gtkui.mainwindow.torrentview.get_selected_torrents()
