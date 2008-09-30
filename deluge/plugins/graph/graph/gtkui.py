#
# gtkui.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007, 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception

from deluge.log import LOG as log
from deluge.ui.client import aclient
import gtk

class GtkUI(object):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling Graph UI init")
        self.plugin = plugin_api

    def enable(self):
        self.glade = gtk.glade.XML(self.get_resource("config.glade"))

        self.plugin.add_preferences_page("Graph", self.glade.get_widget("prefs_box"))
        self.plugin.register_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.register_hook("on_show_prefs", self.on_show_prefs)
        self.on_show_prefs()

    def disable(self):
        self.plugin.remove_preferences_page("Graph")
        self.plugin.deregister_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for Graph")
        config = {
            "test":self.glade.get_widget("txt_test").get_text()
        }
        aclient.graph_set_config(None, config)

    def on_show_prefs(self):
        aclient.graph_get_config(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget("txt_test").set_text(config["test"])

    def get_resource(self, filename):
        import pkg_resources, os
        return pkg_resources.resource_filename("graph", os.path.join("data", filename))
