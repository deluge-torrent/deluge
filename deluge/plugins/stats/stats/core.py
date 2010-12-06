#
# core.py
#
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception

from twisted.internet.task import LoopingCall
import time

import deluge
from deluge.log import getPluginLogger
from deluge.plugins.pluginbase import CorePluginBase
from deluge import component
from deluge import configmanager
from deluge.core.rpcserver import export

log = getPluginLogger(__name__)

DEFAULT_PREFS = {
    "test": "NiNiNi",
    "update_interval": 2, #2 seconds.
    "length": 150, # 2 seconds * 150 --> 5 minutes.
}

DEFAULT_TOTALS = {
    "total_upload": 0,
    "total_download": 0,
    "total_payload_upload": 0,
    "total_payload_download": 0,
    "stats": {}
}

class Core(CorePluginBase):
    totals = {} #class var to catch only updating this once per session in enable.

    def enable(self):
        self.core = component.get("Core")
        self.stats ={}

        self.config = configmanager.ConfigManager("stats.conf", DEFAULT_PREFS)
        self.saved_stats = configmanager.ConfigManager("stats.totals", DEFAULT_TOTALS)
        if self.totals == {}:
            self.totals.update(self.saved_stats.config)

        self.stats = self.saved_stats["stats"] or {}

        self.stats_keys = [
            "payload_download_rate",
            "payload_upload_rate"
        ]
        self.update_stats()

        self.update_timer = LoopingCall(self.update_stats)
        self.update_timer.start(self.config["update_interval"])

        self.save_timer = LoopingCall(self.save_stats)
        self.save_timer.start(60)

    def disable(self):
        self.save_stats()
        try:
            self.update_timer.stop()
            self.save_timer.stop()
        except:
            pass

    def update_stats(self):
        try:
            status = self.core.get_session_status(self.stats_keys)
            for key, value in status.items():
                if key not in self.stats:
                    self.stats[key] = []
                self.stats[key].insert(0, value)

            for stat_list in self.stats.values():
                if len(stat_list) > self.config["length"]:
                    stat_list.pop()
            self.last_update = time.time()

        except Exception, e:
            log.exception(e)

    def save_stats(self):
        try:
            self.saved_stats["stats"] = self.stats
            self.saved_stats.config.update(self.get_totals())
            self.saved_stats.save()
        except Exception,e:
            log.exception(e)
        return True


    # export:
    @export
    def get_stats(self, keys):
        stats_dict = {}
        for key in keys:
            if key in self.stats:
                stats_dict[key] = self.stats[key]
        stats_dict["_last_update"] = self.last_update
        return stats_dict

    @export
    def get_totals(self):
        result = {}
        session_totals = self.get_session_totals()
        for key in session_totals:
            result[key] = self.totals[key] + session_totals[key]
        return result

    @export
    def get_session_totals(self):
        status = self.core.session.status()
        return {
            "total_upload": status.total_upload,
            "total_download": status.total_download,
            "total_payload_upload": status.total_payload_upload,
            "total_payload_download": status.total_payload_download
        }

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config
