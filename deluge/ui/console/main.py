#
# main.py
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
# 	Boston, MA    02110-1301, USA.
#

import os, sys
import optparse
import shlex

from twisted.internet import defer, reactor

from deluge.ui.console import UI_PATH
import deluge.component as component
from deluge.ui.client import client
import deluge.common
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.console.statusbars import StatusBars
from deluge.ui.console.eventlog import EventLog
import deluge.ui.console.screen as screen
import deluge.ui.console.colors as colors
from deluge.log import LOG as log

# XXX: Remove when the commands are all fixed up
def match_torrents(a=[]):
    pass

class OptionParser(optparse.OptionParser):
    """subclass from optparse.OptionParser so exit() won't exit."""
    def exit(self, status=0, msg=None):
        self.values._exit = True
        if msg:
            print msg

    def error(self, msg):
        """error(msg : string)

           Print a usage message incorporating 'msg' to stderr and exit.
           If you override this in a subclass, it should not return -- it
           should either exit or raise an exception.
        """
        raise

class BaseCommand(object):

    usage = 'usage'
    option_list = tuple()
    aliases = []

    def complete(self, text, *args):
        return []
    def handle(self, *args, **options):
        pass

    @property
    def name(self):
        return 'base'

    @property
    def epilog(self):
        return self.__doc__

    def split(self, text):
        return shlex.split(text)

    def create_parser(self):
        return OptionParser(prog = self.name,
                            usage = self.usage,
                            epilog = self.epilog,
                            option_list = self.option_list)

def load_commands(command_dir, exclude=[]):
    def get_command(name):
        return getattr(__import__('deluge.ui.console.commands.%s' % name, {}, {}, ['Command']), 'Command')()

    try:
        commands = []
        for filename in os.listdir(command_dir):
            if filename.split('.')[0] in exclude or filename.startswith('_') or not filename.endswith('.py'):
                continue
            cmd = get_command(filename[:-3])
            aliases = [ filename[:-3] ]
            aliases.extend(cmd.aliases)
            for a in aliases:
                commands.append((a, cmd))
        return dict(commands)
    except OSError, e:
        return {}

class ConsoleUI(component.Component):
    def __init__(self, args=None):
        component.Component.__init__(self, "ConsoleUI", 2)
        # Load all the commands
        self._commands = load_commands(os.path.join(UI_PATH, 'commands'))

        # Try to connect to the localhost daemon
        def on_connect(result):
            component.start()
        client.connect().addCallback(on_connect)

        # Set the interactive flag to indicate where we should print the output
        self.interactive = True
        if args:
            self.interactive = False
            # If we have args, lets process them and quit
            #allow multiple commands split by ";"
            for arg in args.split(";"):
                self.do_command(arg)
            sys.exit(0)

        self.coreconfig = CoreConfig()

        # We use the curses.wrapper function to prevent the console from getting
        # messed up if an uncaught exception is experienced.
        import curses.wrapper
        curses.wrapper(self.run)

    def run(self, stdscr):
        """
        This method is called by the curses.wrapper to start the mainloop and
        screen.

        :param stdscr: curses screen passed in from curses.wrapper

        """
        # We want to do an interactive session, so start up the curses screen and
        # pass it the function that handles commands
        colors.init_colors()
        self.screen = screen.Screen(stdscr, self.do_command, self.tab_completer)
        self.statusbars = StatusBars()
        self.eventlog = EventLog()

        self.screen.topbar = "{{status}}Deluge " + deluge.common.get_version() + " Console"
        self.screen.bottombar = "{{status}}"
        self.screen.refresh()

        # The Screen object is designed to run as a twisted reader so that it
        # can use twisted's select poll for non-blocking user input.
        reactor.addReader(self.screen)

        # Start the twisted mainloop
        reactor.run()

    def start(self):
        # Maintain a list of (torrent_id, name) for use in tab completion
        self.torrents = []
        def on_session_state(result):
            def on_torrents_status(torrents):
                for torrent_id, status in torrents.items():
                    self.torrents.append((torrent_id, status["name"]))

            client.core.get_torrents_status({"id": result}, ["name"]).addCallback(on_torrents_status)
        client.core.get_session_state().addCallback(on_session_state)

        # Register some event handlers to keep the torrent list up-to-date
        client.register_event_handler("TorrentAddedEvent", self.on_torrent_added_event)
        client.register_event_handler("TorrentRemovedEvent", self.on_torrent_removed_event)

    def update(self):
        pass

    def write(self, line):
        """
        Writes a line out depending on if we're in interactive mode or not.

        :param line: str, the line to print

        """
        if self.interactive:
            self.screen.add_line(line)
        else:
            print(line)

    def do_command(self, cmd):
        """
        Processes a command.

        :param cmd: str, the command string

        """
        if not cmd:
            return
        cmd, _, line = cmd.partition(' ')
        try:
            parser = self._commands[cmd].create_parser()
        except KeyError:
            self.write("{{error}}Unknown command: %s" % cmd)
            return
        args = self._commands[cmd].split(line)

        # Do a little hack here to print 'command --help' properly
        parser._print_help = parser.print_help
        def print_help(f=None):
            if self.interactive:
                self.write(parser.format_help())
            else:
                parser._print_help(f)
        parser.print_help = print_help

        options, args = parser.parse_args(args)
        if not getattr(options, '_exit', False):
            try:
                self._commands[cmd].handle(*args, **options.__dict__)
            except Exception, e:
                self.write("{{error}}" + str(e))
                log.exception(e)
                import traceback
                self.write("%s" % traceback.format_exc())

    def tab_completer(self, line, cursor, second_hit):
        """
        Called when the user hits 'tab' and will autocomplete or show options.

        :param line: str, the current input string
        :param cursor: int, the cursor position in the line
        :param second_hit: bool, if this is the second time in a row the tab key
            has been pressed

        :returns: 2-tuple (string, cursor position)

        """
        # First check to see if there is no space, this will mean that it's a
        # command that needs to be completed.
        if " " not in line:
            if len(line) == 0:
                # We only print these out if it's a second_hit
                if second_hit:
                    # There is nothing in line so just print out all possible commands
                    # and return.
                    self.write(" ")
                    for cmd in self._commands:
                        self.write(cmd)
                return ("", 0)
            # Iterate through the commands looking for ones that startwith the
            # line.
            possible_matches = []
            for cmd in self._commands:
                if cmd.startswith(line):
                    possible_matches.append(cmd)

            line_prefix = ""

        else:
            # This isn't a command so treat it as a torrent_id or torrent name
            name = line.split(" ")[-1]
            if len(name) == 0:
                # There is nothing in the string, so just display all possible options
                if second_hit:
                    self.write(" ")
                    # Display all torrent_ids and torrent names
                    for torrent_id, name in self.torrents:
                        self.write(torrent_id)
                        self.write(name)
                return (line, cursor)

            # Find all possible matches
            possible_matches = []
            for torrent_id, torrent_name in self.torrents:
                if torrent_id.startswith(name):
                    possible_matches.append(torrent_id)
                elif torrent_name.startswith(name):
                    possible_matches.append(torrent_name)

            # Set the line prefix that should be prepended to any input line match
            line_prefix = " ".join(line.split(" ")[:-1]) + " "

        # No matches, so just return what we got passed
        if len(possible_matches) == 0:
            return (line, cursor)
        # If we only have 1 possible match, then just modify the line and
        # return it, else we need to print out the matches without modifying
        # the line.
        elif len(possible_matches) == 1:
            new_line = line_prefix + possible_matches[0] + " "
            return (new_line, len(new_line))
        else:
            if second_hit:
                # Only print these out if it's a second_hit
                self.write(" ")
                for cmd in possible_matches:
                    self.write(cmd)
            return (line, cursor)

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

    def on_torrent_added_event(self, torrent_id):
        def on_torrent_status(status):
            self.torrents.append((torrent_id, status["name"]))
        client.core.get_torrent_status(torrent_id, ["name"]).addCallback(on_torrent_status)

    def on_torrent_removed_event(self, torrent_id):
        for index, (tid, name) in enumerate(self.torrents):
            if torrent_id == tid:
                del self.torrents[index]
