#
# connectionmanager.py
#
# Copyright (C) 2007-2009 Nick Lanham <nick@afternight.org>
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

# a mode that show's a popup to select which host to connect to

import hashlib,time

from collections import deque

import deluge.ui.client
from deluge.ui.client import client
from deluge.configmanager import ConfigManager
from deluge.ui.coreconfig import CoreConfig
import deluge.component as component

from alltorrents import AllTorrents
from basemode import BaseMode
from popup import SelectablePopup,MessagePopup
from input_popup import InputPopup


try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 58846

DEFAULT_CONFIG = {
    "hosts": [(hashlib.sha1(str(time.time())).hexdigest(), DEFAULT_HOST, DEFAULT_PORT, "", "")]
}


class ConnectionManager(BaseMode):
    def __init__(self, stdscr, encoding=None):
        self.popup = None
        self.statuses = {}
        self.messages = deque()
        self.config = ConfigManager("hostlist.conf.1.2", DEFAULT_CONFIG)
        BaseMode.__init__(self, stdscr, encoding)
        self.__update_statuses()
        self.__update_popup()

    def __update_popup(self):
        self.popup = SelectablePopup(self,"Select Host",self.__host_selected)
        self.popup.add_line("{!white,black,bold!}'Q'=quit, 'r'=refresh, 'a'=add new host, 'D'=delete host",selectable=False)
        for host in self.config["hosts"]:
            if host[0] in self.statuses:
                self.popup.add_line("%s:%d [Online] (%s)"%(host[1],host[2],self.statuses[host[0]]),data=host[0],foreground="green")
            else:
                self.popup.add_line("%s:%d [Offline]"%(host[1],host[2]),data=host[0],foreground="red")
        self.inlist = True
        self.refresh()

    def __update_statuses(self):
        """Updates the host status"""
        def on_connect(result, c, host_id):
            def on_info(info, c):
                self.statuses[host_id] = info
                self.__update_popup()
                c.disconnect()

            def on_info_fail(reason, c):
                if host_id in self.statuses:
                    del self.statuses[host_id]
                c.disconnect()

            d = c.daemon.info()
            d.addCallback(on_info, c)
            d.addErrback(on_info_fail, c)

        def on_connect_failed(reason, host_id):
            if host_id in self.statuses:
                del self.statuses[host_id]

        for host in self.config["hosts"]:
            c = deluge.ui.client.Client()
            hadr = host[1]
            port = host[2]
            user = host[3]
            password = host[4]
            d = c.connect(hadr, port, user, password)
            d.addCallback(on_connect, c, host[0])
            d.addErrback(on_connect_failed, host[0])

    def __on_connected(self,result):
        component.start()
        self.stdscr.erase()
        at = AllTorrents(self.stdscr, self.encoding)
        component.get("ConsoleUI").set_mode(at)
        at.resume()

    def __host_selected(self, idx, data):
        for host in self.config["hosts"]:
            if host[0] == data and host[0] in self.statuses:
                client.connect(host[1], host[2], host[3], host[4]).addCallback(self.__on_connected)
        return False

    def __do_add(self,result):
        hostname = result["hostname"]
        try:
            port = int(result["port"])
        except ValueError:
            self.report_message("Can't add host","Invalid port.  Must be an integer")
            return
        username = result["username"]
        password = result["password"]
        for host in self.config["hosts"]:
            if (host[1],host[2],host[3]) == (hostname, port, username):
                self.report_message("Can't add host","Host already in list")
                return
        newid = hashlib.sha1(str(time.time())).hexdigest()
        self.config["hosts"].append((newid, hostname, port, username, password))
        self.config.save()
        self.__update_popup()

    def __add_popup(self):
        self.inlist = False
        self.popup = InputPopup(self,"Add Host (up & down arrows to navigate, esc to cancel)",close_cb=self.__do_add)
        self.popup.add_text_input("Hostname:","hostname")
        self.popup.add_text_input("Port:","port")
        self.popup.add_text_input("Username:","username")
        self.popup.add_text_input("Password:","password")
        self.refresh()

    def __delete_current_host(self):
        idx,data = self.popup.current_selection()
        log.debug("deleting host: %s",data)
        for host in self.config["hosts"]:
            if host[0] == data:
                self.config["hosts"].remove(host)
                break
        self.config.save()

    def report_message(self,title,message):
        self.messages.append((title,message))

    def refresh(self):
        self.stdscr.erase()
        self.draw_statusbars()
        self.stdscr.noutrefresh()

        if self.popup == None and self.messages:
            title,msg = self.messages.popleft()
            self.popup = MessagePopup(self,title,msg)

        if not self.popup:
            self.__update_popup()

        self.popup.refresh()
        curses.doupdate()


    def _doRead(self):
        # Read the character
        c = self.stdscr.getch()

        if c > 31 and c < 256:
            if chr(c) == 'q' and self.inlist: return
            if chr(c) == 'Q':
                from twisted.internet import reactor
                if client.connected():
                    def on_disconnect(result):
                        reactor.stop()
                    client.disconnect().addCallback(on_disconnect)
                else:
                    reactor.stop()
                return
            if chr(c) == 'D' and self.inlist:
                self.__delete_current_host()
                self.__update_popup()
                return
            if chr(c) == 'r' and self.inlist:
                self.__update_statuses()
            if chr(c) == 'a' and self.inlist:
                self.__add_popup()
                return

        if self.popup:
            if self.popup.handle_read(c):
                self.popup = None
            self.refresh()
            return
