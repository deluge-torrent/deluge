#
# gtkui.py
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
import gettext
import locale
import pkg_resources

import deluge.ui.component as component
import deluge.ui.client as client
from mainwindow import MainWindow
from menubar import MenuBar
from toolbar import ToolBar
from torrentview import TorrentView
from torrentdetails import TorrentDetails
from preferences import Preferences
from systemtray import SystemTray
from statusbar import StatusBar
from connectionmanager import ConnectionManager
from signals import Signals
from pluginmanager import PluginManager
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log
import deluge.configmanager

DEFAULT_PREFS = {
    "interactive_add": False,
    "enable_files_dialog": False,
    "enable_system_tray": True,
    "close_to_tray": True,
    "start_in_tray": False,
    "lock_tray": False,
    "tray_password": "",
    "open_folder_stock": True,
    "stock_file_manager": 0,
    "open_folder_location": "",
    "check_new_releases": False,
    "send_info": False,
    "default_load_path": None,
    "window_maximized": False,
    "window_x_pos": 0,
    "window_y_pos": 0,
    "window_width": 640,
    "window_height": 480,
    "window_pane_position": -1,
    "tray_download_speed_list" : [5.0, 10.0, 30.0, 80.0, 300.0],
    "tray_upload_speed_list" : [5.0, 10.0, 30.0, 80.0, 300.0],
    "enabled_plugins": [],
    "show_connection_manager_on_start": True,
    "autoconnect": False,
    "autoconnect_host_uri": None,
    "autostart_localhost": False
}

class GtkUI:
    def __init__(self, args):
        # Initialize gettext
        locale.setlocale(locale.LC_MESSAGES, '')
        locale.bindtextdomain("deluge", 
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        locale.textdomain("deluge")
        gettext.bindtextdomain("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        gettext.textdomain("deluge")
        gettext.install("deluge",
                    pkg_resources.resource_filename(
                                            "deluge", "i18n"))
        
        # Make sure gtkui.conf has at least the defaults set
        config = ConfigManager("gtkui.conf", DEFAULT_PREFS)
        
        # We make sure that the UI components start once we get a core URI
        client.connect_on_new_core(component.start)
        client.connect_on_no_core(component.stop)
        
        # Initialize various components of the gtkui
        self.mainwindow = MainWindow()
        self.menubar = MenuBar()
        self.toolbar = ToolBar()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.preferences = Preferences()
        self.systemtray = SystemTray()
        self.statusbar = StatusBar()

        # Start the signal receiver
        self.signal_receiver = Signals()

        # Initalize the plugins
        self.plugins = PluginManager()
        
        # Show the connection manager
        self.connectionmanager = ConnectionManager()
        if config["show_connection_manager_on_start"]:
            self.connectionmanager.show()
                
        # Start the gtk main loop
        gtk.gdk.threads_init()
        gtk.main()
        
        log.debug("gtkui shutting down..")

        # Make sure the config is saved.
        config.save()
        del config
        
        # Clean-up
        del self.mainwindow
        del self.systemtray
        del self.menubar
        del self.toolbar
        del self.torrentview
        del self.torrentdetails
        del self.preferences
        del self.signal_receiver
        del self.plugins
        del deluge.configmanager
