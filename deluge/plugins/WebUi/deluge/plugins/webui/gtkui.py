# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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

from gi.repository import Gtk

import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

from .common import get_resource

log = logging.getLogger(__name__)


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('config.ui'))

        component.get('Preferences').add_page(
            _('WebUi'), self.builder.get_object('prefs_box')
        )
        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs
        )
        client.webui.get_config().addCallback(self.cb_get_config)
        client.webui.got_deluge_web().addCallback(self.cb_chk_deluge_web)

    def disable(self):
        component.get('Preferences').remove_page(_('WebUi'))
        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )

    def on_apply_prefs(self):
        if not self.have_web:
            return
        log.debug('applying prefs for WebUi')
        config = {
            'enabled': self.builder.get_object('enabled_checkbutton').get_active(),
            'ssl': self.builder.get_object('ssl_checkbutton').get_active(),
            'port': self.builder.get_object('port_spinbutton').get_value_as_int(),
        }
        client.webui.set_config(config)

    def on_show_prefs(self):
        client.webui.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        """Callback for on show_prefs."""
        self.builder.get_object('enabled_checkbutton').set_active(config['enabled'])
        self.builder.get_object('ssl_checkbutton').set_active(config['ssl'])
        self.builder.get_object('port_spinbutton').set_value(config['port'])

    def cb_chk_deluge_web(self, have_web):
        self.have_web = have_web
        if have_web:
            return
        self.builder.get_object('settings_vbox').set_sensitive(False)

        vbox = self.builder.get_object('prefs_box')

        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=0)
        icon = Gtk.Image.new_from_icon_name('dialog-error', Gtk.IconSize.BUTTON)
        icon.set_padding(5, 5)
        hbox.pack_start(icon, False, False, 0)

        label = Gtk.Label(
            _(
                'The Deluge web interface is not installed, '
                'please install the\ninterface and try again'
            )
        )
        label.set_alignment(0, 0.5)
        label.set_padding(5, 5)
        hbox.pack_start(label, False, False, 0)

        vbox.pack_start(hbox, False, False, 10)
        vbox.reorder_child(hbox, 0)
        vbox.show_all()
