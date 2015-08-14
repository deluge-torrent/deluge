# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import gtk
import gtk.glade

import deluge.component as component
from deluge.plugins.pluginbase import GtkPluginBase
from deluge.ui.client import client

from .common import get_resource

log = logging.getLogger(__name__)


class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(get_resource("extractor_prefs.glade"))

        component.get("Preferences").add_page(_("Extractor"), self.glade.get_widget("extractor_prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.on_show_prefs()

    def disable(self):
        component.get("Preferences").remove_page(_("Extractor"))
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        del self.glade

    def on_apply_prefs(self):
        log.debug("applying prefs for Extractor")
        if client.is_localhost():
            path = self.glade.get_widget("folderchooser_path").get_filename()
        else:
            path = self.glade.get_widget("entry_path").get_text()

        config = {
            "extract_path": path,
            "use_name_folder": self.glade.get_widget("chk_use_name").get_active()
        }

        client.extractor.set_config(config)

    def on_show_prefs(self):
        if client.is_localhost():
            self.glade.get_widget("folderchooser_path").show()
            self.glade.get_widget("entry_path").hide()
        else:
            self.glade.get_widget("folderchooser_path").hide()
            self.glade.get_widget("entry_path").show()

        def on_get_config(config):
            if client.is_localhost():
                self.glade.get_widget("folderchooser_path").set_current_folder(config["extract_path"])
            else:
                self.glade.get_widget("entry_path").set_text(config["extract_path"])

            self.glade.get_widget("chk_use_name").set_active(config["use_name_folder"])

        client.extractor.get_config().addCallback(on_get_config)
