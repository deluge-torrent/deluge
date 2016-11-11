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

# isort:imports-thirdparty
from gi.repository.Gdk import WINDOWING, threads_enter, threads_init, threads_leave
from gi.repository.Gtk import RESPONSE_YES
from gi.repository.GObject import set_prgname
from twisted.internet import defer, gtk3reactor
from twisted.internet.error import ReactorAlreadyInstalledError
from twisted.internet.task import LoopingCall

try:
    # Install twisted reactor, before any other modules import reactor.
    reactor = gtk3reactor.install()
except ReactorAlreadyInstalledError as ex:
    # Running unit tests so trial already installed a rector
    from twisted.internet import reactor

# isort:imports-firstparty
import deluge.component as component
from deluge.common import fsize, fspeed, get_default_download_dir, osx_check, windows_check
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import DaemonRunningError
from deluge.ui.client import client
from deluge.ui.gtkui.addtorrentdialog import AddTorrentDialog
from deluge.ui.gtkui.common import associate_magnet_links
from deluge.ui.gtkui.connectionmanager import ConnectionManager
from deluge.ui.gtkui.dialogs import YesNoDialog
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
from deluge.ui.hostlist import LOCALHOST
from deluge.ui.sessionproxy import SessionProxy
from deluge.ui.tracker_icons import TrackerIcons
from deluge.ui.translations_util import set_language, setup_translations

set_prgname('deluge'.encode('utf8'))
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
    'window_pane_position': 235,
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
    'ntf_tray_blink': True,
    'ntf_sound': False,
    'ntf_sound_path': get_default_download_dir(),
    'ntf_popup': False,
    'ntf_email': False,
    'ntf_email_add': '',
    'ntf_username': '',
    'ntf_pass': '',
    'ntf_server': '',
    'ntf_security': None,
    'show_sidebar': True,
    'show_toolbar': True,
    'show_statusbar': True,
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
        setup_translations(setup_gettext=False, setup_pygtk=True)

        # Setup signals
        def on_die(*args):
            log.debug('OS signal "die" caught with args: %s', args)
            reactor.stop()

        if windows_check():
            from win32api import SetConsoleCtrlHandler
            SetConsoleCtrlHandler(on_die, True)
            log.debug('Win32 "die" handler registered')
        elif osx_check() and WINDOWING == 'quartz':
            import gtkosx_application
            self.osxapp = gtkosx_application.gtkosx_application_get()
            self.osxapp.connect('NSApplicationWillTerminate', on_die)
            log.debug('OSX quartz "die" handler registered')

        # Set process name again to fix gtk issue
        setproctitle(getproctitle())

        # Attempt to register a magnet URI handler with gconf, but do not overwrite
        # if already set by another program.
        associate_magnet_links(False)

        # Make sure gtkui.conf has at least the defaults set
        self.config = ConfigManager('gtkui.conf', DEFAULT_PREFS)

        # Make sure the gtkui state folder has been created
        if not os.path.exists(os.path.join(get_config_dir(), 'gtkui_state')):
            os.makedirs(os.path.join(get_config_dir(), 'gtkui_state'))

        # Set language
        if self.config['language'] is not None:
            set_language(self.config['language'])

        # Start the IPC Interface before anything else.. Just in case we are
        # already running.
        self.queuedtorrents = QueuedTorrents()
        self.ipcinterface = IPCInterface(args.torrents)

        # FIXME: Verify that removing gdk threading has no adverse effects.
        # There are the two commits [64a94ec] [1f3e930] that added gdk threading
        # and my thinking is there is no need for the code anymore.
	# Since PyGObject 3.10.2, calling GObject.threads_init() this is no longer needed. 
        # threads_init()

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

        if osx_check() and WINDOWING == 'quartz':
            def nsapp_open_file(osxapp, filename):
                # Ignore command name which is raised at app launch (python opening main script).
                if filename == sys.argv[0]:
                    return True
                process_args([filename])
            self.osxapp.connect('NSApplicationOpenFile', nsapp_open_file)
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

        # Initialize gdk threading
        threads_enter()
        reactor.run()
        # Reactor no longer running so async callbacks (Deferreds) cannot be
        # processed after this point.
        threads_leave()

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
        log.debug('RPC: Sent %s (%s) Recv %s (%s)', fsize(sent), sent_rate, fsize(recv), recv_rate)

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
                'To use Standalone mode, stop local daemon and restart Deluge.',
            )
        except ImportError as ex:
            if 'No module named libtorrent' in ex.message:
                err_msg = _(
                    'Only Thin Client mode is available because libtorrent is not installed.\n'
                    'To use Standalone mode, please install libtorrent package.',
                )
            else:
                log.exception(ex)
                err_msg = _(
                    'Only Thin Client mode is available due to unknown Import Error.\n'
                    'To use Standalone mode, please see logs for error details.',
                )
        except Exception as ex:
            log.exception(ex)
            err_msg = _(
                'Only Thin Client mode is available due to unknown Import Error.\n'
                'To use Standalone mode, please see logs for error details.',
            )
        else:
            component.start()
            return

        def on_dialog_response(response):
            """User response to switching mode dialog."""
            if response == RESPONSE_YES:
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
