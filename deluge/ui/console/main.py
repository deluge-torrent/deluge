#
# main.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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

import os
import sys
import logging
import optparse
import shlex
import locale

from twisted.internet import defer, reactor

import deluge.component as component
from deluge.ui.client import client
import deluge.common
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.sessionproxy import SessionProxy
from deluge.ui.console.statusbars import StatusBars
from deluge.ui.console.eventlog import EventLog
#import screen
import colors
from deluge.ui.ui import _UI
from deluge.ui.console import UI_PATH

log = logging.getLogger(__name__)

class Console(_UI):

    help = """Starts the Deluge console interface"""

    def __init__(self):
        super(Console, self).__init__("console")
        group = optparse.OptionGroup(self.parser, "Console Options","These options control how "
                                     "the console connects to the daemon.  These options will be "
                                     "used if you pass a command, or if you have autoconnect "
                                     "enabled for the console ui.")

        group.add_option("-d","--daemon",dest="daemon_addr",
                         action="store",type="str",default="127.0.0.1",
                         help="Set the address of the daemon to connect to."
                              " [default: %default]")
        group.add_option("-p","--port",dest="daemon_port",
                         help="Set the port to connect to the daemon on. [default: %default]",
                         action="store",type="int",default=58846)
        group.add_option("-u","--username",dest="daemon_user",
                         help="Set the username to connect to the daemon with. [default: %default]",
                         action="store",type="string")
        group.add_option("-P","--password",dest="daemon_pass",
                         help="Set the password to connect to the daemon with. [default: %default]",
                         action="store",type="string")
        self.parser.add_option_group(group)

        self.cmds = load_commands(os.path.join(UI_PATH, 'commands'))
        class CommandOptionGroup(optparse.OptionGroup):
            def __init__(self, parser, title, description=None, cmds = None):
                optparse.OptionGroup.__init__(self,parser,title,description)
                self.cmds = cmds

            def format_help(self, formatter):
                result = formatter.format_heading(self.title)
                formatter.indent()
                if self.description:
                    result += "%s\n"%formatter.format_description(self.description)
                for cname in self.cmds:
                    cmd = self.cmds[cname]
                    if cmd.interactive_only or cname in cmd.aliases: continue
                    allnames = [cname]
                    allnames.extend(cmd.aliases)
                    cname = "/".join(allnames)
                    result += formatter.format_heading(" - ".join([cname,cmd.__doc__]))
                    formatter.indent()
                    result += "%*s%s\n" % (formatter.current_indent, "", cmd.usage)
                    formatter.dedent()
                formatter.dedent()
                return result
        cmd_group = CommandOptionGroup(self.parser, "Console Commands",
                                       description="The following commands can be issued at the "
                                       "command line.  Commands should be quoted, so, for example, "
                                       "to pause torrent with id 'abc' you would run: '%s "
                                       "\"pause abc\"'"%os.path.basename(sys.argv[0]),
                                       cmds=self.cmds)
        self.parser.add_option_group(cmd_group)

    def start(self):
        super(Console, self).start()
        ConsoleUI(self.args,self.cmds,(self.options.daemon_addr,
                  self.options.daemon_port,self.options.daemon_user,
                  self.options.daemon_pass))

def start():
    Console().start()

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
        raise Exception(msg)


class BaseCommand(object):

    usage = 'usage'
    interactive_only = False
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
        if deluge.common.windows_check():
            text = text.replace('\\', '\\\\')
        return shlex.split(text)

    def create_parser(self):
        return OptionParser(prog = self.name,
                            usage = self.usage,
                            epilog = self.epilog,
                            option_list = self.option_list)


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
            aliases = [ filename.split('.')[len(filename.split('.')) - 2] ]
            aliases.extend(cmd.aliases)
            for a in aliases:
                commands.append((a, cmd))
        return dict(commands)
    except OSError, e:
        return {}


class ConsoleUI(component.Component):
    def __init__(self, args=None, cmds = None, daemon = None):
        component.Component.__init__(self, "ConsoleUI", 2)

        # keep track of events for the log view
        self.events = []

        try:
            locale.setlocale(locale.LC_ALL, '')
            self.encoding = locale.getpreferredencoding()
        except:
            self.encoding = sys.getdefaultencoding()

        log.debug("Using encoding: %s", self.encoding)


        # start up the session proxy
        self.sessionproxy = SessionProxy()

        client.set_disconnect_callback(self.on_client_disconnect)

        # Set the interactive flag to indicate where we should print the output
        self.interactive = True
        if args:
            args = args[0]
            self.interactive = False
            if not cmds:
                print "Sorry, couldn't find any commands"
                return
            else:
                self._commands = cmds
                from commander import Commander
                cmdr = Commander(cmds)
                if daemon:
                    cmdr.exec_args(args,*daemon)
                else:
                    cmdr.exec_args(args,None,None,None,None)
                

        self.coreconfig = CoreConfig()
        if self.interactive and not deluge.common.windows_check():
            # We use the curses.wrapper function to prevent the console from getting
            # messed up if an uncaught exception is experienced.
            import curses.wrapper
            curses.wrapper(self.run)
        elif self.interactive and deluge.common.windows_check():
            print """\nDeluge-console does not run in interactive mode on Windows. \n
Please use commands from the command line, eg:\n
    deluge-console.exe help
    deluge-console.exe info
    deluge-console.exe "add --help"
    deluge-console.exe "add -p c:\\mytorrents c:\\new.torrent"
            """
        else:
            reactor.run()

    def run(self, stdscr):
        """
        This method is called by the curses.wrapper to start the mainloop and
        screen.

        :param stdscr: curses screen passed in from curses.wrapper

        """
        # We want to do an interactive session, so start up the curses screen and
        # pass it the function that handles commands
        colors.init_colors()
        self.statusbars = StatusBars()
        from modes.connectionmanager import ConnectionManager
        self.screen = ConnectionManager(stdscr, self.encoding)
        self.eventlog = EventLog()

        self.screen.topbar = "{!status!}Deluge " + deluge.common.get_version() + " Console"
        self.screen.bottombar = "{!status!}"
        self.screen.refresh()

        # The Screen object is designed to run as a twisted reader so that it
        # can use twisted's select poll for non-blocking user input.
        reactor.addReader(self.screen)

        # Start the twisted mainloop
        reactor.run()


    def start(self):
        # Maintain a list of (torrent_id, name) for use in tab completion
        self.torrents = []
        if not self.interactive:
            self.started_deferred = defer.Deferred()
            def on_session_state(result):
                def on_torrents_status(torrents):
                    for torrent_id, status in torrents.items():
                        self.torrents.append((torrent_id, status["name"]))
                    self.started_deferred.callback(True)

                client.core.get_torrents_status({"id": result}, ["name"]).addCallback(on_torrents_status)
            client.core.get_session_state().addCallback(on_session_state)

            
    def match_torrent(self, string):
        """
        Returns a list of torrent_id matches for the string.  It will search both
        torrent_ids and torrent names, but will only return torrent_ids.

        :param string: str, the string to match on

        :returns: list of matching torrent_ids. Will return an empty list if
            no matches are found.

        """
        ret = []
        for tid, name in self.torrents:
            if tid.startswith(string) or name.startswith(string):
                ret.append(tid)

        return ret


    def get_torrent_name(self, torrent_id):
        if self.interactive and hasattr(self.screen,"get_torrent_name"):
            return self.screen.get_torrent_name(torrent_id)

        for tid, name in self.torrents:
            if torrent_id == tid:
                return name
        
        return None


    def set_batch_write(self, batch):
        # only kept for legacy reasons, don't actually do anything
        pass

    def set_mode(self, mode):
        reactor.removeReader(self.screen)
        self.screen = mode
        self.statusbars.screen = self.screen
        reactor.addReader(self.screen)

    def on_client_disconnect(self):
        component.stop()

    def write(self, s):
        if self.interactive:
            self.events.append(s)
        else:
            print colors.strip_colors(s)
