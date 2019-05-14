# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
from . import common

log = logging.getLogger(__name__)

EXECUTE_ID = 0
EXECUTE_EVENT = 1
EXECUTE_COMMAND = 2

EVENT_MAP = {
    'complete': _('Torrent Complete'),
    'added': _('Torrent Added'),
    'removed': _('Torrent Removed'),
}

EVENTS = ['complete', 'added', 'removed']


class ExecutePreferences(object):
    def __init__(self, plugin):
        self.plugin = plugin

    def load(self):
        log.debug('Adding Execute Preferences page')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(common.get_resource('execute_prefs.ui'))
        self.builder.connect_signals(self)

        events = self.builder.get_object('event_combobox')

        store = Gtk.ListStore(str, str)
        for event in EVENTS:
            event_label = EVENT_MAP[event]
            store.append((event_label, event))
        events.set_model(store)
        events.set_active(0)

        self.plugin.add_preferences_page(
            _('Execute'), self.builder.get_object('execute_box')
        )
        self.plugin.register_hook('on_show_prefs', self.load_commands)
        self.plugin.register_hook('on_apply_prefs', self.on_apply_prefs)

        self.load_commands()

        client.register_event_handler(
            'ExecuteCommandAddedEvent', self.on_command_added_event
        )
        client.register_event_handler(
            'ExecuteCommandRemovedEvent', self.on_command_removed_event
        )

    def unload(self):
        self.plugin.remove_preferences_page(_('Execute'))
        self.plugin.deregister_hook('on_apply_prefs', self.on_apply_prefs)
        self.plugin.deregister_hook('on_show_prefs', self.load_commands)

    def add_command(self, command_id, event, command):
        log.debug('Adding command `%s`', command_id)
        vbox = self.builder.get_object('commands_vbox')
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=5)
        hbox.set_name(command_id + '_' + event)
        label = Gtk.Label(EVENT_MAP[event])
        entry = Gtk.Entry()
        entry.set_text(command)
        button = Gtk.Button()
        button.set_name('remove_%s' % command_id)
        button.connect('clicked', self.on_remove_button_clicked)

        img = Gtk.Image()
        img.set_from_stock(Gtk.STOCK_REMOVE, Gtk.IconSize.BUTTON)
        button.set_image(img)

        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(entry, False, False, 0)
        hbox.pack_start(button, True, True, 0)
        hbox.show_all()
        vbox.pack_start(hbox, True, True, 0)

    def remove_command(self, command_id):
        vbox = self.builder.get_object('commands_vbox')
        children = vbox.get_children()
        for child in children:
            if child.get_name().split('_')[0] == command_id:
                vbox.remove(child)
                break

    def clear_commands(self):
        vbox = self.builder.get_object('commands_vbox')
        children = vbox.get_children()
        for child in children:
            vbox.remove(child)

    def load_commands(self):
        def on_get_commands(commands):
            self.clear_commands()
            log.debug('on_get_commands: %s', commands)
            for command in commands:
                command_id, event, command = command
                self.add_command(command_id, event, command)

        client.execute.get_commands().addCallback(on_get_commands)

    def on_add_button_clicked(self, *args):
        command = self.builder.get_object('command_entry').get_text()
        events = self.builder.get_object('event_combobox')
        event = events.get_model()[events.get_active()][1]
        client.execute.add_command(event, command)

    def on_remove_button_clicked(self, widget, *args):
        command_id = widget.get_name().replace('remove_', '')
        client.execute.remove_command(command_id)

    def on_apply_prefs(self):
        vbox = self.builder.get_object('commands_vbox')
        children = vbox.get_children()
        for child in children:
            command_id, event = child.get_name().split('_')
            for widget in child.get_children():
                if isinstance(widget, Gtk.Entry):
                    command = widget.get_text()
            client.execute.save_command(command_id, event, command)

    def on_command_added_event(self, command_id, event, command):
        log.debug('Adding command %s: %s', event, command)
        self.add_command(command_id, event, command)

    def on_command_removed_event(self, command_id):
        log.debug('Removing command %s', command_id)
        self.remove_command(command_id)


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.plugin = component.get('PluginManager')
        self.preferences = ExecutePreferences(self.plugin)
        self.preferences.load()

    def disable(self):
        self.preferences.unload()
