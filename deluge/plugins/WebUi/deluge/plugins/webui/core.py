#
# core.py
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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

import os

from deluge import common, component, configmanager
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
from deluge.core.rpcserver import export

DEFAULT_PREFS = {
    "enabled": False,
    "ssl": False,
    "port": 8112
}

class Core(CorePluginBase):
    
    
    def enable(self):
        self.config = configmanager.ConfigManager("web_plugin.conf", DEFAULT_PREFS)
        self.server = None
        if self.config['enabled']:
            self.start()

    def disable(self):
        if self.server:
            self.server.stop()

    def update(self):
        pass
    
    def restart(self):
        if self.server:
            self.server.stop().addCallback(self.on_stop)
        else:
            self.start()
        
    def on_stop(self, *args):
        self.start()

    @export
    def got_deluge_web(self):
        try:
            from deluge.ui.web import server
            return True
        except ImportError:
            return False
    
    @export
    def start(self):
        if not self.server:
            try:
                from deluge.ui.web import server
            except ImportError:
                return False

            self.server = server.DelugeWeb()

        self.server.port = self.config["port"]
        self.server.https = self.config["ssl"]
        self.server.start(False)
        return True
    
    @export
    def stop(self):
        if self.server:
            self.server.stop()

    @export
    def set_config(self, config):
        "sets the config dictionary"

        action = None
        if "enabled" in config:
            if config["enabled"] != self.config["enabled"]:
                action = config["enabled"] and 'start' or 'stop'
        
        if "ssl" in config:
            if not action:
                action = 'restart'

        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()
        
        if action == 'start':
            return self.start()
        elif action == 'stop':
            return self.stop()
        elif action == 'restart':
            return self.restart()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config
