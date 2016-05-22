# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import argparse
import locale
import logging
import shlex
import sys

from twisted.internet import defer, reactor

import deluge.common
import deluge.component as component
from deluge.error import DelugeError
from deluge.ui.client import client
from deluge.ui.console import colors
from deluge.ui.console.colors import ConsoleColorFormatter
from deluge.ui.console.commander import Commander
from deluge.ui.console.eventlog import EventLog
from deluge.ui.console.statusbars import StatusBars
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.sessionproxy import SessionProxy

log = logging.getLogger(__name__)


class ConsoleBaseParser(argparse.ArgumentParser):

    def format_help(self):
        """
        Differs from ArgumentParser.format_help by adding the raw epilog
        as formatted in the string. Default bahavior mangles the formatting.

        """
        # Handle epilog manually to keep the text formatting
        epilog = self.epilog
        self.epilog = ""
        help_str = super(ConsoleBaseParser, self).format_help()
        if epilog is not None:
            help_str += epilog
        self.epilog = epilog
        return help_str


class ConsoleCommandParser(ConsoleBaseParser):

    def _split_args(self, args):
        command_options = []
        for a in args:
            if not a:
                continue
            if ";" in a:
                cmd_lines = [arg.strip() for arg in a.split(";")]
            elif " " in a:
                cmd_lines = [a]
            else:
                continue

            for cmd_line in cmd_lines:
                cmds = shlex.split(cmd_line)
                cmd_options = super(ConsoleCommandParser, self).parse_args(args=cmds)
                cmd_options.command = cmds[0]
                command_options.append(cmd_options)

        return command_options

    def parse_args(self, args=None):
        """Parse known UI args and handle common and process group options.

            Notes:
                If started by deluge entry script this has already been done.

            Args:
                args (list, optional): The arguments to parse.

            Returns:
                argparse.Namespace: The parsed arguments.
        """
        from deluge.ui.ui_entry import AMBIGUOUS_CMD_ARGS
        self.base_parser.parse_known_ui_args(args, withhold=AMBIGUOUS_CMD_ARGS)

        multi_command = self._split_args(args)
        # If multiple commands were passed to console
        if multi_command:
            # With multiple commands, normal parsing will fail, so only parse
            # known arguments using the base parser, and then set
            # options.parsed_cmds to the already parsed commands
            options, remaining = self.base_parser.parse_known_args(args=args)
            options.parsed_cmds = multi_command
        else:
            subcommand = False
            if hasattr(self.base_parser, "subcommand"):
                subcommand = getattr(self.base_parser, "subcommand")
            if not subcommand:
                # We must use parse_known_args to handle case when no subcommand
                # is provided, because argparse does not support parsing without
                # a subcommand
                options, remaining = self.base_parser.parse_known_args(args=args)
                # If any options remain it means they do not exist. Reparse with
                # parse_args to trigger help message
                if remaining:
                    options = self.base_parser.parse_args(args=args)
                options.parsed_cmds = []
            else:
                options = super(ConsoleCommandParser, self).parse_args(args=args)
                options.parsed_cmds = [options]

        if not hasattr(options, "remaining"):
            options.remaining = []

        return options


class OptionParser(ConsoleBaseParser):

    def __init__(self, **kwargs):
        super(OptionParser, self).__init__(**kwargs)
        self.formatter = ConsoleColorFormatter()

    def exit(self, status=0, msg=None):
        self._exit = True
        if msg:
            print(msg)

    def error(self, msg):
        """error(msg : string)

           Print a usage message incorporating 'msg' to stderr and exit.
           If you override this in a subclass, it should not return -- it
           should either exit or raise an exception.
        """
        raise Exception(msg)

    def print_usage(self, _file=None):
        console = component.get("ConsoleUI")
        if self.usage:
            for line in self.format_usage().splitlines():
                console.write(line)

    def print_help(self, _file=None):
        console = component.get("ConsoleUI")
        console.set_batch_write(True)
        for line in self.format_help().splitlines():
            console.write(line)
        console.set_batch_write(False)

    def format_help(self):
        """Return help formatted with colors."""
        help_str = super(OptionParser, self).format_help()
        return self.formatter.format_colors(help_str)


class BaseCommand(object):

    usage = None
    interactive_only = False
    aliases = []
    _name = "base"
    epilog = ""

    def complete(self, text, *args):
        return []

    def handle(self, options):
        pass

    @property
    def name(self):
        return self._name

    @property
    def name_with_alias(self):
        return "/".join([self._name] + self.aliases)

    @property
    def description(self):
        return self.__doc__

    def split(self, text):
        if deluge.common.windows_check():
            text = text.replace("\\", "\\\\")
        result = shlex.split(text)
        for i, s in enumerate(result):
            result[i] = s.replace(r"\ ", " ")
        result = [s for s in result if s != ""]
        return result

    def create_parser(self):
        opts = {"prog": self.name_with_alias, "description": self.__doc__, "epilog": self.epilog}
        if self.usage:
            opts["usage"] = self.usage
        parser = OptionParser(**opts)
        parser.add_argument(self.name, metavar="")
        parser.base_parser = parser
        self.add_arguments(parser)
        return parser

    def add_subparser(self, subparsers):
        opts = {"prog": self.name_with_alias, "help": self.__doc__, "description": self.__doc__}
        if self.usage:
            opts["usage"] = self.usage
        parser = subparsers.add_parser(self.name, **opts)
        self.add_arguments(parser)

    def add_arguments(self, parser):
        pass


class ConsoleUI(component.Component):

    def __init__(self, options=None, cmds=None):
        component.Component.__init__(self, "ConsoleUI", 2)
        # keep track of events for the log view
        self.events = []
        self.statusbars = None
        try:
            locale.setlocale(locale.LC_ALL, "")
            self.encoding = locale.getpreferredencoding()
        except Exception:
            self.encoding = sys.getdefaultencoding()

        log.debug("Using encoding: %s", self.encoding)

        # start up the session proxy
        self.sessionproxy = SessionProxy()

        client.set_disconnect_callback(self.on_client_disconnect)

        # Set the interactive flag to indicate where we should print the output
        self.interactive = True
        self._commands = cmds
        if options.parsed_cmds:
            self.interactive = False
            if not cmds:
                print("Sorry, couldn't find any commands")
                return
            else:
                self.exec_args(options)

        self.coreconfig = CoreConfig()
        if self.interactive and not deluge.common.windows_check():
            # We use the curses.wrapper function to prevent the console from getting
            # messed up if an uncaught exception is experienced.
            import curses.wrapper
            curses.wrapper(self.run)
        elif self.interactive and deluge.common.windows_check():
            print("""\nDeluge-console does not run in interactive mode on Windows. \n
Please use commands from the command line, e.g.:\n
    deluge-console.exe help
    deluge-console.exe info
    deluge-console.exe "add --help"
    deluge-console.exe "add -p c:\\mytorrents c:\\new.torrent"
            """)
        else:
            reactor.run()

    def exec_args(self, options):
        commander = Commander(self._commands)

        def on_connect(result):
            def on_started(result):
                def on_started(result):
                    def do_command(result, cmd):
                        return commander.do_command(cmd)

                    def exec_command(result, cmd):
                        return commander.exec_command(cmd)
                    d = defer.succeed(None)
                    for command in options.parsed_cmds:
                        if command.command in ("quit", "exit"):
                            break
                        d.addCallback(exec_command, command)
                    d.addCallback(do_command, "quit")

                # We need to wait for the rpcs in start() to finish before processing
                # any of the commands.
                self.started_deferred.addCallback(on_started)
            component.start().addCallback(on_started)

        def on_connect_fail(reason):
            if reason.check(DelugeError):
                rm = reason.getErrorMessage()
            else:
                rm = reason.value.message
            print("Could not connect to daemon: %s:%s\n %s" % (options.daemon_addr, options.daemon_port, rm))
            commander.do_command("quit")

        d = None
        if not self.interactive and options.parsed_cmds[0].command == "connect":
            d = commander.do_command(options.parsed_cmds.pop(0))
        else:
            log.info("connect: host=%s, port=%s, username=%s, password=%s",
                     options.daemon_addr, options.daemon_port, options.daemon_user, options.daemon_pass)
            d = client.connect(options.daemon_addr, options.daemon_port, options.daemon_user, options.daemon_pass)
        d.addCallback(on_connect)
        d.addErrback(on_connect_fail)

    def run(self, stdscr):
        """
        This method is called by the curses.wrapper to start the mainloop and
        screen.

        :param stdscr: curses screen passed in from curses.wrapper

        """
        # We want to do an interactive session, so start up the curses screen and
        # pass it the function that handles commands
        colors.init_colors()
        self.statusbars = StatusBars()
        from deluge.ui.console.modes.connectionmanager import ConnectionManager
        self.stdscr = stdscr
        self.screen = ConnectionManager(stdscr, self.encoding)
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
        # Maintain a list of (torrent_id, name) for use in tab completion
        self.torrents = []
        if not self.interactive:
            self.started_deferred = defer.Deferred()

            def on_session_state(result):
                def on_torrents_status(torrents):
                    for torrent_id, status in torrents.items():
                        self.torrents.append((torrent_id, status["name"]))
                    self.started_deferred.callback(True)

                client.core.get_torrents_status({"id": result}, ["name"]).addCallback(on_torrents_status)
            client.core.get_session_state().addCallback(on_session_state)

    def match_torrent(self, string):
        """
        Returns a list of torrent_id matches for the string.  It will search both
        torrent_ids and torrent names, but will only return torrent_ids.

        :param string: str, the string to match on

        :returns: list of matching torrent_ids. Will return an empty list if
            no matches are found.

        """
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.match_torrent(string)
        matches = []

        string = string.decode(self.encoding)
        for tid, name in self.torrents:
            if tid.startswith(string) or name.startswith(string):
                matches.append(tid)

        return matches

    def get_torrent_name(self, torrent_id):
        if self.interactive and hasattr(self.screen, "get_torrent_name"):
            return self.screen.get_torrent_name(torrent_id)

        for tid, name in self.torrents:
            if torrent_id == tid:
                return name

        return None

    def set_batch_write(self, batch):
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.set_batch_write(batch)

    def tab_complete_torrent(self, line):
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.tab_complete_torrent(line)

    def tab_complete_path(self, line, path_type="file", ext="", sort="name", dirs_first=True):
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.tab_complete_path(line, path_type=path_type, ext=ext, sort=sort, dirs_first=dirs_first)

    def set_mode(self, mode):
        reactor.removeReader(self.screen)
        self.screen = mode
        self.statusbars.screen = self.screen
        reactor.addReader(self.screen)
        self.stdscr.clear()
        mode.refresh()

    def on_client_disconnect(self):
        component.stop()

    def write(self, s):
        if self.interactive:
            if isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
                self.screen.write(s)
            else:
                component.get("LegacyUI").add_line(s, False)
                self.events.append(s)
        else:
            print(colors.strip_colors(deluge.common.utf8_encoded(s)))

    def write_event(self, s):
        if self.interactive:
            if isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
                self.events.append(s)
                self.screen.write(s)
            else:
                component.get("LegacyUI").add_line(s, False)
                self.events.append(s)
        else:
            print(colors.strip_colors(deluge.common.utf8_encoded(s)))
