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
import sys

from twisted.internet import defer

import deluge.component as component
from deluge.error import DelugeError
from deluge.ui.client import client
from deluge.ui.console.colors import strip_colors

log = logging.getLogger(__name__)


class Commander:
    def __init__(self, cmds, interactive=False):
        self._commands = cmds
        self.console = component.get("ConsoleUI")
        self.interactive = interactive

    def write(self, line):
        print(strip_colors(line))

    def do_command(self, cmd):
        """
        Processes a command.

        :param cmd: str, the command string

        """
        if not cmd:
            return
        cmd, _, line = cmd.partition(" ")
        try:
            parser = self._commands[cmd].create_parser()
        except KeyError:
            self.write("{!error!}Unknown command: %s" % cmd)
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
        except TypeError as ex:
            self.write("{!error!}Error parsing options: %s" % ex)
            return

        if not getattr(options, "_exit", False):
            try:
                ret = self._commands[cmd].handle(*args, **options.__dict__)
            except Exception as ex:
                self.write("{!error!} %s" % ex)
                log.exception(ex)
                import traceback
                self.write("%s" % traceback.format_exc())
                return defer.succeed(True)
            else:
                return ret

    def exec_args(self, args, host, port, username, password):
        commands = []
        if args:
            # Multiple commands split by ";"
            commands = [arg.strip() for arg in args.split(";")]

        def on_connect(result):
            def on_started(result):
                def on_started(result):
                    def do_command(result, cmd):
                        return self.do_command(cmd)
                    d = defer.succeed(None)
                    for command in commands:
                        if command in ("quit", "exit"):
                            break
                        d.addCallback(do_command, command)
                    d.addCallback(do_command, "quit")

                # We need to wait for the rpcs in start() to finish before processing
                # any of the commands.
                self.console.started_deferred.addCallback(on_started)
            component.start().addCallback(on_started)

        def on_connect_fail(reason):
            if reason.check(DelugeError):
                rm = reason.value.message
            else:
                rm = reason.getErrorMessage()
            if host:
                print("Could not connect to daemon: %s:%s\n %s" % (host, port, rm))
            else:
                print("Could not connect to localhost daemon\n %s" % rm)
            self.do_command("quit")

        if host:
            d = client.connect(host, port, username, password)
        else:
            d = client.connect()
        if not self.interactive:
            if commands[0].startswith("connect"):
                d = self.do_command(commands.pop(0))
            elif "help" in commands:
                self.do_command("help")
                sys.exit(0)
        d.addCallback(on_connect)
        d.addErrback(on_connect_fail)
