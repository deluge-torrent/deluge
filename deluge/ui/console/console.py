# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import optparse
import os
import sys

from deluge.ui.console import UI_PATH
from deluge.ui.ui import UI


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
            aliases = [filename.split('.')[len(filename.split('.')) - 2]]
            aliases.extend(cmd.aliases)
            for a in aliases:
                commands.append((a, cmd))
        return dict(commands)
    except OSError:
        return {}


class Console(UI):

    help = """Starts the Deluge console interface"""
    cmdline = """A console or command-line interface"""

    def __init__(self, *args, **kwargs):
        super(Console, self).__init__("console", *args, **kwargs)
        group = optparse.OptionGroup(self.parser, "Console Options", "These options control how "
                                     "the console connects to the daemon.  These options will be "
                                     "used if you pass a command, or if you have autoconnect "
                                     "enabled for the console ui.")

        group.add_option("-d", "--daemon", dest="daemon_addr",
                         action="store", type="str", default="127.0.0.1",
                         help="Set the address of the daemon to connect to. [default: %default]")
        group.add_option("-p", "--port", dest="daemon_port",
                         help="Set the port to connect to the daemon on. [default: %default]",
                         action="store", type="int", default=58846)
        group.add_option("-u", "--username", dest="daemon_user",
                         help="Set the username to connect to the daemon with. [default: %default]",
                         action="store", type="string")
        group.add_option("-P", "--password", dest="daemon_pass",
                         help="Set the password to connect to the daemon with. [default: %default]",
                         action="store", type="string")
        self.parser.add_option_group(group)

        self.cmds = load_commands(os.path.join(UI_PATH, 'commands'))

        class CommandOptionGroup(optparse.OptionGroup):
            def __init__(self, parser, title, description=None, cmds=None):
                optparse.OptionGroup.__init__(self, parser, title, description)
                self.cmds = cmds

            def format_help(self, formatter):
                result = formatter.format_heading(self.title)
                formatter.indent()
                if self.description:
                    result += "%s\n" % formatter.format_description(self.description)
                for cname in self.cmds:
                    cmd = self.cmds[cname]
                    if cmd.interactive_only or cname in cmd.aliases:
                        continue
                    allnames = [cname]
                    allnames.extend(cmd.aliases)
                    cname = "/".join(allnames)
                    result += formatter.format_heading(" - ".join([cname, cmd.__doc__]))
                    formatter.indent()
                    result += "%*s%s\n" % (formatter.current_indent, "", cmd.usage)
                    formatter.dedent()
                formatter.dedent()
                return result
        cmd_group = CommandOptionGroup(self.parser, "Console Commands",
                                       description="The following commands can be issued at the "
                                       "command line.  Commands should be quoted, so, for example, "
                                       "to pause torrent with id 'abc' you would run: '%s "
                                       "\"pause abc\"'" % os.path.basename(sys.argv[0]),
                                       cmds=self.cmds)
        self.parser.add_option_group(cmd_group)

    def start(self, args=None):
        from main import ConsoleUI
        super(Console, self).start(args)
        ConsoleUI(self.args, self.cmds, (self.options.daemon_addr,
                  self.options.daemon_port, self.options.daemon_user,
                  self.options.daemon_pass))
