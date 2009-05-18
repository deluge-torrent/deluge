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


import gtk
import gtk.glade
import os
import pkg_resources    # access plugin egg
import deluge.component as component
import deluge.common
from deluge.log import LOG as log
from deluge.ui.client import client


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
        client.label.get_config().addCallback(self.cb_global_options)

    def cb_global_options(self, options):
        log.debug("options=%s" % options)
        """
        for id in self.chk_ids:
            self.glade.get_widget(id).set_active(bool(options[id]))
        """

    def on_apply_prefs(self):
        options = {}
        #update options dict here.
        client.label.set_config(options)
