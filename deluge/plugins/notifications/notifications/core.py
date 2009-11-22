#
# core.py
#
# Copyright (C) 2009 Pedro Algarvio <ufs@ufsoft.org>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.configmanager
from deluge.core.rpcserver import export

from notifications.common import CoreNotifications

DEFAULT_PREFS = {
    "smtp_enabled": False,
    "smtp_host": "",
    "smtp_port": 25,
    "smtp_user": "",
    "smtp_pass": "",
    "smtp_from": "",
    "smtp_tls": False, # SSL or TLS
    "smtp_recipients": [],
    # Subscriptions
    "subscriptions": {
        "email": []
    }
}

class Core(CorePluginBase, CoreNotifications):
    def __init__(self, plugin_name):
        CorePluginBase.__init__(self, plugin_name)
        CoreNotifications.__init__(self)

    def enable(self):
        CoreNotifications.enable(self)
        self.config = deluge.configmanager.ConfigManager(
            "notifications-core.conf", DEFAULT_PREFS)
        log.debug("\n\nENABLING CORE NOTIFICATIONS\n\n")

    def disable(self):
        log.debug("\n\nDISABLING CORE NOTIFICATIONS\n\n")
        CoreNotifications.disable(self)

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

    @export
    def get_handled_events(self):
        return CoreNotifications.get_handled_events(self)
