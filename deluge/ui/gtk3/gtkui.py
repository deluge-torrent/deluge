# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
# pylint: disable=wrong-import-position

from __future__ import division, unicode_literals

import logging
import os
import signal
import sys
import time

import gi  # isort:skip (Required before Gtk import).

gi.require_version('Gtk', '3.0')  # NOQA: E402
gi.require_version('Gdk', '3.0')  # NOQA: E402

# isort:imports-thirdparty
from gi.repository.GLib import set_prgname
from gi.repository.Gtk import Builder, ResponseType
from twisted.internet import defer, gtk3reactor
from twisted.internet.error import ReactorAlreadyInstalledError
from twisted.internet.task import LoopingCall

try:
    # Install twisted reactor, before any other modules import reactor.
    reactor = gtk3reactor.install()
except ReactorAlreadyInstalledError:
    # Running unit tests so trial already installed a rector
    from twisted.internet import reactor

# isort:imports-firstparty
import deluge.component as component
from deluge.common import (
    fsize,
    fspeed,
    get_default_download_dir,
    osx_check,
    windows_check,
)
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import DaemonRunningError, LibtorrentImportError
from deluge.i18n import I18N_DOMAIN, set_language, setup_translation
from deluge.ui.client import client
from deluge.ui.hostlist import LOCALHOST
from deluge.ui.sessionproxy import SessionProxy
from deluge.ui.tracker_icons import TrackerIcons

# isort:imports-localfolder
from .addtorrentdialog import AddTorrentDialog
from .common import associate_magnet_links, windowing
from .connectionmanager import ConnectionManager
from .dialogs import YesNoDialog
from .filtertreeview import FilterTreeView
from .ipcinterface import IPCInterface, process_args
from .mainwindow import MainWindow
from .menubar import MenuBar
from .pluginmanager import PluginManager
from .preferences import Preferences
from .queuedtorrents import QueuedTorrents
from .sidebar import SideBar
from .statusbar import StatusBar
from .systemtray import SystemTray
from .toolbar import ToolBar
from .torrentdetails import TorrentDetails
from .torrentview import TorrentView

set_prgname('deluge')
log = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle, getproctitle
except ImportError:

    def setproctitle(title):
        return

    def getproctitle():
        return


DEFAULT_PREFS = {
    'standalone': True,
    'interactive_add': True,
    'focus_add_dialog': True,
    'enable_system_tray': True,
    'close_to_tray': False,
    'start_in_tray': False,
    'enable_appindicator': False,
    'lock_tray': False,
    'tray_password': '',
    'check_new_releases': True,
    'default_load_path': None,
    'window_maximized': False,
    'window_x_pos': 0,
    'window_y_pos': 0,
    'window_width': 640,
    'window_height': 480,
    'pref_dialog_width': None,
    'pref_dialog_height': None,
    'edit_trackers_dialog_width': None,
    'edit_trackers_dialog_height': None,
    'tray_download_speed_list': [5.0, 10.0, 30.0, 80.0, 300.0],
    'tray_upload_speed_list': [5.0, 10.0, 30.0, 80.0, 300.0],
    'connection_limit_list': [50, 100, 200, 300, 500],
    'enabled_plugins': [],
    'show_connection_manager_on_start': True,
    'autoconnect': False,
    'autoconnect_host_id': None,
    'autostart_localhost': False,
    'autoadd_queued': False,
    'choose_directory_dialog_path': get_default_download_dir(),
    'show_new_releases': True,
    'show_sidebar': True,
    'show_toolbar': True,
    'show_statusbar': True,
    'show_tabsbar': True,
    'tabsbar_position': 235,
    'sidebar_show_zero': False,
    'sidebar_show_trackers': True,
    'sidebar_show_owners': True,
    'sidebar_position': 170,
    'show_rate_in_title': False,
    'createtorrent.trackers': [],
    'show_piecesbar': False,
    'pieces_color_missing': [65535, 0, 0],
    'pieces_color_waiting': [4874, 56494, 0],
    'pieces_color_downloading': [65535, 55255, 0],
    'pieces_color_completed': [4883, 26985, 56540],
    'focus_main_window_on_add': True,
    'language': None,
}


class GtkUI(object):
    def __init__(self, args):
        # Setup gtkbuilder/glade translation
        setup_translation()
        Builder().set_translation_domain(I18N_DOMAIN)

        # Setup signals
        def on_die(*args):
            log.debug('OS signal "die" caught with args: %s', args)
            reactor.stop()

        self.osxapp = None
        if windows_check():
            from win32api import SetConsoleCtrlHandler

            SetConsoleCtrlHandler(on_die, True)
            log.debug('Win32 "die" handler registered')
        elif osx_check() and windowing('quartz'):
            try:
                gi.require_version('GtkosxApplication', '1.0')
                from gi.repository import GtkosxApplication
            except ImportError:
                pass
            else:
                self.osxapp = GtkosxApplication.Application()
                self.osxapp.connect('NSApplicationWillTerminate', on_die)
                log.debug('OSX quartz "die" handler registered')

                if os.getenv('DELUGE_IS_RUNNING_BUNDLE') != "":
                    launcherpath = os.path.join(os.path.dirname(sys.argv[0]), 'Deluge')
                    sys.argv[0] = launcherpath

        # Set process name again to fix gtk issue
        setproctitle(getproctitle())

        # Attempt to register a magnet URI handler with gconf, but do not overwrite
        # if already set by another program.
        associate_magnet_links(False)

        # Make sure gtk3ui.conf has at least the defaults set
        self.config = ConfigManager('gtk3ui.conf', DEFAULT_PREFS)

        # Make sure the gtkui state folder has been created
        if not os.path.exists(os.path.join(get_config_dir(), 'gtk3ui_state')):
            os.makedirs(os.path.join(get_config_dir(), 'gtk3ui_state'))

        # Set language
        if self.config['language'] is not None:
            set_language(self.config['language'])
        elif osx_check() and os.getenv('DELUGE_IS_RUNNING_BUNDLE') != "":
            set_language(os.getenv('LANG'))

        # Start the IPC Interface before anything else.. Just in case we are
        # already running.
        self.queuedtorrents = QueuedTorrents()
        self.ipcinterface = IPCInterface(args.torrents)

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

        if self.osxapp:

            def nsapp_open_file(osxapp, filename):
                # Ignore command name which is raised at app launch (python opening main script).
                if (filename == sys.argv[0] or filename == sys.argv[0]+"-bin"):
                    return True
                process_args([filename])

            self.osxapp.connect('NSApplicationOpenFile', nsapp_open_file)
            from .menubar_osx import menubar_osx

            menubar_osx(self, self.osxapp)
            self.osxapp.ready()

        # Initalize the plugins
        self.plugins = PluginManager()

        # Show the connection manager
        self.connectionmanager = ConnectionManager()

        # Setup RPC stats logging
        # daemon_bps: time, bytes_sent, bytes_recv
        self.daemon_bps = (0, 0, 0)
        self.rpc_stats = LoopingCall(self.log_rpc_stats)
        self.closing = False

        # Twisted catches signals to terminate, so have it call a pre_shutdown method.
        reactor.addSystemEventTrigger('before', 'gtkui_close', self.close)

        def gtkui_sigint_handler(num, frame):
            log.debug('SIGINT signal caught, firing event: gtkui_close')
            reactor.callLater(0, reactor.fireSystemEvent, 'gtkui_close')

        signal.signal(signal.SIGINT, gtkui_sigint_handler)

    def start(self):
        reactor.callWhenRunning(self._on_reactor_start)
        reactor.run()
        # Reactor is not running. Any async callbacks (Deferreds) can no longer
        # be processed from this point on.

    def shutdown(self, *args, **kwargs):
        log.debug('GTKUI shutting down...')
        # Shutdown all components
        if client.is_standalone:
            return component.shutdown()

    @defer.inlineCallbacks
    def close(self):
        if self.closing:
            return
        self.closing = True
        # Make sure the config is saved.
        self.config.save()
        # Ensure columns state is saved
        self.torrentview.save_state()
        # Shut down components
        yield self.shutdown()

        # The gtk modal dialogs (e.g. Preferences) can prevent the application
        # quitting, so force exiting by destroying MainWindow. Must be done here
        # to avoid hanging when quitting with SIGINT (CTRL-C).
        self.mainwindow.window.destroy()

        reactor.stop()

        # Restart the application after closing if MainWindow restart attribute set.
        if component.get('MainWindow').restart:
            os.execv(sys.argv[0], sys.argv)

    def log_rpc_stats(self):
        """Log RPC statistics for thinclient mode."""
        if not client.connected():
            return

        t = time.time()
        recv = client.get_bytes_recv()
        sent = client.get_bytes_sent()
        delta_time = t - self.daemon_bps[0]
        delta_sent = sent - self.daemon_bps[1]
        delta_recv = recv - self.daemon_bps[2]
        self.daemon_bps = (t, sent, recv)
        sent_rate = fspeed(delta_sent / delta_time)
        recv_rate = fspeed(delta_recv / delta_time)
        log.debug(
            'RPC: Sent %s (%s) Recv %s (%s)',
            fsize(sent),
            sent_rate,
            fsize(recv),
            recv_rate,
        )

    def _on_reactor_start(self):
        log.debug('_on_reactor_start')
        self.mainwindow.first_show()

        if not self.config['standalone']:
            return self._start_thinclient()

        err_msg = ''
        try:
            client.start_standalone()
        except DaemonRunningError:
            err_msg = _(
                'A Deluge daemon (deluged) is already running.\n'
                'To use Standalone mode, stop local daemon and restart Deluge.'
            )
        except LibtorrentImportError as ex:
            if 'libtorrent library not found' in str(ex):
                err_msg = _(
                    'Only Thin Client mode is available because libtorrent is not installed.\n'
                    'To use Standalone mode, please install libtorrent package.'
                )
            else:
                log.exception(ex)
                err_msg = _(
                    'Only Thin Client mode is available due to libtorrent import error: %s\n'
                    'To use Standalone mode, please see logs for error details.'
                    % (str(ex))
                )

        except ImportError as ex:
            log.exception(ex)
            err_msg = _(
                'Only Thin Client mode is available due to unknown Import Error.\n'
                'To use Standalone mode, please see logs for error details.'
            )
        except Exception as ex:
            log.exception(ex)
            err_msg = _(
                'Only Thin Client mode is available due to unknown Import Error.\n'
                'To use Standalone mode, please see logs for error details.'
            )
        else:
            component.start()
            return

        def on_dialog_response(response):
            """User response to switching mode dialog."""
            if response == ResponseType.YES:
                # Turning off standalone
                self.config['standalone'] = False
                self._start_thinclient()
            else:
                # User want keep Standalone Mode so just quit.
                self.mainwindow.quit()

        # An error occurred so ask user to switch from Standalone to Thin Client mode.
        err_msg += '\n\n' + _('Continue in Thin Client mode?')
        d = YesNoDialog(_('Change User Interface Mode'), err_msg).run()
        d.addCallback(on_dialog_response)

    def _start_thinclient(self):
        """Start the gtkui in thinclient mode"""
        if log.isEnabledFor(logging.DEBUG):
            self.rpc_stats.start(10)

        # Check to see if we need to start the localhost daemon
        if self.config['autostart_localhost']:

            def on_localhost_status(status_info, port):
                if status_info[1] == 'Offline':
                    log.debug('Autostarting localhost: %s', host_config[0:3])
                    self.connectionmanager.start_daemon(port, get_config_dir())

            for host_config in self.connectionmanager.hostlist.config['hosts']:
                if host_config[1] in LOCALHOST:
                    d = self.connectionmanager.hostlist.get_host_status(host_config[0])
                    d.addCallback(on_localhost_status, host_config[2])
                    break

        # Autoconnect to a host
        if self.config['autoconnect']:
            for host_config in self.connectionmanager.hostlist.config['hosts']:
                host_id, host, port, user, __ = host_config
                if host_id == self.config['autoconnect_host_id']:
                    log.debug('Trying to connect to %s@%s:%s', user, host, port)
                    self.connectionmanager._connect(host_id, try_counter=6)
                    break

        if self.config['show_connection_manager_on_start']:
            # Dialog is blocking so call last.
            self.connectionmanager.show()

    def __on_disconnect(self):
        """
        Called when disconnected from the daemon.  We basically just stop all
        the components here.
        """
        self.daemon_bps = (0, 0, 0)
        component.stop()
