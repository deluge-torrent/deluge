# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import hashlib
import logging
import time

import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.decorators import overrides
from deluge.ui import common as uicommon
from deluge.ui.client import Client, client
from deluge.ui.console.modes.basemode import BaseMode
from deluge.ui.console.widgets.popup import InputPopup, PopupsHandler, SelectablePopup

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
        self.config = ConfigManager('hostlist.conf.1.2', uicommon.DEFAULT_HOSTS)
        self.update_hosts_status()
        BaseMode.__init__(self, stdscr, encoding=encoding)
        self.update_select_host_popup()

    def update_select_host_popup(self):
        selected_index = None
        if self.popup:
            selected_index = self.popup.current_selection()

        popup = SelectablePopup(self, _('Select Host'), self._host_selected, border_off_west=1, active_wrap=True)
        popup.add_header("{!white,black,bold!}'Q'=%s, 'a'=%s, 'D'=%s" %
                         (_('quit'), _('add new host'), _('delete host')),
                         space_below=True)
        self.push_popup(popup, clear=True)

        for host in self.config['hosts']:
            args = {'data': host[0], 'foreground': 'red'}
            state = 'Offline'
            if host[0] in self.statuses:
                state = 'Online'
                args.update({'data': self.statuses[host[0]], 'foreground': 'green'})
            host_str = '%s:%d [%s]' % (host[1], host[2], state)
            self.popup.add_line(host[0], host_str, selectable=True, use_underline=True, **args)

        if selected_index is not None:
            self.popup.set_selection(selected_index)
        self.inlist = True
        self.refresh()

    def update_hosts_status(self):
        """Updates the host status"""
        def on_connect(result, c, host_id):
            def on_info(info, c):
                self.statuses[host_id] = info
                self.update_select_host_popup()
                c.disconnect()

            def on_info_fail(reason, c):
                if host_id in self.statuses:
                    del self.statuses[host_id]
                c.disconnect()

            d = c.daemon.info()
            d.addCallback(on_info, c)
            d.addErrback(on_info_fail, c)

        def on_connect_failed(reason, host_id):
            if host_id in self.statuses:
                del self.statuses[host_id]
                self.update_select_host_popup()

        for host in self.config['hosts']:
            c = Client()
            hadr = host[1]
            port = host[2]
            user = host[3]
            password = host[4]
            log.debug('connect: hadr=%s, port=%s, user=%s, password=%s', hadr, port, user, password)
            d = c.connect(hadr, port, user, password)
            d.addCallback(on_connect, c, host[0])
            d.addErrback(on_connect_failed, host[0])

    def _on_connected(self, result):
        d = component.get('ConsoleUI').start_console()

        def on_console_start(result):
            component.get('ConsoleUI').set_mode('TorrentList')
        d.addCallback(on_console_start)

    def _on_connect_fail(self, result):
        self.report_message('Failed to connect!', result)
        self.refresh()
        if hasattr(result, 'getTraceback'):
            log.exception(result)

    def _host_selected(self, selected_host, *args, **kwargs):
        if selected_host not in self.statuses:
            return
        for host in self.config['hosts']:
            if host[0] == selected_host:
                d = client.connect(host[1], host[2], host[3], host[4])
                d.addCallback(self._on_connected)
                d.addErrback(self._on_connect_fail)
                return
        return False

    def _do_add(self, result, **kwargs):
        if not result or kwargs.get('close', False):
            self.pop_popup()
            return
        hostname = result['hostname']['value']
        try:
            port = int(result['port']['value'])
        except ValueError:
            self.report_message('Cannot add host', 'Invalid port.  Must be an integer')
            return
        username = result['username']['value']
        password = result['password']['value']
        for host in self.config['hosts']:
            if (host[1], host[2], host[3]) == (hostname, port, username):
                self.report_message('Cannot add host', 'Host already in list')
                return
        newid = hashlib.sha1(str(time.time())).hexdigest()
        self.config['hosts'].append((newid, hostname, port, username, password))
        self.config.save()
        self.update_select_host_popup()

    def add_popup(self):
        self.inlist = False
        popup = InputPopup(self, 'Add Host (up & down arrows to navigate, esc to cancel)',
                           border_off_north=1, border_off_east=1,
                           close_cb=self._do_add)
        popup.add_text_input('hostname', '%s:' % _('Hostname'))
        popup.add_text_input('port', '%s:' % _('Port'))
        popup.add_text_input('username', '%s:' % _('Username'))
        popup.add_text_input('password', '%s:' % _('Password'))
        self.push_popup(popup, clear=True)
        self.refresh()

    def delete_current_host(self):
        idx, data = self.popup.current_selection()
        log.debug('deleting host: %s', data)
        for host in self.config['hosts']:
            if host[0] == data:
                self.config['hosts'].remove(host)
                break
        self.config.save()

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

        if c > 31 and c < 256:
            if chr(c) == 'q' and self.inlist:
                return
            if chr(c) == 'Q':
                from twisted.internet import reactor
                if client.connected():
                    def on_disconnect(result):
                        reactor.stop()
                    client.disconnect().addCallback(on_disconnect)
                else:
                    reactor.stop()
                return
            if chr(c) == 'D' and self.inlist:
                self.delete_current_host()
                self.update_select_host_popup()
                return
            if chr(c) == 'a' and self.inlist:
                self.add_popup()
                return

        if self.popup:
            if self.popup.handle_read(c) and self.popup.closed():
                self.pop_popup()
            self.refresh()
            return
