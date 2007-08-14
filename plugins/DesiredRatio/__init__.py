# Copyright (C) 2007 - Andrew Resch <andrewresch@gmail.com>
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

plugin_name = _("Desired Ratio")
plugin_author = "Andrew Resch"
plugin_version = "0.1"
plugin_description = _("Set the desired ratio for a torrent.")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return DesiredRatio(path, core, interface)

### The Plugin ###

DEFAULT_PREFS = {
    "ratios": [1.0, 1.5, 2.0, 2.5, 3.0]
}

import deluge
import gtk, gtk.glade

class DesiredRatio:
    
    def __init__(self, path, core, interface):
        self.path = path
        self.core = core
        self.interface = interface
        self.set_ratios = {}
        self.callback_ids = []
     
        # Setup preferences
        self.config = deluge.pref.Preferences(filename=deluge.common.CONFIG_DIR + "/desired_ratio.conf", global_defaults=False, defaults=DEFAULT_PREFS)

    # Connect to events for the torrent menu so we know when to build and remove our sub-menu
        self.callback_ids.append(self.interface.torrent_menu.connect_after("realize", self.torrent_menu_show))
        self.callback_ids.append(self.interface.torrent_menu.connect("show", self.torrent_menu_show))
        self.callback_ids.append(self.interface.torrent_menu.connect("hide", self.torrent_menu_hide))
    
    def torrent_menu_show(self, widget, data=None):
        # Get the selected torrent
        self.unique_ID = self.interface.get_selected_torrent()

        # Make the sub-menu for the torrent menu
        self.ratio_menuitem = gtk.MenuItem(_("_Desired Ratio"))


     
        self.ratio_menu = self.interface.build_menu_radio_list(self.config.get("ratios"), self.ratio_clicked, self.get_torrent_desired_ratio(), None, True, _("_Not Set"), 1, None)

        self.ratio_menuitem.set_submenu(self.ratio_menu)
        self.interface.torrent_menu.append(self.ratio_menuitem)
  
        self.ratio_menuitem.show_all()

    def torrent_menu_hide(self, widget):
        try:
            self.interface.torrent_menu.remove(self.ratio_menuitem)
        except AttributeError:
            pass
        
    def update(self):
        pass
      
    def unload(self):
        # Disconnect all callbacks
        for callback_id in self.callback_ids:
            self.interface.torrent_menu.disconnect(callback_id)
            
        self.callback_ids = []

        # Reset all desired ratios in the core        
        for unique_ID, ratio in self.set_ratios.items():
            if ratio >= 1:
                self.core.set_ratio(unique_ID, ratio)
        
        self.set_ratios = {}
      
    def ratio_clicked(self, widget):
        value = widget.get_children()[0].get_text()
        if value == _("Not Set"):
            value = 0.0
        
        if value == _("Other..."):
            dialog_glade = gtk.glade.XML(deluge.common.get_glade_file("dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_title = dialog_glade.get_widget("spin_title")
            spin_title.set_text(_("Desired Ratio"))
            spin_speed = dialog_glade.get_widget("spin_speed")
            spin_speed.set_value(self.get_torrent_desired_ratio())
            spin_speed.set_increments(0.1, 1.0)
            spin_speed.set_digits(1)
            spin_speed.set_range(1.0, 1000.0)
            spin_speed.select_region(0, -1)
            response = speed_dialog.run()
            if response == 1: # OK Response
                value = spin_speed.get_value()
            else:
                speed_dialog.destroy()
                return
            speed_dialog.destroy()
        
        value = float(value) # Make sure the value is a float
        
        # Set the ratio in the core and remember the setting
        self.core.set_ratio(self.unique_ID, value)
        self.set_ratios[self.unique_ID] = value
        
        # Update the ratios list if necessary
        if value not in self.config.get("ratios") and value >= 1:
            self.config.get("ratios").insert(0, value)
            self.config.get("ratios").pop()
      
    def get_torrent_desired_ratio(self):
        return self.set_ratios.get(self.unique_ID, 1)
