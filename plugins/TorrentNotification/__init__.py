# Copyright (C) 2007 - Micah Bucy <eternalsword@gmail.com>
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

plugin_name = _("Torrent Notification")
plugin_author = "Micah Bucy"
plugin_version = "0.1"
plugin_description = _("Make tray icon blink when torrent finishes downloading and/or popup a notification")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return TorrentNotification(path, core, interface)

### The Plugin ###
import deluge
import gtk

class TorrentNotification:

    def __init__(self, path, core, interface):
        print "Loading TorrentNotification plugin..."
        self.path = path
        self.core = core
        self.interface = interface
        self.window = self.interface.window
        self.window.connect("focus_in_event", self.set_tray_flashing_off)
        self.core.connect_event(self.core.constants['EVENT_FINISHED'], self.handle_event)

        # Create an options file and try to load existing Values
        self.config_file = deluge.common.CONFIG_DIR + "/notification.conf"
        self.config = deluge.pref.Preferences()
        try:
            self.config.load(self.config_file)
        except IOError:
            # File does not exist
            pass
        
        self.glade = gtk.glade.XML(path + "/notification_preferences.glade")
        self.dialog = self.glade.get_widget("dialog")
    
    def handle_event(self, event):
        if self.config.get("enable_tray_blink"):
            self.set_tray_flashing_on()
        if self.config.get("enable_notification"):
            self.show_notification(event)

    def unload(self):
        self.core.disconnect_event(self.core.constants['EVENT_FINISHED'], self.handle_event)
        self.config.save(self.config_file)
    
    def set_tray_flashing_off(self, focusdata1, focusdata2):
        self.interface.tray_icon.set_blinking(False)
    
    def set_tray_flashing_on(self):
        if self.window.has_toplevel_focus() is not True:
            self.interface.tray_icon.set_blinking(True)
    

    def show_notification(self, event):
        import pynotify
        file_info = self.interface.manager.get_torrent_file_info(event['unique_ID'])
        self.filelist = ""
        for file in file_info:
            self.filelist += file['path']+"\n"
        if pynotify.init("My Application Name"):
            n = pynotify.Notification("Torrent complete", "Files:\n"+self.filelist)
            n.show()
        else:
            print "there was a problem initializing the pynotify module"

    def configure(self):
        try:
            self.glade.get_widget("chk_tray_blink").set_active(self.config.get("enable_tray_blink"))
            self.glade.get_widget("chk_notification").set_active(self.config.get("enable_notification"))
        except:
            self.glade.get_widget("chk_tray_blink").set_active(False)
            self.glade.get_widget("chk_notification").set_active(False)
        self.dialog.show()
        response = self.dialog.run()
        self.dialog.hide()
        if response:
            self.config.set("enable_tray_blink", self.glade.get_widget("chk_tray_blink").get_active())
            self.config.set("enable_notification", self.glade.get_widget("chk_notification").get_active())
