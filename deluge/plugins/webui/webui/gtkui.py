#
# gtkui.py
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

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import get_resource

class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(get_resource("config.glade"))

        component.get("Preferences").add_page(_("WebUi"), self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        client.webui.get_config().addCallback(self.cb_get_config)
        client.webui.got_deluge_web().addCallback(self.cb_chk_deluge_web)

    def disable(self):
        component.get("Preferences").remove_page(_("WebUi"))
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        if not self.have_web:
            return
        log.debug("applying prefs for WebUi")
        config = {
            "enabled": self.glade.get_widget("enabled_checkbutton").get_active(),
            "ssl": self.glade.get_widget("ssl_checkbutton").get_active(),
            "port": self.glade.get_widget("port_spinbutton").get_value_as_int()
        }
        client.webui.set_config(config)

    def on_show_prefs(self):
        client.webui.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget("enabled_checkbutton").set_active(config["enabled"])
        self.glade.get_widget("ssl_checkbutton").set_active(config["ssl"])
        self.glade.get_widget("port_spinbutton").set_value(config["port"])

    def cb_chk_deluge_web(self, have_web):
        self.have_web = have_web
        if have_web:
            return
        self.glade.get_widget("settings_vbox").set_sensitive(False)

        vbox = self.glade.get_widget("prefs_box")

        hbox = gtk.HBox()
        icon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_SMALL_TOOLBAR)
        icon.set_padding(5, 5)
        hbox.pack_start(icon, False, False)

        label = gtk.Label(_("The Deluge web interface is not installed, "
            "please install the\ninterface and try again"))
        label.set_alignment(0, 0.5)
        label.set_padding(5, 5)
        hbox.pack_start(label)

        vbox.pack_start(hbox, False, False, 10)
        vbox.reorder_child(hbox, 0)
        vbox.show_all()
