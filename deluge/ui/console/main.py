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

import os, sys
import optparse
import shlex
import locale

from twisted.internet import defer, reactor

from deluge.ui.console import UI_PATH
import deluge.component as component
from deluge.ui.client import client
import deluge.common
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.console.statusbars import StatusBars
from deluge.ui.console.eventlog import EventLog
import screen
import colors
from deluge.log import LOG as log
from deluge.ui.ui import _UI

class Console(_UI):

    help = """Starts the Deluge console interface"""

    def __init__(self):
        super(Console, self).__init__("console")
        cmds = load_commands(os.path.join(UI_PATH, 'commands'))

        group = optparse.OptionGroup(self.parser, "Console Commands",
            "\n".join(cmds.keys()))
        self.parser.add_option_group(group)
        self.parser.disable_interspersed_args()

    def start(self):
        super(Console, self).start()

        ConsoleUI(self.args)

def start():
    Console().start()

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
        raise Exception(msg)

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
        if deluge.common.windows_check():
            text = text.replace('\\', '\\\\')
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
            if filename.split('.')[0] in exclude or filename.startswith('_'):
                continue
            if not (filename.endswith('.py') or filename.endswith('.pyc')):
                continue
            cmd = get_command(filename.split('.')[len(filename.split('.')) - 2])
            aliases = [ filename.split('.')[len(filename.split('.')) - 2] ]
            aliases.extend(cmd.aliases)
            for a in aliases:
                commands.append((a, cmd))
        return dict(commands)
    except OSError, e:
        return {}

class ConsoleUI(component.Component):
    def __init__(self, args=None):
        component.Component.__init__(self, "ConsoleUI", 2)

        self.batch_write = False

        try:
            locale.setlocale(locale.LC_ALL, '')
            self.encoding = locale.getpreferredencoding()
        except:
            self.encoding = sys.getdefaultencoding()

        log.debug("Using encoding: %s", self.encoding)
        # Load all the commands
        self._commands = load_commands(os.path.join(UI_PATH, 'commands'))

        client.set_disconnect_callback(self.on_client_disconnect)

        # Set the interactive flag to indicate where we should print the output
        self.interactive = True
        if args:
            # Multiple commands split by ";"
            commands = [arg.strip() for arg in ' '.join(args).split(';')]
            self.interactive = False

        # Try to connect to the daemon (localhost by default)
        def on_connect(result):
            def on_started(result):
                if not self.interactive:
                    def on_started(result):
                        def do_command(result, cmd):
                            return self.do_command(cmd)

                        d = defer.succeed(None)
                        # If we have commands, lets process them, then quit.
                        for command in commands:
                            d.addCallback(do_command, command)

                        if "quit" not in commands and "exit" not in commands:
                            d.addCallback(do_command, "quit")

                    # We need to wait for the rpcs in start() to finish before processing
                    # any of the commands.
                    self.started_deferred.addCallback(on_started)
            component.start().addCallback(on_started)

        def on_connect_fail(result):
            if not self.interactive:
                self.do_command('quit')

        connect_cmd = 'connect'
        if not self.interactive:
            if commands[0].startswith(connect_cmd):
                connect_cmd = commands.pop(0)
            elif 'help' in commands:
                self.do_command('help')
                return
        d = self.do_command(connect_cmd)
        d.addCallback(on_connect)
        d.addErrback(on_connect_fail)

        self.coreconfig = CoreConfig()
        if self.interactive and not deluge.common.windows_check():
            # We use the curses.wrapper function to prevent the console from getting
            # messed up if an uncaught exception is experienced.
            import curses.wrapper
            curses.wrapper(self.run)
        elif self.interactive and deluge.common.windows_check():
            print """\nDeluge-console does not run in interactive mode on Windows. \n
Please use commands from the command line, eg:\n
    deluge-console.exe help
    deluge-console.exe info
    deluge-console.exe "add --help"
    deluge-console.exe "add -p c:\\mytorrents c:\\new.torrent"
            """
        else:
            reactor.run()

    def run(self, stdscr):
        """
        This method is called by the curses.wrapper to start the mainloop and
        screen.

        :param stdscr: curses screen passed in from curses.wrapper

        """
        # We want to do an interactive session, so start up the curses screen and
        # pass it the function that handles commands
        colors.init_colors()
        self.screen = screen.Screen(stdscr, self.do_command, self.tab_completer, self.encoding)
        self.statusbars = StatusBars()
        self.eventlog = EventLog()

        self.screen.topbar = "{!status!}Deluge " + deluge.common.get_version() + " Console"
        self.screen.bottombar = "{!status!}"
        self.screen.refresh()

        # The Screen object is designed to run as a twisted reader so that it
        # can use twisted's select poll for non-blocking user input.
        reactor.addReader(self.screen)

        # Start the twisted mainloop
        reactor.run()

    def start(self):
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

    def set_batch_write(self, batch):
        """
        When this is set the screen is not refreshed after a `:meth:write` until
        this is set to False.

        :param batch: set True to prevent screen refreshes after a `:meth:write`
        :type batch: bool

        """
        self.batch_write = batch
        if not batch and self.interactive:
            self.screen.refresh()

    def write(self, line):
        """
        Writes a line out depending on if we're in interactive mode or not.

        :param line: str, the line to print

        """
        if self.interactive:
            self.screen.add_line(line, not self.batch_write)
        else:
            print colors.strip_colors(deluge.common.utf8_encoded(line))

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
            self.write("{!error!}Unknown command: %s" % cmd)
            return

        try:
            args = self._commands[cmd].split(line)
        except ValueError, e:
            self.write("{!error!}Error parsing command: %s" % e)
            return

        # Do a little hack here to print 'command --help' properly
        parser._print_help = parser.print_help
        def print_help(f=None):
            if self.interactive:
                self.write(parser.format_help())
            else:
                parser._print_help(f)
        parser.print_help = print_help

        # Only these commands can be run when not connected to a daemon
        not_connected_cmds = ["help", "connect", "quit"]
        aliases = []
        for c in not_connected_cmds:
            aliases.extend(self._commands[c].aliases)
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
                ret = self._commands[cmd].handle(*args, **options.__dict__)
            except Exception, e:
                self.write("{!error!}" + str(e))
                log.exception(e)
                import traceback
                self.write("%s" % traceback.format_exc())
                return defer.succeed(True)
            else:
                return ret

    def tab_completer(self, line, cursor, second_hit):
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
        if " " not in line:
            possible_matches = []
            # Iterate through the commands looking for ones that startwith the
            # line.
            for cmd in self._commands:
                if cmd.startswith(line):
                    possible_matches.append(cmd)

            line_prefix = ""
        else:
            cmd = line.split(" ")[0]
            if cmd in self._commands:
                # Call the command's complete method to get 'er done
                possible_matches = self._commands[cmd].complete(line.split(" ")[-1])
                line_prefix = " ".join(line.split(" ")[:-1]) + " "
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
            new_line = line_prefix + possible_matches[0] + " "
            return (new_line, len(new_line))
        else:
            if second_hit:
                # Only print these out if it's a second_hit
                self.write(" ")
                for match in possible_matches:
                    self.write(match)
            else:
                p = " ".join(line.split(" ")[:-1])
                new_line = " ".join([p, os.path.commonprefix(possible_matches)]).lstrip()
                if len(new_line) > len(line):
                    line = new_line
                    cursor = len(line)
            return (line, cursor)

    def tab_complete_torrent(self, line):
        """
        Completes torrent_ids or names.

        :param line: str, the string to complete

        :returns: list of matches

        """

        possible_matches = []

        # Find all possible matches
        for torrent_id, torrent_name in self.torrents:
            if torrent_id.startswith(line):
                possible_matches.append(torrent_id)
            torrent_name = deluge.common.decode_string(torrent_name)
            if torrent_name.startswith(line):
                possible_matches.append(torrent_name)

        return possible_matches

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
        string = string.decode(self.encoding)
        for tid, name in self.torrents:
            name = deluge.common.decode_string(name)
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

    def on_client_disconnect(self):
        component.stop()
