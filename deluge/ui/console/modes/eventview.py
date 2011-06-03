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
try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)

class EventView(BaseMode):
    def __init__(self, parent_mode, stdscr, encoding=None):
        self.parent_mode = parent_mode
        BaseMode.__init__(self, stdscr, encoding)

    def refresh(self):
        "This method just shows each line of the event log"
        events = component.get("ConsoleUI").events

        self.add_string(0,self.statusbars.topbar)
        hstr =  "%sPress [h] for help"%(" "*(self.cols - len(self.statusbars.bottombar) - 10))
        self.add_string(self.rows - 1, "%s%s"%(self.statusbars.bottombar,hstr))

        if events:
            for i,event in enumerate(events):
                self.add_string(i+1,event)
        else:
            self.add_string(1,"{!white,black,bold!}No events to show yet")

        self.stdscr.noutrefresh()
        curses.doupdate()

    def back_to_overview(self):
        self.stdscr.clear()
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
        if c == curses.KEY_UP:
            pass
        elif c == curses.KEY_PPAGE:
            pass
        elif c == curses.KEY_DOWN:
            pass
        elif c == curses.KEY_NPAGE:
            pass

        #self.refresh()
