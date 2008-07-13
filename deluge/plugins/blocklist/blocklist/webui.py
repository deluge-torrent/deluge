#
# blocklist/webui.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>

#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
#    statement from all source files in the program, then also delete it here.

import os
from deluge.log import LOG as log
from deluge.ui.client import sclient
from deluge import component
import ui

import deluge.ui.webui.lib.newforms_plus as forms

config_page_manager = component.get("ConfigPageManager")

FORMAT_LIST =  [
       ('gzmule',_("Emule IP list (GZip)")),
       ('spzip',_("SafePeer Text (Zipped)")),
       ('pgtext',_("PeerGuardian Text (Uncompressed)")),
       ('p2bgz',_("PeerGuardian P2B (GZip)"))
]

class BlockListCfgForm(forms.Form):
    """
    a config form based on django forms.
    see webui.lib.newforms_plus, config_forms, etc.
    """
    #meta:
    title = _("BlockList")

    #load/save:
    def initial_data(self):
        return sclient.block_list_get_options()

    def save(self, data):
        sclient.block_list_set_options(dict(data))

    #input fields :
    listtype = forms.ChoiceField(FORMAT_LIST)
    url = forms.URLField(label=_("Url"))
    check_after_days = forms.IntegerField(label=_("Check for a blocklist every (days)"), min_value=-1, max_value=14)
    timeout =  forms.IntegerField(label=_("Timeout (seconds)"), min_value=15, max_value=360)
    try_times = forms.IntegerField(label=_("Times to attemptdownload of new list"), min_value=1, max_value=5)
    load_on_start = forms.CheckBox(_('Import blocklist on daemon startup'))

class WebUI(ui.UI):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling UI init")
        # Call UI constructor
        ui.UI.__init__(self, plugin_api, plugin_name)
        log.debug("Blocklist WebUI plugin initalized..")

    def enable(self):
        config_page_manager.register('plugins','blocklist',BlockListCfgForm)

    def disable(self):
        config_page_manager.unregister('blocklist')





