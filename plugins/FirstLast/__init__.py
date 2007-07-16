# Copyright (C) 2007 - Marcos Pinto <markybob@gmail.com>
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

### Initialization ###

plugin_name = _("First/Last Priority")
plugin_author = "Marcos Pinto"
plugin_version = "0.1"
plugin_description = _("Set the highest priority to the first and last pieces.")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return FirstLast(path, core, interface)

### The Plugin ###

DEFAULT_PREFS = {
    "flpriorities": [7]
}

import deluge
import gtk, gtk.glade

class FirstLast:
    
    def __init__(self, path, core, interface):
        self.path = path
        self.core = core
        self.interface = interface
        self.set_flpriorities = {}
        self.callback_ids = []
     
        # Setup preferences
	self.config_file = deluge.common.CONFIG_DIR + "/firstlast_priorty.conf"
        self.config = deluge.pref.Preferences(filename=deluge.common.CONFIG_DIR + "/firstlast_priority.conf", global_defaults=False, defaults=DEFAULT_PREFS)
        try:
            self.config.load(self.config_file)
        except IOError:
            # File does not exist
            pass
        print self.config.get
    # Connect to events for the torrent menu so we know when to build and remove our sub-menu
        self.callback_ids.append(self.interface.torrent_menu.connect_after("realize", self.torrent_menu_show))
        self.callback_ids.append(self.interface.torrent_menu.connect("show", self.torrent_menu_show))
        self.callback_ids.append(self.interface.torrent_menu.connect("hide", self.torrent_menu_hide))
    
    def torrent_menu_show(self, widget, data=None):
        # Get the selected torrent
        self.unique_ID = self.interface.get_selected_torrent()

        # Make the sub-menu for the torrent menu
        self.flp_menuitem = gtk.MenuItem(_("_First/Last Priority"))
     
        self.flp_menu = self.interface.build_menu_radio_list(self.config.get("flpriorities"), self.flp_clicked, self.get_torrent_flp(), None, True, _("_Not Set"), 1, None, True)

        self.flp_menuitem.set_submenu(self.flp_menu)
        self.interface.torrent_menu.append(self.flp_menuitem)
  
        self.flp_menuitem.show_all()

    def torrent_menu_hide(self, widget):
        try:
            self.interface.torrent_menu.remove(self.flp_menuitem)
        except AttributeError:
            pass
        
    def update(self):
        pass
      
    def unload(self):
        self.config.save(self.config_file)
        # Disconnect all callbacks
        for callback_id in self.callback_ids:
            self.interface.torrent_menu.disconnect(callback_id)
            
        self.callback_ids = []

        # Reset all desired flpriorities in the core        
        for unique_ID, flp in self.set_flpriorities.items():
            if flp > 1:
                self.core.set_flp(unique_ID, flp)
        
        self.set_flpriorities = {}
      
    def flp_clicked(self, widget):
        value = widget.get_children()[0].get_text()
        if value == _("Not Set"):
            value = 1

        if value == _("Activated"):
            value = 7
        
        value = int(value) # Make sure the value is an int
        
        # Set the flp in the core and remember the setting
        self.core.set_flp(self.unique_ID, value)
        self.set_flpriorities[self.unique_ID] = value
        
    def get_torrent_flp(self):
        if self.set_flpriorities.has_key(self.unique_ID):
            return self.set_flpriorities[self.unique_ID]
        else:
            return 1
