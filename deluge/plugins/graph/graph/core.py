#
# core.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
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

import deluge
from deluge.log import LOG as log
from deluge.plugins.corepluginbase import CorePluginBase
from deluge import component
import gobject
#from deluge.plugins.coreclient import client #1.1 and later only
#client: see http://dev.deluge-torrent.org/wiki/Development/UiClient#Remoteapi

DEFAULT_PREFS = {
    "test":"NiNiNi",
    "update_interval":2000, #2 seconds.
    "length":150, # 2 seconds * 150 --> 5 minutes.
}

"""
port of the old NetworkGraph Plugin.
"""
class Core(CorePluginBase):

    def enable(self):
        self.core = component.get("Core")
        self.savedUpSpeeds   = []
        self.savedDownSpeeds = []
        self.savedConnections = []
        self.config = deluge.configmanager.ConfigManager("graph.conf", DEFAULT_PREFS)
        self.update_timer = gobject.timeout_add(self.config.get("update_interval"), self.update_stats)
        self.length = self.config.get("length")

    def disable(self):
        gobject.source_remove(self.update_timer)

    def update_stats(self):
        try:
            status = self.core.session.status()
            self.savedUpSpeeds.insert(0, int(status.payload_upload_rate))
            if len(self.savedUpSpeeds) > self.length:
                self.savedUpSpeeds.pop()
            self.savedDownSpeeds.insert(0, int(status.payload_download_rate))
            if len(self.savedDownSpeeds) > self.length:
                self.savedDownSpeeds.pop()
        except Exception,e:
            log.error(e.message)

        return True

    def export_get_upload(self,length=None):
        return self.savedUpSpeeds

    def export_get_download(self,length=None):
        return self.savedDownSpeeds

    def export_set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    def export_get_config(self):
        "returns the config dictionary"
        return self.config.get_config()
