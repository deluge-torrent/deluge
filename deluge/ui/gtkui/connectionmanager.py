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

from gi.repository import Gtk
from twisted.internet import defer, reactor

import deluge.component as component
from deluge.common import resource_filename, windows_check
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import AuthenticationRequired, BadLoginError, IncompatibleClient
from deluge.ui.client import Client, client
from deluge.ui.gtkui.common import get_clipboard_text
from deluge.ui.gtkui.dialogs import AuthenticationDialog, ErrorDialog
from deluge.ui.hostlist import DEFAULT_PORT, LOCALHOST, HostList

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

HOSTLIST_PIXBUFS = [
    # This is populated in ConnectionManager.show
]

HOSTLIST_STATUS = [
    'Offline',
    'Online',
    'Connected',
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
        self.hostlist = HostList()
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

    # Public methods
    def show(self):
        """Show the ConnectionManager dialog."""
        self.builder = Gtk.Builder()
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'connection_manager.ui'),
        ))
        self.connection_manager = self.builder.get_object('connection_manager')
        self.connection_manager.set_transient_for(component.get('MainWindow').window)

        # Create status pixbufs
        if not HOSTLIST_PIXBUFS:
            for stock_id in (Gtk.STOCK_NO, Gtk.STOCK_YES, Gtk.STOCK_CONNECT):
                HOSTLIST_PIXBUFS.append(
                    self.connection_manager.render_icon(stock_id, Gtk.ICON_SIZE_MENU),
                )

        # Setup the hostlist liststore and treeview
        self.treeview = self.builder.get_object('treeview_hostlist')
        self.liststore = self.builder.get_object('liststore_hostlist')

        render = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn(_('Status'), render)
        column.set_cell_data_func(render, cell_render_status, HOSTLIST_COL_STATUS)
        self.treeview.append_column(column)

        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Host'), render, text=HOSTLIST_COL_HOST)
        host_data = (HOSTLIST_COL_HOST, HOSTLIST_COL_PORT, HOSTLIST_COL_USER)
        column.set_cell_data_func(render, cell_render_host, host_data)
        column.set_expand(True)
        self.treeview.append_column(column)

        column = gtk.TreeViewColumn(_('Version'), gtk.CellRendererText(), text=HOSTLIST_COL_VERSION)
        self.treeview.append_column(column)

        # Load any saved host entries
        self._load_liststore()
        # Set widgets to values from gtkui config.
        self._load_widget_config()
        self._update_widget_buttons()

        # Connect the signals to the handlers
        self.builder.connect_signals(self)
        self.treeview.get_selection().connect('changed', self.on_hostlist_selection_changed)

        # Set running True before update status call.
        self.running = True

        if windows_check():
            # Call to simulate() required to workaround showing daemon status (see #2813)
            reactor.simulate()
        self._update_host_status()

        # Trigger the on_selection_changed code and select the first host if possible
        self.treeview.get_selection().unselect_all()
        if len(self.liststore):
            self.treeview.get_selection().select_path(0)

        # Run the dialog
        self.connection_manager.run()

        # Dialog closed so cleanup.
        self.running = False
        self.connection_manager.destroy()
        del self.builder
        del self.connection_manager
        del self.liststore
        del self.treeview

    def _load_liststore(self):
        """Load saved host entries"""
        for host_entry in self.hostlist.get_hosts_info():
            host_id, host, port, username = host_entry
            self.liststore.append([host_id, host, port, username, '', '', ''])

    def _load_widget_config(self):
        """Set the widgets to show the correct options from the config."""
        self.builder.get_object('chk_autoconnect').set_active(
            self.gtkui_config['autoconnect'],
        )
        self.builder.get_object('chk_autostart').set_active(
            self.gtkui_config['autostart_localhost'],
        )
        self.builder.get_object('chk_donotshow').set_active(
            not self.gtkui_config['show_connection_manager_on_start'],
        )

    def _update_host_status(self):
        """Updates the host status"""
        if not self.running:
            # Callback likely fired after the window closed.
            return

        def on_host_status(status_info, row):
            if self.running and row:
                row[HOSTLIST_COL_STATUS] = status_info[1]
                row[HOSTLIST_COL_VERSION] = status_info[2]
                self._update_widget_buttons()

        deferreds = []
        for row in self.liststore:
            host_id = row[HOSTLIST_COL_ID]
            d = self.hostlist.get_host_status(host_id)
            try:
                d.addCallback(on_host_status, row)
            except AttributeError:
                on_host_status(d, row)
            else:
                deferreds.append(d)
        defer.DeferredList(deferreds)

    def _update_widget_buttons(self):
        """Updates the dialog button states."""
        self.builder.get_object('button_refresh').set_sensitive(len(self.liststore))
        self.builder.get_object('button_startdaemon').set_sensitive(False)
        self.builder.get_object('button_connect').set_sensitive(False)
        self.builder.get_object('button_connect').set_label(_('C_onnect'))
        self.builder.get_object('button_edithost').set_sensitive(False)
        self.builder.get_object('button_removehost').set_sensitive(False)
        self.builder.get_object('button_startdaemon').set_sensitive(False)
        self.builder.get_object('image_startdaemon').set_from_stock(
            gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU,
        )
        self.builder.get_object('label_startdaemon').set_text_with_mnemonic('_Start Daemon')

        model, row = self.treeview.get_selection().get_selected()
        if row:
            self.builder.get_object('button_edithost').set_sensitive(True)
            self.builder.get_object('button_removehost').set_sensitive(True)
        else:
            return

        # Get selected host info.
        __, host, port, __, __, status, __ = model[row]
        try:
            gethostbyname(host)
        except gaierror as ex:
            log.error('Error resolving host %s to ip: %s', row[HOSTLIST_COL_HOST], ex.args[1])
            self.builder.get_object('button_connect').set_sensitive(False)
            return

        log.debug('Host Status: %s, %s', host, status)

        # Check to see if the host is online
        if status == 'Connected' or status == 'Online':
            self.builder.get_object('button_connect').set_sensitive(True)
            self.builder.get_object('image_startdaemon').set_from_stock(
                Gtk.STOCK_STOP, Gtk.ICON_SIZE_MENU,
            )
            self.builder.get_object('label_startdaemon').set_text_with_mnemonic(_('_Stop Daemon'))
            self.builder.get_object('button_startdaemon').set_sensitive(False)
            if status == 'Connected':
                # Display a disconnect button if we're connected to this host
                self.builder.get_object('button_connect').set_label(_('_Disconnect'))
                self.builder.get_object('button_removehost').set_sensitive(False)
                # Currently can only stop daemon when connected to it
                self.builder.get_object('button_startdaemon').set_sensitive(True)
        elif host in LOCALHOST:
            # If localhost we can start the dameon.
            self.builder.get_object('button_startdaemon').set_sensitive(True)

    def start_daemon(self, port, config):
        """Attempts to start local daemon process and will show an ErrorDialog if not.

        Args:
            port (int): Port for the daemon to listen on.
            config (str): Config path to pass to daemon.

        Returns:
            bool: True is successfully started the daemon, False otherwise.

        """
        if client.start_daemon(port, config):
            log.debug('Localhost daemon started')
            reactor.callLater(1, self._update_host_status)
            return True
        else:
            ErrorDialog(
                _('Unable to start daemon!'),
                _('Check deluged package is installed and logs for further details'),
            ).run()
            return False

    # Signal handlers
    def _connect(self, host_id, username=None, password=None, try_counter=0):
        def do_connect(result, username=None, password=None, *args):
            log.debug('Attempting to connect to daemon...')
            for host_entry in self.hostlist.config['hosts']:
                if host_entry[0] == host_id:
                    __, host, port, host_user, host_pass = host_entry

            username = username if username else host_user
            password = password if password else host_pass

            d = client.connect(host, port, username, password)
            d.addCallback(self._on_connect, host_id)
            d.addErrback(self._on_connect_fail, host_id, try_counter)
            return d

        if client.connected():
            return client.disconnect().addCallback(do_connect, username, password)
        else:
            return do_connect(None, username, password)

    def _on_connect(self, daemon_info, host_id):
        log.debug('Connected to daemon: %s', host_id)
        if self.gtkui_config['autoconnect']:
            self.gtkui_config['autoconnect_host_id'] = host_id
        if self.running:
            # When connected to a client, and then trying to connect to another,
            # this component will be stopped(while the connect deferred is
            # running), so, self.connection_manager will be deleted.
            # If that's not the case, close the dialog.
            self.connection_manager.response(Gtk.ResponseType.OK)
        component.start()

    def _on_connect_fail(self, reason, host_id, try_counter):
        log.debug('Failed to connect: %s', reason.value)

        if reason.check(AuthenticationRequired, BadLoginError):
            log.debug('PasswordRequired exception')
            dialog = AuthenticationDialog(reason.value.message, reason.value.username)

            def dialog_finished(response_id):
                if response_id == Gtk.RESPONSE_OK:
                    self._connect(host_id, dialog.get_username(), dialog.get_password())
            return dialog.run().addCallback(dialog_finished)

        elif reason.check(IncompatibleClient):
            return ErrorDialog(_('Incompatible Client'), reason.value.message).run()

        if try_counter:
            log.info('Retrying connection.. Retries left: %s', try_counter)
            return reactor.callLater(0.5, self._connect, host_id, try_counter=try_counter - 1)

        msg = str(reason.value)
        if not self.gtkui_config['autostart_localhost']:
            msg += '\n' + _(
                'Auto-starting the daemon locally is not enabled. '
                'See "Options" on the "Connection Manager".',
            )
        ErrorDialog(_('Failed To Connect'), msg).run()

    def on_button_connect_clicked(self, widget=None):
        """Button handler for connect to or disconnect from daemon."""
        model, row = self.treeview.get_selection().get_selected()
        if not row:
            return

        host_id, host, port, __, __, status, __ = model[row]
        # If status is connected then connect button disconnects instead.
        if status == 'Connected':
            def on_disconnect(reason):
                self._update_host_status()
            return client.disconnect().addCallback(on_disconnect)

        try_counter = 0
        auto_start = self.builder.get_object('chk_autostart').get_active()
        if auto_start and host in LOCALHOST and status == 'Offline':
            # Start the local daemon and then connect with retries set.
            if self.start_daemon(port, get_config_dir()):
                try_counter = 6
            else:
                # Don't attempt to connect to offline daemon.
                return

        self._connect(host_id, try_counter=try_counter)

    def on_button_close_clicked(self, widget):
        self.connection_manager.response(Gtk.ResponseType.CLOSE)

    def _run_addhost_dialog(self, edit_host_info=None):
        """Create and runs the add host dialog.

        Supplying edit_host_info changes the dialog to an edit dialog.

        Args:
            edit_host_info (list): A list of (host, port, user, pass) to edit.

        Returns:
            list: The new host info values (host, port, user, pass).

        """
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'connection_manager.addhost.ui'),
        ))
        dialog = self.builder.get_object('addhost_dialog')
        dialog.set_transient_for(self.connection_manager)
        hostname_entry = self.builder.get_object('entry_hostname')
        port_spinbutton = self.builder.get_object('spinbutton_port')
        username_entry = self.builder.get_object('entry_username')
        password_entry = self.builder.get_object('entry_password')

        if edit_host_info:
            dialog.set_title(_('Edit Host'))
            hostname_entry.set_text(edit_host_info[0])
            port_spinbutton.set_value(edit_host_info[1])
            username_entry.set_text(edit_host_info[2])
            password_entry.set_text(edit_host_info[3])

        response = dialog.run()
        new_host_info = []
        if response:
            new_host_info.append(hostname_entry.get_text())
            new_host_info.append(port_spinbutton.get_value_as_int())
            new_host_info.append(username_entry.get_text())
            new_host_info.append(password_entry.get_text())

        dialog.destroy()
        return new_host_info

    def on_button_addhost_clicked(self, widget):
        log.debug('on_button_addhost_clicked')
        host_info = self._run_addhost_dialog()
        if host_info:
            hostname, port, username, password = host_info
            try:
                host_id = self.hostlist.add_host(hostname, port, username, password)
            except ValueError as ex:
                ErrorDialog(_('Error Adding Host'), ex).run()
            else:
                self.liststore.append([host_id, hostname, port, username, password, 'Offline', ''])
                self._update_host_status()

    def on_button_edithost_clicked(self, widget=None):
        log.debug('on_button_edithost_clicked')
        model, row = self.treeview.get_selection().get_selected()
        status = model[row][HOSTLIST_COL_STATUS]
        host_id = model[row][HOSTLIST_COL_ID]

        if status == 'Connected':
            def on_disconnect(reason):
                self._update_host_status()
            client.disconnect().addCallback(on_disconnect)
            return

        host_info = [
            self.liststore[row][HOSTLIST_COL_HOST],
            self.liststore[row][HOSTLIST_COL_PORT],
            self.liststore[row][HOSTLIST_COL_USER],
            self.liststore[row][HOSTLIST_COL_PASS],
        ]
        new_host_info = self._run_addhost_dialog(edit_host_info=host_info)
        if new_host_info:
            hostname, port, username, password = new_host_info
            try:
                self.hostlist.update_host(host_id, hostname, port, username, password)
            except ValueError as ex:
                ErrorDialog(_('Error Updating Host'), ex).run()
            else:
                self.liststore[row] = host_id, hostname, port, username, password, '', ''
                self._update_host_status()

    def on_button_removehost_clicked(self, widget):
        log.debug('on_button_removehost_clicked')
        # Get the selected rows
        model, row = self.treeview.get_selection().get_selected()
        self.hostlist.remove_host(model[row][HOSTLIST_COL_ID])
        self.liststore.remove(row)
        # Update the hostlist
        self._update_host_status()

    def on_button_startdaemon_clicked(self, widget):
        log.debug('on_button_startdaemon_clicked')
        if not self.liststore.iter_n_children(None):
            # There is nothing in the list, so lets create a localhost entry
            try:
                self.hostlist.add_default_host()
            except ValueError as ex:
                log.error('Error adding default host: %s', ex)
            else:
                self.start_daemon(DEFAULT_PORT, get_config_dir())
            finally:
                return

        paths = self.treeview.get_selection().get_selected_rows()[1]
        if len(paths):
            __, host, port, user, password, status, __ = self.liststore[paths[0]]
        else:
            return

        if host not in LOCALHOST:
            return

        def on_daemon_status_change(result):
            """Daemon start/stop callback"""
            reactor.callLater(0.7, self._update_host_status)

        if status in ('Online', 'Connected'):
            # Button will stop the daemon if status is online or connected.
            def on_connect(d, c):
                """Client callback to call daemon shutdown"""
                c.daemon.shutdown().addCallback(on_daemon_status_change)

            if client.connected() and (host, port, user) == client.connection_info():
                client.daemon.shutdown().addCallback(on_daemon_status_change)
            elif user and password:
                c = Client()
                c.connect(host, port, user, password).addCallback(on_connect, c)
        else:
            # Otherwise button will start the daemon.
            self.start_daemon(port, get_config_dir())

    def on_button_refresh_clicked(self, widget):
        self._update_host_status()

    def on_hostlist_row_activated(self, tree, path, view_column):
        self.on_button_connect_clicked()

    def on_hostlist_selection_changed(self, treeselection):
        self._update_widget_buttons()

    def on_chk_toggled(self, widget):
        self.gtkui_config['autoconnect'] = self.builder.get_object('chk_autoconnect').get_active()
        self.gtkui_config['autostart_localhost'] = self.builder.get_object('chk_autostart').get_active()
        self.gtkui_config['show_connection_manager_on_start'] = not self.builder.get_object(
            'chk_donotshow',
        ).get_active()

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
