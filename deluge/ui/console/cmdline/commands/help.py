# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from twisted.internet import defer

import deluge.component as component

from . import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Displays help on other commands"""

    def add_arguments(self, parser):
        parser.add_argument(
            'commands', metavar='<command>', nargs='*', help=_('One or more commands')
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')
        self._commands = self.console._commands
        deferred = defer.succeed(True)
        if options.commands:
            for arg in options.commands:
                try:
                    cmd = self._commands[arg]
                except KeyError:
                    self.console.write('{!error!}Unknown command %s' % arg)
                    continue
                try:
                    parser = cmd.create_parser()
                    self.console.write(parser.format_help())
                except AttributeError:
                    self.console.write(cmd.__doc__ or 'No help for this command')
                self.console.write(' ')
        else:
            self.console.set_batch_write(True)
            cmds_doc = ''
            for cmd in sorted(self._commands):
                if cmd in self._commands[cmd].aliases:
                    continue
                parser = self._commands[cmd].create_parser()
                cmd_doc = (
                    '{!info!}'
                    + '%-9s' % self._commands[cmd].name_with_alias
                    + '{!input!} - '
                    + self._commands[cmd].__doc__
                    + '\n     '
                    + parser.format_usage()
                    or ''
                )
                cmds_doc += parser.formatter.format_colors(cmd_doc)
            self.console.write(cmds_doc)
            self.console.write(' ')
            self.console.write('For help on a specific command, use `<command> --help`')
            self.console.set_batch_write(False)

        return deferred

    def complete(self, line):
        return [x for x in component.get('ConsoleUI')._commands if x.startswith(line)]
