# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.internet import defer

import deluge.component as component
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """displays help on other commands"""

    usage = "Usage: help [command]"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        self._commands = self.console._commands
        deferred = defer.succeed(True)
        if args:
            for arg in args:
                try:
                    cmd = self._commands[arg]
                except KeyError:
                    self.console.write("{!error!}Unknown command %r" % args[0])
                    continue
                try:
                    parser = cmd.create_parser()
                    self.console.write(parser.format_help())
                except AttributeError:
                    self.console.write(cmd.__doc__ or "No help for this command")
                self.console.write(" ")
        else:
            self.console.set_batch_write(True)
            for cmd in sorted(self._commands):
                self.console.write("{!info!}" + cmd + "{!input!} - " + self._commands[cmd].__doc__ or '')
            self.console.write(" ")
            self.console.write("For help on a specific command, use '<command> --help'")
            self.console.set_batch_write(False)

        return deferred

    def complete(self, line):
        return [x for x in component.get("ConsoleUI")._commands if x.startswith(line)]
