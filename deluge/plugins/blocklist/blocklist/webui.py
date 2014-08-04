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


import os
from deluge.log import LOG as log
from deluge.ui.client import client
from deluge import component
from deluge.plugins.pluginbase import WebPluginBase

from common import get_resource

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

    scripts = [get_resource("blocklist.js")]
    debug_scripts = scripts
