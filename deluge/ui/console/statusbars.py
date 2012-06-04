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

from deluge.core.preferencesmanager import DEFAULT_PREFS

import deluge.component as component
import deluge.common
from deluge.ui.client import client

class StatusBars(component.Component):
    def __init__(self):
        component.Component.__init__(self, "StatusBars", 2, depend=["CoreConfig"])
        self.config = component.get("CoreConfig")

        # Hold some values we get from the core
        self.connections = 0
        self.download = ""
        self.upload = ""
        self.dht = 0

        # Default values
        self.topbar = "{!status!}Deluge %s Console - " % deluge.common.get_version()
        self.bottombar = "{!status!}C: %s" % self.connections

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
        self.topbar = "{!status!}Deluge %s Console - " % deluge.common.get_version()

        if client.connected():
            info = client.connection_info()
            connection_info = ""

            #Client name
            if info[2] == "localclient":
                connection_info += "{!white,blue!}%s"
            else:
                connection_info += "{!green,blue,bold!}%s"

            #Hostname
            if info[0] == "127.0.0.1":
                connection_info += "{!white,blue,bold!}@{!white,blue!}%s"
            else:
                connection_info += "{!white,blue,bold!}@{!red,blue,bold!}%s"

            #Port
            if info[1] == DEFAULT_PREFS["daemon_port"]:
                connection_info += "{!white,blue!}:%s"
            else:
                connection_info += "{!status!}:%s"

            #Change color back to normal, just in case
            connection_info += "{!status!}"

            self.topbar += connection_info % (info[2], info[0], info[1])
        else:
            self.topbar += "Not Connected"

        # Update the bottombar string
        self.bottombar = "{!status!}C: {!white,blue!}%s{!status!}" % self.connections

        if self.config["max_connections_global"] > -1:
            self.bottombar += " (%s)" % self.config["max_connections_global"]

        if self.download != "0.0 KiB":
            self.bottombar += " D: {!magenta,blue,bold!}%s{!status!}" % self.download
        else:
            self.bottombar += " D: {!white,blue!}%s{!status!}" % self.download

        if self.config["max_download_speed"] > -1:
            self.bottombar += " (%s " % self.config["max_download_speed"] + _("KiB/s") + ")"

        if self.upload != "0.0 KiB":
            self.bottombar += " U: {!green,blue,bold!}%s{!status!}" % self.upload
        else:
            self.bottombar += " U: {!white,blue!}%s{!status!}" % self.upload


        if self.config["max_upload_speed"] > -1:
            self.bottombar += " (%s " % self.config["max_upload_speed"] + _("KiB/s") + ")"

        if self.config["dht"]:
            self.bottombar += " " + _("DHT") + ": {!white,blue!}%s{!status!}" % self.dht
