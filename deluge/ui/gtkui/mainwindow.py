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


import copy
import os.path
import pygtk
pygtk.require('2.0')
import gtk
import logging
import urllib

from deluge.ui.client import client
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.ipcinterface import process_args
from twisted.internet import reactor

import deluge.common
import common

log = logging.getLogger(__name__)

class _GtkBuilderSignalsHolder(object):
    def connect_signals(self, mapping_or_class):

        if isinstance(mapping_or_class, dict):
            for name, handler in mapping_or_class.iteritems():
                if hasattr(self, name):
                    raise RuntimeError(
                        "A handler for signal %r has already been registered: %s" %
                        (name, getattr(self, name))
                    )
                setattr(self, name, handler)
        else:
            for name in dir(mapping_or_class):
                if not name.startswith('on_'):
                    continue
                if hasattr(self, name):
                    raise RuntimeError("A handler for signal %r has already been registered: %s" %
                                         (name, getattr(self, name)))
                setattr(self, name, getattr(mapping_or_class, name))

class MainWindow(component.Component):
    def __init__(self):
        component.Component.__init__(self, "MainWindow", interval=2)
        self.config = ConfigManager("gtkui.conf")
        self.gtk_builder_signals_holder = _GtkBuilderSignalsHolder()
        self.main_builder = gtk.Builder()
        # Patch this GtkBuilder to avoid connecting signals from elsewhere
        #
        # Think about splitting up the main window gtkbuilder file into the necessary parts
        # in order not to have to monkey patch GtkBuilder. Those parts would then need to
        # be added to the main window "by hand".
        self.main_builder.prev_connect_signals = copy.deepcopy(self.main_builder.connect_signals)
        def patched_connect_signals(*a, **k):
            raise RuntimeError("In order to connect signals to this GtkBuilder instance please use "
                               "'component.get(\"MainWindow\").connect_signals()'")
        self.main_builder.connect_signals = patched_connect_signals

        # Get the gtk builder file for the main window
        self.main_builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "main_window.ui"))
        )
        # The new release dialog
        self.main_builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "main_window.new_release.ui"))
        )
        # The move storage dialog
        self.main_builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "main_window.move_storage.ui"))
        )
        # The tabs
        self.main_builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "main_window.tabs.ui"))
        )
        # The tabs file menu
        self.main_builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "main_window.tabs.menu_file.ui"))
        )
        # The tabs peer menu
        self.main_builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "main_window.tabs.menu_peer.ui"))
        )


        self.window = self.main_builder.get_object("main_window")

        self.window.set_icon(common.get_deluge_icon())

        self.vpaned = self.main_builder.get_object("vpaned")
        self.initial_vpaned_position = self.config["window_pane_position"]

        # Load the window state
        self.load_window_state()

        # Keep track of window's minimization state so that we don't update the
        # UI when it is minimized.
        self.is_minimized = False

        self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL, [('text/uri-list', 0, 80)], gtk.gdk.ACTION_COPY)

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

    def connect_signals(self, mapping_or_class):
        self.gtk_builder_signals_holder.connect_signals(mapping_or_class)

    def first_show(self):
        if not(self.config["start_in_tray"] and \
               self.config["enable_system_tray"]) and not \
                self.window.get_property("visible"):
            log.debug("Showing window")
            self.main_builder.prev_connect_signals(self.gtk_builder_signals_holder)
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
        # Restore the proper x,y coords for the window prior to showing it
        try:
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

    def active(self):
        """Returns True if the window is active, False if not."""
        return self.window.is_active()

    def visible(self):
        """Returns True if window is visible, False if not."""
        return self.window.get_property("visible")

    def get_builder(self):
        """Returns a reference to the main window GTK builder object."""
        return self.main_builder

    def quit(self, shutdown=False):
        """
        Quits the GtkUI

        :param shutdown: whether or not to shutdown the daemon as well
        :type shutdown: boolean
        """
        if shutdown:
            def on_daemon_shutdown(result):
                reactor.stop()
            client.daemon.shutdown().addCallback(on_daemon_shutdown)
            return
        if client.is_classicmode():
            reactor.stop()
            return
        if not client.connected():
            reactor.stop()
            return
        def on_client_disconnected(result):
            reactor.stop()
        client.disconnect().addCallback(on_client_disconnected)


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
            else:
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
