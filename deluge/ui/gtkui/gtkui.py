#
# gtkui.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
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
# 	Boston, MA  02110-1301, USA.
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
#

#


from deluge.log import LOG as log
import pygtk
try:
    pygtk.require('2.0')
except:
    log.warning("It is suggested that you upgrade your PyGTK to 2.10 or greater.")
import gtk, gtk.glade
import gobject
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
from filtertreeview import FilterTreeView
from preferences import Preferences
from systemtray import SystemTray
from statusbar import StatusBar
from connectionmanager import ConnectionManager
from signals import Signals
from pluginmanager import PluginManager
from ipcinterface import IPCInterface

from queuedtorrents import QueuedTorrents
from addtorrentdialog import AddTorrentDialog
from coreconfig import CoreConfig
import deluge.configmanager
import deluge.common

DEFAULT_PREFS = {
    "config_location": deluge.configmanager.get_config_dir(),
    "classic_mode": True,
    "interactive_add": True,
    "focus_add_dialog": True,
    "enable_system_tray": True,
    "close_to_tray": True,
    "start_in_tray": False,
    "lock_tray": False,
    "tray_password": "",
    "check_new_releases": True,
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
    "show_new_releases": True,
    "signal_port": 40000,
    "ntf_tray_blink": True,
    "ntf_sound": False,
    "ntf_sound_path": deluge.common.get_default_download_dir(),
    "ntf_popup": False,
    "ntf_email": False,
    "ntf_email_add": "",
    "ntf_username": "",
    "ntf_pass": "",
    "ntf_server": "",
    "ntf_security": None,
    "signal_port": 40000,
    "show_sidebar": True,
    "show_toolbar": True,
    "show_statusbar": True,
    "sidebar_show_zero": False,
    "sidebar_show_trackers": True,
    "sidebar_position": 170,
    "show_rate_in_title": False
}

class GtkUI:
    def __init__(self, args):
        # Initialize gdk threading
        gtk.gdk.threads_init()
        gobject.threads_init()

        # Initialize gettext
        try:
            if hasattr(locale, "bindtextdomain"):
                locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            if hasattr(locale, "textdomain"):
                locale.textdomain("deluge")
            gettext.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            gettext.textdomain("deluge")
            gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            gtk.glade.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
            gtk.glade.textdomain("deluge")
        except Exception, e:
            log.error("Unable to initialize gettext/locale!")
            log.exception(e)

        # Setup signals
        try:
            import gnome.ui
            self.gnome_client = gnome.ui.Client()
            self.gnome_client.connect("die", self.shutdown)
        except:
            pass
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        if deluge.common.windows_check():
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT
            from win32con import CTRL_SHUTDOWN_EVENT
            result = 0
            def win_handler(ctrl_type):
                log.debug("ctrl_type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self.shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)

        # Make sure gtkui.conf has at least the defaults set
        self.config = deluge.configmanager.ConfigManager("gtkui.conf", DEFAULT_PREFS)

        # We need to check for the existence of 'deluged' in the system path
        # before allowing to continue in classic mode.
        if self.config["classic_mode"]:
            try:
                if deluge.common.windows_check():
                    import win32api
                    win32api.WinExec("deluged --version")
                else:
                    import subprocess
                    retcode = subprocess.call("deluged" + " --version", shell=True)
                    log.debug("retcode: %s", retcode)
                    if retcode == 127:
                        log.error("Unable to find deluged!")
                        self.config["classic_mode"] = False
            except Exception, e:
                log.error("Unable to find deluged: %s", e)
                self.config["classic_mode"] = False

        # We need to check on exit if it was started in classic mode to ensure we
        # shutdown the daemon.
        self.started_in_classic = self.config["classic_mode"]

        # Start the Dbus Interface before anything else.. Just in case we are
        # already running.
        self.queuedtorrents = QueuedTorrents()

        self.ipcinterface = IPCInterface(args)

        # We make sure that the UI components start once we get a core URI
        client.connect_on_new_core(self._on_new_core)
        client.connect_on_no_core(self._on_no_core)

        # Start the signal receiver
        self.signal_receiver = Signals()

        # Initialize various components of the gtkui
        self.mainwindow = MainWindow()
        self.menubar = MenuBar()
        self.toolbar = ToolBar()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.sidebar = SideBar()
        self.filtertreeview = FilterTreeView()
        self.preferences = Preferences()
        self.systemtray = SystemTray()
        self.statusbar = StatusBar()
        self.addtorrentdialog = AddTorrentDialog()

        self.coreconfig = CoreConfig()

        # Initalize the plugins
        self.plugins = PluginManager()

        # Show the connection manager
        self.connectionmanager = ConnectionManager()
        if self.config["show_connection_manager_on_start"] and not self.config["classic_mode"]:
            self.connectionmanager.show()

        # Start the gtk main loop
        try:
            gtk.gdk.threads_enter()
            gtk.main()
            gtk.gdk.threads_leave()
        except KeyboardInterrupt:
            self.shutdown()
        else:
            self.shutdown()

    def shutdown(self, *args, **kwargs):
        log.debug("gtkui shutting down..")

        # Shutdown all components
        component.shutdown()
        if self.started_in_classic:
            try:
                client.shutdown()
            except:
                pass

        # Make sure the config is saved.
        self.config.save()

        try:
            gtk.main_quit()
        except RuntimeError:
            pass

    def _on_new_core(self, data):
        component.start()

    def _on_no_core(self, data):
        component.stop()
