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

from deluge.log import LOG as log
import pygtk
try:
    pygtk.require('2.0')
except:
    log.warning("It is suggested that you upgrade your PyGTK to 2.10 or greater.")
import gtk, gtk.glade
import gettext
import locale
import pkg_resources
import signal

import deluge.component as component
from deluge.ui.client import aclient as client
from mainwindow import MainWindow
from menubar import MenuBar
from toolbar import ToolBar
from torrentview import TorrentView
from torrentdetails import TorrentDetails
from sidebar import SideBar
from preferences import Preferences
from systemtray import SystemTray
from statusbar import StatusBar
from connectionmanager import ConnectionManager
from signals import Signals
from pluginmanager import PluginManager
try:
    from dbusinterface import DbusInterface
except Exception, e:
    log.error("Unable to load DBUS component.  This will limit functionality!")
    
from queuedtorrents import QueuedTorrents
from addtorrentdialog import AddTorrentDialog
from coreconfig import CoreConfig
import deluge.configmanager
import deluge.common

DEFAULT_PREFS = {
    "config_location": deluge.configmanager.get_config_dir(),
    "interactive_add": True,
    "focus_add_dialog": True,
    "enable_system_tray": True,
    "close_to_tray": True,
    "start_in_tray": False,
    "lock_tray": False,
    "tray_password": "",
    "check_new_releases": False,
    "default_load_path": None,
    "window_maximized": False,
    "window_x_pos": 0,
    "window_y_pos": 0,
    "window_width": 640,
    "window_height": 480,
    "window_pane_position": -1,
    "tray_download_speed_list" : [5.0, 10.0, 30.0, 80.0, 300.0],
    "tray_upload_speed_list" : [5.0, 10.0, 30.0, 80.0, 300.0],
    "connection_limit_list": [50, 100, 200, 300, 500],
    "enabled_plugins": [],
    "show_connection_manager_on_start": True,
    "autoconnect": False,
    "autoconnect_host_uri": None,
    "autostart_localhost": False,
    "autoadd_queued": False,
    "autoadd_enable": False,
    "autoadd_location": "",
    "choose_directory_dialog_path": deluge.common.get_default_download_dir(),
    "classic_mode": False
}

class GtkUI:
    def __init__(self, args):
        # Initialize gdk threading
        gtk.gdk.threads_init()

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
        
        # Setup signals
        try:
            import gnome.ui
            self.gnome_client = gnome.ui.Client()
            self.gnome_client.connect("die", self.shutdown)
        except:
            pass
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        # Make sure gtkui.conf has at least the defaults set
        self.config = deluge.configmanager.ConfigManager("gtkui.conf", DEFAULT_PREFS)

        # Start the Dbus Interface before anything else.. Just in case we are
        # already running.
        self.queuedtorrents = QueuedTorrents()
        try:
            self.dbusinterface = DbusInterface(args)
        except Exception, e:
            log.warning("Unable to start DBUS component.  This will limit functionality!")
                
        # We make sure that the UI components start once we get a core URI
        client.connect_on_new_core(self._on_new_core)
        client.connect_on_no_core(self._on_no_core)
        
        # Initialize various components of the gtkui
        self.mainwindow = MainWindow()
        self.menubar = MenuBar()
        self.toolbar = ToolBar()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.sidebar = SideBar()
        self.preferences = Preferences()
        self.systemtray = SystemTray()
        self.statusbar = StatusBar()
        self.addtorrentdialog = AddTorrentDialog()

        # Start the signal receiver
        self.signal_receiver = Signals()
        self.coreconfig = CoreConfig()
        
        # Initalize the plugins
        self.plugins = PluginManager()
        
        # Show the connection manager
        self.connectionmanager = ConnectionManager()
        if self.config["show_connection_manager_on_start"] and not self.config["classic_mode"]:
            self.connectionmanager.show()
                
        # Start the gtk main loop
        try:
            gtk.main()
        except KeyboardInterrupt:
            self.shutdown()
        else:           
            self.shutdown()

    def shutdown(self, data=None):
        log.debug("gtkui shutting down..")

        # Make sure the config is saved.
        self.config.save()
        
        # Shutdown all components
        component.shutdown()

    def _on_new_core(self, data):
        component.start()
        
    def _on_no_core(self, data):
        component.stop()
