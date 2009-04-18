#
# screen.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
#

import curses
import colors
from deluge.log import LOG as log
from twisted.internet import reactor

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

LINES_BUFFER_SIZE = 5000
INPUT_HISTORY_SIZE = 500

class Screen(CursesStdIO):
    def __init__(self, stdscr, command_parser, tab_completer=None):
        """
        A curses screen designed to run as a reader in a twisted reactor.

        :param command_parser: a function that will be passed a string when the
            user hits enter
        :param tab_completer: a function that is sent the `:prop:input` string when
            the user hits tab.  It's intended purpose is to modify the input string.
            It should return a 2-tuple (input string, input cursor).

        """
        log.debug("Screen init!")
        # Function to be called with commands
        self.command_parser = command_parser
        self.tab_completer = tab_completer
        self.stdscr = stdscr
        # Make the input calls non-blocking
        self.stdscr.nodelay(1)

        # Holds the user input and is cleared on 'enter'
        self.input = ""
        self.input_incomplete = ""
        # Keep track of where the cursor is
        self.input_cursor = 0
        # Keep a history of inputs
        self.input_history = []
        self.input_history_index = 0

        # Keep track of double-tabs
        self.tab_count = 0

        # Strings for the 2 status bars
        self.topbar = ""
        self.bottombar = ""

        self.rows, self.cols = self.stdscr.getmaxyx()

        # A list of strings to be displayed based on the offset (scroll)
        self.lines = []
        # The offset to display lines
        self.display_lines_offset = 0

        # Refresh the screen to display everything right away
        self.refresh()

    def connectionLost(self, reason):
        self.close()

    def add_line(self, text):
        """
        Add a line to the screen.  This will be showed between the two bars.
        The text can be formatted with color using the following format:

        "{{fg, bg, attributes, ...}}"

        See: http://docs.python.org/library/curses.html#constants for attributes.

        Alternatively, it can use some built-in scheme for coloring.
        See colors.py for built-in schemes.

        "{{scheme}}"

        Examples:

        "{{blue, black, bold}}My Text is {{white, black}}cool"
        "{{info}}I am some info text!"
        "{{error}}Uh oh!"

        :param text: str, the text to show
        """
        log.debug("adding line: %s", text)

        self.lines.extend(text.splitlines())
        while len(self.lines) > LINES_BUFFER_SIZE:
            # Remove the oldest line if the max buffer size has been reached
            del self.lines[0]

        self.refresh()

    def add_string(self, row, string):
        """
        Adds a string to the desired `:param:row`.

        :param row: int, the row number to write the string

        """
        col = 0
        parsed = colors.parse_color_string(string)
        for index, (color, s) in enumerate(parsed):
            if index + 1 == len(parsed):
                # This is the last string so lets append some " " to it
                s += " " * (self.cols - (col + len(s)) - 1)
            self.stdscr.addstr(row, col, s, color)
            col += len(s)

    def refresh(self):
        """
        Refreshes the screen.
        Updates the lines based on the`:attr:lines` based on the `:attr:display_lines_offset`
        attribute and the status bars.
        """
        self.stdscr.clear()

        # Update the status bars
        self.add_string(0, self.topbar)
        self.add_string(self.rows - 2, self.bottombar)

        # The number of rows minus the status bars and the input line
        available_lines = self.rows - 3
        # If the amount of lines exceeds the number of rows, we need to figure out
        # which ones to display based on the offset
        if len(self.lines) > available_lines:
            # Get the lines to display based on the offset
            offset = len(self.lines) - self.display_lines_offset
            lines = self.lines[-(available_lines - offset):offset]
        elif len(self.lines) == available_lines:
            lines = self.lines
        else:
            lines = [""] * (available_lines - len(self.lines))
            lines.extend(self.lines)

        # Add the lines to the screen
        for index, line in enumerate(lines):
            self.add_string(index + 1, line)

        # Add the input string
        self.add_string(self.rows - 1, self.input)

        # Move the cursor
        self.stdscr.move(self.rows - 1, self.input_cursor)
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

        # We clear the input string and send it to the command parser on ENTER
        if c == curses.KEY_ENTER or c == 10:
            if self.input:
                self.add_line(">>> " + self.input)
                self.command_parser(self.input)
                if len(self.input_history) == INPUT_HISTORY_SIZE:
                    # Remove the oldest input history if the max history size
                    # is reached.
                    del self.input_history[0]
                self.input_history.append(self.input)
                self.input_history_index = len(self.input_history)
                self.input = ""
                self.input_incomplete = ""
                self.input_cursor = 0
                self.stdscr.refresh()

        # Run the tab completer function
        elif c == 9:
            # Keep track of tab hit count to know when it's double-hit
            self.tab_count += 1
            if self.tab_count > 1:
                second_hit = True
                self.tab_count = 0
            else:
                second_hit = False

            if self.tab_completer:
                # We only call the tab completer function if we're at the end of
                # the input string on the cursor is on a space
                if self.input_cursor == len(self.input) or self.input[self.input_cursor] == " ":
                    self.input, self.input_cursor = self.tab_completer(self.input, self.input_cursor, second_hit)

        # We use the UP and DOWN keys to cycle through input history
        elif c == curses.KEY_UP:
            if self.input_history_index - 1 >= 0:
                if self.input_history_index == len(self.input_history):
                    # We're moving from non-complete input so save it just incase
                    # we move back down to it.
                    self.input_incomplete = self.input
                # Going back in the history
                self.input_history_index -= 1
                self.input = self.input_history[self.input_history_index]
        elif c == curses.KEY_DOWN:
            if self.input_history_index + 1 < len(self.input_history):
                # Going forward in the history
                self.input_history_index += 1
                self.input = self.input_history[self.input_history_index]
            elif self.input_history_index + 1 == len(self.input_history):
                # We're moving back down to an incomplete input
                self.input_history_index += 1
                self.input = self.input_incomplete

        # Cursor movement
        elif c == curses.KEY_LEFT:
            if self.input_cursor:
                self.input_cursor -= 1
        elif c == curses.KEY_RIGHT:
            if self.input_cursor < len(self.input):
                self.input_cursor += 1
        elif c == curses.KEY_HOME:
            self.input_cursor = 0
        elif c == curses.KEY_END:
            self.input_cursor = len(self.input)

        # Delete a character in the input string based on cursor position
        if c == curses.KEY_BACKSPACE or c == 127:
            if self.input and self.input_cursor > 0:
                self.input = self.input[:self.input_cursor - 1] + self.input[self.input_cursor:]
                self.input_cursor -= 1

        # A key to add to the input string
        else:
            if c > 31 and c < 127:
                if self.input_cursor == len(self.input):
                    self.input += chr(c)
                else:
                    # Insert into string
                    self.input = self.input[:self.input_cursor] + chr(c) + self.input[self.input_cursor:]
                # Move the cursor forward
                self.input_cursor += 1

        # We remove the tab count if the key wasn't a tab
        if c != 9:
            self.tab_count = 0

        # Update the input string on the screen
        self.add_string(self.rows - 1, self.input)
        self.stdscr.move(self.rows - 1, self.input_cursor)
        self.stdscr.refresh()

    def close(self):
        """
        Clean up the curses stuff on exit.
        """
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
