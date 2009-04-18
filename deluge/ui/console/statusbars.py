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
# 	Boston, MA    02110-1301, USA.
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

        # This lets us know when the CoreConfig component is ready
        self.__core_config_ready = False

    def start(self):
        def on_coreconfig_ready(result):
            self.__core_config_ready = True
            self.update()

        # We need to add a callback to wait for the CoreConfig to be ready
        self.config.start_defer.addCallback(on_coreconfig_ready)

    def update(self):
        if not self.__core_config_ready:
            return

        if self.config["dht"]:
            def on_get_dht_nodes(result):
                self.dht = result
            client.core.get_dht_nodes().addCallback(on_get_dht_nodes)

        def on_get_num_connections(result):
            self.connections = result
        client.core.get_num_connections().addCallback(on_get_num_connections)

        def on_get_session_status(status):
            self.upload = deluge.common.fsize(status["payload_upload_rate"])
            self.download = deluge.common.fsize(status["payload_download_rate"])
            self.update_statusbars()

        client.core.get_session_status([
            "payload_upload_rate",
            "payload_download_rate"]).addCallback(on_get_session_status)


    def update_statusbars(self):
        # Update the topbar string
        self.screen.topbar = "{{status}}Deluge %s Console - " % deluge.common.get_version()
        if client.connected():
            info = client.connection_info()
            self.screen.topbar += "%s@%s:%s" % (info[2], info[0], info[1])
        else:
            self.screen.topbar += "Not Connected"

        # Update the bottombar string
        self.screen.bottombar = "{{status}}C: %s" % self.connections

        if self.config["max_connections_global"] > -1:
            self.screen.bottombar += " (%s)" % self.config["max_connections_global"]

        self.screen.bottombar += " D: %s/s" % self.download

        if self.config["max_download_speed"] > -1:
            self.screen.bottombar += " (%s/s)" % self.config["max_download_speed"]

        self.screen.bottombar += " U: %s/s" % self.upload

        if self.config["max_upload_speed"] > -1:
            self.screen.bottombar += " (%s/s)" % self.config["max_upload_speed"]

        if self.config["dht"]:
            self.screen.bottombar += " DHT: %s" % self.dht

        self.screen.refresh()
