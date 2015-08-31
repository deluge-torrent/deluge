#
# mainwindow.py
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


import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gobject
import pkg_resources
from hashlib import sha1 as sha

try:
    import wnck
except ImportError:
    wnck = None

from deluge.ui.client import client
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.ipcinterface import process_args
from deluge.ui.gtkui.dialogs import PasswordDialog
from twisted.internet import reactor, defer
from twisted.internet.error import ReactorNotRunning

import deluge.common
import common

from deluge.log import LOG as log

class MainWindow(component.Component):
    def __init__(self):
        if wnck:
            self.screen = wnck.screen_get_default()
        component.Component.__init__(self, "MainWindow", interval=2)
        self.config = ConfigManager("gtkui.conf")
        # Get the glade file for the main window
        self.main_glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui",
                                                    "glade/main_window.glade"))

        self.window = self.main_glade.get_widget("main_window")

        self.window.set_icon(common.get_deluge_icon())

        self.vpaned = self.main_glade.get_widget("vpaned")
        self.initial_vpaned_position = self.config["window_pane_position"]

        # Load the window state
        self.load_window_state()

        # Keep track of window's minimization state so that we don't update the
        # UI when it is minimized.
        self.is_minimized = False

        self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL, [('text/uri-list', 0,
            80)], gtk.gdk.ACTION_COPY)

        # Connect events
        self.window.connect("window-state-event", self.on_window_state_event)
        self.window.connect("configure-event", self.on_window_configure_event)
        self.window.connect("delete-event", self.on_window_delete_event)
        self.window.connect("drag-data-received", self.on_drag_data_received_event)
        self.vpaned.connect("notify::position", self.on_vpaned_position_event)
        self.window.connect("expose-event", self.on_expose_event)

        self.config.register_set_function("show_rate_in_title", self._on_set_show_rate_in_title, apply_now=False)

        client.register_event_handler("NewVersionAvailableEvent", self.on_newversionavailable_event)
        client.register_event_handler("TorrentFinishedEvent", self.on_torrentfinished_event)

    def first_show(self):
        if not(self.config["start_in_tray"] and \
               self.config["enable_system_tray"]) and not \
                self.window.get_property("visible"):
            log.debug("Showing window")
            self.show()
            while gtk.events_pending():
                gtk.main_iteration(False)
            self.vpaned.set_position(self.initial_vpaned_position)

    def show(self):
        try:
            component.resume("TorrentView")
            component.resume("StatusBar")
            component.resume("TorrentDetails")
        except:
            pass
        self.window.show()

    def hide(self):
        component.pause("TorrentView")
        component.get("TorrentView").save_state()
        component.pause("StatusBar")
        component.pause("TorrentDetails")
        # Store the x, y positions for when we restore the window
        self.window_x_pos = self.window.get_position()[0]
        self.window_y_pos = self.window.get_position()[1]
        self.window.hide()

    def present(self):
        def restore():
            # Restore the proper x,y coords for the window prior to showing it
            try:
                if self.window_x_pos == -32000 or self.window_y_pos == -32000:
                    self.config["window_x_pos"] = 0
                    self.config["window_y_pos"] = 0
                else:
                    self.config["window_x_pos"] = self.window_x_pos
                    self.config["window_y_pos"] = self.window_y_pos
            except:
                pass
            try:
                component.resume("TorrentView")
                component.resume("StatusBar")
                component.resume("TorrentDetails")
            except:
                pass

            self.window.present()
            self.load_window_state()

        if self.config["lock_tray"] and not self.visible():
            dialog = PasswordDialog(_("Enter your password to show Deluge..."))
            def on_dialog_response(response_id):
                if response_id == gtk.RESPONSE_OK:
                    if self.config["tray_password"] == sha(dialog.get_password()).hexdigest():
                        restore()
            dialog.run().addCallback(on_dialog_response)
        else:
            restore()

    def active(self):
        """Returns True if the window is active, False if not."""
        return self.window.is_active()

    def visible(self):
        """Returns True if window is visible, False if not."""
        return self.window.get_property("visible")

    def get_glade(self):
        """Returns a reference to the main window glade object."""
        return self.main_glade

    def quit(self, shutdown=False):
        """
        Quits the GtkUI

        :param shutdown: whether or not to shutdown the daemon as well
        :type shutdown: boolean
        """
        def quit_gtkui():
            def shutdown_daemon(result):
                return client.daemon.shutdown()

            def disconnect_client(result):
                return client.disconnect()

            def stop_reactor(result):
                try:
                    reactor.stop()
                except ReactorNotRunning:
                    log.debug("Attempted to stop the reactor but it is not running...")

            def log_failure(failure, action):
                log.error("Encountered error attempting to %s: %s" % \
                          (action, failure.getErrorMessage()))

            d = defer.succeed(None)
            if shutdown:
                d.addCallback(shutdown_daemon)
                d.addErrback(log_failure, "shutdown daemon")
            if not client.is_classicmode() and client.connected():
                d.addCallback(disconnect_client)
                d.addErrback(log_failure, "disconnect client")
            d.addBoth(stop_reactor)

        if self.config["lock_tray"] and not self.visible():
            dialog = PasswordDialog(_("Enter your password to Quit Deluge..."))
            def on_dialog_response(response_id):
                if response_id == gtk.RESPONSE_OK:
                    if self.config["tray_password"] == sha(dialog.get_password()).hexdigest():
                        quit_gtkui()
            dialog.run().addCallback(on_dialog_response)
        else:
            quit_gtkui()

    def load_window_state(self):
        x = self.config["window_x_pos"]
        y = self.config["window_y_pos"]
        w = self.config["window_width"]
        h = self.config["window_height"]
        self.window.move(x, y)
        self.window.resize(w, h)
        if self.config["window_maximized"]:
            self.window.maximize()

    def on_window_configure_event(self, widget, event):
        if not self.config["window_maximized"] and self.visible:
            self.config["window_x_pos"] = self.window.get_position()[0]
            self.config["window_y_pos"] = self.window.get_position()[1]
            self.config["window_width"] = event.width
            self.config["window_height"] = event.height

    def on_window_state_event(self, widget, event):
        if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
                log.debug("pos: %s", self.window.get_position())
                self.config["window_maximized"] = True
            elif not event.new_window_state & gtk.gdk.WINDOW_STATE_WITHDRAWN:
                self.config["window_maximized"] = False
        if event.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
            if event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED:
                log.debug("MainWindow is minimized..")
                component.pause("TorrentView")
                component.pause("StatusBar")
                self.is_minimized = True
            else:
                log.debug("MainWindow is not minimized..")
                try:
                    component.resume("TorrentView")
                    component.resume("StatusBar")
                except:
                    pass
                self.is_minimized = False
        return False

    def on_window_delete_event(self, widget, event):
        if self.config["close_to_tray"] and self.config["enable_system_tray"]:
            self.hide()
        else:
            self.quit()

        return True

    def on_vpaned_position_event(self, obj, param):
        self.config["window_pane_position"] = self.vpaned.get_position()

    def on_drag_data_received_event(self, widget, drag_context, x, y, selection_data, info, timestamp):
        log.debug("Selection(s) dropped on main window %s", selection_data.data)
        if selection_data.get_uris():
            process_args(selection_data.get_uris())
        else:
            process_args(selection_data.data.split())
        drag_context.finish(True, True)

    def on_expose_event(self, widget, event):
        component.get("SystemTray").blink(False)

    def stop(self):
        self.window.set_title("Deluge")

    def update(self):
        # Update the window title
        def _on_get_session_status(status):
            download_rate = deluge.common.fsize_short(status["payload_download_rate"])
            upload_rate = deluge.common.fsize_short(status["payload_upload_rate"])
            self.window.set_title("%s%s %s%s - Deluge" % (_("D:"), download_rate, _("U:"), upload_rate))
        if self.config["show_rate_in_title"]:
            client.core.get_session_status(["payload_download_rate", "payload_upload_rate"]).addCallback(_on_get_session_status)

    def _on_set_show_rate_in_title(self, key, value):
        if value:
            self.update()
        else:
            self.window.set_title("Deluge")

    def on_newversionavailable_event(self, new_version):
        if self.config["show_new_releases"]:
            from deluge.ui.gtkui.new_release_dialog import NewReleaseDialog
            reactor.callLater(5.0, NewReleaseDialog().show, new_version)

    def on_torrentfinished_event(self, torrent_id):
        from deluge.ui.gtkui.notification import Notification
        Notification().notify(torrent_id)

    def is_on_active_workspace(self):
        """Determines if MainWindow is on the active workspace.

        Returns:
            bool: True if on active workspace (or wnck module not available), otherwise False.

        """
        if wnck:
            self.screen.force_update()
            win = wnck.window_get(self.window.window.xid)
            if win:
                active_wksp = win.get_screen().get_active_workspace()
                if active_wksp:
                    return win.is_on_workspace(active_wksp)
                else:
                    return False
        return True
