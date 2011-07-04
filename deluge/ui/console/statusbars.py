#
# statusbars.py
#
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

import deluge.component as component
import deluge.common
from deluge.ui.client import client

class StatusBars(component.Component):
    def __init__(self):
        component.Component.__init__(self, "StatusBars", 2, depend=["CoreConfig"])
        self.config = component.get("CoreConfig")
        self.screen = component.get("ConsoleUI").screen

        # Hold some values we get from the core
        self.connections = 0
        self.download = ""
        self.upload = ""
        self.dht = 0

    def start(self):
        self.update()

    def update(self):
        def on_get_num_connections(result):
            self.connections = result
        client.core.get_num_connections().addCallback(on_get_num_connections)

        def on_get_session_status(status):
            self.upload = deluge.common.fsize(status["payload_upload_rate"])
            self.download = deluge.common.fsize(status["payload_download_rate"])
            if "dht_nodes" in status:
                self.dht = status["dht_nodes"]

            self.update_statusbars()

        keys = [
            "payload_upload_rate",
            "payload_download_rate"]

        if self.config["dht"]:
            keys.append("dht_nodes")

        client.core.get_session_status(keys).addCallback(on_get_session_status)


    def update_statusbars(self):
        # Update the topbar string
        self.screen.topbar = "{!status!}Deluge %s Console - " % deluge.common.get_version()
        if client.connected():
            info = client.connection_info()
            self.screen.topbar += "%s@%s:%s" % (info[2], info[0], info[1])
        else:
            self.screen.topbar += "Not Connected"

        # Update the bottombar string
        self.screen.bottombar = "{!status!}C: %s" % self.connections

        if self.config["max_connections_global"] > -1:
            self.screen.bottombar += " (%s)" % self.config["max_connections_global"]

        self.screen.bottombar += " D: %s" % self.download

        if self.config["max_download_speed"] > -1:
            self.screen.bottombar += " (%s " % self.config["max_download_speed"] + _("KiB/s") + ")" 

        self.screen.bottombar += " U: %s" % self.upload

        if self.config["max_upload_speed"] > -1:
            self.screen.bottombar += " (%s " % self.config["max_upload_speed"] + _("KiB/s") + ")"

        if self.config["dht"]:
            self.screen.bottombar += " " + _("DHT") + ": %s" % self.dht

        self.screen.refresh()
