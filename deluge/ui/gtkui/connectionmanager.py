# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
from socket import gaierror, gethostbyname

import gtk
from twisted.internet import reactor

import deluge.component as component
from deluge.common import resource_filename
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import AuthenticationRequired, BadLoginError, IncompatibleClient
from deluge.ui.client import Client, client
from deluge.ui.gtkui.common import get_clipboard_text, get_deluge_icon
from deluge.ui.gtkui.dialogs import AuthenticationDialog, ErrorDialog
from deluge.ui.hostlist import DEFAULT_PORT, HostList

try:
    from urllib.parse import urlparse
except ImportError:
    # PY2 fallback
    from urlparse import urlparse  # pylint: disable=ungrouped-imports

log = logging.getLogger(__name__)

HOSTLIST_COL_ID = 0
HOSTLIST_COL_HOST = 1
HOSTLIST_COL_PORT = 2
HOSTLIST_COL_USER = 3
HOSTLIST_COL_PASS = 4
HOSTLIST_COL_STATUS = 5
HOSTLIST_COL_VERSION = 6

LOCALHOST = ('127.0.0.1', 'localhost')

HOSTLIST_PIXBUFS = [
    # This is populated in ConnectionManager.show
]

HOSTLIST_STATUS = [
    'Offline',
    'Online',
    'Connected'
]


def cell_render_host(column, cell, model, row, data):
    host, port, username = model.get(row, *data)
    text = host + ':' + str(port)
    if username:
        text = username + '@' + text
    cell.set_property('text', text)


def cell_render_status(column, cell, model, row, data):
    status = model[row][data]
    status = status if status else 'Offline'
    pixbuf = None
    if status in HOSTLIST_STATUS:
        pixbuf = HOSTLIST_PIXBUFS[HOSTLIST_STATUS.index(status)]

    cell.set_property('pixbuf', pixbuf)


class ConnectionManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'ConnectionManager')
        self.gtkui_config = ConfigManager('gtkui.conf')

        self.running = False

    # Component overrides
    def start(self):
        pass

    def stop(self):
        # Close this dialog when we are shutting down
        if self.running:
            self.connection_manager.response(gtk.RESPONSE_CLOSE)

    def shutdown(self):
        pass

    # Public methods
    def show(self):
        """
        Show the ConnectionManager dialog.
        """
        # Get the gtk builder file for the connection manager
        self.builder = gtk.Builder()
        # The main dialog
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'connection_manager.ui')))
        # The add host dialog
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'connection_manager.addhost.ui')))
        # The ask password dialog
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'connection_manager.askpassword.ui')))

        # Setup the ConnectionManager dialog
        self.connection_manager = self.builder.get_object('connection_manager')
        self.connection_manager.set_transient_for(component.get('MainWindow').window)

        self.askpassword_dialog = self.builder.get_object('askpassword_dialog')
        self.askpassword_dialog.set_transient_for(self.connection_manager)
        self.askpassword_dialog.set_icon(get_deluge_icon())
        self.askpassword_dialog_entry = self.builder.get_object('askpassword_dialog_entry')

        self.hostlist_config = HostList()
        self.hostlist = self.builder.get_object('hostlist')

        # Create status pixbufs
        if not HOSTLIST_PIXBUFS:
            for stock_id in (gtk.STOCK_NO, gtk.STOCK_YES, gtk.STOCK_CONNECT):
                HOSTLIST_PIXBUFS.append(
                    self.connection_manager.render_icon(
                        stock_id, gtk.ICON_SIZE_MENU
                    )
                )

        # Create the host list gtkliststore
        # id-hash, hostname, port, username, password, status, version
        self.liststore = gtk.ListStore(str, str, int, str, str, str, str)

        # Setup host list treeview
        self.hostlist.set_model(self.liststore)
        render = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn(_('Status'), render)
        column.set_cell_data_func(render, cell_render_status, HOSTLIST_COL_STATUS)
        self.hostlist.append_column(column)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Host'), render, text=HOSTLIST_COL_HOST)
        column.set_cell_data_func(
            render, cell_render_host, (HOSTLIST_COL_HOST, HOSTLIST_COL_PORT, HOSTLIST_COL_USER))
        column.set_expand(True)
        self.hostlist.append_column(column)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Version'), render, text=HOSTLIST_COL_VERSION)
        self.hostlist.append_column(column)

        # Connect the signals to the handlers
        self.builder.connect_signals(self)
        self.hostlist.get_selection().connect(
            'changed', self.on_hostlist_selection_changed
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
            self.hostlist.get_selection().select_path(0)

        # Run the dialog
        self.connection_manager.run()
        self.running = False

        # Save the toggle options
        self.__save_options()

        self.connection_manager.destroy()
        del self.builder
        del self.connection_manager
        del self.liststore
        del self.hostlist

    def on_entry_host_paste_clipboard(self, widget):
        text = get_clipboard_text()
        log.debug('on_entry_proxy_host_paste-clipboard: got paste: %s', text)
        text = text if '//' in text else '//' + text
        parsed = urlparse(text)
        if parsed.hostname:
            widget.set_text(parsed.hostname)
            widget.emit_stop_by_name('paste-clipboard')
        if parsed.port:
            self.builder.get_object('spinbutton_port').set_value(parsed.port)
        if parsed.username:
            self.builder.get_object('entry_username').set_text(parsed.username)
        if parsed.password:
            self.builder.get_object('entry_password').set_text(parsed.password)

    def __load_hostlist(self):
        """Load saved host entries"""
        status = version = ''
        for host_entry in self.hostlist_config.get_hosts_info2():
            host_id, host, port, username, password = host_entry
            self.liststore.append([host_id, host, port, username, password, status, version])

    def __get_host_row(self, host_id):
        """Get the row in the liststore for the host_id.

        Args:
            host_id (str): The host id.

        Returns:
            list: The listsrore row with host details.

        """
        for row in self.liststore:
            if host_id == row[HOSTLIST_COL_ID]:
                return row
        return None

    def __update_list(self):
        """Updates the host status"""
        if not hasattr(self, 'liststore'):
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
                    row[HOSTLIST_COL_STATUS] = 'Online'
                    row[HOSTLIST_COL_VERSION] = info
                    self.__update_buttons()
                c.disconnect()

            def on_info_fail(reason, c):
                if not self.running:
                    return
                if row:
                    row[HOSTLIST_COL_STATUS] = 'Offline'
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
                row[HOSTLIST_COL_STATUS] = 'Offline'
                row[HOSTLIST_COL_VERSION] = ''
                self.__update_buttons()

        for row in self.liststore:
            host_id = row[HOSTLIST_COL_ID]
            host = row[HOSTLIST_COL_HOST]
            port = row[HOSTLIST_COL_PORT]
            user = row[HOSTLIST_COL_USER]

            try:
                ip = gethostbyname(host)
            except gaierror as ex:
                log.error('Error resolving host %s to ip: %s', host, ex.args[1])
                continue

            host_info = (ip, port, 'localclient' if not user and host in LOCALHOST else user)
            if client.connected() and host_info == client.connection_info():
                def on_info(info, row):
                    if not self.running:
                        return
                    log.debug('Client connected, query info: %s', info)
                    row[HOSTLIST_COL_VERSION] = info
                    self.__update_buttons()

                row[HOSTLIST_COL_STATUS] = 'Connected'
                log.debug('Query daemon info')
                client.daemon.info().addCallback(on_info, row)
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
        self.builder.get_object('chk_autoconnect').set_active(
            self.gtkui_config['autoconnect'])
        self.builder.get_object('chk_autostart').set_active(
            self.gtkui_config['autostart_localhost'])
        self.builder.get_object('chk_donotshow').set_active(
            not self.gtkui_config['show_connection_manager_on_start'])

    def __save_options(self):
        """
        Set options in gtkui config from the toggle buttons.
        """
        self.gtkui_config['autoconnect'] = self.builder.get_object('chk_autoconnect').get_active()
        self.gtkui_config['autostart_localhost'] = self.builder.get_object('chk_autostart').get_active()
        self.gtkui_config['show_connection_manager_on_start'] = not self.builder.get_object(
            'chk_donotshow').get_active()

    def __update_buttons(self):
        """Updates the buttons states."""
        if len(self.liststore) == 0:
            # There is nothing in the list
            self.builder.get_object('button_startdaemon').set_sensitive(False)
            self.builder.get_object('button_connect').set_sensitive(False)
            self.builder.get_object('button_removehost').set_sensitive(False)
            self.builder.get_object('image_startdaemon').set_from_stock(
                gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)
            self.builder.get_object('label_startdaemon').set_text_with_mnemonic('_Start Daemon')

        model, row = self.hostlist.get_selection().get_selected()
        if not row:
            self.builder.get_object('button_edithost').set_sensitive(False)
            return

        self.builder.get_object('button_edithost').set_sensitive(True)
        self.builder.get_object('button_startdaemon').set_sensitive(True)
        self.builder.get_object('button_connect').set_sensitive(True)
        self.builder.get_object('button_removehost').set_sensitive(True)

        # Get some values about the selected host
        __, host, port, user, password, status, __ = model[row]

        try:
            ip = gethostbyname(host)
        except gaierror as ex:
            log.error('Error resolving host %s to ip: %s', row[HOSTLIST_COL_HOST], ex.args[1])
            return

        log.debug('Status: %s', status)
        # Check to see if we have a localhost entry selected
        localhost = host in LOCALHOST

        # See if this is the currently connected host
        if status == 'Connected':
            # Display a disconnect button if we're connected to this host
            self.builder.get_object('button_connect').set_label('gtk-disconnect')
            self.builder.get_object('button_removehost').set_sensitive(False)
        else:
            self.builder.get_object('button_connect').set_label('gtk-connect')
            if status == 'Offline' and not localhost:
                self.builder.get_object('button_connect').set_sensitive(False)

        # Check to see if the host is online
        if status == 'Connected' or status == 'Online':
            self.builder.get_object('image_startdaemon').set_from_stock(
                gtk.STOCK_STOP, gtk.ICON_SIZE_MENU)
            self.builder.get_object('label_startdaemon').set_text_with_mnemonic(_('_Stop Daemon'))

        # Update the start daemon button if the selected host is localhost
        if localhost and status == 'Offline':
            # The localhost is not online
            self.builder.get_object('image_startdaemon').set_from_stock(
                gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)
            self.builder.get_object('label_startdaemon').set_text_with_mnemonic(_('_Start Daemon'))

        if client.connected() and (ip, port, user) == client.connection_info():
            # If we're connected, we can stop the dameon
            self.builder.get_object('button_startdaemon').set_sensitive(True)
        elif user and password:
            # In this case we also have all the info to shutdown the daemon
            self.builder.get_object('button_startdaemon').set_sensitive(True)
        else:
            # Can't stop non localhost daemons, specially without the necessary info
            self.builder.get_object('button_startdaemon').set_sensitive(False)

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
                    _('Unable to start daemon!'),
                    _('Deluge cannot find the `deluged` executable, check that '
                      'the deluged package is installed, or added to your PATH.')).run()

                return False
            else:
                raise ex
        except Exception:
            import traceback
            import sys
            tb = sys.exc_info()
            ErrorDialog(
                _('Unable to start daemon!'),
                _('Please examine the details for more information.'),
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
        if self.gtkui_config['autoconnect']:
            self.gtkui_config['autoconnect_host_id'] = host_id
        if self.running:
            # When connected to a client, and then trying to connect to another,
            # this component will be stopped(while the connect deferred is
            # running), so, self.connection_manager will be deleted.
            # If that's not the case, close the dialog.
            self.connection_manager.response(gtk.RESPONSE_OK)
        component.start()

    def __on_connected_failed(self, reason, host_id, host, port, user, password,
                              try_counter):
        log.debug('Failed to connect: %s', reason.value)

        if reason.check(AuthenticationRequired, BadLoginError):
            log.debug('PasswordRequired exception')
            dialog = AuthenticationDialog(reason.value.message, reason.value.username)

            def dialog_finished(response_id, host, port, user):
                if response_id == gtk.RESPONSE_OK:
                    self.__connect(host_id, host, port,
                                   user and user or dialog.get_username(),
                                   dialog.get_password())
            d = dialog.run().addCallback(dialog_finished, host, port, user)
            return d

        elif reason.trap(IncompatibleClient):
            return ErrorDialog(_('Incompatible Client'), reason.value.message).run()

        if try_counter:
            log.info('Retrying connection.. Retries left: %s', try_counter)
            return reactor.callLater(
                0.5, self.__connect, host_id, host, port, user, password,
                try_counter=try_counter - 1)

        msg = str(reason.value)
        if not self.builder.get_object('chk_autostart').get_active():
            msg += '\n' + _('Auto-starting the daemon locally is not enabled. '
                            'See "Options" on the "Connection Manager".')
        ErrorDialog(_('Failed To Connect'), msg).run()

    def on_button_connect_clicked(self, widget=None):
        model, row = self.hostlist.get_selection().get_selected()
        if not row:
            return

        status = model[row][HOSTLIST_COL_STATUS]

        # If status is connected then connect button disconnects instead.
        if status == 'Connected':
            def on_disconnect(reason):
                self.__update_list()
            client.disconnect().addCallback(on_disconnect)
            return

        host_id, host, port, user, password, __, __ = model[row]
        try_counter = 0
        auto_start = self.builder.get_object('chk_autostart').get_active()
        if status == 'Offline' and auto_start and host in LOCALHOST:
            if not self.start_daemon(port, get_config_dir()):
                log.debug('Failed to auto-start daemon')
                return
            try_counter = 6

        return self.__connect(host_id, host, port, user, password, try_counter=try_counter)

    def on_button_close_clicked(self, widget):
        self.connection_manager.response(gtk.RESPONSE_CLOSE)

    def on_button_addhost_clicked(self, widget):
        log.debug('on_button_addhost_clicked')
        dialog = self.builder.get_object('addhost_dialog')
        dialog.set_transient_for(self.connection_manager)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        hostname_entry = self.builder.get_object('entry_hostname')
        port_spinbutton = self.builder.get_object('spinbutton_port')
        username_entry = self.builder.get_object('entry_username')
        password_entry = self.builder.get_object('entry_password')
        button_addhost_save = self.builder.get_object('button_addhost_save')
        button_addhost_save.hide()
        button_addhost_add = self.builder.get_object('button_addhost_add')
        button_addhost_add.show()
        response = dialog.run()
        if response == 1:
            username = username_entry.get_text()
            password = password_entry.get_text()
            hostname = hostname_entry.get_text()
            port = port_spinbutton.get_value_as_int()

            try:
                host_id = self.hostlist_config.add_host(hostname, port, username, password)
            except ValueError as ex:
                ErrorDialog(_('Error Adding Host'), ex, parent=dialog).run()
            else:
                self.liststore.append([host_id, hostname, port, username, password, 'Offline', ''])

        # Update the status of the hosts
        self.__update_list()

        username_entry.set_text('')
        password_entry.set_text('')
        hostname_entry.set_text('')
        port_spinbutton.set_value(DEFAULT_PORT)
        dialog.hide()

    def on_button_edithost_clicked(self, widget=None):
        log.debug('on_button_edithost_clicked')
        model, row = self.hostlist.get_selection().get_selected()
        status = model[row][HOSTLIST_COL_STATUS]
        host_id = model[row][HOSTLIST_COL_ID]

        if status == 'Connected':
            def on_disconnect(reason):
                self.__update_list()
            client.disconnect().addCallback(on_disconnect)
            return

        dialog = self.builder.get_object('addhost_dialog')
        dialog.set_transient_for(self.connection_manager)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        hostname_entry = self.builder.get_object('entry_hostname')
        port_spinbutton = self.builder.get_object('spinbutton_port')
        username_entry = self.builder.get_object('entry_username')
        password_entry = self.builder.get_object('entry_password')
        button_addhost_save = self.builder.get_object('button_addhost_save')
        button_addhost_save.show()
        button_addhost_add = self.builder.get_object('button_addhost_add')
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
            port = port_spinbutton.get_value_as_int()

            try:
                self.hostlist_config.update_host(host_id, hostname, port, username, password)
            except ValueError as ex:
                ErrorDialog(_('Error Updating Host'), ex, parent=dialog).run()
            else:
                self.liststore[row] = host_id, hostname, port, username, password, '', ''

        # Update the status of the hosts
        self.__update_list()

        username_entry.set_text('')
        password_entry.set_text('')
        hostname_entry.set_text('')
        port_spinbutton.set_value(DEFAULT_PORT)
        dialog.hide()

    def on_button_removehost_clicked(self, widget):
        log.debug('on_button_removehost_clicked')
        # Get the selected rows
        model, row = self.hostlist.get_selection().get_selected()
        self.hostlist_config.remove_host(model[row][HOSTLIST_COL_ID])
        self.liststore.remove(row)
        # Update the hostlist
        self.__update_list()

    def on_button_startdaemon_clicked(self, widget):
        log.debug('on_button_startdaemon_clicked')
        if self.liststore.iter_n_children(None) < 1:
            # There is nothing in the list, so lets create a localhost entry
            try:
                self.hostlist_config.add_default_host()
            except ValueError as ex:
                log.error('Error adding default host: %s', ex)

            # ..and start the daemon.
            self.start_daemon(DEFAULT_PORT, get_config_dir())
            return

        paths = self.hostlist.get_selection().get_selected_rows()[1]
        if len(paths) < 1:
            return

        __, host, port, user, password, status, __ = self.liststore[paths[0]]

        if host not in LOCALHOST:
            return

        if status in ('Online', 'Connected'):
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
                    log.debug('on_connect')
                    c.daemon.shutdown().addCallback(on_daemon_shutdown)

                c.connect(host, port, user, password).addCallback(on_connect, c)

        elif status == 'Offline':
            self.start_daemon(port, get_config_dir())
            reactor.callLater(0.8, self.__update_list)

    def on_button_refresh_clicked(self, widget):
        self.__update_list()

    def on_hostlist_row_activated(self, tree, path, view_column):
        self.on_button_connect_clicked()

    def on_hostlist_selection_changed(self, treeselection):
        self.__update_buttons()

    def on_askpassword_dialog_connect_button_clicked(self, widget):
        log.debug('on on_askpassword_dialog_connect_button_clicked')
        self.askpassword_dialog.response(gtk.RESPONSE_OK)

    def on_askpassword_dialog_entry_activate(self, entry):
        self.askpassword_dialog.response(gtk.RESPONSE_OK)
