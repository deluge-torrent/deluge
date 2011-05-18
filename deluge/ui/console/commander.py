#
# commander.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
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

from twisted.internet import defer, reactor
import deluge.component as component
from deluge.error import DelugeError
from deluge.ui.client import client
from deluge.ui.console import UI_PATH
from colors import strip_colors

import logging
log = logging.getLogger(__name__)

class Commander:
    def __init__(self, cmds, interactive=False):
        self._commands = cmds
        self.console = component.get("ConsoleUI")
        self.interactive = interactive

    def write(self,line):
        print(strip_colors(line))

    def do_command(self, cmd):
        """
        Processes a command.

        :param cmd: str, the command string

        """
        if not cmd:
            return
        cmd, _, line = cmd.partition(' ')
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
        except Exception, e:
            self.write("{!error!}Error parsing options: %s" % e)
            return

        if not getattr(options, '_exit', False):
            try:
                ret = self._commands[cmd].handle(*args, **options.__dict__)
            except Exception, e:
                self.write("{!error!}" + str(e))
                log.exception(e)
                import traceback
                self.write("%s" % traceback.format_exc())
                return defer.succeed(True)
            else:
                return ret

    def exec_args(self,args,host,port,username,password):
        def on_connect(result):
            def on_started(result):
                def on_started(result):
                    deferreds = []
                    # If we have args, lets process them and quit
                    # allow multiple commands split by ";"
                    for arg in args.split(";"):
                        deferreds.append(defer.maybeDeferred(self.do_command, arg.strip()))

                    def on_complete(result):
                        self.do_command("quit")

                    dl = defer.DeferredList(deferreds).addCallback(on_complete)

                # We need to wait for the rpcs in start() to finish before processing
                # any of the commands.
                self.console.started_deferred.addCallback(on_started)
            component.start().addCallback(on_started)

        def on_connect_fail(reason):
            if reason.check(DelugeError):
                rm = reason.value.message
            else:
                rm = reason.getErrorMessage()
            print "Could not connect to: %s:%d\n %s"%(host,port,rm)
            self.do_command("quit")

        if host:
            d = client.connect(host,port,username,password)
        else:
            d = client.connect()
        d.addCallback(on_connect)
        d.addErrback(on_connect_fail)

