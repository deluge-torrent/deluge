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

log = logging.getLogger(__name__)

class Console(_UI):

    help = """Starts the Deluge console interface"""

    def __init__(self):
        super(Console, self).__init__("console")

    def start(self):
        super(Console, self).start()

        ConsoleUI(self.args)

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


class ConsoleUI(component.Component):
    def __init__(self, args=None):
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

        self.coreconfig = CoreConfig()
        if self.interactive and not deluge.common.windows_check():
            # We use the curses.wrapper function to prevent the console from getting
            # messed up if an uncaught exception is experienced.
            import curses.wrapper
            curses.wrapper(self.run)
        elif self.interactive and deluge.common.windows_check():
            print "You cannot run the deluge-console in interactive mode in Windows.\
            Please use commands from the command line, eg: deluge-console config;help;exit"
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


    def set_mode(self, mode):
        reactor.removeReader(self.screen)
        self.screen = mode
        self.statusbars.screen = self.screen
        reactor.addReader(self.screen)

    def on_client_disconnect(self):
        component.stop()

    def write(self, s):
        self.events.append(s)
