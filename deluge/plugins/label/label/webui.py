#
# blocklist/webui.py
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


import os
from deluge.log import LOG as log
from deluge.ui.client import sclient
from deluge import component
import ui

import webui_config
import webui_pages

class WebUI(ui.UI):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling UI init")
        # Call UI constructor
        ui.UI.__init__(self, plugin_api, plugin_name)
        log.debug("Label WebUI plugin initalized..")

    def enable(self):
        webui_pages.register()
        webui_config.register()

    def disable(self):
        webui_pages.unregister()
        webui_config.unregister()






