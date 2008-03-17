#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.
#

from deluge import component, pluginmanagerbase
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class PluginManager(pluginmanagerbase.PluginManagerBase,
    component.Component):
    def __init__(self):
        component.Component.__init__(self, "WebPluginManager")
        self.config = ConfigManager("webui.conf")
        pluginmanagerbase.PluginManagerBase.__init__(
            self, "webui.conf", "deluge.plugin.webui")

    def start(self):
        """Start the plugin manager"""
        # Update the enabled_plugins from the core
        client.get_enabled_plugins(self._on_get_enabled_plugins)

    def stop(self):
        # Disable the plugins
        self.disable_plugins()

    def _on_get_enabled_plugins(self, enabled_plugins):
        log.debug("Webui has these plugins enabled: %s", enabled_plugins)
        self.config["enabled_plugins"] = enabled_plugins

        # Enable the plugins that are enabled in the config and core
        self.enable_plugins()


__plugin_manager = PluginManager()



