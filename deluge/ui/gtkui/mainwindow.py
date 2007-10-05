#
# mainwindow.py
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

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gobject
import pkg_resources

from deluge.configmanager import ConfigManager
from menubar import MenuBar
from toolbar import ToolBar
from torrentview import TorrentView
from torrentdetails import TorrentDetails
from preferences import Preferences
from systemtray import SystemTray
from statusbar import StatusBar
import deluge.common

from deluge.log import LOG as log

class MainWindow:
    def __init__(self):
        self.config = ConfigManager("gtkui.conf")
        # Get the glade file for the main window
        self.main_glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui", 
                                                    "glade/main_window.glade"))

        self.window = self.main_glade.get_widget("main_window")
        self.window.set_icon(deluge.common.get_logo(32))
        self.vpaned = self.main_glade.get_widget("vpaned")
        # Load the window state
        self.load_window_state()
        
        # Keep track of window's minimization state so that we don't update the
        # UI when it is minimized.
        self.is_minimized = False

        # Connect events
        self.window.connect("window-state-event", self.on_window_state_event)
        self.window.connect("configure-event", self.on_window_configure_event)
        self.window.connect("delete-event", self.on_window_delete_event)
        self.vpaned.connect("notify::position", self.on_vpaned_position_event)
        
        # Initialize various components of the gtkui
        self.menubar = MenuBar(self)
        self.toolbar = ToolBar(self)
        self.torrentview = TorrentView(self)
        self.torrentdetails = TorrentDetails(self)
        self.preferences = Preferences(self)
        self.systemtray = SystemTray(self)
        self.statusbar = StatusBar(self)
        
    def start(self):
        """Start the update thread and show the window"""
        self.update_timer = gobject.timeout_add(1000, self.update)
        if not(self.config["start_in_tray"] and \
               self.config["enable_system_tray"]) and not \
                self.window.get_property("visible"):
            log.debug("Showing window")
            self.show()
        
    def update(self):
        # Don't update the UI if the the window is minimized.
        if self.is_minimized == True:
            return True
        self.torrentview.update()
        self.torrentdetails.update()
        self.statusbar.update()
        return True
        
    def show(self):
        # Load the state prior to showing
        self.load_window_state()
        self.window.show()
    
    def hide(self):
        self.window.hide()
    
    def present(self):
        self.window.present()
    
    def active(self):
        """Returns True if the window is active, False if not."""
        return self.window.is_active()
        
    def visible(self):
        """Returns True if window is visible, False if not."""
        return self.window.get_property("visible")
               
    def quit(self):
        # Stop the update timer from running
        gobject.source_remove(self.update_timer)
        del self.systemtray
        del self.menubar
        del self.toolbar
        del self.torrentview
        del self.torrentdetails
        del self.preferences
        del self.config
        self.hide()
        gtk.main_quit()
    
    def load_window_state(self):
        x = self.config["window_x_pos"]
        y = self.config["window_y_pos"]
        w = self.config["window_width"]
        h = self.config["window_height"]
        self.window.move(x, y)
        self.window.resize(w, h)
        if self.config["window_maximized"] == True:
            self.window.maximize()
        self.vpaned.set_position(
            self.config["window_height"] - self.config["window_pane_position"])
            
    def on_window_configure_event(self, widget, event):
        if self.config["window_maximized"] == False:
            self.config.set("window_x_pos", self.window.get_position()[0])
            self.config.set("window_y_pos", self.window.get_position()[1])
            self.config.set("window_width", event.width)
            self.config.set("window_height", event.height)

    def on_window_state_event(self, widget, event):
        if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
                self.config.set("window_maximized", True)
            else:
                self.config.set("window_maximized", False)
        if event.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
            if event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED:
                log.debug("MainWindow is minimized..")
                self.is_minimized = True
            else:
                log.debug("MainWindow is not minimized..")
                self.is_minimized = False
                # Force UI update as we don't update it while minimized
                self.update()
        return False

    def on_window_delete_event(self, widget, event):
        if self.config["close_to_tray"] and self.config["enable_system_tray"]:
            self.hide()
        else:
            self.quit()
            
        return True
        
    def on_vpaned_position_event(self, obj, param):
        self.config.set("window_pane_position", 
            self.config["window_height"] - self.vpaned.get_position())

