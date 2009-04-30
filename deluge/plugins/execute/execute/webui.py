#
# webui.py
#
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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#

import pkg_resources

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge import component
from deluge.plugins.pluginbase import WebPluginBase

class WebUI(WebPluginBase):
    def enable(self):
        log.debug("Execute Web plugin enabled!")
        deluge_web = component.get("DelugeWeb").top_level
        deluge_web.scripts.append("/js/deluge-execute.js")
        deluge_web.debug_scripts.append("/js/deluge-execute.js")
        
        javascript = component.get("Javascript").directories
        javascript.append(pkg_resources.resource_filename("execute", "data"))

    def disable(self):
        log.debug("Execute Web plugin disabled!")
        deluge_web = component.get("DelugeWeb").top_level
        deluge_web.scripts.remove("/js/deluge-execute.js")
        deluge_web.debug_scripts.remove("/js/deluge-execute.js")
