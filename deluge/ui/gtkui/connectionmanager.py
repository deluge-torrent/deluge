# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import hashlib
import logging
import os
import time

from twisted.internet import reactor

import deluge.component as component
from deluge.common import resource_filename
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import AuthenticationRequired, BadLoginError, IncompatibleClient
from deluge.ui.client import Client, client
from deluge.ui.common import get_localhost_auth
from deluge.ui.gtkui.common import get_deluge_icon, get_logo
from deluge.ui.gtkui.dialogs import AuthenticationDialog, ErrorDialog
from gi.repository import Gtk

log = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 58846

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
        self.config = self.__load_config()
        self.running = False

    # Component overrides
    def start(self):
        pass

    def stop(self):
        # Close this dialog when we are shutting down
        if self.running:
            self.connection_manager.response(Gtk.ResponseType.CLOSE)

    def shutdown(self):
        pass

    def __load_config(self):
        auth_file = get_config_dir("auth")
        if not os.path.exists(auth_file):
            from deluge.common import create_localclient_account
            create_localclient_account()

        localclient_username, localclient_password = get_localhost_auth()
        default_config = {
            "hosts": [(
                hashlib.sha1(str(time.time())).hexdigest(),
                DEFAULT_HOST,
                DEFAULT_PORT,
                localclient_username,
                localclient_password
            )]
        }
        config = ConfigManager("hostlist.conf.1.2", default_config)
        config.run_converter((0, 1), 2, self.__migrate_config_1_to_2)
        return config

    # Public methods
    def show(self):
        """
        Show the ConnectionManager dialog.
        """
        self.config = self.__load_config()
        # Get the gtk builder file for the connection manager
        self.builder = Gtk.Builder()
        # The main dialog
        self.builder.add_from_file(resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "connection_manager.ui")
        ))
        # The add host dialog
        self.builder.add_from_file(resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "connection_manager.addhost.ui")
        ))
        # The ask password dialog
        self.builder.add_from_file(resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "connection_manager.askpassword.ui")
        ))
        self.window = component.get("MainWindow")

        # Setup the ConnectionManager dialog
        self.connection_manager = self.builder.get_object("connection_manager")
        self.connection_manager.set_transient_for(self.window.window)

        self.connection_manager.set_icon(get_deluge_icon())

        self.builder.get_object("image1").set_from_pixbuf(get_logo(32))

        self.askpassword_dialog = self.builder.get_object("askpassword_dialog")
        self.askpassword_dialog.set_transient_for(self.connection_manager)
        self.askpassword_dialog.set_icon(get_deluge_icon())
        self.askpassword_dialog_entry = self.builder.get_object("askpassword_dialog_entry")

        self.hostlist = self.builder.get_object("hostlist")

        # Create status pixbufs
        if not HOSTLIST_PIXBUFS:
            for stock_id in (Gtk.STOCK_NO, Gtk.STOCK_YES, Gtk.STOCK_CONNECT):
                HOSTLIST_PIXBUFS.append(
                    self.connection_manager.render_icon(
                        stock_id, Gtk.IconSize.MENU
                    )
                )

        # Create the host list gtkliststore
        # id-hash, hostname, port, status, username, password, version
        self.liststore = Gtk.ListStore(str, str, int, str, str, str, str)

        # Setup host list treeview
        self.hostlist.set_model(self.liststore)
        render = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn(_("Status"), render)
        column.set_cell_data_func(render, cell_render_status, 3)
        self.hostlist.append_column(column)
        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Host"), render, text=HOSTLIST_COL_HOST)
        column.set_cell_data_func(render, cell_render_host, (1, 2, 4))
        column.set_expand(True)
        self.hostlist.append_column(column)
        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Version"), render, text=HOSTLIST_COL_VERSION)
        self.hostlist.append_column(column)

        # Connect the signals to the handlers
        self.builder.connect_signals(self)
        self.hostlist.get_selection().connect(
            "changed", self.on_hostlist_selection_changed
        )

        # Load any saved host entries
        self.__load_hostlist()
        self.__load_options()
        self.__update_list()

        self.running = True
        # Trigger the on_selection_changed code and select the first host
        # if possible
        self.hostlist.get_selection().unselect_all()
        if len(self.liststore) > 0:
            self.hostlist.get_selection().select_path("0")

        # Run the dialog
        self.connection_manager.run()
        self.running = False

        # Save the toggle options
        self.__save_options()
        self.__save_hostlist()

        self.connection_manager.destroy()
        del self.builder
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
        self.liststore[row][HOSTLIST_COL_STATUS] = "Offline"

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
            self.config["hosts"].append((row[HOSTLIST_COL_ID],
                                         row[HOSTLIST_COL_HOST],
                                         row[HOSTLIST_COL_PORT],
                                         row[HOSTLIST_COL_USER],
                                         row[HOSTLIST_COL_PASS]))

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
            self.liststore[new_row][HOSTLIST_COL_STATUS] = "Offline"
            self.liststore[new_row][HOSTLIST_COL_VERSION] = ""

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
        if not hasattr(self, "liststore"):
            # This callback was probably fired after the window closed
            return

        def on_connect(result, c, host_id):
            # Return if the deferred callback was done after the dialog was closed
            if not self.running:
                return
            row = self.__get_host_row(host_id)

            def on_info(info, c):
                if not self.running:
                    return
                if row:
                    row[HOSTLIST_COL_STATUS] = "Online"
                    row[HOSTLIST_COL_VERSION] = info
                    self.__update_buttons()
                c.disconnect()

            def on_info_fail(reason, c):
                if not self.running:
                    return
                if row:
                    row[HOSTLIST_COL_STATUS] = "Offline"
                    self.__update_buttons()
                c.disconnect()

            d = c.daemon.info()
            d.addCallback(on_info, c)
            d.addErrback(on_info_fail, c)

        def on_connect_failed(reason, host_id):
            if not self.running:
                return
            row = self.__get_host_row(host_id)
            if row:
                row[HOSTLIST_COL_STATUS] = "Offline"
                row[HOSTLIST_COL_VERSION] = ""
                self.__update_buttons()

        for row in self.liststore:
            host_id = row[HOSTLIST_COL_ID]
            host = row[HOSTLIST_COL_HOST]
            port = row[HOSTLIST_COL_PORT]
            user = row[HOSTLIST_COL_USER]

            if (client.connected() and
                    (host, port, "localclient" if not user and host in ("127.0.0.1", "localhost") else user)
                    == client.connection_info()):
                def on_info(info):
                    if not self.running:
                        return
                    log.debug("Client connected, query info: %s", info)
                    row[HOSTLIST_COL_VERSION] = info
                    self.__update_buttons()

                row[HOSTLIST_COL_STATUS] = "Connected"
                log.debug("Query daemon's info")
                client.daemon.info().addCallback(on_info)
                continue

            # Create a new Client instance
            c = Client()
            d = c.connect(host, port, skip_authentication=True)
            d.addCallback(on_connect, c, host_id)
            d.addErrback(on_connect_failed, host_id)

    def __load_options(self):
        """
        Set the widgets to show the correct options from the config.
        """
        self.builder.get_object("chk_autoconnect").set_active(
            self.gtkui_config["autoconnect"]
        )
        self.builder.get_object("chk_autostart").set_active(
            self.gtkui_config["autostart_localhost"]
        )
        self.builder.get_object("chk_donotshow").set_active(
            not self.gtkui_config["show_connection_manager_on_start"]
        )

    def __save_options(self):
        """
        Set options in gtkui config from the toggle buttons.
        """
        self.gtkui_config["autoconnect"] = self.builder.get_object("chk_autoconnect").get_active()
        self.gtkui_config["autostart_localhost"] = self.builder.get_object("chk_autostart").get_active()
        self.gtkui_config["show_connection_manager_on_start"] = not self.builder.get_object(
            "chk_donotshow").get_active()

    def __update_buttons(self):
        """
        Updates the buttons states.
        """
        if len(self.liststore) == 0:
            # There is nothing in the list
            self.builder.get_object("button_startdaemon").set_sensitive(True)
            self.builder.get_object("button_connect").set_sensitive(False)
            self.builder.get_object("button_removehost").set_sensitive(False)
            self.builder.get_object("image_startdaemon").set_from_stock(
                Gtk.STOCK_EXECUTE, Gtk.IconSize.MENU)
            self.builder.get_object("label_startdaemon").set_text("_Start Daemon")

        model, row = self.hostlist.get_selection().get_selected()
        if not row:
            self.builder.get_object("button_edithost").set_sensitive(False)
            return

        self.builder.get_object("button_edithost").set_sensitive(True)

        # Get some values about the selected host
        status = model[row][HOSTLIST_COL_STATUS]
        host = model[row][HOSTLIST_COL_HOST]
        port = model[row][HOSTLIST_COL_PORT]
        user = model[row][HOSTLIST_COL_USER]
        passwd = model[row][HOSTLIST_COL_PASS]

        log.debug("Status: %s", status)
        # Check to see if we have a localhost entry selected
        localhost = False
        if host in ("127.0.0.1", "localhost"):
            localhost = True

        # Make sure buttons are sensitive at start
        self.builder.get_object("button_startdaemon").set_sensitive(True)
        self.builder.get_object("button_connect").set_sensitive(True)
        self.builder.get_object("button_removehost").set_sensitive(True)

        # See if this is the currently connected host
        if status == "Connected":
            # Display a disconnect button if we're connected to this host
            self.builder.get_object("button_connect").set_label("gtk-disconnect")
            self.builder.get_object("button_removehost").set_sensitive(False)
        else:
            self.builder.get_object("button_connect").set_label("gtk-connect")
            if status == "Offline" and not localhost:
                self.builder.get_object("button_connect").set_sensitive(False)

        # Check to see if the host is online
        if status == "Connected" or status == "Online":
            self.builder.get_object("image_startdaemon").set_from_stock(
                Gtk.STOCK_STOP, Gtk.IconSize.MENU)
            self.builder.get_object("label_startdaemon").set_text(
                _("_Stop Daemon"))

        # Update the start daemon button if the selected host is localhost
        if localhost and status == "Offline":
            # The localhost is not online
            self.builder.get_object("image_startdaemon").set_from_stock(
                Gtk.STOCK_EXECUTE, Gtk.IconSize.MENU)
            self.builder.get_object("label_startdaemon").set_text(
                _("_Start Daemon"))

        if client.connected() and (host, port, user) == client.connection_info():
            # If we're connected, we can stop the dameon
            self.builder.get_object("button_startdaemon").set_sensitive(True)
        elif user and passwd:
            # In this case we also have all the info to shutdown the daemon
            self.builder.get_object("button_startdaemon").set_sensitive(True)
        else:
            # Can't stop non localhost daemons, specially without the necessary info
            self.builder.get_object("button_startdaemon").set_sensitive(False)

        # Make sure label is displayed correctly using mnemonics
        self.builder.get_object("label_startdaemon").set_use_underline(True)

    def start_daemon(self, port, config):
        """
        Attempts to start a daemon process and will show an ErrorDialog if unable
        to.
        """
        try:
            return client.start_daemon(port, config)
        except OSError as ex:
            from errno import ENOENT
            if ex.errno == ENOENT:
                ErrorDialog(
                    _("Unable to start daemon!"),
                    _("Deluge cannot find the 'deluged' executable, it is "
                      "likely that you forgot to install the deluged package "
                      "or it's not in your PATH.")).run()
                return False
            else:
                raise ex
        except Exception:
            import traceback
            import sys
            tb = sys.exc_info()
            ErrorDialog(
                _("Unable to start daemon!"),
                _("Please examine the details for more information."),
                details=traceback.format_exc(tb[2])).run()

    # Signal handlers
    def __connect(self, host_id, host, port, username, password,
                  skip_authentication=False, try_counter=0):
        def do_connect(*args):
            d = client.connect(host, port, username, password, skip_authentication)
            d.addCallback(self.__on_connected, host_id)
            d.addErrback(self.__on_connected_failed, host_id, host, port,
                         username, password, try_counter)
            return d

        if client.connected():
            return client.disconnect().addCallback(do_connect)
        else:
            return do_connect()

    def __on_connected(self, daemon_info, host_id):
        if self.gtkui_config["autoconnect"]:
            self.gtkui_config["autoconnect_host_id"] = host_id
        if self.running:
            # When connected to a client, and then trying to connect to another,
            # this component will be stopped(while the connect deferred is
            # running), so, self.connection_manager will be deleted.
            # If that's not the case, close the dialog.
            self.connection_manager.response(Gtk.ResponseType.OK)
        component.start()

    def __on_connected_failed(self, reason, host_id, host, port, user, passwd,
                              try_counter):
        log.debug("Failed to connect: %s", reason.value)

        if reason.check(AuthenticationRequired, BadLoginError):
            log.debug("PasswordRequired exception")
            dialog = AuthenticationDialog(reason.value.message, reason.value.username)

            def dialog_finished(response_id, host, port, user):
                if response_id == Gtk.ResponseType.OK:
                    self.__connect(host_id, host, port,
                                   user and user or dialog.get_username(),
                                   dialog.get_password())
            d = dialog.run().addCallback(dialog_finished, host, port, user)
            return d

        elif reason.trap(IncompatibleClient):
            dialog = ErrorDialog(
                _("Incompatible Client"), reason.value.message
            )
            return dialog.run()

        if try_counter:
            log.info("Retrying connection.. Retries left: %s", try_counter)
            return reactor.callLater(
                0.5, self.__connect, host_id, host, port, user, passwd,
                try_counter=try_counter - 1
            )

        msg = str(reason.value)
        if not self.builder.get_object("chk_autostart").get_active():
            msg += '\n' + _("Auto-starting the daemon locally is not enabled. "
                            "See \"Options\" on the \"Connection Manager\".")
        ErrorDialog(_("Failed To Connect"), msg).run()

    def on_button_connect_clicked(self, widget=None):
        model, row = self.hostlist.get_selection().get_selected()
        if not row:
            return
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

        if (status == "Offline" and self.builder.get_object("chk_autostart").get_active() and
                host in ("127.0.0.1", "localhost")):
            if not self.start_daemon(port, get_config_dir()):
                log.debug("Failed to auto-start daemon")
                return
            return self.__connect(
                host_id, host, port, user, password, try_counter=6
            )
        return self.__connect(host_id, host, port, user, password)

    def on_button_close_clicked(self, widget):
        self.connection_manager.response(Gtk.ResponseType.CLOSE)

    def on_button_addhost_clicked(self, widget):
        log.debug("on_button_addhost_clicked")
        dialog = self.builder.get_object("addhost_dialog")
        dialog.set_transient_for(self.connection_manager)
        dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        hostname_entry = self.builder.get_object("entry_hostname")
        port_spinbutton = self.builder.get_object("spinbutton_port")
        username_entry = self.builder.get_object("entry_username")
        password_entry = self.builder.get_object("entry_password")
        button_addhost_save = self.builder.get_object("button_addhost_save")
        button_addhost_save.hide()
        button_addhost_add = self.builder.get_object("button_addhost_add")
        button_addhost_add.show()
        response = dialog.run()
        if response == 1:
            username = username_entry.get_text()
            password = password_entry.get_text()
            hostname = hostname_entry.get_text()

            if (not password and not username or username == "localclient") and hostname in ["127.0.0.1", "localhost"]:
                username, password = get_localhost_auth()

            # We add the host
            try:
                self.add_host(hostname, port_spinbutton.get_value_as_int(),
                              username, password)
            except Exception as ex:
                ErrorDialog(_("Error Adding Host"), ex).run()

        username_entry.set_text("")
        password_entry.set_text("")
        hostname_entry.set_text("")
        port_spinbutton.set_value(58846)
        dialog.hide()

    def on_button_edithost_clicked(self, widget=None):
        log.debug("on_button_edithost_clicked")
        model, row = self.hostlist.get_selection().get_selected()
        status = model[row][HOSTLIST_COL_STATUS]
        if status == "Connected":
            def on_disconnect(reason):
                self.__update_list()
            client.disconnect().addCallback(on_disconnect)
            return

        dialog = self.builder.get_object("addhost_dialog")
        dialog.set_transient_for(self.connection_manager)
        dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        hostname_entry = self.builder.get_object("entry_hostname")
        port_spinbutton = self.builder.get_object("spinbutton_port")
        username_entry = self.builder.get_object("entry_username")
        password_entry = self.builder.get_object("entry_password")
        button_addhost_save = self.builder.get_object("button_addhost_save")
        button_addhost_save.show()
        button_addhost_add = self.builder.get_object("button_addhost_add")
        button_addhost_add.hide()

        username_entry.set_text(self.liststore[row][HOSTLIST_COL_USER])
        password_entry.set_text(self.liststore[row][HOSTLIST_COL_PASS])
        hostname_entry.set_text(self.liststore[row][HOSTLIST_COL_HOST])
        port_spinbutton.set_value(self.liststore[row][HOSTLIST_COL_PORT])

        response = dialog.run()

        if response == 2:
            username = username_entry.get_text()
            password = password_entry.get_text()
            hostname = hostname_entry.get_text()

            if (not password and not username or username == "localclient") and hostname in ["127.0.0.1", "localhost"]:
                username, password = get_localhost_auth()

            self.liststore[row][HOSTLIST_COL_HOST] = hostname
            self.liststore[row][HOSTLIST_COL_PORT] = port_spinbutton.get_value_as_int()
            self.liststore[row][HOSTLIST_COL_USER] = username
            self.liststore[row][HOSTLIST_COL_PASS] = password
            self.liststore[row][HOSTLIST_COL_STATUS] = "Offline"

        # Save the host list to file
        self.__save_hostlist()

        # Update the status of the hosts
        self.__update_list()

        username_entry.set_text("")
        password_entry.set_text("")
        hostname_entry.set_text("")
        port_spinbutton.set_value(58846)
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
            self.add_host(DEFAULT_HOST, DEFAULT_PORT, *get_localhost_auth())
            # ..and start the daemon.
            self.start_daemon(
                DEFAULT_PORT, get_config_dir()
            )
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
                reactor.callLater(0.8, self.__update_list)
            if client.connected() and client.connection_info() == (host, port, user):
                client.daemon.shutdown().addCallback(on_daemon_shutdown)
            elif user and password:
                # Create a new client instance
                c = Client()

                def on_connect(d, c):
                    log.debug("on_connect")
                    c.daemon.shutdown().addCallback(on_daemon_shutdown)

                c.connect(host, port, user, password).addCallback(on_connect, c)

        elif status == "Offline":
            self.start_daemon(port, get_config_dir())
            reactor.callLater(0.8, self.__update_list)

    def on_button_refresh_clicked(self, widget):
        self.__update_list()

    def on_hostlist_row_activated(self, tree, path, view_column):
        self.on_button_connect_clicked()

    def on_hostlist_selection_changed(self, treeselection):
        self.__update_buttons()

    def on_askpassword_dialog_connect_button_clicked(self, widget):
        log.debug("on on_askpassword_dialog_connect_button_clicked")
        self.askpassword_dialog.response(Gtk.ResponseType.OK)

    def on_askpassword_dialog_entry_activate(self, entry):
        self.askpassword_dialog.response(Gtk.ResponseType.OK)

    def __migrate_config_1_to_2(self, config):
        localclient_username, localclient_password = get_localhost_auth()
        if not localclient_username:
            # Nothing to do here, there's no auth file
            return
        for idx, (_, host, _, username, _) in enumerate(config["hosts"][:]):
            if host in ("127.0.0.1", "localhost"):
                if not username:
                    config["hosts"][idx][3] = localclient_username
                    config["hosts"][idx][4] = localclient_password
        return config
