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
from collections import deque

import deluge.component as component
from deluge.decorators import overrides
from deluge.ui.client import client
from deluge.ui.console.modes.basemode import BaseMode
from deluge.ui.console.modes.preferences.preference_panes import (
    BandwidthPane,
    CachePane,
    DaemonPane,
    DownloadsPane,
    InterfacePane,
    NetworkPane,
    OtherPane,
    ProxyPane,
    QueuePane,
)
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.widgets.fields import SelectInput
from deluge.ui.console.widgets.popup import MessagePopup, PopupsHandler
from deluge.ui.console.widgets.sidebar import Sidebar

try:
    import curses
except ImportError:
    pass


log = logging.getLogger(__name__)


# Big help string that gets displayed when the user hits 'h'
HELP_STR = """This screen lets you view and configure various options in deluge.

There are three main sections to this screen. Only one section is active at a time. \
You can switch the active section by hitting TAB (or Shift-TAB to go back one)

The section on the left displays the various categories that the settings fall in. \
You can navigate the list using the up/down arrows

The section on the right shows the settings for the selected category. When this \
section is active you can navigate the various settings with the up/down arrows. \
Special keys for each input type are described below.

The final section is at the bottom right, the: [Cancel] [Apply] [OK] buttons.
When this section is active, simply select the option you want using the arrow
keys and press Enter to confim.


Special keys for various input types are as follows:
- For text inputs you can simply type in the value.

{|indent:  |}- For numeric inputs (indicated by the value being in []s), you can type a value, \
or use PageUp and PageDown to increment/decrement the value.

- For checkbox inputs use the spacebar to toggle

{|indent:  |}- For checkbox plus something else inputs (the something else being only visible \
when you check the box) you can toggle the check with space, use the right \
arrow to edit the other value, and escape to get back to the check box.

"""


class ZONE(object):
    length = 3
    CATEGORIES, PREFRENCES, ACTIONS = list(range(length))


class PreferenceSidebar(Sidebar):
    def __init__(self, torrentview, width):
        height = curses.LINES - 2
        Sidebar.__init__(
            self, torrentview, width, height, title=None, border_off_north=1
        )
        self.categories = [
            _('Interface'),
            _('Downloads'),
            _('Network'),
            _('Bandwidth'),
            _('Other'),
            _('Daemon'),
            _('Queue'),
            _('Proxy'),
            _('Cache'),
        ]
        for name in self.categories:
            self.add_text_field(
                name,
                name,
                selectable=True,
                font_unfocused_active='bold',
                color_unfocused_active='white,black',
            )

    def on_resize(self):
        self.resize_window(curses.LINES - 2, self.width)


class Preferences(BaseMode, PopupsHandler):
    def __init__(self, parent_mode, stdscr, console_config, encoding=None):
        BaseMode.__init__(self, stdscr, encoding=encoding, do_refresh=False)
        PopupsHandler.__init__(self)
        self.parent_mode = parent_mode
        self.cur_cat = 0
        self.messages = deque()
        self.action_input = None
        self.config_loaded = False
        self.console_config = console_config
        self.active_port = -1
        self.active_zone = ZONE.CATEGORIES
        self.sidebar_width = 15  # Width of the categories pane

        self.sidebar = PreferenceSidebar(parent_mode, self.sidebar_width)
        self.sidebar.set_focused(True)
        self.sidebar.active_input = 0

        self._calc_sizes(resize=False)

        self.panes = [
            InterfacePane(self),
            DownloadsPane(self),
            NetworkPane(self),
            BandwidthPane(self),
            OtherPane(self),
            DaemonPane(self),
            QueuePane(self),
            ProxyPane(self),
            CachePane(self),
        ]

        self.action_input = SelectInput(
            self, None, None, [_('Cancel'), _('Apply'), _('OK')], [0, 1, 2], 0
        )

    def load_config(self):
        if self.config_loaded:
            return

        def on_get_config(core_config):
            self.core_config = core_config
            self.config_loaded = True
            for p in self.panes:
                p.create_pane(core_config, self.console_config)
            self.refresh()

        client.core.get_config().addCallback(on_get_config)

        def on_get_listen_port(port):
            self.active_port = port

        client.core.get_listen_port().addCallback(on_get_listen_port)

    @property
    def height(self):
        # top/bottom bars: 2, Action buttons (Cancel/Apply/OK): 1
        return self.rows - 3

    @property
    def width(self):
        return self.prefs_width

    def _calc_sizes(self, resize=True):
        self.prefs_width = self.cols - self.sidebar_width

        if not resize:
            return

        for p in self.panes:
            p.resize_window(self.height, p.pane_width)

    def _draw_preferences(self):
        self.cur_cat = self.sidebar.active_input
        self.panes[self.cur_cat].render(
            self, self.stdscr, self.prefs_width, self.active_zone == ZONE.PREFRENCES
        )
        self.panes[self.cur_cat].refresh()

    def _draw_actions(self):
        selected = self.active_zone == ZONE.ACTIONS
        self.stdscr.hline(self.rows - 3, self.sidebar_width, b'_', self.cols)
        self.action_input.render(
            self.stdscr,
            self.rows - 2,
            width=self.cols,
            active=selected,
            focus=True,
            col=self.cols - 22,
        )

    @overrides(BaseMode)
    def on_resize(self, rows, cols):
        BaseMode.on_resize(self, rows, cols)
        self._calc_sizes()

        if self.popup:
            self.popup.handle_resize()

        self.sidebar.on_resize()
        self.refresh()

    @overrides(component.Component)
    def update(self):
        for i, p in enumerate(self.panes):
            self.panes[i].update(i == self.cur_cat)

    @overrides(BaseMode)
    def resume(self):
        BaseMode.resume(self)
        self.sidebar.show()

    @overrides(BaseMode)
    def refresh(self):
        if (
            not component.get('ConsoleUI').is_active_mode(self)
            or not self.config_loaded
        ):
            return

        if self.popup is None and self.messages:
            title, msg = self.messages.popleft()
            self.push_popup(MessagePopup(self, title, msg))

        self.stdscr.erase()
        self.draw_statusbars()
        self._draw_actions()
        # Necessary to force updating the stdscr
        self.stdscr.noutrefresh()

        self.sidebar.refresh()

        # do this last since it moves the cursor
        self._draw_preferences()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()

    def _apply_prefs(self):
        if self.core_config is None:
            return

        def update_conf_value(key, source_dict, dest_dict, updated):
            if dest_dict[key] != source_dict[key]:
                dest_dict[key] = source_dict[key]
                updated = True
            return updated

        new_core_config = {}
        for pane in self.panes:
            if not isinstance(pane, InterfacePane):
                pane.add_config_values(new_core_config)
        # Apply Core Prefs
        if client.connected():
            # Only do this if we're connected to a daemon
            config_to_set = {}
            for key in new_core_config:
                # The values do not match so this needs to be updated
                if self.core_config[key] != new_core_config[key]:
                    config_to_set[key] = new_core_config[key]

            if config_to_set:
                # Set each changed config value in the core
                client.core.set_config(config_to_set)
                client.force_call(True)
                # Update the configuration
                self.core_config.update(config_to_set)

        # Update Interface Prefs
        new_console_config = {}
        didupdate = False
        for pane in self.panes:
            # could just access panes by index, but that would break if panes
            # are ever reordered, so do it the slightly slower but safer way
            if isinstance(pane, InterfacePane):
                pane.add_config_values(new_console_config)
                for k in ['ring_bell', 'language']:
                    didupdate = update_conf_value(
                        k, new_console_config, self.console_config, didupdate
                    )
                for k in ['separate_complete', 'move_selection']:
                    didupdate = update_conf_value(
                        k,
                        new_console_config,
                        self.console_config['torrentview'],
                        didupdate,
                    )
                for k in [
                    'ignore_duplicate_lines',
                    'save_command_history',
                    'third_tab_lists_all',
                    'torrents_per_tab_press',
                ]:
                    didupdate = update_conf_value(
                        k, new_console_config, self.console_config['cmdline'], didupdate
                    )

        if didupdate:
            self.parent_mode.on_config_changed()

    def _update_preferences(self, core_config):
        self.core_config = core_config
        for pane in self.panes:
            pane.update_values(core_config)

    def _actions_read(self, c):
        self.action_input.handle_read(c)
        if c in [curses.KEY_ENTER, util.KEY_ENTER2]:
            # take action
            if self.action_input.selected_index == 0:  # Cancel
                self.back_to_parent()
            elif self.action_input.selected_index == 1:  # Apply
                self._apply_prefs()
                client.core.get_config().addCallback(self._update_preferences)
            elif self.action_input.selected_index == 2:  # OK
                self._apply_prefs()
                self.back_to_parent()

    def back_to_parent(self):
        component.get('ConsoleUI').set_mode(self.parent_mode.mode_name)

    @overrides(BaseMode)
    def read_input(self):
        c = self.stdscr.getch()

        if self.popup:
            if self.popup.handle_read(c):
                self.pop_popup()
            self.refresh()
            return

        if util.is_printable_chr(c):
            char = chr(c)
            if char == 'Q':
                component.get('ConsoleUI').quit()
            elif char == 'h':
                self.push_popup(MessagePopup(self, 'Preferences Help', HELP_STR))

        if self.sidebar.has_focus() and c == util.KEY_ESC:
            self.back_to_parent()
            return

        def update_active_zone(val):
            self.active_zone += val
            if self.active_zone == -1:
                self.active_zone = ZONE.length - 1
            else:
                self.active_zone %= ZONE.length
            self.sidebar.set_focused(self.active_zone == ZONE.CATEGORIES)

        if c == util.KEY_TAB:
            update_active_zone(1)
        elif c == curses.KEY_BTAB:
            update_active_zone(-1)
        else:
            if self.active_zone == ZONE.CATEGORIES:
                self.sidebar.handle_read(c)
            elif self.active_zone == ZONE.PREFRENCES:
                self.panes[self.cur_cat].handle_read(c)
            elif self.active_zone == ZONE.ACTIONS:
                self._actions_read(c)

        self.refresh()

    def is_active_pane(self, pane):
        return pane == self.panes[self.cur_cat]
