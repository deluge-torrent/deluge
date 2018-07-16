# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 John Garland <johnnybg+deluge@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

log = logging.getLogger(__name__)


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.core = client.toggle
        self.plugin = component.get('PluginManager')
        self.separator = self.plugin.add_toolbar_separator()
        self.button = self.plugin.add_toolbar_button(
            self._on_button_clicked,
            label='Pause Session',
            stock='gtk-media-pause',
            tooltip='Pause the session',
        )

    def disable(self):
        component.get('PluginManager').remove_toolbar_button(self.button)
        component.get('PluginManager').remove_toolbar_button(self.separator)

    def update(self):
        def _on_get_status(paused):
            if paused:
                self.button.set_label('Resume Session')
                self.button.set_tooltip_text('Resume the session')
                self.button.set_stock_id('gtk-media-play')
            else:
                self.button.set_label('Pause Session')
                self.button.set_tooltip_text('Pause the session')
                self.button.set_stock_id('gtk-media-pause')

        self.core.get_status().addCallback(_on_get_status)

    def _on_button_clicked(self, widget):
        self.core.toggle()
