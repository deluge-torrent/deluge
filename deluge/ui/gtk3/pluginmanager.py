# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
import deluge.pluginmanagerbase
from deluge.configmanager import ConfigManager
from deluge.ui.client import client

log = logging.getLogger(__name__)


class PluginManager(deluge.pluginmanagerbase.PluginManagerBase, component.Component):
    def __init__(self):
        component.Component.__init__(self, 'PluginManager')
        self.config = ConfigManager('gtk3ui.conf')
        deluge.pluginmanagerbase.PluginManagerBase.__init__(
            self, 'gtk3ui.conf', 'deluge.plugin.gtk3ui'
        )

        self.hooks = {'on_apply_prefs': [], 'on_show_prefs': []}

        client.register_event_handler(
            'PluginEnabledEvent', self._on_plugin_enabled_event
        )
        client.register_event_handler(
            'PluginDisabledEvent', self._on_plugin_disabled_event
        )

    def register_hook(self, hook, function):
        """Register a hook function with the plugin manager"""
        try:
            self.hooks[hook].append(function)
        except KeyError:
            log.warning('Plugin attempting to register invalid hook.')

    def deregister_hook(self, hook, function):
        """Deregisters a hook function"""
        try:
            self.hooks[hook].remove(function)
        except KeyError:
            log.warning('Unable to deregister hook %s', hook)

    def start(self):
        """Start the plugin manager"""
        # Update the enabled_plugins from the core
        client.core.get_enabled_plugins().addCallback(self._on_get_enabled_plugins)
        for instance in self.plugins.values():
            component.start([instance.plugin._component_name])

    def stop(self):
        # Disable the plugins
        self.disable_plugins()

    def update(self):
        pass

    def _on_get_enabled_plugins(self, enabled_plugins):
        log.debug('Core has these plugins enabled: %s', enabled_plugins)
        for plugin in enabled_plugins:
            self.enable_plugin(plugin)

    def _on_plugin_enabled_event(self, name):
        try:
            self.enable_plugin(name)
        except Exception as ex:
            log.warning('Failed to enable plugin "%s": ex: %s', name, ex)

        self.run_on_show_prefs()

    def _on_plugin_disabled_event(self, name):
        self.disable_plugin(name)

    # Hook functions
    def run_on_show_prefs(self):
        """This hook is run before the user is shown the preferences dialog.
        It is designed so that plugins can update their preference page with
        the config."""
        log.debug('run_on_show_prefs')
        for function in self.hooks['on_show_prefs']:
            function()

    def run_on_apply_prefs(self):
        """This hook is run after the user clicks Apply or OK in the preferences
        dialog.
        """
        log.debug('run_on_apply_prefs')
        for function in self.hooks['on_apply_prefs']:
            function()

    # Plugin functions.. will likely move to own class..

    def add_torrentview_text_column(self, *args, **kwargs):
        return component.get('TorrentView').add_text_column(*args, **kwargs)

    def remove_torrentview_column(self, *args):
        return component.get('TorrentView').remove_column(*args)

    def add_toolbar_separator(self):
        return component.get('ToolBar').add_separator()

    def add_toolbar_button(self, *args, **kwargs):
        return component.get('ToolBar').add_toolbutton(*args, **kwargs)

    def remove_toolbar_button(self, *args):
        return component.get('ToolBar').remove(*args)

    def add_torrentmenu_menu(self, *args):
        return component.get('MenuBar').torrentmenu.append(*args)

    def add_torrentmenu_separator(self):
        return component.get('MenuBar').add_torrentmenu_separator()

    def remove_torrentmenu_item(self, *args):
        return component.get('MenuBar').torrentmenu.remove(*args)

    def add_preferences_page(self, *args):
        return component.get('Preferences').add_page(*args)

    def remove_preferences_page(self, *args):
        return component.get('Preferences').remove_page(*args)

    def update_torrent_view(self, *args):
        return component.get('TorrentView').update(*args)

    def get_selected_torrents(self):
        """Returns a list of the selected torrent_ids"""
        return component.get('TorrentView').get_selected_torrents()
