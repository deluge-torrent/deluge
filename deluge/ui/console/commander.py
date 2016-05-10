# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


from __future__ import print_function

import logging

from twisted.internet import defer

from deluge.ui.client import client
from deluge.ui.console.colors import strip_colors

log = logging.getLogger(__name__)


class Commander(object):

    def __init__(self, cmds, interactive=False):
        self._commands = cmds
        self.interactive = interactive

    def write(self, line):
        print(strip_colors(line))

    def do_command(self, cmd_line):
        """Run a console command

        Args:
            cmd_line (str): Console command

        Returns:
            Deferred: A deferred that fires when command has been executed

        """
        options = self.parse_command(cmd_line)
        if options:
            return self.exec_command(options)
        return defer.succeed(None)

    def parse_command(self, cmd_line):
        """Parse a console command and process with argparse

        Args:
            cmd_line (str): Console command

        Returns:
            argparse.Namespace: The parsed command

        """
        if not cmd_line:
            return
        cmd, _, line = cmd_line.partition(" ")
        try:
            parser = self._commands[cmd].create_parser()
        except KeyError:
            self.write("{!error!}Unknown command: %s" % cmd)
            return

        try:
            args = [cmd] + self._commands[cmd].split(line)
        except ValueError as ex:
            self.write("{!error!}Error parsing command: %s" % ex)
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
            options = parser.parse_args(args=args)
            options.command = cmd
        except TypeError as ex:
            self.write("{!error!}Error parsing options: %s" % ex)
            import traceback
            self.write("%s" % traceback.format_exc())
            return
        except Exception as ex:
            self.write("{!error!} %s" % ex)
            parser.print_help()
            return

        if getattr(parser, "_exit", False):
            return
        return options

    def exec_command(self, options, *args):
        """
        Execute a console command.

        Args:
            options (argparse.Namespace): The command to execute

        Returns:
            Deferred: A deferred that fires when command has been executed

        """
        try:
            ret = self._commands[options.command].handle(options)
        except Exception as ex:
            self.write("{!error!} %s" % ex)
            log.exception(ex)
            import traceback
            self.write("%s" % traceback.format_exc())
            return defer.succeed(True)
        else:
            return ret
