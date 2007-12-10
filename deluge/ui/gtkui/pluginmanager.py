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

import deluge.component as component
import deluge.pluginmanagerbase
import deluge.ui.client as client
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class PluginManager(deluge.pluginmanagerbase.PluginManagerBase, 
    component.Component):
    def __init__(self):
        component.Component.__init__(self, "PluginManager")
        self.config = ConfigManager("gtkui.conf")
            
    def start(self):
        """Start the plugin manager"""
        # Update the enabled_plugins from the core
        enabled_plugins = client.get_enabled_plugins()
        enabled_plugins += self.config["enabled_plugins"]
        enabled_plugins = list(set(enabled_plugins))
        self.config["enabled_plugins"] = enabled_plugins
        
        deluge.pluginmanagerbase.PluginManagerBase.__init__(
            self, "gtkui.conf", "deluge.plugin.gtkui")

    ## Plugin functions.. will likely move to own class..
        
    def add_torrentview_text_column(self, *args, **kwargs):
        return component.get("TorrentView").add_text_column(*args, **kwargs)
    
    def remove_torrentview_column(self, *args):
        return component.get("TorrentView").remove_column(*args)
           
    def add_toolbar_separator(self):
        return component.get("ToolBar").add_separator()
    
    def add_toolbar_button(self, *args, **kwargs):
        return component.get("ToolBar").add_toolbutton(*args, **kwargs)
    
    def remove_toolbar_button(self, *args):
        return component.get("ToolBar").remove(*args)
    
    def add_torrentmenu_menu(self, *args):
        return component.get("MenuBar").torrentmenu.append(*args)
    
    def add_torrentmenu_separator(self):
        return component.get("MenuBar").add_torrentmenu_separator()

    def remove_torrentmenu_item(self, *args):
        return component.get("MenuBar").torrentmenu.remove(*args)
    
    def add_preferences_page(self, *args):
        return component.get("Preferences").add_page(*args)
    
    def remove_preferences_page(self, *args):
        return component.get("Preferences").remove_page(*args)
                
    def update_torrent_view(self, *args):
        return component.get("TorrentView").update(*args)

    def get_selected_torrents(self):
        """Returns a list of the selected torrent_ids"""
        return component.get("TorrentView").get_selected_torrents()
