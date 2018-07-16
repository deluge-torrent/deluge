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

from __future__ import unicode_literals

import logging

import gi  # isort:skip (Required before Gtk import).

gi.require_version('Gtk', '3.0')  # NOQA: E402

# isort:imports-thirdparty
from gi.repository import Gtk

# isort:imports-firstparty
import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

# isort:imports-localfolder
from .common import get_resource

log = logging.getLogger(__name__)


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('extractor_prefs.ui'))

        component.get('Preferences').add_page(
            _('Extractor'), self.builder.get_object('extractor_prefs_box')
        )
        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs
        )
        self.on_show_prefs()

    def disable(self):
        component.get('Preferences').remove_page(_('Extractor'))
        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )
        del self.builder

    def on_apply_prefs(self):
        log.debug('applying prefs for Extractor')
        if client.is_localhost():
            path = self.builder.get_object('folderchooser_path').get_filename()
        else:
            path = self.builder.get_object('entry_path').get_text()

        config = {
            'extract_path': path,
            'use_name_folder': self.builder.get_object('chk_use_name').get_active(),
        }

        client.extractor.set_config(config)

    def on_show_prefs(self):
        if client.is_localhost():
            self.builder.get_object('folderchooser_path').show()
            self.builder.get_object('entry_path').hide()
        else:
            self.builder.get_object('folderchooser_path').hide()
            self.builder.get_object('entry_path').show()

        def on_get_config(config):
            if client.is_localhost():
                self.builder.get_object('folderchooser_path').set_current_folder(
                    config['extract_path']
                )
            else:
                self.builder.get_object('entry_path').set_text(config['extract_path'])

            self.builder.get_object('chk_use_name').set_active(
                config['use_name_folder']
            )

        client.extractor.get_config().addCallback(on_get_config)
