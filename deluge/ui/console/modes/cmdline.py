# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
import re
from io import open

import deluge.component as component
import deluge.configmanager
from deluge.common import PY2
from deluge.decorators import overrides
from deluge.ui.console.cmdline.command import Commander
from deluge.ui.console.modes.basemode import BaseMode, move_cursor
from deluge.ui.console.utils import colors
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.utils.format_utils import (
    delete_alt_backspace,
    remove_formatting,
    strwidth,
)

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)
LINES_BUFFER_SIZE = 5000
INPUT_HISTORY_SIZE = 500
MAX_HISTFILE_SIZE = 2000


def complete_line(line, possible_matches):
    """Find the common prefix of possible matches.

    Proritizing matching-case elements.
    """

    if not possible_matches:
        return line

    line = line.replace(r'\ ', ' ')

    matches1 = []
    matches2 = []

    for match in possible_matches:
        match = remove_formatting(match)
        match = match.replace(r'\ ', ' ')
        m1, m2 = '', ''
        for i, c in enumerate(line):
            if m1 and m2:
                break
            if not m1 and c != line[i]:
                m1 = line[:i]
            if not m2 and c.lower() != line[i].lower():
                m2 = line[:i]
        if not m1:
            matches1.append(match)
        elif not m2:
            matches2.append(match)

    possible_matches = matches1 + matches2

    maxlen = 9001

    for match in possible_matches[1:]:
        for i, c in enumerate(match):
            try:
                if c.lower() != possible_matches[0][i].lower():
                    maxlen = min(maxlen, i)
                    break
            except IndexError:
                maxlen = min(maxlen, i)
                break

    return possible_matches[0][:maxlen].replace(' ', r'\ ')


def commonprefix(m):
    """Returns the longest common leading component from list of pathnames."""
    if not m:
        return ''
    s1 = min(m)
    s2 = max(m)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s2


class CmdLine(BaseMode, Commander):
    def __init__(self, stdscr, encoding=None):
        # Get a handle to the main console
        self.console = component.get('ConsoleUI')
        Commander.__init__(self, self.console._commands, interactive=True)

        self.batch_write = False

        # A list of strings to be displayed based on the offset (scroll)
        self.lines = []
        # The offset to display lines
        self.display_lines_offset = 0

        # Holds the user input and is cleared on 'enter'
        self.input = ''
        self.input_incomplete = ''

        # Keep track of where the cursor is
        self.input_cursor = 0
        # Keep a history of inputs
        self.input_history = []
        self.input_history_index = 0

        # Keep track of double- and multi-tabs
        self.tab_count = 0

        self.console_config = component.get('TorrentList').config

        # To avoid having to truncate the file every time we're writing
        # or doing it on exit(and therefore relying on an error-less
        # or in other words clean exit, we're going to have two files
        # that we swap around based on length
        config_dir = deluge.configmanager.get_config_dir()
        self.history_file = [
            os.path.join(config_dir, 'cmd_line.hist1'),
            os.path.join(config_dir, 'cmd_line.hist2'),
        ]
        self._hf_lines = [0, 0]
        if self.console_config['cmdline']['save_command_history']:
            try:
                with open(self.history_file[0], 'r', encoding='utf8') as _file:
                    lines1 = _file.read().splitlines()
                self._hf_lines[0] = len(lines1)
            except IOError:
                lines1 = []
                self._hf_lines[0] = 0

            try:
                with open(self.history_file[1], 'r', encoding='utf8') as _file:
                    lines2 = _file.read().splitlines()
                self._hf_lines[1] = len(lines2)
            except IOError:
                lines2 = []
                self._hf_lines[1] = 0

            # The non-full file is the active one
            if self._hf_lines[0] > self._hf_lines[1]:
                self.lines = lines1 + lines2
            else:
                self.lines = lines2 + lines1

            if len(self.lines) > MAX_HISTFILE_SIZE:
                self.lines = self.lines[-MAX_HISTFILE_SIZE:]

            # Instead of having additional input history file, we can
            # simply scan for lines beginning with ">>> "
            for i, line in enumerate(self.lines):
                line = remove_formatting(line)
                if line.startswith('>>> '):
                    console_input = line[4:]
                    if self.console_config['cmdline']['ignore_duplicate_lines']:
                        if len(self.input_history) > 0:
                            if self.input_history[-1] != console_input:
                                self.input_history.append(console_input)
                        else:
                            self.input_history.append(console_input)

            self.input_history_index = len(self.input_history)

        # show the cursor
        util.safe_curs_set(util.Curser.VERY_VISIBLE)
        BaseMode.__init__(self, stdscr, encoding, depend=['SessionProxy'])

    @overrides(component.Component)
    def update(self):
        if not component.get('ConsoleUI').is_active_mode(self):
            return
        # Update just the status bars
        self.draw_statusbars(bottom_row=-2, bottombar_help=False)
        move_cursor(self.stdscr, self.rows - 1, min(self.input_cursor, curses.COLS - 1))
        self.stdscr.refresh()

    @overrides(BaseMode)
    def pause(self):
        self.stdscr.leaveok(0)

    @overrides(BaseMode)
    def resume(self):
        util.safe_curs_set(util.Curser.VERY_VISIBLE)

    @overrides(BaseMode)
    def read_input(self):
        # Read the character
        c = self.stdscr.getch()

        # Either ESC or ALT+<some key>
        if c == util.KEY_ESC:
            n = self.stdscr.getch()
            if n == -1:
                # Escape key
                return
            c = [c, n]

        # We remove the tab count if the key wasn't a tab
        if c != util.KEY_TAB:
            self.tab_count = 0

        # We clear the input string and send it to the command parser on ENTER
        if c in [curses.KEY_ENTER, util.KEY_ENTER2]:
            if self.input:
                if self.input.endswith('\\'):
                    self.input = self.input[:-1]
                    self.input_cursor -= 1
                self.add_line('{!yellow,black,bold!}>>>{!input!} %s' % self.input)
                self.do_command(self.input)
                if len(self.input_history) == INPUT_HISTORY_SIZE:
                    # Remove the oldest input history if the max history size
                    # is reached.
                    del self.input_history[0]
                if self.console_config['cmdline']['ignore_duplicate_lines']:
                    if len(self.input_history) > 0:
                        if self.input_history[-1] != self.input:
                            self.input_history.append(self.input)
                    else:
                        self.input_history.append(self.input)
                else:
                    self.input_history.append(self.input)
                self.input_history_index = len(self.input_history)
                self.input = ''
                self.input_incomplete = ''
                self.input_cursor = 0
                self.stdscr.refresh()

        # Run the tab completer function
        elif c == util.KEY_TAB:
            # Keep track of tab hit count to know when it's double-hit
            self.tab_count += 1

            if self.tab_completer:
                # We only call the tab completer function if we're at the end of
                # the input string on the cursor is on a space
                if (
                    self.input_cursor == len(self.input)
                    or self.input[self.input_cursor] == ' '
                ):
                    self.input, self.input_cursor = self.tab_completer(
                        self.input, self.input_cursor, self.tab_count
                    )

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

        # Delete a character in the input string based on cursor position
        elif c in [curses.KEY_BACKSPACE, util.KEY_BACKSPACE2]:
            if self.input and self.input_cursor > 0:
                self.input = (
                    self.input[: self.input_cursor - 1]
                    + self.input[self.input_cursor :]
                )
                self.input_cursor -= 1
        # Delete a word when alt+backspace is pressed
        elif c == [util.KEY_ESC, util.KEY_BACKSPACE2] or c == [
            util.KEY_ESC,
            curses.KEY_BACKSPACE,
        ]:
            self.input, self.input_cursor = delete_alt_backspace(
                self.input, self.input_cursor
            )
        elif c == curses.KEY_DC:
            if self.input and self.input_cursor < len(self.input):
                self.input = (
                    self.input[: self.input_cursor]
                    + self.input[self.input_cursor + 1 :]
                )

        # A key to add to the input string
        else:
            if c > 31 and c < 256:
                # Emulate getwch
                stroke = chr(c)
                uchar = '' if PY2 else stroke
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
                        self.input = (
                            self.input[: self.input_cursor]
                            + uchar
                            + self.input[self.input_cursor :]
                        )

                    # Move the cursor forward
                    self.input_cursor += 1

        self.refresh()

    @overrides(BaseMode)
    def on_resize(self, rows, cols):
        BaseMode.on_resize(self, rows, cols)
        self.stdscr.erase()
        self.refresh()

    @overrides(BaseMode)
    def refresh(self):
        """
        Refreshes the screen.
        Updates the lines based on the`:attr:lines` based on the `:attr:display_lines_offset`
        attribute and the status bars.
        """
        if not component.get('ConsoleUI').is_active_mode(self):
            return
        self.stdscr.erase()

        # Update the status bars
        self.add_string(0, self.statusbars.topbar)
        self.add_string(self.rows - 2, self.statusbars.bottombar)

        # The number of rows minus the status bars and the input line
        available_lines = self.rows - 3
        # If the amount of lines exceeds the number of rows, we need to figure out
        # which ones to display based on the offset
        if len(self.lines) > available_lines:
            # Get the lines to display based on the offset
            offset = len(self.lines) - self.display_lines_offset
            lines = self.lines[-(available_lines - offset) : offset]
        elif len(self.lines) == available_lines:
            lines = self.lines
        else:
            lines = [''] * (available_lines - len(self.lines))
            lines.extend(self.lines)

        # Add the lines to the screen
        for index, line in enumerate(lines):
            self.add_string(index + 1, line)

        # Add the input string
        self.add_string(self.rows - 1, self.input, pad=False, trim=False)

        move_cursor(self.stdscr, self.rows - 1, min(self.input_cursor, curses.COLS - 1))
        self.stdscr.redrawwin()
        self.stdscr.refresh()

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

        if self.console_config['cmdline']['save_command_history']:
            # Determine which file is the active one
            # If both are under maximum, it's first, otherwise it's the one not full
            if (
                self._hf_lines[0] < MAX_HISTFILE_SIZE
                and self._hf_lines[1] < MAX_HISTFILE_SIZE
            ):
                active_file = 0
            elif self._hf_lines[0] == MAX_HISTFILE_SIZE:
                active_file = 1
            else:
                active_file = 0

            # Write the line
            with open(self.history_file[active_file], 'a', encoding='utf8') as _file:
                _file.write(text + '\n')

            # And increment line counter
            self._hf_lines[active_file] += 1

            # If the active file reaches max size, we truncate it
            # therefore swapping the currently active file
            if self._hf_lines[active_file] == MAX_HISTFILE_SIZE:
                self._hf_lines[1 - active_file] = 0
                with open(
                    self.history_file[1 - active_file], 'w', encoding='utf8'
                ) as _file:
                    _file.truncate(0)

        def get_line_chunks(line):
            """
            Returns a list of 2-tuples (color string, text)

            """
            if not line or line.count('{!') != line.count('!}'):
                return []

            chunks = []
            if not line.startswith('{!'):
                begin = line.find('{!')
                if begin == -1:
                    begin = len(line)
                chunks.append(('', line[:begin]))
                line = line[begin:]

            while line:
                # We know the line starts with "{!" here
                end_color = line.find('!}')
                next_color = line.find('{!', end_color)
                if next_color == -1:
                    next_color = len(line)
                chunks.append((line[: end_color + 2], line[end_color + 2 : next_color]))
                line = line[next_color:]
            return chunks

        for line in text.splitlines():
            # We need to check for line lengths here and split as necessary
            try:
                line_length = colors.get_line_width(line)
            except colors.BadColorString:
                log.error('Passed a bad colored line: %s', line)
                continue

            if line_length >= (self.cols - 1):
                s = ''
                # The length of the text without the color tags
                s_len = 0
                # We need to split this over multiple lines
                for chunk in get_line_chunks(line):
                    if (strwidth(chunk[1]) + s_len) < (self.cols - 1):
                        # This chunk plus the current string in 's' isn't over
                        # the maximum width, so just append the color tag and text
                        s += chunk[0] + chunk[1]
                        s_len += strwidth(chunk[1])
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
                        s_len = strwidth(chunk[1][remain:])
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

    def _add_string(self, row, string):
        """
        Adds a string to the desired `:param:row`.

        :param row: int, the row number to write the string

        """
        col = 0
        try:
            parsed = colors.parse_color_string(string)
        except colors.BadColorString as ex:
            log.error('Cannot add bad color string %s: %s', string, ex)
            return

        for index, (color, p_str) in enumerate(parsed):
            if index + 1 == len(parsed):
                # This is the last string so lets append some " " to it
                p_str += ' ' * (self.cols - (col + strwidth(p_str)) - 1)
            try:
                self.stdscr.addstr(row, col, p_str.encode(self.encoding), color)
            except curses.error:
                pass

            col += strwidth(p_str)

    def set_batch_write(self, batch):
        """
        When this is set the screen is not refreshed after a `:meth:write` until
        this is set to False.

        :param batch: set True to prevent screen refreshes after a `:meth:write`
        :type batch: bool

        """
        self.batch_write = batch
        if not batch:
            self.refresh()

    def write(self, line):
        """
        Writes a line out

        :param line: str, the line to print

        """

        self.add_line(line, not self.batch_write)

    def tab_completer(self, line, cursor, hits):
        """
        Called when the user hits 'tab' and will autocomplete or show options.
        If a command is already supplied in the line, this function will call the
        complete method of the command.

        :param line: str, the current input string
        :param cursor: int, the cursor position in the line
        :param second_hit: bool, if this is the second time in a row the tab key
            has been pressed

        :returns: 2-tuple (string, cursor position)

        """
        # First check to see if there is no space, this will mean that it's a
        # command that needs to be completed.

        # We don't want to split by escaped spaces
        def split(string):
            return re.split(r'(?<!\\) ', string)

        if ' ' not in line:
            possible_matches = []
            # Iterate through the commands looking for ones that startwith the
            # line.
            for cmd in self.console._commands:
                if cmd.startswith(line):
                    possible_matches.append(cmd)

            line_prefix = ''
        else:
            cmd = split(line)[0]
            if cmd in self.console._commands:
                # Call the command's complete method to get 'er done
                possible_matches = self.console._commands[cmd].complete(split(line)[-1])
                line_prefix = ' '.join(split(line)[:-1]) + ' '
            else:
                # This is a bogus command
                return (line, cursor)

        # No matches, so just return what we got passed
        if len(possible_matches) == 0:
            return (line, cursor)
        # If we only have 1 possible match, then just modify the line and
        # return it, else we need to print out the matches without modifying
        # the line.
        elif len(possible_matches) == 1:
            # Do not append space after directory names
            new_line = line_prefix + possible_matches[0]
            if not new_line.endswith('/') and not new_line.endswith(r'\\'):
                new_line += ' '
            # We only want to print eventual colors or other control characters, not return them
            new_line = remove_formatting(new_line)
            return (new_line, len(new_line))
        else:
            if hits == 1:
                p = ' '.join(split(line)[:-1])

                try:
                    l_arg = split(line)[-1]
                except IndexError:
                    l_arg = ''

                new_line = ' '.join(
                    [p, complete_line(l_arg, possible_matches)]
                ).lstrip()

                if len(remove_formatting(new_line)) > len(line):
                    line = new_line
                    cursor = len(line)
            elif hits >= 2:
                max_list = self.console_config['cmdline']['torrents_per_tab_press']
                match_count = len(possible_matches)
                listed = (hits - 2) * max_list
                pages = (match_count - 1) // max_list + 1
                left = match_count - listed
                if hits == 2:
                    self.write(' ')

                    if match_count >= 4:
                        self.write('{!green!}Autocompletion matches:')
                # Only list some of the matching torrents as there can be hundreds of them
                if self.console_config['cmdline']['third_tab_lists_all']:
                    if hits == 2 and left > max_list:
                        for i in range(listed, listed + max_list):
                            match = possible_matches[i]
                            self.write(match.replace(r'\ ', ' '))
                        self.write(
                            '{!error!}And %i more. Press <tab> to list them'
                            % (left - max_list)
                        )
                    else:
                        self.tab_count = 0
                        for match in possible_matches[listed:]:
                            self.write(match.replace(r'\ ', ' '))
                else:
                    if left > max_list:
                        for i in range(listed, listed + max_list):
                            match = possible_matches[i]
                            self.write(match.replace(r'\ ', ' '))
                        self.write(
                            '{!error!}And %i more (%i/%i). Press <tab> to view more'
                            % (left - max_list, hits - 1, pages)
                        )
                    else:
                        self.tab_count = 0
                        for match in possible_matches[listed:]:
                            self.write(match.replace(r'\ ', ' '))
                        if hits > 2:
                            self.write(
                                '{!green!}Finished listing %i torrents (%i/%i)'
                                % (match_count, hits - 1, pages)
                            )

            # We only want to print eventual colors or other control characters, not return them
            line = remove_formatting(line)
            cursor = len(line)
            return (line, cursor)

    def tab_complete_path(
        self, line, path_type='file', ext='', sort='name', dirs_first=1
    ):
        self.console = component.get('ConsoleUI')

        line = line.replace('\\ ', ' ')
        line = os.path.abspath(os.path.expanduser(line))
        ret = []
        if os.path.exists(line):
            # This is a correct path, check to see if it's a directory
            if os.path.isdir(line):
                # Directory, so we need to show contents of directory
                # ret.extend(os.listdir(line))
                try:
                    for f in os.listdir(line):
                        # Skip hidden
                        if f.startswith('.'):
                            continue
                        f = os.path.join(line, f)
                        if os.path.isdir(f):
                            if os.sep == '\\':  # Windows path support
                                f += '\\'
                            else:  # Unix
                                f += '/'
                        elif not f.endswith(ext):
                            continue
                        ret.append(f)
                except OSError:
                    self.console.write('{!error!}Permission denied: {!info!}%s' % line)
            else:
                try:
                    # This is a file, but we could be looking for another file that
                    # shares a common prefix.
                    for f in os.listdir(os.path.dirname(line)):
                        if f.startswith(os.path.split(line)[1]):
                            ret.append(os.path.join(os.path.dirname(line), f))
                except OSError:
                    self.console.write('{!error!}Permission denied: {!info!}%s' % line)
        else:
            # This path does not exist, so lets do a listdir on it's parent
            # and find any matches.
            try:
                ret = []
                if os.path.isdir(os.path.dirname(line)):
                    for f in os.listdir(os.path.dirname(line)):
                        if f.startswith(os.path.split(line)[1]):
                            p = os.path.join(os.path.dirname(line), f)

                            if os.path.isdir(p):
                                if os.sep == '\\':  # Windows path support
                                    p += '\\'
                                else:  # Unix
                                    p += '/'
                            ret.append(p)
            except OSError:
                self.console.write('{!error!}Permission denied: {!info!}%s' % line)

        if sort == 'date':
            ret = sorted(ret, key=os.path.getmtime, reverse=True)

        if dirs_first == 1:
            ret = sorted(ret, key=os.path.isdir, reverse=True)
        elif dirs_first == -1:
            ret = sorted(ret, key=os.path.isdir, reverse=False)

        # Highlight directory names
        for i, filename in enumerate(ret):
            if os.path.isdir(filename):
                ret[i] = '{!cyan!}%s' % filename

        for i in range(0, len(ret)):
            ret[i] = ret[i].replace(' ', r'\ ')
        return ret

    def tab_complete_torrent(self, line):
        """
        Completes torrent_ids or names.

        :param line: str, the string to complete

        :returns: list of matches

        """

        empty = len(line) == 0

        # Remove dangling backslashes to avoid breaking shlex
        if line.endswith('\\'):
            line = line[:-1]

        raw_line = line
        line = line.replace('\\ ', ' ')

        possible_matches = []
        possible_matches2 = []

        match_count = 0
        match_count2 = 0
        for torrent_id, torrent_name in self.console.torrents:
            if torrent_id.startswith(line):
                match_count += 1
            if torrent_name.startswith(line):
                match_count += 1
            elif torrent_name.lower().startswith(line.lower()):
                match_count2 += 1

        # Find all possible matches
        for torrent_id, torrent_name in self.console.torrents:
            # Escape spaces to avoid, for example, expanding "Doc" into "Doctor Who" and removing
            # everything containing one of these words
            escaped_name = torrent_name.replace(' ', '\\ ')
            # If we only matched one torrent, don't add the full name or it'll also get autocompleted
            if match_count == 1:
                if torrent_id.startswith(line):
                    possible_matches.append(torrent_id)
                    break
                if torrent_name.startswith(line):
                    possible_matches.append(escaped_name)
                    break
            elif match_count == 0 and match_count2 == 1:
                if torrent_name.lower().startswith(line.lower()):
                    possible_matches.append(escaped_name)
                    break
            else:
                line_len = len(raw_line)

                # Let's avoid listing all torrents twice if there's no pattern
                if not empty and torrent_id.startswith(line):
                    # Highlight the matching part
                    text = '{!info!}%s{!input!}%s - "%s"' % (
                        torrent_id[:line_len],
                        torrent_id[line_len:],
                        torrent_name,
                    )
                    possible_matches.append(text)
                if torrent_name.startswith(line):
                    text = '{!info!}%s{!input!}%s ({!cyan!}%s{!input!})' % (
                        escaped_name[:line_len],
                        escaped_name[line_len:],
                        torrent_id,
                    )
                    possible_matches.append(text)
                elif torrent_name.lower().startswith(line.lower()):
                    text = '{!info!}%s{!input!}%s ({!cyan!}%s{!input!})' % (
                        escaped_name[:line_len],
                        escaped_name[line_len:],
                        torrent_id,
                    )
                    possible_matches2.append(text)

        return possible_matches + possible_matches2
