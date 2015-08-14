# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

from deluge import component  # for systray
from deluge.plugins.pluginbase import GtkPluginBase

from . import label_config, sidebar_menu, submenu

log = logging.getLogger(__name__)

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
            torrentmenu.remove(self.label_menu)  # ok

            self.labelcfg.unload()  # ok
            self.sidebar_menu.unload()
            del self.sidebar_menu

            component.get("TorrentView").remove_column(_("Label"))
            log.debug(1.1)

        except Exception as ex:
            log.debug(ex)

    def load_interface(self):
        # sidebar
        # disabled
        if not self.sidebar_menu:
            self.sidebar_menu = sidebar_menu.LabelSidebarMenu()
        # self.sidebar.load()

        # menu:
        log.debug("add items to torrentview-popup menu.")
        torrentmenu = component.get("MenuBar").torrentmenu
        self.label_menu = submenu.LabelMenu()
        torrentmenu.append(self.label_menu)
        self.label_menu.show_all()

        # columns:
        self.load_columns()

        # config:
        if not self.labelcfg:
            self.labelcfg = label_config.LabelConfig(self.plugin)
        self.labelcfg.load()

        log.debug('Finished loading Label plugin')

    def load_columns(self):
        log.debug("add columns")

        component.get("TorrentView").add_text_column(_("Label"), status_field=["label"])
