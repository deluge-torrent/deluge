# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import print_function, unicode_literals

import fnmatch
import logging
import os
import sys

import deluge.common
from deluge.argparserbase import ArgParserBase, DelugeTextHelpFormatter
from deluge.ui.ui import UI

log = logging.getLogger(__name__)

#
# Note: Cannot import from console.main here because it imports the twisted reactor.
# Console is imported from console/__init__.py loaded by the script entry points
# defined in setup.py
#


def load_commands(command_dir):
    def get_command(name):
        command = getattr(
            __import__(
                'deluge.ui.console.cmdline.commands.%s' % name, {}, {}, ['Command']
            ),
            'Command',
        )()
        command._name = name
        return command

    try:
        dir_list = fnmatch.filter(os.listdir(command_dir), '*.py')
    except OSError:
        return {}

    commands = []
    for filename in dir_list:
        if filename.startswith('_'):
            continue
        cmd = get_command(os.path.splitext(filename)[0])
        for cmd_name in [cmd._name] + cmd.aliases:
            commands.append((cmd_name, cmd))
    return dict(commands)


class LogStream(object):
    out = sys.stdout

    def write(self, data):
        self.out.write(data)

    def flush(self):
        self.out.flush()


class Console(UI):

    cmd_description = """Console or command-line user interface"""

    def __init__(self, *args, **kwargs):
        super(Console, self).__init__(
            'console', *args, log_stream=LogStream(), **kwargs
        )

        group = self.parser.add_argument_group(
            _('Console Options'),
            _(
                'These daemon connect options will be '
                'used for commands, or if console ui autoconnect is enabled.'
            ),
        )
        group.add_argument(
            '-d',
            '--daemon',
            metavar='<ip_addr>',
            dest='daemon_addr',
            help=_('Deluge daemon IP address to connect to (default 127.0.0.1)'),
            default='127.0.0.1',
        )
        group.add_argument(
            '-p',
            '--port',
            metavar='<port>',
            dest='daemon_port',
            type=int,
            help=_('Deluge daemon port to connect to (default 58846)'),
            default='58846',
        )
        group.add_argument(
            '-U',
            '--username',
            metavar='<user>',
            dest='daemon_user',
            help=_('Deluge daemon username to use when connecting'),
        )
        group.add_argument(
            '-P',
            '--password',
            metavar='<pass>',
            dest='daemon_pass',
            help=_('Deluge daemon password to use when connecting'),
        )
        # To properly print help message for the console commands ( e.g. deluge-console info -h),
        # we add a subparser for each command which will trigger the help/usage when given
        from deluge.ui.console.parser import (  # import here because (see top)
            ConsoleCommandParser,
        )

        self.console_parser = ConsoleCommandParser(
            parents=[self.parser],
            add_help=False,
            prog=self.parser.prog,
            description='Starts the Deluge console interface',
            formatter_class=lambda prog: DelugeTextHelpFormatter(
                prog, max_help_position=33, width=90
            ),
        )
        self.parser.subparser = self.console_parser
        self.console_parser.base_parser = self.parser
        subparsers = self.console_parser.add_subparsers(
            title=_('Console Commands'),
            help=_('Description'),
            description=_('The following console commands are available:'),
            metavar=_('Command'),
            dest='command',
        )
        from deluge.ui.console import UI_PATH  # Must import here

        self.console_cmds = load_commands(os.path.join(UI_PATH, 'cmdline', 'commands'))
        for cmd in sorted(self.console_cmds):
            self.console_cmds[cmd].add_subparser(subparsers)

    def start(self):
        if self.ui_args is None:
            # Started directly by deluge-console script so must find the UI args manually
            options, remaining = ArgParserBase(common_help=False).parse_known_args()
            self.ui_args = remaining

        i = self.console_parser.find_subcommand(args=self.ui_args)
        self.console_parser.subcommand = False
        self.parser.subcommand = False if i == -1 else True

        super(Console, self).start(self.console_parser)
        from deluge.ui.console.main import ConsoleUI  # import here because (see top)

        def run(options):
            try:
                c = ConsoleUI(self.options, self.console_cmds, self.parser.log_stream)
                return c.start_ui()
            except Exception as ex:
                log.exception(ex)
                raise

        return deluge.common.run_profiled(
            run,
            self.options,
            output_file=self.options.profile,
            do_profile=self.options.profile,
        )
