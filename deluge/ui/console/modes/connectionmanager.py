# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.decorators import overrides
from deluge.ui.console.modes.basemode import BaseMode
from deluge.ui.console.utils.curses_util import is_printable_chr
from deluge.ui.console.widgets.popup import InputPopup, PopupsHandler, SelectablePopup
from deluge.ui.hostlist import HostList

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


class ConnectionManager(BaseMode, PopupsHandler):
    def __init__(self, stdscr, encoding=None):
        PopupsHandler.__init__(self)
        self.statuses = {}
        self.all_torrents = None
        self.hostlist = HostList()
        BaseMode.__init__(self, stdscr, encoding=encoding)
        self.update_hosts_status()

    def update_select_host_popup(self):
        selected_index = self.popup.current_selection() if self.popup else None

        popup = SelectablePopup(
            self,
            _('Select Host'),
            self._host_selected,
            border_off_west=1,
            active_wrap=True,
        )
        popup.add_header(
            "{!white,black,bold!}'Q'=%s, 'a'=%s, 'D'=%s"
            % (_('Quit'), _('Add Host'), _('Delete Host')),
            space_below=True,
        )
        self.push_popup(popup, clear=True)

        for host_entry in self.hostlist.get_hosts_info():
            host_id, hostname, port, user = host_entry
            args = {'data': host_id, 'foreground': 'red'}
            state = 'Offline'
            if host_id in self.statuses:
                state = 'Online'
                args.update({'data': self.statuses[host_id], 'foreground': 'green'})
            host_str = '%s:%d [%s]' % (hostname, port, state)
            self.popup.add_line(
                host_id, host_str, selectable=True, use_underline=True, **args
            )

        if selected_index:
            self.popup.set_selection(selected_index)
        self.inlist = True
        self.refresh()

    def update_hosts_status(self):
        def on_host_status(status_info):
            self.statuses[status_info[0]] = status_info
            self.update_select_host_popup()

        for host_entry in self.hostlist.get_hosts_info():
            self.hostlist.get_host_status(host_entry[0]).addCallback(on_host_status)

    def _on_connected(self, result):
        def on_console_start(result):
            component.get('ConsoleUI').set_mode('TorrentList')

        d = component.get('ConsoleUI').start_console()
        d.addCallback(on_console_start)

    def _on_connect_fail(self, result):
        self.report_message('Failed to connect!', result)
        self.refresh()
        if hasattr(result, 'getTraceback'):
            log.exception(result)

    def _host_selected(self, selected_host, *args, **kwargs):
        if selected_host in self.statuses:
            d = self.hostlist.connect_host(selected_host)
            d.addCallback(self._on_connected)
            d.addErrback(self._on_connect_fail)

    def _do_add(self, result, **kwargs):
        if not result or kwargs.get('close', False):
            self.pop_popup()
        else:
            self.add_host(
                result['hostname']['value'],
                result['port']['value'],
                result['username']['value'],
                result['password']['value'],
            )

    def add_popup(self):
        self.inlist = False
        popup = InputPopup(
            self,
            _('Add Host (Up & Down arrows to navigate, Esc to cancel)'),
            border_off_north=1,
            border_off_east=1,
            close_cb=self._do_add,
        )
        popup.add_text_input('hostname', _('Hostname:'))
        popup.add_text_input('port', _('Port:'))
        popup.add_text_input('username', _('Username:'))
        popup.add_text_input('password', _('Password:'))
        self.push_popup(popup, clear=True)
        self.refresh()

    def add_host(self, hostname, port, username, password):
        log.info('Adding host: %s', hostname)
        try:
            self.hostlist.add_host(hostname, port, username, password)
        except ValueError as ex:
            self.report_message(_('Error adding host'), '%s: %s' % (hostname, ex))
        else:
            self.update_select_host_popup()

    def delete_host(self, host_id):
        log.info('Deleting host: %s', host_id)
        self.hostlist.remove_host(host_id)
        self.update_select_host_popup()

    @overrides(component.Component)
    def start(self):
        self.refresh()

    @overrides(component.Component)
    def update(self):
        self.update_hosts_status()

    @overrides(BaseMode)
    def pause(self):
        self.pop_popup()
        BaseMode.pause(self)

    @overrides(BaseMode)
    def resume(self):
        BaseMode.resume(self)
        self.refresh()

    @overrides(BaseMode)
    def refresh(self):
        if self.mode_paused():
            return

        self.stdscr.erase()
        self.draw_statusbars()
        self.stdscr.noutrefresh()

        if not self.popup:
            self.update_select_host_popup()

        self.popup.refresh()
        curses.doupdate()

    @overrides(BaseMode)
    def on_resize(self, rows, cols):
        BaseMode.on_resize(self, rows, cols)

        if self.popup:
            self.popup.handle_resize()

        self.stdscr.erase()
        self.refresh()

    @overrides(BaseMode)
    def read_input(self):
        c = self.stdscr.getch()

        if is_printable_chr(c):
            if chr(c) == 'Q':
                component.get('ConsoleUI').quit()
            elif self.inlist:
                if chr(c) == 'q':
                    return
                elif chr(c) == 'D':
                    host_id = self.popup.current_selection()[1]
                    self.delete_host(host_id)
                    return
                elif chr(c) == 'a':
                    self.add_popup()
                    return

        if self.popup:
            if self.popup.handle_read(c) and self.popup.closed():
                self.pop_popup()
            self.refresh()
