#
# core.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import deluge.component as component
from deluge.log import LOG as log
from deluge.common import fspeed, fsize

class StatusBarManager(component.Component):
    """StatusBarManager
    """
    def __init__(self, core):
        component.Component.__init__(self, "StatusBarManager")
        log.debug("StatusBarManager init..")
        self.core = core
        self.torrents = core.torrents
        self.icon_order = []
        self.registered_icons = {}
        self.stats = {}

    def register_icon(self, id, icon_func):
        self.icon_order.append(id)
        self.registered_icons[id] = icon_func

    def deregister_icon(self, id):
        self.icon_order.remove(id)
        del self.registered_icons[id]

    def get_statusbar(self , include_defaults = True):
        stats = self.core.export_get_stats()
        #self.stats = stats
        statusbar = []
        if include_defaults:
            """hardcoded part first.."""
            statusbar.append(("num_connections" , "connections16.png",_("Connections"),"%(num_connections)s (%(max_num_connections)s)" % stats))

            txt = "%s KiB/s" % fspeed(stats["download_rate"])
            if stats["max_download"]:
                txt += " (%s KiB/s)" % stats["max_download"]
            statusbar.append(("downloading","downloading16.png",_("Downloading"),txt))

            txt = "%s KiB/s" % fspeed(stats["upload_rate"])
            if stats["max_download"]:
                txt += " (%s KiB/s)" % stats["max_upload"]
            statusbar.append(("uploading", "seeding16.png",_("Uploading"),txt))

            statusbar.append(("free_space", None ,_("Free Space"), fsize(stats["free_space"])))

            if not stats["has_incoming_connections"]:
                statusbar.append(("network_health", "alert16.png","",_("No Incoming Connections!")))

            statusbar.append(("dht", "dht16.png",_("DHT Nodes"),"%(dht_nodes)s" % stats ))


        for id in self.icon_order:
            item = self.registered_icons[id]() #function call.
            statusbar.append(item)
        return statusbar





