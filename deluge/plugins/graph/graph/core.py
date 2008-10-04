#
# core.py
#
# Copyright (C) 2008 Damien Churchill <damoxc@gmail.com>
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
from deluge import configmanager
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
        self.saved_stats = {}
        self.add_stats(
            'upload_rate',
            'download_rate',
            'num_connections',
            'dht_nodes',
            'dht_cache_nodes',
            'dht_torrents',
        )

        self.base_total_upload = 0
        self.base_total_download = 0

        self.config = configmanager.ConfigManager("graph.conf", DEFAULT_PREFS)
        self.update_timer = gobject.timeout_add(
            self.config.get("update_interval"), self.update_stats)
        self.length = self.config.get("length")

        self.plugin.register_hook("post_torrent_remove", self.post_torrent_remove)


    def disable(self):
        gobject.source_remove(self.update_timer)
        self.plugin.deregister_hook("post_torrent_remove", self.post_torrent_remove)

    # plugin hooks:
    def post_torrent_remove(self, torrent_id):
        log.debug("post_torrent_remove")
        """torrent = self.core.torrents.torrents[torrent_id]
        self.base_total_download += torrent.total_done
        self.base_total_upload +=  torrent.total_uploaded + torrent.status.total_payload_upload
        """
    # /plugin hooks

    def add_stats(self, *stats):
        for stat in stats:
            if stat not in self.saved_stats:
                self.saved_stats[stat] = []

    def update_stats(self):
        try:
            stats = self.core.export_get_stats()
            status = self.core.session.status()
            #log.debug(dir(status))
            for stat, stat_list in self.saved_stats.iteritems():
                if stat in stats:
                    stat_list.insert(0, int(stats[stat]))
                else:
                    stat_list.insert(0, int(getattr(status, stat)))
                if len(stat_list) > self.length:
                    stat_list.pop()
        except Exception,e:
            log.error(e.message)
        return True

    # export:
    def export_get_stats(self, keys):
        stats_dict = {}
        for stat in self.saved_stats:
            if stat not in keys:
                continue
            stats_dict[stat] = self.saved_stats[stat]
        return stats_dict

    def export_get_totals(self):
        status = self.core.session.status()
        #dht = status
        #og.debug(status)
        return {
            "upload":self.base_total_upload + status.total_upload + status.total_payload_upload,
            "download":self.base_total_download + status.total_download + status.total_payload_download,
            "total_payload_upload":status.total_payload_upload,
            "total_payload_download":status.total_payload_upload
        }

    def export_set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    def export_get_config(self):
        "returns the config dictionary"
        return self.config.get_config()
