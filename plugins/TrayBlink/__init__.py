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

plugin_name = _("Tray Blink")
plugin_author = "Micah Bucy"
plugin_version = "0.1"
plugin_description = _("Make tray icon blink when torrent finishes downloading")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return TrayBlink(path, core, interface)

### The Plugin ###

import deluge
import gtk

class TrayBlink:

    def __init__(self, path, core, interface):
        print "Loading TrayBlink plugin..."
        self.path = path
        self.core = core
        self.interface = interface
        self.window = self.interface.window
        self.window.connect("focus_in_event", self.set_tray_flashing_off)
        self.core.connect_event(self.core.constants['EVENT_FINISHED'], self)
    
    def handle_event(self, event):
        self.set_tray_flashing_on()
    
    def set_tray_flashing_off(self, focusdata1, focusdata2):
        self.interface.tray_icon.set_blinking(False)
    
    def set_tray_flashing_on(self):
        if self.window.has_toplevel_focus() is not True:
            self.interface.tray_icon.set_blinking(True)
    
