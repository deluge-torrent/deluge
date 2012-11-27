#
# pluginmanager.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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


import deluge.component as component
import deluge.pluginmanagerbase
from deluge.ui.client import client
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class PluginManager(deluge.pluginmanagerbase.PluginManagerBase,
    component.Component):
    def __init__(self):
        component.Component.__init__(self, "PluginManager")
        self.config = ConfigManager("gtkui.conf")
        deluge.pluginmanagerbase.PluginManagerBase.__init__(
            self, "gtkui.conf", "deluge.plugin.gtkui")

        self.hooks = {
            "on_apply_prefs": [],
            "on_show_prefs": []
        }

        client.register_event_handler("PluginEnabledEvent", self._on_plugin_enabled_event)
        client.register_event_handler("PluginDisabledEvent", self._on_plugin_disabled_event)

    def register_hook(self, hook, function):
        """Register a hook function with the plugin manager"""
        try:
            self.hooks[hook].append(function)
        except KeyError:
            log.warning("Plugin attempting to register invalid hook.")

    def deregister_hook(self, hook, function):
        """Deregisters a hook function"""
        try:
            self.hooks[hook].remove(function)
        except:
            log.warning("Unable to deregister hook %s", hook)

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
        log.debug("Core has these plugins enabled: %s", enabled_plugins)
        for plugin in enabled_plugins:
            self.enable_plugin(plugin)

    def _on_plugin_enabled_event(self, name):
        self.enable_plugin(name)
        self.run_on_show_prefs()

    def _on_plugin_disabled_event(self, name):
        self.disable_plugin(name)

    ## Hook functions
    def run_on_show_prefs(self):
        """This hook is run before the user is shown the preferences dialog.
        It is designed so that plugins can update their preference page with
        the config."""
        log.debug("run_on_show_prefs")
        for function in self.hooks["on_show_prefs"]:
            function()

    def run_on_apply_prefs(self):
        """This hook is run after the user clicks Apply or OK in the preferences
        dialog.
        """
        log.debug("run_on_apply_prefs")
        for function in self.hooks["on_apply_prefs"]:
            function()

    ## Plugin functions.. will likely move to own class..

    def add_torrentview_text_column(self, *args, **kwargs):
        return component.get("TorrentView").add_text_column(*args, **kwargs)

    def remove_torrentview_column(self, *args):
        return component.get("TorrentView").remove_column(*args)

    def add_toolbar_separator(self):
        return component.get("ToolBar").add_separator()

    def add_toolbar_button(self, *args, **kwargs):
        return component.get("ToolBar").add_toolbutton(*args, **kwargs)

    def remove_toolbar_button(self, *args):
        return component.get("ToolBar").remove(*args)

    def add_torrentmenu_menu(self, *args):
        return component.get("MenuBar").torrentmenu.append(*args)

    def add_torrentmenu_separator(self):
        return component.get("MenuBar").add_torrentmenu_separator()

    def remove_torrentmenu_item(self, *args):
        return component.get("MenuBar").torrentmenu.remove(*args)

    def add_preferences_page(self, *args):
        return component.get("Preferences").add_page(*args)

    def remove_preferences_page(self, *args):
        return component.get("Preferences").remove_page(*args)

    def update_torrent_view(self, *args):
        return component.get("TorrentView").update(*args)

    def get_selected_torrents(self):
        """Returns a list of the selected torrent_ids"""
        return component.get("TorrentView").get_selected_torrents()
