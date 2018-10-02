# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import curses
import logging

from deluge.component import Component
from deluge.decorators import overrides
from deluge.ui.client import client
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.widgets import BaseInputPane
from deluge.ui.console.widgets.sidebar import Sidebar

log = logging.getLogger(__name__)


class FilterSidebar(Sidebar, Component):
    """The sidebar in the main torrentview

    Shows the different states of the torrents and allows to filter the
    torrents based on state.

    """

    def __init__(self, torrentlist, config):
        self.config = config
        height = curses.LINES - 2
        width = self.config['torrentview']['sidebar_width']
        Sidebar.__init__(
            self,
            torrentlist,
            width,
            height,
            title=' Filter ',
            border_off_north=1,
            allow_resize=True,
        )
        Component.__init__(self, 'FilterSidebar')
        self.checked_index = 0
        kwargs = {
            'checked_char': '*',
            'unchecked_char': '-',
            'checkbox_format': ' %s ',
            'col': 0,
        }
        self.add_checked_input('All', 'All', checked=True, **kwargs)
        self.add_checked_input('Active', 'Active', **kwargs)
        self.add_checked_input(
            'Downloading', 'Downloading', color='green,black', **kwargs
        )
        self.add_checked_input('Seeding', 'Seeding', color='cyan,black', **kwargs)
        self.add_checked_input('Paused', 'Paused', **kwargs)
        self.add_checked_input('Error', 'Error', color='red,black', **kwargs)
        self.add_checked_input('Checking', 'Checking', color='blue,black', **kwargs)
        self.add_checked_input('Queued', 'Queued', **kwargs)
        self.add_checked_input(
            'Allocating', 'Allocating', color='yellow,black', **kwargs
        )
        self.add_checked_input('Moving', 'Moving', color='green,black', **kwargs)

    @overrides(Component)
    def update(self):
        if not self.hidden() and client.connected():
            d = client.core.get_filter_tree(True, []).addCallback(
                self._cb_update_filter_tree
            )

            def on_filter_tree_updated(changed):
                if changed:
                    self.refresh()

            d.addCallback(on_filter_tree_updated)

    def _cb_update_filter_tree(self, filter_items):
        """Callback function on client.core.get_filter_tree"""
        states = filter_items['state']
        largest_count = 0
        largest_state_width = 0
        for state in states:
            largest_state_width = max(len(state[0]), largest_state_width)
            largest_count = max(int(state[1]), largest_count)

        border_and_spacing = 6  # Account for border + whitespace
        filter_state_width = largest_state_width
        filter_count_width = self.width - filter_state_width - border_and_spacing

        changed = False
        for state in states:
            field = self.get_input(state[0])
            if field:
                txt = (
                    '%%-%ds%%%ds'
                    % (filter_state_width, filter_count_width)
                    % (state[0], state[1])
                )
                if field.set_message(txt):
                    changed = True
        return changed

    @overrides(BaseInputPane)
    def immediate_action_cb(self, state_changed=True):
        if state_changed:
            self.parent.torrentview.set_torrent_filter(
                self.inputs[self.active_input].name
            )

    @overrides(Sidebar)
    def handle_read(self, c):
        if c == util.KEY_SPACE:
            if self.checked_index != self.active_input:
                self.inputs[self.checked_index].set_value(False)
                Sidebar.handle_read(self, c)
                self.checked_index = self.active_input
            return util.ReadState.READ
        else:
            return Sidebar.handle_read(self, c)

    @overrides(Sidebar)
    def on_resize(self, width):
        sidebar_width = self.config['torrentview']['sidebar_width']
        if sidebar_width != width:
            self.config['torrentview']['sidebar_width'] = width
            self.config.save()
        self.resize_window(self.height, width)
        self.parent.toggle_sidebar()
        self.refresh()
