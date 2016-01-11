# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
# We skip isorting this file as it want to move the gtk2reactor.install() below the imports
# isort:skip_file

from __future__ import division

import logging
import os
import sys
import time

import gobject
import gtk
from twisted.internet import gtk2reactor
from twisted.internet.error import ReactorAlreadyInstalledError
from twisted.internet.task import LoopingCall

try:
    # Install twisted reactor, before any other modules import reactor.
    reactor = gtk2reactor.install()
except ReactorAlreadyInstalledError as ex:
    # Running unit tests so trial already installed a rector
    pass

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import AuthenticationRequired, BadLoginError, DaemonRunningError
from deluge.ui.client import client
from deluge.ui.gtkui.addtorrentdialog import AddTorrentDialog
from deluge.ui.gtkui.common import associate_magnet_links
from deluge.ui.gtkui.connectionmanager import ConnectionManager
from deluge.ui.gtkui.dialogs import AuthenticationDialog, ErrorDialog, YesNoDialog
from deluge.ui.gtkui.filtertreeview import FilterTreeView
from deluge.ui.gtkui.ipcinterface import IPCInterface, process_args
from deluge.ui.gtkui.mainwindow import MainWindow
from deluge.ui.gtkui.menubar import MenuBar
from deluge.ui.gtkui.pluginmanager import PluginManager
from deluge.ui.gtkui.preferences import Preferences
from deluge.ui.gtkui.queuedtorrents import QueuedTorrents
from deluge.ui.gtkui.sidebar import SideBar
from deluge.ui.gtkui.statusbar import StatusBar
from deluge.ui.gtkui.systemtray import SystemTray
from deluge.ui.gtkui.toolbar import ToolBar
from deluge.ui.gtkui.torrentdetails import TorrentDetails
from deluge.ui.gtkui.torrentview import TorrentView
from deluge.ui.sessionproxy import SessionProxy
from deluge.ui.tracker_icons import TrackerIcons
from deluge.ui.ui import UI


gobject.set_prgname("deluge")

log = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle, getproctitle
except ImportError:
    def setproctitle(title):
        return

    def getproctitle():
        return


DEFAULT_PREFS = {
    "classic_mode": True,
    "interactive_add": True,
    "focus_add_dialog": True,
    "enable_system_tray": True,
    "close_to_tray": False,
    "start_in_tray": False,
    "enable_appindicator": False,
    "lock_tray": False,
    "tray_password": "",
    "check_new_releases": True,
    "default_load_path": None,
    "window_maximized": False,
    "window_x_pos": 0,
    "window_y_pos": 0,
    "window_width": 640,
    "window_height": 480,
    "pref_dialog_width": None,
    "pref_dialog_height": None,
    "edit_trackers_dialog_width": None,
    "edit_trackers_dialog_height": None,
    "window_pane_position": 235,
    "tray_download_speed_list": [5.0, 10.0, 30.0, 80.0, 300.0],
    "tray_upload_speed_list": [5.0, 10.0, 30.0, 80.0, 300.0],
    "connection_limit_list": [50, 100, 200, 300, 500],
    "enabled_plugins": [],
    "show_connection_manager_on_start": True,
    "autoconnect": False,
    "autoconnect_host_id": None,
    "autostart_localhost": False,
    "autoadd_queued": False,
    "choose_directory_dialog_path": deluge.common.get_default_download_dir(),
    "show_new_releases": True,
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
    "show_sidebar": True,
    "show_toolbar": True,
    "show_statusbar": True,
    "sidebar_show_zero": False,
    "sidebar_show_trackers": True,
    "sidebar_show_owners": True,
    "sidebar_position": 170,
    "show_rate_in_title": False,
    "createtorrent.trackers": [],
    "show_piecesbar": False,
    "pieces_color_missing": [65535, 0, 0],
    "pieces_color_waiting": [4874, 56494, 0],
    "pieces_color_downloading": [65535, 55255, 0],
    "pieces_color_completed": [4883, 26985, 56540],
    "focus_main_window_on_add": True,
    "language": None,
}


class Gtk(UI):

    help = """Starts the Deluge GTK+ interface"""
    cmdline = """A GTK-based graphical user interface"""

    def __init__(self, *args, **kwargs):
        super(Gtk, self).__init__("gtk", *args, **kwargs)

        group = self.parser.add_argument_group(_('GTK Options'))
        group.add_argument("torrents", metavar="<torrent>", nargs="*", default=None,
                           help="Add one or more torrent files, torrent URLs or magnet URIs"
                           " to a currently running Deluge GTK instance")

    def start(self, args=None):
        from gtkui import GtkUI
        super(Gtk, self).start(args)
        GtkUI(self.options)


class GtkUI(object):
    def __init__(self, args):
        # Setup gtkbuilder/glade translation
        deluge.common.setup_translations(setup_gettext=False, setup_pygtk=True)

        # Setup signals
        def on_die(*args):
            log.debug("OS signal 'die' caught with args: %s", args)
            reactor.stop()

        if deluge.common.windows_check():
            from win32api import SetConsoleCtrlHandler
            SetConsoleCtrlHandler(on_die, True)
            log.debug("Win32 'die' handler registered")
        elif deluge.common.osx_check():
            if gtk.gdk.WINDOWING == "quartz":
                import gtkosx_application
                self.osxapp = gtkosx_application.gtkosx_application_get()
                self.osxapp.connect("NSApplicationWillTerminate", on_die)
                log.debug("OSX quartz 'die' handler registered")

        # Set process name again to fix gtk issue
        setproctitle(getproctitle())

        # Attempt to register a magnet URI handler with gconf, but do not overwrite
        # if already set by another program.
        associate_magnet_links(False)

        # Make sure gtkui.conf has at least the defaults set
        self.config = ConfigManager("gtkui.conf", DEFAULT_PREFS)

        # Make sure the gtkui state folder has been created
        if not os.path.exists(os.path.join(get_config_dir(), "gtkui_state")):
            os.makedirs(os.path.join(get_config_dir(), "gtkui_state"))

        # We need to check on exit if it was started in classic mode to ensure we
        # shutdown the daemon.
        self.started_in_classic = self.config["classic_mode"]

        # Set language
        if self.config["language"] is not None:
            deluge.common.set_language(self.config["language"])

        # Start the IPC Interface before anything else.. Just in case we are
        # already running.
        self.queuedtorrents = QueuedTorrents()
        self.ipcinterface = IPCInterface(args.torrents)

        # Initialize gdk threading
        gtk.gdk.threads_init()

        # We make sure that the UI components start once we get a core URI
        client.set_disconnect_callback(self.__on_disconnect)

        self.trackericons = TrackerIcons()
        self.sessionproxy = SessionProxy()
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

        if deluge.common.osx_check() and gtk.gdk.WINDOWING == "quartz":
            def nsapp_open_file(osxapp, filename):
                # Will be raised at app launch (python opening main script)
                if filename.endswith('Deluge-bin'):
                    return True
                process_args([filename])
            self.osxapp.connect("NSApplicationOpenFile", nsapp_open_file)
            from deluge.ui.gtkui.menubar_osx import menubar_osx
            menubar_osx(self, self.osxapp)
            self.osxapp.ready()

        # Initalize the plugins
        self.plugins = PluginManager()

        # Show the connection manager
        self.connectionmanager = ConnectionManager()

        # Setup RPC stats logging
        # daemon_bps: time, bytes_sent, bytes_recv
        self.daemon_bps = (0, 0, 0)
        self.rpc_stats = LoopingCall(self.print_rpc_stats)

        # Twisted catches signals to terminate, so have it call a pre_shutdown method.
        reactor.addSystemEventTrigger("before", "shutdown", self.pre_shutdown)
        reactor.callWhenRunning(self._on_reactor_start)

        # Initialize gdk threading
        gtk.gdk.threads_enter()
        reactor.run()
        self.shutdown()
        gtk.gdk.threads_leave()

    def shutdown(self, *args, **kwargs):
        log.debug("gtkui shutting down..")

        component.stop()

        # Process any pending gtk events since the mainloop has been quit
        while gtk.events_pending():
            gtk.main_iteration(0)

        # Shutdown all components
        component.shutdown()

        # Make sure the config is saved.
        self.config.save()

    def pre_shutdown(self, *args, **kwargs):
        """Modal dialogs can prevent the application exiting so destroy mainwindow"""
        # Ensure columns state is saved
        self.torrentview.save_state()
        self.mainwindow.window.destroy()

    def print_rpc_stats(self):
        if not client.connected():
            return

        t = time.time()
        recv = client.get_bytes_recv()
        sent = client.get_bytes_sent()
        delta_time = t - self.daemon_bps[0]
        delta_sent = sent - self.daemon_bps[1]
        delta_recv = recv - self.daemon_bps[2]
        self.daemon_bps = (t, sent, recv)
        sent_rate = deluge.common.fspeed(delta_sent / delta_time)
        recv_rate = deluge.common.fspeed(delta_recv / delta_time)
        log.debug("RPC: Sent %s (%s) Recv %s (%s)",
                  deluge.common.fsize(sent), sent_rate, deluge.common.fsize(recv), recv_rate)

    def _on_reactor_start(self):
        log.debug("_on_reactor_start")
        self.mainwindow.first_show()

        if self.config["classic_mode"]:
            def on_dialog_response(response):
                if response != gtk.RESPONSE_YES:
                    # The user does not want to turn Standalone Mode off, so just quit
                    self.mainwindow.quit()
                    return
                # Turning off classic_mode
                self.config["classic_mode"] = False
                self.__start_non_classic()

            try:
                try:
                    client.start_classic_mode()
                except DaemonRunningError:
                    d = YesNoDialog(
                        _("Switch to Thin Client Mode?"),
                        _("A Deluge daemon process (deluged) is already running. "
                          "To use Standalone mode, stop this daemon and restart Deluge."
                          "\n\n"
                          "Continue in Thin Client mode?")).run()
                    self.started_in_classic = False
                    d.addCallback(on_dialog_response)
                except ImportError as ex:
                    if "No module named libtorrent" in ex.message:
                        d = YesNoDialog(
                            _("Switch to Thin Client Mode?"),
                            _("Only Thin Client mode is available because libtorrent is not installed."
                              "\n\n"
                              "To use Deluge Standalone mode, please install libtorrent.")).run()
                        self.started_in_classic = False
                        d.addCallback(on_dialog_response)
                    else:
                        raise ex
                else:
                    component.start()
                    return
            except Exception:
                import traceback
                tb = sys.exc_info()
                ed = ErrorDialog(
                    _("Error Starting Core"),
                    _("An error occurred starting the core component required to run Deluge in Standalone mode."
                      "\n\n"
                      "Please see the details below for more information."), details=traceback.format_exc(tb[2])).run()

                def on_ed_response(response):
                    d = YesNoDialog(
                        _("Switch to Thin Client Mode?"),
                        _("Unable to start Standalone mode would you like to continue in Thin Client mode?")
                    ).run()
                    self.started_in_classic = False
                    d.addCallback(on_dialog_response)
                ed.addCallback(on_ed_response)
        else:
            self.rpc_stats.start(10)
            self.__start_non_classic()

    def __start_non_classic(self):
        # Autoconnect to a host
        if self.config["autoconnect"]:

            def update_connection_manager():
                if not self.connectionmanager.running:
                    return
                self.connectionmanager.builder.get_object("button_refresh").emit("clicked")

            def close_connection_manager():
                if not self.connectionmanager.running:
                    return
                self.connectionmanager.builder.get_object("button_close").emit("clicked")

            for host_config in self.connectionmanager.config["hosts"]:
                hostid, host, port, user, passwd = host_config
                if hostid == self.config["autoconnect_host_id"]:
                    try_connect = True
                    # Check to see if we need to start the localhost daemon
                    if self.config["autostart_localhost"] and host in ("localhost", "127.0.0.1"):
                        log.debug("Autostarting localhost:%s", host)
                        try_connect = client.start_daemon(
                            port, get_config_dir()
                        )
                        log.debug("Localhost started: %s", try_connect)
                        if not try_connect:
                            ErrorDialog(
                                _("Error Starting Daemon"),
                                _("There was an error starting the daemon "
                                  "process.  Try running it from a console "
                                  "to see if there is an error.")
                            ).run()

                        # Daemon Started, let's update it's info
                        reactor.callLater(0.5, update_connection_manager)

                    def on_connect(connector):
                        component.start()
                        reactor.callLater(0.2, update_connection_manager)
                        reactor.callLater(0.5, close_connection_manager)

                    def on_connect_fail(reason, try_counter,
                                        host, port, user, passwd):
                        if not try_counter:
                            return

                        if reason.check(AuthenticationRequired, BadLoginError):
                            log.debug("PasswordRequired exception")
                            dialog = AuthenticationDialog(reason.value.message, reason.value.username)

                            def dialog_finished(response_id, host, port):
                                if response_id == gtk.RESPONSE_OK:
                                    reactor.callLater(
                                        0.5, do_connect, try_counter - 1,
                                        host, port, dialog.get_username(),
                                        dialog.get_password())
                            dialog.run().addCallback(dialog_finished, host, port)
                            return

                        log.info("Connection to host failed..")
                        log.info("Retrying connection.. Retries left: "
                                 "%s", try_counter)
                        reactor.callLater(0.5, update_connection_manager)
                        reactor.callLater(0.5, do_connect, try_counter - 1,
                                          host, port, user, passwd)

                    def do_connect(try_counter, host, port, user, passwd):
                        log.debug("Trying to connect to %s@%s:%s",
                                  user, host, port)
                        d = client.connect(host, port, user, passwd)
                        d.addCallback(on_connect)
                        d.addErrback(on_connect_fail, try_counter,
                                     host, port, user, passwd)

                    if try_connect:
                        reactor.callLater(
                            0.5, do_connect, 6, host, port, user, passwd
                        )
                    break

        if self.config["show_connection_manager_on_start"]:
            self.connectionmanager.show()

    def __on_disconnect(self):
        """
        Called when disconnected from the daemon.  We basically just stop all
        the components here.
        """
        self.daemon_bps = (0, 0, 0)
        component.stop()
