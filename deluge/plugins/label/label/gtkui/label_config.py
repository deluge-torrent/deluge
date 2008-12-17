#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Deluge is free software.
#
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


import gtk
import gtk.glade
import os
import pkg_resources    # access plugin egg
import deluge.component as component
import deluge.common
from deluge.log import LOG as log
from deluge.ui.client import aclient


class LabelConfig(object):
    """
    there used to be some options here...
    """

    def __init__(self, plugin):
        self.plugin = plugin

    def load(self):
        log.debug('Adding Label Preferences page')
        self.glade = gtk.glade.XML(self.get_resource("label_pref.glade"))


        self.plugin.add_preferences_page(_("Label"), self.glade.get_widget("label_prefs_box"))
        self.plugin.register_hook("on_show_prefs", self.load_settings)
        self.plugin.register_hook("on_apply_prefs", self.on_apply_prefs)

        self.load_settings()

    def unload(self):
        self.plugin.remove_preferences_page(_("Label"))
        self.plugin.deregister_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.deregister_hook("on_show_prefs", self.load_settings)

    def get_resource(self, filename):
        return pkg_resources.resource_filename("label", os.path.join("data", filename))

    def load_settings(self, widget=None, data=None):
        aclient.label_get_config(self.cb_global_options)

    def cb_global_options(self, options):
        log.debug("options=%s" % options)
        """
        for id in self.chk_ids:
            self.glade.get_widget(id).set_active(bool(options[id]))
        """

    def on_apply_prefs(self):
        options = {}
        #update options dict here.
        aclient.label_set_config(None, options)
