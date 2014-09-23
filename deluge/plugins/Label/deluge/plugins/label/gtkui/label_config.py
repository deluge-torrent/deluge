# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os

import gtk
import gtk.glade
import pkg_resources  # access plugin egg

from deluge.ui.client import client

log = logging.getLogger(__name__)


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
        return pkg_resources.resource_filename(
            "deluge.plugins.label", os.path.join("data", filename)
        )

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
        # update options dict here.
        client.label.set_config(options)
