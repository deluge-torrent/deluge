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
try:
    import curses
except ImportError:
    pass

import colors
try:
    import signal
    from fcntl import ioctl
    import termios
    import struct
except:
    pass

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
    def __init__(self, stdscr, command_parser, tab_completer=None, encoding=None):
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

        # A list of strings to be displayed based on the offset (scroll)
        self.lines = []
        # The offset to display lines
        self.display_lines_offset = 0

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

        # Do a refresh right away to draw the screen
        self.refresh()

    def on_resize(self, *args):
        log.debug("on_resize_from_signal")
        # Get the new rows and cols value
        self.rows, self.cols = struct.unpack("hhhh", ioctl(0, termios.TIOCGWINSZ ,"\000"*8))[0:2]
        curses.resizeterm(self.rows, self.cols)
        self.refresh()

    def connectionLost(self, reason):
        self.close()

    def add_line(self, text, refresh=True):
        """
        Add a line to the screen.  This will be showed between the two bars.
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

        :param text: the text to show
        :type text: string
        :param refresh: if True, the screen will refresh after the line is added
        :type refresh: bool

        """

        def get_line_chunks(line):
            """
            Returns a list of 2-tuples (color string, text)

            """
            if not line or line.count("{!") != line.count("!}"):
                return []

            chunks = []
            if not line.startswith('{!'):
                begin = line.find('{!')
                if begin == -1:
                    begin = len(line)
                chunks.append( ('', line[:begin]) )
                line = line[begin:]

            while line:
                # We know the line starts with '{!' here
                end_color = line.find('!}')
                next_color = line.find('{!', end_color)
                if next_color == -1:
                    next_color = len(line)
                chunks.append( (line[:end_color+2], line[end_color+2:next_color]) )
                line = line[next_color:]
            return chunks

        for line in text.splitlines():
            # We need to check for line lengths here and split as necessary
            try:
                line_length = colors.get_line_length(line)
            except colors.BadColorString:
                log.error("Passed a bad colored line: %s", line)
                continue

            if line_length >= (self.cols - 1):
                s = ""
                # The length of the text without the color tags
                s_len = 0
                # We need to split this over multiple lines
                for chunk in get_line_chunks(line):
                    if (len(chunk[1]) + s_len) < (self.cols - 1):
                        # This chunk plus the current string in 's' isn't over
                        # the maximum width, so just append the color tag and text
                        s += chunk[0] + chunk[1]
                        s_len += len(chunk[1])
                    else:
                        # The chunk plus the current string in 's' is too long.
                        # We need to take as much of the chunk and put it into 's'
                        # with the color tag.
                        remain = (self.cols - 1) - s_len
                        s += chunk[0] + chunk[1][:remain]
                        # We append the line since it's full
                        self.lines.append(s)
                        # Start a new 's' with the remainder chunk
                        s = chunk[0] + chunk[1][remain:]
                        s_len = len(chunk[1][remain:])
                # Append the final string which may or may not be the full width
                if s:
                    self.lines.append(s)
            else:
                self.lines.append(line)

        while len(self.lines) > LINES_BUFFER_SIZE:
            # Remove the oldest line if the max buffer size has been reached
            del self.lines[0]

        if refresh:
            self.refresh()

    def add_string(self, row, string):
        """
        Adds a string to the desired `:param:row`.

        :param row: int, the row number to write the string

        """
        col = 0
        try:
            parsed = colors.parse_color_string(string, self.encoding)
        except colors.BadColorString, e:
            log.error("Cannot add bad color string %s: %s", string, e)
            return

        for index, (color, s) in enumerate(parsed):
            if index + 1 == len(parsed):
                # This is the last string so lets append some " " to it
                s += " " * (self.cols - (col + len(s)) - 1)
            try:
                self.stdscr.addstr(row, col, s, color)
            except curses.error:
                pass

            col += len(s)

    def refresh(self):
        """
        Refreshes the screen.
        Updates the lines based on the`:attr:lines` based on the `:attr:display_lines_offset`
        attribute and the status bars.
        """
        self.stdscr.erase()

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
        try:
            self.stdscr.move(self.rows - 1, self.input_cursor)
        except curses.error:
            pass
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

        # We clear the input string and send it to the command parser on ENTER
        if c == curses.KEY_ENTER or c == 10:
            if self.input:
                self.add_line(">>> " + self.input)
                self.command_parser(self.input.encode(self.encoding))
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
                self.input_cursor = len(self.input)
        elif c == curses.KEY_DOWN:
            if self.input_history_index + 1 < len(self.input_history):
                # Going forward in the history
                self.input_history_index += 1
                self.input = self.input_history[self.input_history_index]
                self.input_cursor = len(self.input)
            elif self.input_history_index + 1 == len(self.input_history):
                # We're moving back down to an incomplete input
                self.input_history_index += 1
                self.input = self.input_incomplete
                self.input_cursor = len(self.input)

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

        # Scrolling through buffer
        elif c == curses.KEY_PPAGE:
            self.display_lines_offset += self.rows - 3
            # We substract 3 for the unavailable lines and 1 extra due to len(self.lines)
            if self.display_lines_offset > (len(self.lines) - 4 - self.rows):
                self.display_lines_offset = len(self.lines) - 4 - self.rows

            self.refresh()
        elif c == curses.KEY_NPAGE:
            self.display_lines_offset -= self.rows - 3
            if self.display_lines_offset < 0:
                self.display_lines_offset = 0
            self.refresh()

        # We remove the tab count if the key wasn't a tab
        if c != 9:
            self.tab_count = 0

        # Delete a character in the input string based on cursor position
        if c == curses.KEY_BACKSPACE or c == 127:
            if self.input and self.input_cursor > 0:
                self.input = self.input[:self.input_cursor - 1] + self.input[self.input_cursor:]
                self.input_cursor -= 1

        elif c == curses.KEY_DC:
            if self.input and self.input_cursor < len(self.input):
                self.input = self.input[:self.input_cursor] + self.input[self.input_cursor + 1:]

        # A key to add to the input string
        else:
            if c > 31 and c < 256:
                # Emulate getwch
                stroke = chr(c)
                uchar = ""
                while not uchar:
                    try:
                        uchar = stroke.decode(self.encoding)
                    except UnicodeDecodeError:
                        c = self.stdscr.getch()
                        stroke += chr(c)

                if uchar:
                    if self.input_cursor == len(self.input):
                        self.input += uchar
                    else:
                        # Insert into string
                        self.input = self.input[:self.input_cursor] + uchar + self.input[self.input_cursor:]

                    # Move the cursor forward
                    self.input_cursor += 1

        # Update the input string on the screen
        self.add_string(self.rows - 1, self.input)
        try:
            self.stdscr.move(self.rows - 1, self.input_cursor)
        except curses.error:
            pass
        self.stdscr.refresh()

    def close(self):
        """
        Clean up the curses stuff on exit.
        """
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
