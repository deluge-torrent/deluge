#
# basemode.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
# 
# Most code in this file taken from screen.py: 
#  Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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

import sys
import logging
try:
    import curses
except ImportError:
    pass

import deluge.component as component
import deluge.ui.console.colors as colors
try:
    import signal
    from fcntl import ioctl
    import termios
    import struct
except:
    pass

from twisted.internet import reactor

log = logging.getLogger(__name__)

class CursesStdIO(object):
    """fake fd to be registered as a reader with the twisted reactor.
       Curses classes needing input should extend this"""

    def fileno(self):
        """ We want to select on FD 0 """
        return 0

    def doRead(self):
        """called when input is ready"""
        pass
    def logPrefix(self): return 'CursesClient'


class BaseMode(CursesStdIO):
    def __init__(self, stdscr, encoding=None):
        """
        A mode that provides a curses screen designed to run as a reader in a twisted reactor.
        This mode doesn't do much, just shows status bars and "Base Mode" on the screen

        Modes should subclass this and provide overrides for:

        _doRead(self) - Handle user input
        refresh(self) - draw the mode to the screen
        add_string(self, row, string) - add a string of text to be displayed.  
                                        see method for detailed info

        The init method of a subclass *must* call BaseMode.__init__

        Useful fields after calling BaseMode.__init__:
        self.stdscr - the curses screen
        self.rows - # of rows on the curses screen
        self.cols - # of cols on the curses screen
        self.topbar - top statusbar
        self.bottombar - bottom statusbar
        """
        log.debug("BaseMode init!")
        self.stdscr = stdscr
        # Make the input calls non-blocking
        self.stdscr.nodelay(1)

        # Strings for the 2 status bars
        self.statusbars = component.get("StatusBars")

        # Keep track of the screen size
        self.rows, self.cols = self.stdscr.getmaxyx()
        try:
            signal.signal(signal.SIGWINCH, self.on_resize)
        except Exception, e:
            log.debug("Unable to catch SIGWINCH signal!")

        if not encoding:
            self.encoding = sys.getdefaultencoding()
        else:
            self.encoding = encoding

        colors.init_colors()

        # Do a refresh right away to draw the screen
        self.refresh()

    def on_resize_norefresh(self, *args):
        log.debug("on_resize_from_signal")
        # Get the new rows and cols value
        self.rows, self.cols = struct.unpack("hhhh", ioctl(0, termios.TIOCGWINSZ ,"\000"*8))[0:2]
        curses.resizeterm(self.rows, self.cols)

    def on_resize(self, *args):
        self.on_resize_norefresh(args)
        self.refresh()

    def connectionLost(self, reason):
        self.close()

    def add_string(self, row, string, scr=None, col = 0, pad=True, trim=True):
        """
        Adds a string to the desired `:param:row`.

        :param row: int, the row number to write the string
        :param string: string, the string of text to add
        :param scr: curses.window, optional window to add string to instead of self.stdscr
        :param col: int, optional starting column offset
        :param pad: bool, optional bool if the string should be padded out to the width of the screen
        :param trim: bool, optional bool if the string should be trimmed if it is too wide for the screen

        The text can be formatted with color using the following format:

        "{!fg, bg, attributes, ...!}"

        See: http://docs.python.org/library/curses.html#constants for attributes.

        Alternatively, it can use some built-in scheme for coloring.
        See colors.py for built-in schemes.

        "{!scheme!}"

        Examples:

        "{!blue, black, bold!}My Text is {!white, black!}cool"
        "{!info!}I am some info text!"
        "{!error!}Uh oh!"


        """
        if scr:
            screen = scr
        else:
            screen = self.stdscr
        try:
            parsed = colors.parse_color_string(string, self.encoding)
        except colors.BadColorString, e:
            log.error("Cannot add bad color string %s: %s", string, e)
            return

        for index, (color, s) in enumerate(parsed):
            if index + 1 == len(parsed) and pad:
                # This is the last string so lets append some " " to it
                s += " " * (self.cols - (col + len(s)) - 1)
            if trim:
                y,x = screen.getmaxyx()
                if (col+len(s)) > x:
                    s = "%s..."%s[0:x-4-col]
            screen.addstr(row, col, s, color)
            col += len(s)

    def draw_statusbars(self):
        self.add_string(0, self.statusbars.topbar)
        self.add_string(self.rows - 1, self.statusbars.bottombar)        

    def refresh(self):
        """
        Refreshes the screen.
        Updates the lines based on the`:attr:lines` based on the `:attr:display_lines_offset`
        attribute and the status bars.
        """
        self.stdscr.clear()
        self.draw_statusbars()
        # Update the status bars

        self.add_string(1,"{!info!}Base Mode (or subclass hasn't overridden refresh)")

        self.stdscr.redrawwin()
        self.stdscr.refresh()

    def doRead(self):
        """
        Called when there is data to be read, ie, input from the keyboard.
        """
        # We wrap this function to catch exceptions and shutdown the mainloop
        try:
            self._doRead()
        except Exception, e:
            log.exception(e)
            reactor.stop()

    def _doRead(self):
        # Read the character
        c = self.stdscr.getch()
        self.stdscr.refresh()

    def close(self):
        """
        Clean up the curses stuff on exit.
        """
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
