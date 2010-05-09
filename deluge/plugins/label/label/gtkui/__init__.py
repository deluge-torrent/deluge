#
# __init__.py
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
import pkg_resources    # access plugin egg
from deluge.log import LOG as log
from deluge import component    # for systray
from deluge.plugins.pluginbase import GtkPluginBase
import gtk, gobject
from deluge.ui.client import client

import sidebar_menu
import label_config
import submenu

NO_LABEL = "No Label"

def cell_data_label(column, cell, model, row, data):
    cell.set_property('text', str(model.get_value(row, data)))

class GtkUI(GtkPluginBase):
    def start(self):
        if self.label_menu:
            self.label_menu.on_show()

    def enable(self):
        self.plugin = component.get("PluginManager")
        self.label_menu = None
        self.labelcfg = None
        self.sidebar_menu = None
        self.load_interface()

    def disable(self):
        try:
            torrentmenu = component.get("MenuBar").torrentmenu
            torrentmenu.remove(self.label_menu) # ok

            self.labelcfg.unload() # ok
            self.sidebar_menu.unload()
            del self.sidebar_menu



            component.get("TorrentView").remove_column(_("Label"))
            log.debug(1.1)
            component.get("TorrentView").create_model_filter() #todo:improve.

        except Exception, e:
            log.debug(e)

    def load_interface(self):
        #sidebar
        #disabled
        if not self.sidebar_menu:
            self.sidebar_menu  = sidebar_menu.LabelSidebarMenu()
        #self.sidebar.load()

        #menu:
        log.debug("add items to torrentview-popup menu.")
        torrentmenu = component.get("MenuBar").torrentmenu
        self.label_menu = submenu.LabelMenu()
        torrentmenu.append(self.label_menu)
        self.label_menu.show_all()

        #columns:
        self.load_columns()

        #config:
        if not self.labelcfg:
            self.labelcfg  = label_config.LabelConfig(self.plugin)
        self.labelcfg.load()

        log.debug('Finished loading Label plugin')

    def load_columns(self):
        log.debug("add columns")

        component.get("TorrentView").add_text_column(_("Label"), status_field=["label"])
