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

from __future__ import print_function, unicode_literals

import logging
import shlex

from twisted.internet import defer

from deluge.ui.client import client
from deluge.ui.console.parser import OptionParser, OptionParserError
from deluge.ui.console.utils.colors import strip_colors

log = logging.getLogger(__name__)


class Commander(object):
    def __init__(self, cmds, interactive=False):
        self._commands = cmds
        self.interactive = interactive

    def write(self, line):
        print(strip_colors(line))

    def do_command(self, cmd_line):
        """Run a console command.

        Args:
            cmd_line (str): Console command.

        Returns:
            Deferred: A deferred that fires when the command has been executed.

        """
        options = self.parse_command(cmd_line)
        if options:
            return self.exec_command(options)
        return defer.succeed(None)

    def exit(self, status=0, msg=None):
        self._exit = True
        if msg:
            print(msg)

    def parse_command(self, cmd_line):
        """Parse a console command and process with argparse.

        Args:
            cmd_line (str): Console command.

        Returns:
            argparse.Namespace: The parsed command.

        """
        if not cmd_line:
            return
        cmd, _, line = cmd_line.partition(' ')
        try:
            parser = self._commands[cmd].create_parser()
        except KeyError:
            self.write('{!error!}Unknown command: %s' % cmd)
            return

        try:
            args = [cmd] + self._commands[cmd].split(line)
        except ValueError as ex:
            self.write('{!error!}Error parsing command: %s' % ex)
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
        not_connected_cmds = ['help', 'connect', 'quit']
        aliases = []
        for c in not_connected_cmds:
            aliases.extend(self._commands[c].aliases)
        not_connected_cmds.extend(aliases)

        if not client.connected() and cmd not in not_connected_cmds:
            self.write(
                '{!error!}Not connected to a daemon, please use the connect command first.'
            )
            return

        try:
            options = parser.parse_args(args=args)
            options.command = cmd
        except TypeError as ex:
            self.write('{!error!}Error parsing options: %s' % ex)
            import traceback

            self.write('%s' % traceback.format_exc())
            return
        except OptionParserError as ex:
            import traceback

            log.warning('Error parsing command "%s":  %s', args, ex)
            self.write('{!error!} %s' % ex)
            parser.print_help()
            return

        if getattr(parser, '_exit', False):
            return
        return options

    def exec_command(self, options, *args):
        """Execute a console command.

        Args:
            options (argparse.Namespace): The command to execute.

        Returns:
            Deferred: A deferred that fires when command has been executed.

        """
        try:
            ret = self._commands[options.command].handle(options)
        except Exception as ex:  # pylint: disable=broad-except
            self.write('{!error!} %s' % ex)
            log.exception(ex)
            import traceback

            self.write('%s' % traceback.format_exc())
            return defer.succeed(True)
        else:
            return ret


class BaseCommand(object):

    usage = None
    interactive_only = False
    aliases = []
    _name = 'base'
    epilog = ''

    def complete(self, text, *args):
        return []

    def handle(self, options):
        pass

    @property
    def name(self):
        return self._name

    @property
    def name_with_alias(self):
        return '/'.join([self._name] + self.aliases)

    @property
    def description(self):
        return self.__doc__

    def split(self, text):
        text = text.replace('\\', '\\\\')
        result = shlex.split(text)
        for i, s in enumerate(result):
            result[i] = s.replace(r'\ ', ' ')
        result = [s for s in result if s != '']
        return result

    def create_parser(self):
        opts = {
            'prog': self.name_with_alias,
            'description': self.__doc__,
            'epilog': self.epilog,
        }
        if self.usage:
            opts['usage'] = self.usage
        parser = OptionParser(**opts)
        parser.add_argument(self.name, metavar='')
        parser.base_parser = parser
        self.add_arguments(parser)
        return parser

    def add_subparser(self, subparsers):
        opts = {
            'prog': self.name_with_alias,
            'help': self.__doc__,
            'description': self.__doc__,
        }
        if self.usage:
            opts['usage'] = self.usage

        # A workaround for aliases showing as duplicate command names in help output.
        for cmd_name in sorted([self.name] + self.aliases):
            if cmd_name not in subparsers._name_parser_map:
                if cmd_name in self.aliases:
                    opts['help'] = _('`%s` alias' % self.name)
                parser = subparsers.add_parser(cmd_name, **opts)
                break

        self.add_arguments(parser)

    def add_arguments(self, parser):
        pass
