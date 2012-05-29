#
# legacy.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
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

try:
    import curses
except ImportError:
    pass


from basemode import BaseMode
import deluge.ui.console.colors as colors
from twisted.internet import defer, reactor
from deluge.ui.client import client
import deluge.component as component

from deluge.ui.console.modes import format_utils
strwidth = format_utils.strwidth

import logging,os
log = logging.getLogger(__name__)

import re

LINES_BUFFER_SIZE = 5000
INPUT_HISTORY_SIZE = 500

def complete_line(line, possible_matches):
    "Find the common prefix of possible matches, proritizing matching-case elements"

    if not possible_matches: return line

    line = line.replace(r"\ ", " ")

    matches1 = []
    matches2 = []

    for match in possible_matches:
        match = format_utils.remove_formatting(match)
        match = match.replace(r"\ ", " ")
        m1, m2 = "", ""
        for i, c in enumerate(line):
            if m1 and m2: break
            if not m1 and c != line[i]:
                m1 = line[:i]
            if not m2 and c.lower() != line[i].lower():
                m2 = line[:i]
        if   not m1: matches1.append(match)
        elif not m2: matches2.append(match)

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

    return possible_matches[0][:maxlen].replace(" ", r"\ ")

def commonprefix(m):
    "Given a list of pathnames, returns the longest common leading component"
    if not m: return ''
    s1 = min(m)
    s2 = max(m)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s


class Legacy(BaseMode, component.Component):
    def __init__(self, stdscr, encoding=None):

        component.Component.__init__(self, "LegacyUI")

        self.batch_write = False
        self.lines = []

        # A list of strings to be displayed based on the offset (scroll)
        self.lines = []
        # The offset to display lines
        self.display_lines_offset = 0

        # Holds the user input and is cleared on 'enter'
        self.input = ""
        self.input_incomplete = ""
        # Keep track of where the cursor is
        self.input_cursor = 0
        # Keep a history of inputs
        self.input_history = []
        self.input_history_index = 0

        # Keep track of double- and multi-tabs
        self.tab_count = 0

        # Get a handle to the main console
        self.console = component.get("ConsoleUI")

        self.console_config = component.get("AllTorrents").config

        # show the cursor
        curses.curs_set(2)

        BaseMode.__init__(self, stdscr, encoding)

        # This gets fired once we have received the torrents list from the core
        self.started_deferred = defer.Deferred()

        # Maintain a list of (torrent_id, name) for use in tab completion
        self.torrents = []
        def on_session_state(result):
            def on_torrents_status(torrents):
                for torrent_id, status in torrents.items():
                    self.torrents.append((torrent_id, status["name"]))
                self.started_deferred.callback(True)

            client.core.get_torrents_status({"id": result}, ["name"]).addCallback(on_torrents_status)
        client.core.get_session_state().addCallback(on_session_state)

        # Register some event handlers to keep the torrent list up-to-date
        client.register_event_handler("TorrentAddedEvent", self.on_torrent_added_event)
        client.register_event_handler("TorrentRemovedEvent", self.on_torrent_removed_event)

    def update(self):
        pass

    def _doRead(self):
        # Read the character
        c = self.stdscr.getch()

        # We remove the tab count if the key wasn't a tab
        if c != 9:
            self.tab_count = 0

        # We clear the input string and send it to the command parser on ENTER
        if c == curses.KEY_ENTER or c == 10:
            if self.input:
                if self.input.endswith('\\'):
                    self.input = self.input[:-1]
                    self.input_cursor -= 1
                self.add_line(">>> " + self.input)
                self.do_command(self.input.encode(self.encoding))
                if len(self.input_history) == INPUT_HISTORY_SIZE:
                    # Remove the oldest input history if the max history size
                    # is reached.
                    del self.input_history[0]
                if self.console_config["ignore_duplicate_lines"]:
                    if len(self.input_history) > 0:
                        if self.input_history[-1] != self.input:
                            self.input_history.append(self.input)
                    else:
                        self.input_history.append(self.input)
                else:
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

            if self.tab_completer:
                # We only call the tab completer function if we're at the end of
                # the input string on the cursor is on a space
                if self.input_cursor == len(self.input) or self.input[self.input_cursor] == " ":
                    self.input, self.input_cursor = self.tab_completer(self.input, self.input_cursor, self.tab_count)

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
        elif c == curses.KEY_BACKSPACE or c == 127:
            if self.input and self.input_cursor > 0:
                self.input = self.input[:self.input_cursor - 1] + self.input[self.input_cursor:]
                self.input_cursor -= 1

        # Delete a word when alt+backspace is pressed
        elif c == 27:
            sep_chars = " *?!._~-#$^;'\""
            deleted = 0
            seg_start = self.input[:self.input_cursor]
            seg_end = self.input[self.input_cursor:]

            while seg_start and self.input_cursor > 0:
                if (not seg_start) or (self.input_cursor == 0):
                    break
                if deleted and seg_start[-1] in sep_chars:
                    break

                seg_start = seg_start[:-1]
                deleted += 1
                self.input_cursor -= 1
            self.input = seg_start + seg_end

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



    def refresh(self):
        """
        Refreshes the screen.
        Updates the lines based on the`:attr:lines` based on the `:attr:display_lines_offset`
        attribute and the status bars.
        """
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

        if component.get("ConsoleUI").screen != self:
            return

        # Move the cursor
        try:
            self.stdscr.move(self.rows - 1, self.input_cursor)
        except curses.error:
            pass
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
                line_length = colors.get_line_width(line)
            except colors.BadColorString:
                log.error("Passed a bad colored line: %s", line)
                continue

            if line_length >= (self.cols - 1):
                s = ""
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
                s += " " * (self.cols - (col + strwidth(s)) - 1)
            try:
                self.stdscr.addstr(row, col, s, color)
            except curses.error:
                pass

            col += strwidth(s)


    def do_command(self, cmd):
        """
        Processes a command.

        :param cmd: str, the command string

        """
        if not cmd:
            return
        cmd, _, line = cmd.partition(' ')
        try:
            parser = self.console._commands[cmd].create_parser()
        except KeyError:
            self.write("{!error!}Unknown command: %s" % cmd)
            return

        try:
            args = self.console._commands[cmd].split(line)
        except ValueError, e:
            self.write("{!error!}Error parsing command: %s" % e)
            return

        # Do a little hack here to print 'command --help' properly
        parser._print_help = parser.print_help
        def print_help(f=None):
            parser._print_help(f)
        parser.print_help = print_help

        # Only these commands can be run when not connected to a daemon
        not_connected_cmds = ["help", "connect", "quit"]
        aliases = []
        for c in not_connected_cmds:
            aliases.extend(self.console._commands[c].aliases)
        not_connected_cmds.extend(aliases)

        if not client.connected() and cmd not in not_connected_cmds:
            self.write("{!error!}Not connected to a daemon, please use the connect command first.")
            return

        try:
            options, args = parser.parse_args(args)
        except Exception, e:
            self.write("{!error!}Error parsing options: %s" % e)
            return

        if not getattr(options, '_exit', False):
            try:
                ret = self.console._commands[cmd].handle(*args, **options.__dict__)
            except Exception, e:
                self.write("{!error!}" + str(e))
                log.exception(e)
                import traceback
                self.write("%s" % traceback.format_exc())
                return defer.succeed(True)
            else:
                return ret



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

        #We don't want to split by escaped spaces
        def split(string):
            return re.split(r"(?<!\\) ", string)

        if " " not in line:
            possible_matches = []
            # Iterate through the commands looking for ones that startwith the
            # line.
            for cmd in self.console._commands:
                if cmd.startswith(line):
                    possible_matches.append(cmd)

            line_prefix = ""
        else:
            cmd = split(line)[0]
            if cmd in self.console._commands:
                # Call the command's complete method to get 'er done
                possible_matches = self.console._commands[cmd].complete(split(line)[-1])
                line_prefix = " ".join(split(line)[:-1]) + " "
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
            #Do not append space after directory names
            new_line = line_prefix + possible_matches[0]
            if not new_line.endswith("/") and not new_line.endswith(r"\\"):
                new_line += " "
            #We only want to print eventual colors or other control characters, not return them
            new_line = format_utils.remove_formatting(new_line)
            return (new_line, len(new_line))
        else:
            if   hits == 1:
                p = " ".join(split(line)[:-1])

                try:
                    l_arg = split(line)[-1]
                except IndexError:
                    l_arg = ""

                new_line = " ".join( [p, complete_line(l_arg, possible_matches)] ).lstrip()

                if len(format_utils.remove_formatting(new_line)) > len(line):
                    line = new_line
                    cursor = len(line)
            elif hits >= 2:
                max_list = self.console_config["torrents_per_tab_press"]
                match_count = len(possible_matches)
                listed = (hits-2) * max_list
                pages = (match_count-1) // max_list + 1
                left = match_count - listed
                if hits == 2:
                    self.write(" ")

                    if match_count >= 4:
                        self.write("{!green!}Autocompletion matches:")
                #Only list some of the matching torrents as there can be hundreds of them
                if self.console_config["third_tab_lists_all"]:
                    if hits == 2 and left > max_list:
                        for i in range(listed, listed + max_list):
                            match = possible_matches[i]
                            self.write(match.replace(r"\ ", " "))
                        self.write("{!error!}And %i more. Press <tab> to list them" % (left - max_list) )
                    else:
                        self.tab_count = 0
                        for match in possible_matches[listed:]:
                            self.write(match.replace(r"\ ", " "))
                else:
                    if left > max_list:
                        for i in range(listed, listed + max_list):
                            match = possible_matches[i]
                            self.write(match.replace(r"\ ", " "))
                        self.write("{!error!}And %i more (%i/%i). Press <tab> to view more" % (left - max_list, hits-1, pages) )
                    else:
                        self.tab_count = 0
                        for match in possible_matches[listed:]:
                            self.write(match.replace(r"\ ", " "))
                        if hits > 2:
                            self.write("{!green!}Finished listing %i torrents (%i/%i)" % (match_count, hits-1, pages) )

            #We only want to print eventual colors or other control characters, not return them
            line = format_utils.remove_formatting(line)
            cursor = len(line)
            return (line, cursor)


    def tab_complete_torrent(self, line):
        """
        Completes torrent_ids or names.

        :param line: str, the string to complete

        :returns: list of matches

        """

        if len(line) == 0:
            empty = True
        else:
            empty = False

        #Remove dangling backslashes to avoid breaking shlex
        if line.endswith("\\"):
            line = line[:-1]

        raw_line = line
        line = line.replace("\\ ", " ")

        possible_matches = []
        possible_matches2 = []

        match_count  = 0
        match_count2 = 0
        for torrent_id, torrent_name in self.torrents:
            if torrent_id.startswith(line):
                match_count += 1
            if torrent_name.startswith(line):
                match_count += 1
            elif torrent_name.lower().startswith(line.lower()):
                match_count2 += 1

        # Find all possible matches
        for torrent_id, torrent_name in self.torrents:
            #Escape spaces to avoid, for example, expanding "Doc" into "Doctor Who" and removing everything containing one of these words
            escaped_name = torrent_name.replace(" ","\\ ")
            #If we only matched one torrent, don't add the full name or it'll also get autocompleted
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
                l = len(raw_line)

                #Let's avoid listing all torrents twice if there's no pattern
                if not empty and torrent_id.startswith(line):
                    #Highlight the matching part
                    text = "{!info!}%s{!input!}%s - '%s'" % (torrent_id[:l], torrent_id[l:], torrent_name)
                    possible_matches.append(text)
                if torrent_name.startswith(line):
                    text = "{!info!}%s{!input!}%s ({!cyan!}%s{!input!})" % (escaped_name[:l], escaped_name[l:], torrent_id)
                    possible_matches.append(text)
                elif torrent_name.lower().startswith(line.lower()):
                    text = "{!info!}%s{!input!}%s ({!cyan!}%s{!input!})" % (escaped_name[:l], escaped_name[l:], torrent_id)
                    possible_matches2.append(text)

        return possible_matches + possible_matches2

    def get_torrent_name(self, torrent_id):
        """
        Gets a torrent name from the torrents list.

        :param torrent_id: str, the torrent_id

        :returns: the name of the torrent or None
        """

        for tid, name in self.torrents:
            if torrent_id == tid:
                return name

        return None

    def match_torrent(self, string):
        """
        Returns a list of torrent_id matches for the string.  It will search both
        torrent_ids and torrent names, but will only return torrent_ids.

        :param string: str, the string to match on

        :returns: list of matching torrent_ids. Will return an empty list if
            no matches are found.

        """
        ret = []
        for tid, name in self.torrents:
            if tid.startswith(string) or name.startswith(string):
                ret.append(tid)

        return ret

    def on_torrent_added_event(self, event):
        def on_torrent_status(status):
            self.torrents.append((event.torrent_id, status["name"]))
        client.core.get_torrent_status(event.torrent_id, ["name"]).addCallback(on_torrent_status)

    def on_torrent_removed_event(self, event):
        for index, (tid, name) in enumerate(self.torrents):
            if event.torrent_id == tid:
                del self.torrents[index]
