# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

import argparse
import shlex

import deluge.component as component
from deluge.ui.console.utils.colors import ConsoleColorFormatter


class OptionParserError(Exception):
    pass


class ConsoleBaseParser(argparse.ArgumentParser):
    def format_help(self):
        """Differs from ArgumentParser.format_help by adding the raw epilog
        as formatted in the string. Default behavior mangles the formatting.

        """
        # Handle epilog manually to keep the text formatting
        epilog = self.epilog
        self.epilog = ''
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
            if ';' in a:
                cmd_lines = [arg.strip() for arg in a.split(';')]
            elif ' ' in a:
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
            if hasattr(self.base_parser, 'subcommand'):
                subcommand = getattr(self.base_parser, 'subcommand')
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

        if not hasattr(options, 'remaining'):
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
        raise OptionParserError(msg)

    def print_usage(self, _file=None):
        console = component.get('ConsoleUI')
        if self.usage:
            for line in self.format_usage().splitlines():
                console.write(line)

    def print_help(self, _file=None):
        console = component.get('ConsoleUI')
        console.set_batch_write(True)
        for line in self.format_help().splitlines():
            console.write(line)
        console.set_batch_write(False)

    def format_help(self):
        """Return help formatted with colors."""
        help_str = super(OptionParser, self).format_help()
        return self.formatter.format_colors(help_str)
