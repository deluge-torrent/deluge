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
from deluge.ui.client import client
from deluge import component
from deluge.plugins.pluginbase import WebPluginBase

#import deluge.ui.webui.lib.newforms_plus as forms

#config_page_manager = component.get("ConfigPageManager")

FORMAT_LIST =  [
       ('gzmule',_("Emule IP list (GZip)")),
       ('spzip',_("SafePeer Text (Zipped)")),
       ('pgtext',_("PeerGuardian Text (Uncompressed)")),
       ('p2bgz',_("PeerGuardian P2B (GZip)"))
]

class WebUI(WebPluginBase):
    def enable(self):
        #config_page_manager.register('plugins','blocklist',BlockListCfgForm)
        pass

    def disable(self):
        #config_page_manager.deregister('blocklist')
        pass
