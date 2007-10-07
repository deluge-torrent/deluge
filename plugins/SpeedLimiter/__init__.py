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

plugin_name = _("Speed Limiter")
plugin_author = "Marcos Pinto"
plugin_version = "0.1"
plugin_description = _("Set the desired speed limit per torrent.")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return DesiredSpeed(path, core, interface)

### The Plugin ###

DEFAULT_PREFS = {
    "up_speeds": [5, 10, 30, 80, 300],
    "down_speeds": [5, 10, 30, 80, 300]
}

import deluge
import gtk, gtk.glade

class DesiredSpeed:
    
    def __init__(self, path, core, interface):
        self.path = path
        self.core = core
        self.interface = interface
        self.set_up_speeds = {}
        self.set_down_speeds = {}
        self.callback_ids = []
     
        self.config = deluge.pref.Preferences(filename=deluge.common.CONFIG_DIR + "/desired_speed.conf", global_defaults=False, defaults=DEFAULT_PREFS)

        self.callback_ids.append(self.interface.torrent_menu.connect_after("realize", self.torrent_menu_show))
        self.callback_ids.append(self.interface.torrent_menu.connect("show", self.torrent_menu_show))
        self.callback_ids.append(self.interface.torrent_menu.connect("hide", self.torrent_menu_hide))
        for torrent in self.core.get_queue():
            unique_ID = self.core.get_torrent_unique_id(torrent)
            try:
                if self.core.unique_IDs[unique_ID].upload_rate_limit != -1:
                    value = int(self.core.unique_IDs[unique_ID].upload_rate_limit)
                    self.core.set_per_upload_rate_limit(unique_ID, value)
                    self.set_up_speeds[unique_ID] = value
                    if value not in self.config.get("up_speeds") and value >= 1:
                        self.config.get("up_speeds").insert(0, value)
                        self.config.get("up_speeds").pop()
                if self.core.unique_IDs[unique_ID].download_rate_limit != -1:
                    value = int(self.core.unique_IDs[unique_ID].download_rate_limit)
                    self.core.set_per_download_rate_limit(unique_ID, value)
                    self.set_down_speeds[unique_ID] = value
                    if value not in self.config.get("down_speeds") and value >= 1:
                        self.config.get("down_speeds").insert(0, value)
                        self.config.get("down_speeds").pop()
            except AttributeError:
                pass
    
    def torrent_menu_show(self, widget, data=None):
        self.unique_ID = self.interface.get_selected_torrent()

        self.down_image = gtk.Image()
        self.down_image.set_from_file(deluge.common.get_pixmap('downloading16.png'))
        self.down_speed_menuitem = gtk.ImageMenuItem(_("Torrent _Download Speed"))
        self.down_speed_menuitem.set_image(self.down_image)        
        self.down_speed_menu = self.interface.build_menu_radio_list(self.config.get("down_speeds"), self.down_speed_clicked, self.get_torrent_desired_down_speed(), suffix=_("KiB/s"), show_notset=True, notset_lessthan=0, show_other=True)

        self.down_speed_menuitem.set_submenu(self.down_speed_menu)
        self.interface.torrent_menu.append(self.down_speed_menuitem)
        self.down_speed_menuitem.show_all()
        
        self.up_image = gtk.Image()
        self.up_image.set_from_file(deluge.common.get_pixmap('seeding16.png'))
        self.up_speed_menuitem = gtk.ImageMenuItem(_("Torrent Upload _Speed"))
        self.up_speed_menuitem.set_image(self.up_image)
        self.up_speed_menu = self.interface.build_menu_radio_list(self.config.get("up_speeds"), self.up_speed_clicked, self.get_torrent_desired_up_speed(), suffix=_("KiB/s"), show_notset=True, notset_lessthan=0, show_other=True)

        self.up_speed_menuitem.set_submenu(self.up_speed_menu)
        self.interface.torrent_menu.append(self.up_speed_menuitem)
        self.up_speed_menuitem.show_all()

    def torrent_menu_hide(self, widget):
        try:
            self.interface.torrent_menu.remove(self.up_speed_menuitem)
            self.interface.torrent_menu.remove(self.down_speed_menuitem)
        except AttributeError:
            pass
        
    def update(self):
        pass
      
    def unload(self):
        # Disconnect all callbacks
        for callback_id in self.callback_ids:
            try:
                self.interface.torrent_menu.disconnect(callback_id)
            except:
                pass
            
        self.callback_ids = []

        # Reset all desired speeds in the core
        for unique_ID, speed in self.set_up_speeds.items():
            if speed >= 0:
                try:
                    self.core.set_per_upload_rate_limit(unique_ID, int(-1))
                except:
                    pass
        self.set_up_speeds = {}

        for unique_ID, speed in self.set_down_speeds.items():
            if speed >= 0:
                try:
                    self.core.set_per_download_rate_limit(unique_ID, int(-1))
                except:
                    pass
        self.set_down_speeds = {}

    def up_speed_clicked(self, widget):
        value = widget.get_children()[0].get_text().rstrip(" "+_("KiB/s"))
        if value == _("Unlimited"):
            value = -1
        
        if value == _("Other..."):
            dialog_glade = gtk.glade.XML(deluge.common.get_glade_file("dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_title = dialog_glade.get_widget("spin_title")
            spin_title.set_text(_("Torrent Upload Speed (KiB/s):"))
            spin_speed = dialog_glade.get_widget("spin_speed")
            spin_speed.set_value(self.get_torrent_desired_up_speed())
            spin_speed.select_region(0, -1)
            response = speed_dialog.run()
            if response == 1: # OK Response
                value = spin_speed.get_value()
            else:
                speed_dialog.destroy()
                return
            speed_dialog.destroy()
        
        value = int(value)

        self.core.set_per_upload_rate_limit(self.unique_ID, value)
        self.set_up_speeds[self.unique_ID] = value
        self.core.unique_IDs[self.unique_ID].upload_rate_limit = value

        # Update the speeds list if necessary
        if value not in self.config.get("up_speeds") and value >= 1:
            self.config.get("up_speeds").insert(0, value)
            self.config.get("up_speeds").pop()

    def down_speed_clicked(self, widget):
        value = widget.get_children()[0].get_text().rstrip(" "+_("KiB/s"))
        if value == _("Unlimited"):
            value = -1
        
        if value == _("Other..."):
            dialog_glade = gtk.glade.XML(deluge.common.get_glade_file("dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_title = dialog_glade.get_widget("spin_title")
            spin_title.set_text(_("Torrent Download Speed (KiB/s):"))
            spin_speed = dialog_glade.get_widget("spin_speed")
            spin_speed.set_value(self.get_torrent_desired_down_speed())
            spin_speed.select_region(0, -1)
            response = speed_dialog.run()
            if response == 1: # OK Response
                value = spin_speed.get_value()
            else:
                speed_dialog.destroy()
                return
            speed_dialog.destroy()
        
        value = int(value)
        
        self.core.set_per_download_rate_limit(self.unique_ID, value)
        self.set_down_speeds[self.unique_ID] = value
        self.core.unique_IDs[self.unique_ID].download_rate_limit = value
        
        # update the speeds list if necessary
        if value not in self.config.get("down_speeds") and value >= 0:
            self.config.get("down_speeds").insert(0, value)
            self.config.get("down_speeds").pop()
      
    def get_torrent_desired_up_speed(self):
        if self.set_up_speeds.has_key(self.unique_ID):
            return self.set_up_speeds[self.unique_ID]
        else:
            return -1

    def get_torrent_desired_down_speed(self):
        if self.set_down_speeds.has_key(self.unique_ID):
            return self.set_down_speeds[self.unique_ID]
        else:
            return -1
