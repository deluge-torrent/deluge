#!/usr/bin/env python
#
# main.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

#
import logging
logging.disable(logging.ERROR)
import os, sys
import optparse
from deluge.ui.console import UI_PATH
from deluge.ui.console.colors import Template, make_style, templates, default_style as style
from deluge.ui.client import aclient as client
from deluge.ui.common import get_localhost_auth_uri
import shlex


class OptionParser(optparse.OptionParser):
    """subclass from optparse.OptionParser so exit() won't exit."""
    def exit(self, status=0, msg=None):
        self.values._exit = True
        if msg:
            print msg

    def error(self, msg):
        """error(msg : string)

           Print a usage message incorporating 'msg' to stderr and exit.
           If you override this in a subclass, it should not return -- it
           should either exit or raise an exception.
        """
        raise


class BaseCommand(object):

    usage = 'usage'
    option_list = tuple()
    aliases = []


    def complete(self, text, *args):
        return []
    def handle(self, *args, **options):
        pass

    @property
    def name(self):
        return 'base'

    @property
    def epilog(self):
        return self.__doc__

    def split(self, text):
        return shlex.split(text)

    def create_parser(self):
        return OptionParser(prog = self.name,
                            usage = self.usage,
                            epilog = self.epilog,
                            option_list = self.option_list)

def match_torrents(array=None):
    global torrents
    if array is None:
        array = list()
    torrents = []
    array = set(array)
    def _got_session_state(tors):
        if not array:
            torrents.extend(tors)
            return
        tors = set(tors)
        torrents.extend(list(tors.intersection(array)))
        return
    client.get_session_state(_got_session_state)
    client.force_call()
    return torrents

def load_commands(command_dir, exclude=[]):
    def get_command(name):
        return getattr(__import__('deluge.ui.console.commands.%s' % name, {}, {}, ['Command']), 'Command')()

    try:
        commands = []
        for filename in os.listdir(command_dir):
            if filename.split('.')[0] in exclude or filename.startswith('_') or not filename.endswith('.py'):
                continue
            cmd = get_command(filename[:-3])
            aliases = [ filename[:-3] ]
            aliases.extend(cmd.aliases)
            for a in aliases:
                commands.append((a, cmd))
        return dict(commands)
    except OSError, e:
        return {}

class ConsoleUI(object):
    prompt = '>>> '

    def __init__(self, args=None):
        client.set_core_uri(get_localhost_auth_uri("http://localhost:58846"))
        self._commands = load_commands(os.path.join(UI_PATH, 'commands'))
        if args:
            self.precmd()
            #allow multiple commands split by ";"
            for arg in args.split(";"):
                self.onecmd(arg)
                self.postcmd()
            sys.exit(0)

    def completedefault(self, *ignored):
        """Method called to complete an input line when no command-specific
        method is available.

        By default, it returns an empty list.

        """
        return []

    def completenames(self, text, *ignored):
        return [n for n in self._commands.keys() if n.startswith(text)]

    def complete(self, text, state):
        """Return the next possible completion for 'text'.
        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx>0:
                cmd = line.split()[0]
                if cmd == '':
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self._commands[cmd], 'complete')
                    except AttributeError:
                        compfunc = self.completedefault
            else:
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def preloop(self):
        pass

    def postloop(self):
        pass

    def precmd(self):
        pass

    def onecmd(self, line):
        if not line:
            return
        cmd, _, line = line.partition(' ')
        try:
            parser = self._commands[cmd].create_parser()
        except KeyError:
            print templates.ERROR('unknown command: %s' % cmd)
            return
        args = self._commands[cmd].split(line)
        options, args = parser.parse_args(args)
        if not getattr(options, '_exit', False):
            try:
                self._commands[cmd].handle(*args, **options.__dict__)
            except StopIteration, e:
                raise
            except Exception, e:
                print templates.ERROR(str(e))

    def postcmd(self):
        client.force_call()

    def cmdloop(self):
        self.preloop()
        try:
            import readline
            self.old_completer = readline.get_completer()
            readline.set_completer(self.complete)
            readline.parse_and_bind("tab: complete")
        except ImportError:
            pass

        while True:
            try:
                line = raw_input(templates.prompt(self.prompt)).strip()
            except EOFError:
                break
            except Exception, e:
                print e
                continue
            try:
                self.precmd()
                self.onecmd(line)
                self.postcmd()
            except StopIteration:
                break
        self.postloop()
        print
    run = cmdloop

if __name__ == '__main__':
    ui = ConsoleUI()
    ui.precmd()
    ui.onecmd(' '.join(sys.argv[1:]))
    ui.postcmd()
