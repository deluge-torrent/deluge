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
from deluge.ui.console.utils import curses_util as util

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


class EventView(BaseMode):
    def __init__(self, parent_mode, stdscr, encoding=None):
        BaseMode.__init__(self, stdscr, encoding)
        self.parent_mode = parent_mode
        self.offset = 0

    def back_to_overview(self):
        component.get('ConsoleUI').set_mode(self.parent_mode.mode_name)

    @overrides(component.Component)
    def update(self):
        self.refresh()

    @overrides(BaseMode)
    def refresh(self):
        """
        This method just shows each line of the event log
        """
        events = component.get('ConsoleUI').events

        self.stdscr.erase()
        self.draw_statusbars()

        if events:
            for i, event in enumerate(events):
                if i - self.offset >= self.rows - 2:
                    more = len(events) - self.offset - self.rows + 2
                    if more > 0:
                        self.add_string(i - self.offset, '  (And %i more)' % more)
                    break

                elif i - self.offset < 0:
                    continue
                try:
                    self.add_string(i + 1 - self.offset, event)
                except curses.error:
                    pass  # This'll just cut the line. Note: This seriously should be fixed in a better way
        else:
            self.add_string(1, '{!white,black,bold!}No events to show yet')

        if not component.get('ConsoleUI').is_active_mode(self):
            return

        self.stdscr.noutrefresh()
        curses.doupdate()

    @overrides(BaseMode)
    def on_resize(self, rows, cols):
        BaseMode.on_resize(self, rows, cols)
        self.refresh()

    @overrides(BaseMode)
    def read_input(self):
        c = self.stdscr.getch()

        if c in [ord('q'), util.KEY_ESC]:
            self.back_to_overview()
            return

        # TODO: Scroll event list
        jumplen = self.rows - 3
        num_events = len(component.get('ConsoleUI').events)

        if c == curses.KEY_UP:
            self.offset -= 1
        elif c == curses.KEY_PPAGE:
            self.offset -= jumplen
        elif c == curses.KEY_HOME:
            self.offset = 0
        elif c == curses.KEY_DOWN:
            self.offset += 1
        elif c == curses.KEY_NPAGE:
            self.offset += jumplen
        elif c == curses.KEY_END:
            self.offset += num_events
        elif c == ord('j'):
            self.offset -= 1
        elif c == ord('k'):
            self.offset += 1

        if self.offset <= 0:
            self.offset = 0
        elif num_events > self.rows - 3:
            if self.offset > num_events - self.rows + 3:
                self.offset = num_events - self.rows + 3
        else:
            self.offset = 0

        self.refresh()
