# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console.modes import format_utils
from deluge.ui.console.modes.basemode import BaseMode

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


class EventView(BaseMode):
    def __init__(self, parent_mode, stdscr, encoding=None):
        self.parent_mode = parent_mode
        self.offset = 0
        BaseMode.__init__(self, stdscr, encoding)

    def refresh(self):
        "This method just shows each line of the event log"
        events = component.get("ConsoleUI").events

        self.stdscr.erase()

        self.add_string(0, self.statusbars.topbar)
        hstr = "%sPress [h] for help" % (" " * (self.cols - len(self.statusbars.bottombar) - 10))
        # This will quite likely fail when switching modes
        try:
            rf = format_utils.remove_formatting
            string = self.statusbars.bottombar
            hstr = "Press {!magenta,blue,bold!}[h]{!status!} for help"

            string += " " * (self.cols - len(rf(string)) - len(rf(hstr))) + hstr

            self.add_string(self.rows - 1, string)
        except Exception as ex:
            log.debug("Exception caught: %s", ex)

        if events:
            for i, event in enumerate(events):
                if i - self.offset >= self.rows - 2:
                    more = len(events) - self.offset - self.rows + 2
                    if more > 0:
                        self.add_string(i - self.offset, "  (And %i more)" % more)
                    break

                elif i - self.offset < 0:
                    continue
                try:
                    self.add_string(i + 1 - self.offset, event)
                except curses.error:
                    pass  # This'll just cut the line. Note: This seriously should be fixed in a better way
        else:
            self.add_string(1, "{!white,black,bold!}No events to show yet")

        if component.get("ConsoleUI").screen != self:
            return

        self.stdscr.noutrefresh()
        curses.doupdate()

    def on_resize(self, *args):
        BaseMode.on_resize_norefresh(self, *args)

        # Always refresh Legacy(it will also refresh AllTorrents), otherwise it will bug deluge out
        legacy = component.get("LegacyUI")
        legacy.on_resize(*args)
        self.stdscr.erase()
        self.refresh()

    def back_to_overview(self):
        self.stdscr.erase()
        component.get("ConsoleUI").set_mode(self.parent_mode)
        self.parent_mode.resume()

    def read_input(self):
        c = self.stdscr.getch()

        if c > 31 and c < 256:
            if chr(c) == "Q":
                from twisted.internet import reactor
                if client.connected():
                    def on_disconnect(result):
                        reactor.stop()
                    client.disconnect().addCallback(on_disconnect)
                else:
                    reactor.stop()
                return
            elif chr(c) == "q":
                self.back_to_overview()
                return

        if c == 27:
            self.back_to_overview()
            return

        # TODO: Scroll event list
        jumplen = self.rows - 3
        num_events = len(component.get("ConsoleUI").events)

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
        elif c == ord("j"):
            self.offset -= 1
        elif c == ord("k"):
            self.offset += 1

        if self.offset <= 0:
            self.offset = 0
        elif num_events > self.rows - 3:
            if self.offset > num_events - self.rows + 3:
                self.offset = num_events - self.rows + 3
        else:
            self.offset = 0

        self.refresh()
