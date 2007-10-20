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

import deluge.pluginmanagerbase
import deluge.ui.client as client
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class PluginManager(deluge.pluginmanagerbase.PluginManagerBase):
    def __init__(self, gtkui):
        
        self.config = ConfigManager("gtkui.conf")
        self._gtkui = gtkui

        # Register a callback with the client        
        client.connect_on_new_core(self.start)
    
    def start(self):
        """Start the plugin manager"""
        # Update the enabled_plugins from the core
        enabled_plugins = client.get_enabled_plugins()
        enabled_plugins += self.config["enabled_plugins"]
        enabled_plugins = list(set(enabled_plugins))
        self.config["enabled_plugins"] = enabled_plugins
        
        deluge.pluginmanagerbase.PluginManagerBase.__init__(
            self, "gtkui.conf", "deluge.plugin.ui.gtk")
    
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
