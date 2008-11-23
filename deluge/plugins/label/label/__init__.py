#
# __init__.py
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


from deluge.log import LOG as log
from deluge.plugins.init import PluginBase

class CorePlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        # Load the Core portion of the plugin
        try:
            from core import Core
            self.plugin = Core(plugin_api, plugin_name)
        except Exception, e:
            log.debug("Did not load a Core plugin: %s", e)

class WebUIPlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        try:
            from webui import WebUI
            self.plugin = WebUI(plugin_api, plugin_name)
        except Exception, e:
            log.debug("Did not load a WebUI plugin: %s", e)

class GtkUIPlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        # Load the GtkUI portion of the plugin
        try:
            from gtkui import GtkUI
            self.plugin = GtkUI(plugin_api, plugin_name)
        except Exception, e:
            log.debug("Did not load a GtkUI plugin: %s", e)

