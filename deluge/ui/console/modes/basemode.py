# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import sys

import deluge.component as component
import deluge.ui.console.utils.colors as colors
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.utils.format_utils import remove_formatting

try:
    import curses
    import curses.panel
except ImportError:
    pass

try:
    import signal
    import struct
    import termios
    from fcntl import ioctl
except ImportError:
    pass


log = logging.getLogger(__name__)


class InputKeyHandler(object):
    def __init__(self):
        self._input_result = None

    def set_input_result(self, result):
        self._input_result = result

    def get_input_result(self):
        result = self._input_result
        self._input_result = None
        return result

    def handle_read(self, c):
        """Handle a character read from curses screen

        Returns:
            int: One of the constants defined in util.curses_util.ReadState.
            ReadState.IGNORED: The key was not handled. Further processing should continue.
            ReadState.READ: The key was read and processed. Do no further processing
            ReadState.CHANGED: The key was read and processed. Internal state was changed
            leaving data to be read by the caller.

        """
        return util.ReadState.IGNORED


class TermResizeHandler(object):
    def __init__(self):
        try:
            signal.signal(signal.SIGWINCH, self.on_terminal_size)
        except ValueError as ex:
            log.debug('TermResize unavailable, unable to catch SIGWINCH signal: %s', ex)
        except AttributeError as ex:
            log.debug('TermResize unavailable, no SIGWINCH signal on Windows: %s', ex)

    def on_terminal_size(self, *args):
        # Get the new rows and cols value
        rows, cols = struct.unpack('hhhh', ioctl(0, termios.TIOCGWINSZ, b'\000' * 8))[
            0:2
        ]
        curses.resizeterm(rows, cols)
        return rows, cols


class CursesStdIO(object):
    """
    fake fd to be registered as a reader with the twisted reactor.
       Curses classes needing input should extend this
    """

    def fileno(self):
        """ We want to select on FD 0 """
        return 0

    def doRead(self):  # NOQA: N802
        """called when input is ready"""
        pass

    def logPrefix(self):  # NOQA: N802
        return 'CursesClient'


class BaseMode(CursesStdIO, component.Component):
    def __init__(
        self, stdscr, encoding=None, do_refresh=True, mode_name=None, depend=None
    ):
        """
        A mode that provides a curses screen designed to run as a reader in a twisted reactor.
        This mode doesn't do much, just shows status bars and "Base Mode" on the screen

        Modes should subclass this and provide overrides for:

        do_read(self) - Handle user input
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
        self.mode_name = mode_name if mode_name else self.__class__.__name__
        component.Component.__init__(self, self.mode_name, 1, depend=depend)
        self.stdscr = stdscr
        # Make the input calls non-blocking
        self.stdscr.nodelay(1)

        self.paused = False
        # Strings for the 2 status bars
        self.statusbars = component.get('StatusBars')
        self.help_hstr = '{!status!} Press {!magenta,blue,bold!}[h]{!status!} for help'

        # Keep track of the screen size
        self.rows, self.cols = self.stdscr.getmaxyx()

        if not encoding:
            self.encoding = sys.getdefaultencoding()
        else:
            self.encoding = encoding

        # Do a refresh right away to draw the screen
        if do_refresh:
            self.refresh()

    def on_resize(self, rows, cols):
        self.rows, self.cols = rows, cols

    def connectionLost(self, reason):  # NOQA: N802
        self.close()

    def add_string(self, row, string, scr=None, **kwargs):
        if scr:
            screen = scr
        else:
            screen = self.stdscr

        return add_string(row, string, screen, self.encoding, **kwargs)

    def draw_statusbars(
        self,
        top_row=0,
        bottom_row=-1,
        topbar=None,
        bottombar=None,
        bottombar_help=True,
        scr=None,
    ):
        self.add_string(top_row, topbar if topbar else self.statusbars.topbar, scr=scr)
        bottombar = bottombar if bottombar else self.statusbars.bottombar
        if bottombar_help:
            if bottombar_help is True:
                bottombar_help = self.help_hstr
            bottombar += (
                ' '
                * (
                    self.cols
                    - len(remove_formatting(bottombar))
                    - len(remove_formatting(bottombar_help))
                )
                + bottombar_help
            )
        self.add_string(self.rows + bottom_row, bottombar, scr=scr)

    # This mode doesn't do anything with popups
    def set_popup(self, popup):
        pass

    def pause(self):
        self.paused = True

    def mode_paused(self):
        return self.paused

    def resume(self):
        self.paused = False
        self.refresh()

    def refresh(self):
        """
        Refreshes the screen.
        Updates the lines based on the`:attr:lines` based on the `:attr:display_lines_offset`
        attribute and the status bars.
        """
        self.stdscr.erase()
        self.draw_statusbars()
        # Update the status bars

        self.add_string(1, '{!info!}Base Mode (or subclass has not overridden refresh)')

        self.stdscr.redrawwin()
        self.stdscr.refresh()

    def doRead(self):  # NOQA: N802
        """
        Called when there is data to be read, ie, input from the keyboard.
        """
        # We wrap this function to catch exceptions and shutdown the mainloop
        try:
            self.read_input()
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(ex)

    def read_input(self):
        # Read the character
        self.stdscr.getch()
        self.stdscr.refresh()

    def close(self):
        """
        Clean up the curses stuff on exit.
        """
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


def add_string(
    row, fstring, screen, encoding, col=0, pad=True, pad_char=' ', trim='..', leaveok=0
):
    """
    Adds a string to the desired `:param:row`.

    Args:
        row(int): the row number to write the string
        row(int): the row number to write the string
        fstring(str): the (formatted) string of text to add
        scr(curses.window): optional window to add string to instead of self.stdscr
        col(int): optional starting column offset
        pad(bool): optional bool if the string should be padded out to the width of the screen
        trim(bool): optional bool if the string should be trimmed if it is too wide for the screen

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

    Returns:
        int: the next row

    """
    try:
        parsed = colors.parse_color_string(fstring)
    except colors.BadColorString as ex:
        log.error('Cannot add bad color string %s: %s', fstring, ex)
        return

    if leaveok:
        screen.leaveok(leaveok)

    max_y, max_x = screen.getmaxyx()
    for index, (color, string) in enumerate(parsed):
        # Skip printing chars beyond max_x
        if col >= max_x:
            break

        if index + 1 == len(parsed) and pad:
            # This is the last string so lets append some padding to it
            string += pad_char * (max_x - (col + len(string)))

        if col + len(string) > max_x:
            remaining_chrs = max(0, max_x - col)
            if trim:
                string = string[0 : max(0, remaining_chrs - len(trim))] + trim
            else:
                string = string[0:remaining_chrs]

        try:
            screen.addstr(row, col, string.encode(encoding), color)
        except curses.error:
            # Ignore exception for writing offscreen.
            pass

        col += len(string)

    if leaveok:
        screen.leaveok(0)

    return row + 1


def mkpanel(color, rows, cols, tly, tlx):
    win = curses.newwin(rows, cols, tly, tlx)
    pan = curses.panel.new_panel(win)
    if curses.has_colors():
        win.bkgdset(ord(' '), curses.color_pair(color))
    else:
        win.bkgdset(ord(' '), curses.A_BOLD)
    return pan


def mkwin(color, rows, cols, tly, tlx):
    win = curses.newwin(rows, cols, tly, tlx)
    if curses.has_colors():
        win.bkgdset(ord(' '), curses.color_pair(color))
    else:
        win.bkgdset(ord(' '), curses.A_BOLD)
    return win


def mkpad(color, rows, cols):
    win = curses.newpad(rows, cols)
    if curses.has_colors():
        win.bkgdset(ord(' '), curses.color_pair(color))
    else:
        win.bkgdset(ord(' '), curses.A_BOLD)
    return win


def move_cursor(screen, row, col):
    try:
        screen.move(row, col)
    except curses.error as ex:
        import traceback

        log.warning(
            'Error on screen.move(%s, %s): (curses.LINES: %s, curses.COLS: %s) Error: %s\nStack: %s',
            row,
            col,
            curses.LINES,
            curses.COLS,
            ex,
            ''.join(traceback.format_stack()),
        )
