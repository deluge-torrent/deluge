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
from deluge.ui.console import UI_PATH
#from deluge.ui.console.colors import Template, make_style, templates, default_style as style
import deluge.component as component
from deluge.ui.client import client
import deluge.common
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.console.statusbars import StatusBars

from twisted.internet import defer, reactor
import shlex
import screen
import colors

from deluge.log import LOG as log

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


def match_torrents(array=[]):
    # Make sure we don't have any duplicates
    array = set(array)
    # We return this defer and it will be fired once we received the session
    # state and intersect the data.
    d = defer.Deferred()

    def _got_session_state(tors):
        if not array:
            d.callback(tors)
        d.callback(list(tors.intersection(array)))

    client.core.get_session_state().addCallback(_got_session_state)

    return d

def load_commands(command_dir, write_func, exclude=[]):
    def get_command(name):
        return getattr(__import__('deluge.ui.console.commands.%s' % name, {}, {}, ['Command']), 'Command')()

    try:
        commands = []
        for filename in os.listdir(command_dir):
            if filename.split('.')[0] in exclude or filename.startswith('_') or not filename.endswith('.py'):
                continue
            cmd = get_command(filename[:-3])
            # Hack to give the commands a write function
            cmd.write = write_func
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
        self._commands = load_commands(os.path.join(UI_PATH, 'commands'), self.write)

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
        self.screen = screen.Screen(stdscr, self.do_command)
        self.statusbars = StatusBars()

        self.screen.topbar = "{{status}}Deluge " + deluge.common.get_version() + " Console"
        self.screen.bottombar = "{{status}}"
        self.screen.refresh()

        # The Screen object is designed to run as a twisted reader so that it
        # can use twisted's select poll for non-blocking user input.
        reactor.addReader(self.screen)

        # Start the twisted mainloop
        reactor.run()

    def start(self):
        pass

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
            except StopIteration, e:
                raise
            except Exception, e:
                self.write("{{error}}" + str(e))
