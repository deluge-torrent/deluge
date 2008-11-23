#
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

api = component.get("WebPluginApi")

template_dir = os.path.join(os.path.dirname(__file__),"template")

class torrent_label:
    @api.deco.deluge_page
    @api.deco.torrent_list
    def GET(self, torrent_list):
        torrent_str = ",".join([t.id for t in torrent_list])
        labels = sclient.label_get_labels()
        return api.render.torrent_label(torrent_str , torrent_list , labels)

    @api.deco.check_session
    @api.deco.torrent_ids
    def POST(self, torrent_ids):
        label =api.web.input(label = None).label
        for id in torrent_ids:
            sclient.label_set_torrent(id , label)
        api.utils.do_redirect()


def register():
    api.render.register_template_path(template_dir)
    api.page_manager.register_page('/torrent/label/(.*)', torrent_label)
    api.menu_manager.register_toolbar_item("label",_("Label"), "label.png" ,2,
        "GET","/torrent/label/", True)

def unregister():
    api.render.unregister_template_path(template_dir)
    api.page_manager.unregister_page('/torrent/label/(.*)')
    api.menu_manager.unregister_toolbar_item("label")











