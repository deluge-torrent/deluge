#
# connectionmanager.py
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
#

import gtk
import pkg_resources
import urlparse
import time
import hashlib
from twisted.internet import reactor

import deluge.component as component
import deluge.common
import deluge.ui.gtkui.common as common
import deluge.configmanager
from deluge.ui.client import client
import deluge.ui.client
import deluge.ui.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 58846

DEFAULT_CONFIG = {
    "hosts": [(hashlib.sha1(str(time.time())).hexdigest(), DEFAULT_HOST, DEFAULT_PORT, "", "")]
}

HOSTLIST_COL_ID = 0
HOSTLIST_COL_HOST = 1
HOSTLIST_COL_PORT = 2
HOSTLIST_COL_STATUS = 3
HOSTLIST_COL_USER = 4
HOSTLIST_COL_PASS = 5
HOSTLIST_COL_VERSION = 6


HOSTLIST_PIXBUFS = [
    # This is populated in ConnectionManager.show
]

HOSTLIST_STATUS = [
    "Offline",
    "Online",
    "Connected"
]

def cell_render_host(column, cell, model, row, data):
    host, port, username = model.get(row, *data)
    text = host + ":" + str(port)
    if username:
        text = username + "@" + text
    cell.set_property('text', text)

def cell_render_status(column, cell, model, row, data):
    status = model[row][data]
    pixbuf = None
    if status in HOSTLIST_STATUS:
        pixbuf = HOSTLIST_PIXBUFS[HOSTLIST_STATUS.index(status)]

    cell.set_property("pixbuf", pixbuf)

class ConnectionManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "ConnectionManager")
        self.gtkui_config = ConfigManager("gtkui.conf")

        self.config = ConfigManager("hostlist.conf.1.2", DEFAULT_CONFIG)

    # Component overrides
    def start(self):
        pass

    def stop(self):
        pass

    def shutdown(self):
        pass

    # Public methods
    def show(self):
        """
        Show the ConnectionManager dialog.
        """
        # Get the glade file for the connection manager
        self.glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui",
                                            "glade/connection_manager.glade"))
        self.window = component.get("MainWindow")

        # Setup the ConnectionManager dialog
        self.connection_manager = self.glade.get_widget("connection_manager")
        self.connection_manager.set_transient_for(self.window.window)
        self.connection_manager.set_icon(common.get_logo(32))
        self.glade.get_widget("image1").set_from_pixbuf(common.get_logo(32))

        self.hostlist = self.glade.get_widget("hostlist")

        # Create status pixbufs
        if not HOSTLIST_PIXBUFS:
            for stock_id in (gtk.STOCK_NO, gtk.STOCK_YES, gtk.STOCK_CONNECT):
                HOSTLIST_PIXBUFS.append(self.connection_manager.render_icon(stock_id, gtk.ICON_SIZE_MENU))

        # Create the host list gtkliststore
        # id-hash, hostname, port, status, username, password, version
        self.liststore = gtk.ListStore(str, str, int, str, str, str, str)

        # Setup host list treeview
        self.hostlist.set_model(self.liststore)
        render = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("Status", render)
        column.set_cell_data_func(render, cell_render_status, 3)
        self.hostlist.append_column(column)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Host", render, text=HOSTLIST_COL_HOST)
        column.set_cell_data_func(render, cell_render_host, (1, 2, 4))
        column.set_expand(True)
        self.hostlist.append_column(column)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Version", render, text=HOSTLIST_COL_VERSION)
        self.hostlist.append_column(column)

        # Load any saved host entries
        self.__load_hostlist()
        self.__load_options()

        # Connect the signals to the handlers
        self.glade.signal_autoconnect(self)
        self.hostlist.get_selection().connect("changed", self.on_hostlist_selection_changed)

        self.__update_list()

        response = self.connection_manager.run()

        # Save the toggle options
        self.__save_options()

        self.connection_manager.destroy()
        del self.glade
        del self.window
        del self.connection_manager
        del self.liststore
        del self.hostlist

    def add_host(self, host, port, username="", password=""):
        """
        Adds a host to the list.

        :param host: str, the hostname
        :param port: int, the port
        :param username: str, the username to login as
        :param password: str, the password to login with

        """
        # Check to see if there is already an entry for this host and return
        # if thats the case
        for entry in self.liststore:
            if [entry[HOSTLIST_COL_HOST], entry[HOSTLIST_COL_PORT], entry[HOSTLIST_COL_USER]] == [host, port, username]:
                raise Exception("Host already in list!")

        # Host isn't in the list, so lets add it
        row = self.liststore.append()
        import time
        import hashlib
        self.liststore[row][HOSTLIST_COL_ID] = hashlib.sha1(str(time.time())).hexdigest()
        self.liststore[row][HOSTLIST_COL_HOST] = host
        self.liststore[row][HOSTLIST_COL_PORT] = port
        self.liststore[row][HOSTLIST_COL_USER] = username
        self.liststore[row][HOSTLIST_COL_PASS] = password

        # Save the host list to file
        self.__save_hostlist()

        # Update the status of the hosts
        self.__update_list()

    # Private methods
    def __save_hostlist(self):
        """
        Save the current hostlist to the config file.
        """
        # Grab the hosts from the liststore
        self.config["hosts"] = []
        for row in self.liststore:
            self.config["hosts"].append((row[HOSTLIST_COL_ID], row[HOSTLIST_COL_HOST], row[HOSTLIST_COL_PORT], row[HOSTLIST_COL_USER], row[HOSTLIST_COL_PASS]))

        self.config.save()

    def __load_hostlist(self):
        """
        Load saved host entries
        """
        for host in self.config["hosts"]:
            new_row = self.liststore.append()
            self.liststore[new_row][HOSTLIST_COL_ID] = host[0]
            self.liststore[new_row][HOSTLIST_COL_HOST] = host[1]
            self.liststore[new_row][HOSTLIST_COL_PORT] = host[2]
            self.liststore[new_row][HOSTLIST_COL_USER] = host[3]
            self.liststore[new_row][HOSTLIST_COL_PASS] = host[4]

    def __get_host_row(self, host_id):
        """
        Returns the row in the liststore for `:param:host_id` or None

        """
        for row in self.liststore:
            if host_id == row[HOSTLIST_COL_ID]:
                return row
        return None

    def __update_list(self):
        """Updates the host status"""
        def on_connect(result, c, host_id):
            row = self.__get_host_row(host_id)
            def on_info(info, c):
                if row:
                    row[HOSTLIST_COL_STATUS] = "Online"
                    row[HOSTLIST_COL_VERSION] = info
                    self.__update_buttons()
                c.disconnect()

            def on_info_fail(reason):
                if row:
                    row[HOSTLIST_COL_STATUS] = "Offline"
                    self.__update_buttons()

            d = c.daemon.info()
            d.addCallback(on_info, c)
            d.addErrback(on_info_fail)

        def on_connect_failed(reason, host_info):
            row = self.__get_host_row(host_id)
            if row:
                row[HOSTLIST_COL_STATUS] = "Offline"
                self.__update_buttons()

        for row in self.liststore:
            host_id = row[HOSTLIST_COL_ID]
            host = row[HOSTLIST_COL_HOST]
            port = row[HOSTLIST_COL_PORT]
            user = row[HOSTLIST_COL_USER]
            password = row[HOSTLIST_COL_PASS]
            if client.connected() and (host, port, user) == client.connection_info():
                def on_info(info):
                    row[HOSTLIST_COL_VERSION] = info
                    self.__update_buttons()
                row[HOSTLIST_COL_STATUS] = "Connected"
                client.daemon.info().addCallback(on_info)
                continue

            if host in ("127.0.0.1", "localhost") and not user:
                # We need to get the localhost creds
                user, password = deluge.ui.common.get_localhost_auth()
            # Create a new Client instance
            c = deluge.ui.client.Client()
            d = c.connect(host, port, user, password)
            d.addCallback(on_connect, c, host_id)
            d.addErrback(on_connect_failed, host_id)

    def __load_options(self):
        """
        Set the widgets to show the correct options from the config.
        """
        self.glade.get_widget("chk_autoconnect").set_active(self.gtkui_config["autoconnect"])
        self.glade.get_widget("chk_autostart").set_active(self.gtkui_config["autostart_localhost"])
        self.glade.get_widget("chk_donotshow").set_active(not self.gtkui_config["show_connection_manager_on_start"])

    def __save_options(self):
        """
        Set options in gtkui config from the toggle buttons.
        """
        self.gtkui_config["autoconnect"] = self.glade.get_widget("chk_autoconnect").get_active()
        self.gtkui_config["autostart_localhost"] = self.glade.get_widget("chk_autostart").get_active()
        self.gtkui_config["show_connection_manager_on_start"] = not self.glade.get_widget("chk_donotshow").get_active()

    def __update_buttons(self):
        """
        Updates the buttons states.
        """
        if len(self.liststore) == 0:
            # There is nothing in the list
            self.glade.get_widget("button_startdaemon").set_sensitive(True)
            self.glade.get_widget("button_connect").set_sensitive(False)
            self.glade.get_widget("button_removehost").set_sensitive(False)
            self.glade.get_widget("image_startdaemon").set_from_stock(
                gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)
            self.glade.get_widget("label_startdaemon").set_text("_Start Daemon")

        model, row = self.hostlist.get_selection().get_selected()
        if not row:
            return

        # Get some values about the selected host
        status = model[row][HOSTLIST_COL_STATUS]
        host = model[row][HOSTLIST_COL_HOST]

        log.debug("Status: %s", status)
        # Check to see if we have a localhost entry selected
        localhost = False
        if host in ("127.0.0.1", "localhost"):
            localhost = True

        # Make sure buttons are sensitive at start
        self.glade.get_widget("button_startdaemon").set_sensitive(True)
        self.glade.get_widget("button_connect").set_sensitive(True)
        self.glade.get_widget("button_removehost").set_sensitive(True)

        # See if this is the currently connected host
        if status == "Connected":
            # Display a disconnect button if we're connected to this host
            self.glade.get_widget("button_connect").set_label("gtk-disconnect")
            self.glade.get_widget("button_removehost").set_sensitive(False)
        else:
            self.glade.get_widget("button_connect").set_label("gtk-connect")
            if status == "Offline" and not localhost:
                self.glade.get_widget("button_connect").set_sensitive(False)

        # Check to see if the host is online
        if status == "Connected" or status == "Online":
            self.glade.get_widget("image_startdaemon").set_from_stock(
                gtk.STOCK_STOP, gtk.ICON_SIZE_MENU)
            self.glade.get_widget("label_startdaemon").set_text(
                "_Stop Daemon")

        # Update the start daemon button if the selected host is localhost
        if localhost and status == "Offline":
            # The localhost is not online
            self.glade.get_widget("image_startdaemon").set_from_stock(
                gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)
            self.glade.get_widget("label_startdaemon").set_text(
                "_Start Daemon")

        if not localhost:
            # An offline host
            self.glade.get_widget("button_startdaemon").set_sensitive(False)

        # Make sure label is displayed correctly using mnemonics
        self.glade.get_widget("label_startdaemon").set_use_underline(
            True)

    # Signal handlers
    def __on_connected(self, connector, host_id):
        if self.gtkui_config["autoconnect"]:
            self.gtkui_config["autoconnect_host_id"] = host_id

        component.start()

    def on_button_connect_clicked(self, widget=None):
        model, row = self.hostlist.get_selection().get_selected()
        status = model[row][HOSTLIST_COL_STATUS]
        if status == "Connected":
            def on_disconnect(reason):
                self.__update_list()
            client.disconnect().addCallback(on_disconnect)
            return

        host_id = model[row][HOSTLIST_COL_ID]
        host = model[row][HOSTLIST_COL_HOST]
        port = model[row][HOSTLIST_COL_PORT]
        user = model[row][HOSTLIST_COL_USER]
        password = model[row][HOSTLIST_COL_PASS]
        if not user and host in ("127.0.0.1", "localhost"):
            # This is a localhost connection with no username, so lets try to
            # get the localclient creds from the auth file.
            user, password = deluge.ui.common.get_localhost_auth()
        client.connect(host, port, user, password).addCallback(self.__on_connected, host_id)
        self.connection_manager.response(gtk.RESPONSE_OK)

    def on_button_close_clicked(self, widget):
        self.connection_manager.response(gtk.RESPONSE_CLOSE)

    def on_button_addhost_clicked(self, widget):
        log.debug("on_button_addhost_clicked")
        dialog = self.glade.get_widget("addhost_dialog")
        dialog.set_icon(common.get_logo(16))
        hostname_entry = self.glade.get_widget("entry_hostname")
        port_spinbutton = self.glade.get_widget("spinbutton_port")
        username_entry = self.glade.get_widget("entry_username")
        password_entry = self.glade.get_widget("entry_password")
        response = dialog.run()
        if response == 1:
            username = username_entry.get_text()
            password = password_entry.get_text()
            hostname = hostname_entry.get_text()

            # We add the host
            self.add_host(hostname, port_spinbutton.get_value_as_int(), username, password)

        dialog.hide()

    def on_button_removehost_clicked(self, widget):
        log.debug("on_button_removehost_clicked")
        # Get the selected rows
        paths = self.hostlist.get_selection().get_selected_rows()[1]
        for path in paths:
            self.liststore.remove(self.liststore.get_iter(path))

        # Update the hostlist
        self.__update_list()

        # Save the host list
        self.__save_hostlist()

    def on_button_startdaemon_clicked(self, widget):
        log.debug("on_button_startdaemon_clicked")
        if self.liststore.iter_n_children(None) < 1:
            # There is nothing in the list, so lets create a localhost entry
            self.add_host(DEFAULT_HOST, DEFAULT_PORT)
            # ..and start the daemon.
            client.start_daemon(DEFAULT_PORT, deluge.configmanager.get_config_dir())
            return

        paths = self.hostlist.get_selection().get_selected_rows()[1]
        if len(paths) < 1:
            return

        status = self.liststore[paths[0]][HOSTLIST_COL_STATUS]
        host = self.liststore[paths[0]][HOSTLIST_COL_HOST]
        port = self.liststore[paths[0]][HOSTLIST_COL_PORT]
        user = self.liststore[paths[0]][HOSTLIST_COL_USER]
        password = self.liststore[paths[0]][HOSTLIST_COL_PASS]

        if host not in ("127.0.0.1", "localhost"):
            return

        if status in ("Online", "Connected"):
            # We need to stop this daemon
            # Call the shutdown method on the daemon
            def on_daemon_shutdown(d):
                # Update display to show change
                self.__update_list()
            if client.connected():
                client.daemon.shutdown().addCallback(on_daemon_shutdown)
            else:
                # Create a new client instance
                c = deluge.ui.client.Client()
                def on_connect(d, c):
                    log.debug("on_connect")
                    c.daemon.shutdown().addCallback(on_daemon_shutdown)

                c.connect(host, port, user, password).addCallback(on_connect, c)

        elif status == "Offline":
            client.start_daemon(port, deluge.configmanager.get_config_dir())
            reactor.callLater(2.0, self.__update_list)

    def on_button_refresh_clicked(self, widget):
        self.__update_list()

    def on_hostlist_row_activated(self, tree, path, view_column):
        self.on_button_connect_clicked()

    def on_hostlist_selection_changed(self, treeselection):
        self.__update_buttons()
