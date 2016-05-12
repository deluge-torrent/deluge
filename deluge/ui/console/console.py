# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os

import deluge.common
from deluge.ui.baseargparser import DelugeTextHelpFormatter
from deluge.ui.console import UI_PATH
from deluge.ui.ui import UI

log = logging.getLogger(__name__)

#
# Note: Cannot import from console.main here because it imports the twisted reactor.
# Console is imported from console/__init__.py loaded by the script entry points
# defined in setup.py
#


def load_commands(command_dir):

    def get_command(name):
        return getattr(__import__('deluge.ui.console.commands.%s' % name, {}, {}, ['Command']), 'Command')()

    try:
        commands = []
        for filename in os.listdir(command_dir):
            if filename.startswith('_'):
                continue
            if not (filename.endswith('.py') or filename.endswith('.pyc')):
                continue
            cmd = get_command(filename.split('.')[len(filename.split('.')) - 2])
            cmd._name = filename.split('.')[len(filename.split('.')) - 2]
            names = [cmd._name]
            names.extend(cmd.aliases)
            for a in names:
                commands.append((a, cmd))
        return dict(commands)
    except OSError:
        return {}


class Console(UI):

    cmd_description = """Console or command-line user interface"""

    def __init__(self, *args, **kwargs):
        super(Console, self).__init__("console", *args, description="Test", **kwargs)

        group = self.parser.add_argument_group(_("Console Options"), "These daemon connect options will be "
                                               "used for commands, or if console ui autoconnect is enabled.")
        group.add_argument("-d", "--daemon", dest="daemon_addr", required=False, default="127.0.0.1")
        group.add_argument("-p", "--port", dest="daemon_port", type=int, required=False, default="58846")
        group.add_argument("-U", "--username", dest="daemon_user", required=False)
        group.add_argument("-P", "--password", dest="daemon_pass", required=False)

        # To properly print help message for the console commands ( e.g. deluge-console info -h),
        # we add a subparser for each command which will trigger the help/usage when given
        from deluge.ui.console.main import ConsoleCommandParser  # import here because (see top)
        self.console_parser = ConsoleCommandParser(parents=[self.parser], add_help=False,
                                                   description="Starts the Deluge console interface",
                                                   formatter_class=lambda prog:
                                                   DelugeTextHelpFormatter(prog, max_help_position=33, width=90))
        self.parser.subparser = self.console_parser
        subparsers = self.console_parser.add_subparsers(title="Console commands", help="Description", dest="commands",
                                                        description="The following console commands are available:",
                                                        metavar="command")
        self.console_cmds = load_commands(os.path.join(UI_PATH, "commands"))
        for c in sorted(self.console_cmds):
            self.console_cmds[c].add_subparser(subparsers)

    def start(self, args=None):
        super(Console, self).start(args)
        from deluge.ui.console.main import ConsoleUI  # import here because (see top)

        def run(options):
            try:
                ConsoleUI(self.options, self.console_cmds)
            except Exception as ex:
                log.exception(ex)
                raise

        deluge.common.run_profiled(run, self.options, output_file=self.options.profile,
                                   do_profile=self.options.profile)
