# -*- coding: utf-8 -*-
#
# eventview.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
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
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

import deluge.component as component
from basemode import BaseMode

from deluge.ui.client import client

try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)

import format_utils

class EventView(BaseMode):
    def __init__(self, parent_mode, stdscr, encoding=None):
        self.parent_mode = parent_mode
        self.offset = 0
        BaseMode.__init__(self, stdscr, encoding)

    def refresh(self):
        "This method just shows each line of the event log"
        events = component.get("ConsoleUI").events

        self.stdscr.erase()

        self.add_string(0,self.statusbars.topbar)
        hstr =  "%sPress [h] for help"%(" "*(self.cols - len(self.statusbars.bottombar) - 10))
        #This will quite likely fail when switching modes
        try:
            rf = format_utils.remove_formatting
            string = self.statusbars.bottombar
            hstr = "Press {!magenta,blue,bold!}[h]{!status!} for help"

            string += " " * ( self.cols - len(rf(string)) - len(rf(hstr))) + hstr

            self.add_string(self.rows - 1, string)
        except:
            pass

        if events:
            for i,event in enumerate(events):
                if i - self.offset >= self.rows - 2:
                    more = len(events) - self.offset - self.rows + 2
                    if more > 0:
                        self.add_string(i-self.offset, "  (And %i more)" % more)
                    break

                elif i - self.offset < 0:
                    continue
                self.add_string(i+1-self.offset,event)
        else:
            self.add_string(1,"{!white,black,bold!}No events to show yet")

        if component.get("ConsoleUI").screen != self:
            return

        self.stdscr.noutrefresh()
        curses.doupdate()

    def on_resize(self, *args):
        BaseMode.on_resize_norefresh(self, *args)

        #Always refresh Legacy(it will also refresh AllTorrents), otherwise it will bug deluge out
        legacy = component.get("LegacyUI")
        legacy.on_resize(*args)
        self.stdscr.erase()
        self.refresh()

    def back_to_overview(self):
        self.stdscr.erase()
        component.get("ConsoleUI").set_mode(self.parent_mode)
        self.parent_mode.resume()

    def _doRead(self):
        c = self.stdscr.getch()

        if c > 31 and c < 256:
            if chr(c) == 'Q':
                from twisted.internet import reactor
                if client.connected():
                    def on_disconnect(result):
                        reactor.stop()
                    client.disconnect().addCallback(on_disconnect)
                else:
                    reactor.stop()
                return
            elif chr(c) == 'q':
                self.back_to_overview()
                return

        if c == 27:
            self.back_to_overview()
            return

        # TODO: Scroll event list
        jumplen = self.rows - 3
        num_events = len( component.get("ConsoleUI").events )

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
