#
# pluginmanagerbase.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
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


"""PluginManagerBase"""

import os.path

import pkg_resources

import deluge.common
import deluge.configmanager
from deluge.log import LOG as log

import deluge.component as component

METADATA_KEYS = [
    "Name",
    "License",
    "Author",
    "Home-page",
    "Summary",
    "Platform",
    "Version",
    "Author-email",
    "Description",
]

class PluginManagerBase:
    """PluginManagerBase is a base class for PluginManagers to inherit"""

    def __init__(self, config_file, entry_name):
        log.debug("Plugin manager init..")

        self.config = deluge.configmanager.ConfigManager(config_file)

        # Create the plugins folder if it doesn't exist
        if not os.path.exists(os.path.join(deluge.configmanager.get_config_dir(), "plugins")):
            os.mkdir(os.path.join(deluge.configmanager.get_config_dir(), "plugins"))

        # This is the entry we want to load..
        self.entry_name = entry_name

        # Loaded plugins
        self.plugins = {}

        # Scan the plugin folders for plugins
        self.scan_for_plugins()

    def enable_plugins(self):
        # Load plugins that are enabled in the config.
        for name in self.config["enabled_plugins"]:
            self.enable_plugin(name)

    def disable_plugins(self):
        # Disable all plugins that are enabled
        for key in self.plugins.keys():
            self.disable_plugin(key)

    def __getitem__(self, key):
        return self.plugins[key]

    def get_available_plugins(self):
        """Returns a list of the available plugins name"""
        return self.available_plugins

    def get_enabled_plugins(self):
        """Returns a list of enabled plugins"""
        return self.plugins.keys()

    def scan_for_plugins(self):
        """Scans for available plugins"""
        base_plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        pkg_resources.working_set.add_entry(base_plugin_dir)
        user_plugin_dir = os.path.join(deluge.configmanager.get_config_dir(), "plugins")

        plugins_dirs = [base_plugin_dir]
        for dirname in os.listdir(base_plugin_dir):
            plugin_dir = os.path.join(base_plugin_dir, dirname)
            pkg_resources.working_set.add_entry(plugin_dir)
            plugins_dirs.append(plugin_dir)
        pkg_resources.working_set.add_entry(user_plugin_dir)
        plugins_dirs.append(user_plugin_dir)

        self.pkg_env = pkg_resources.Environment(plugins_dirs)

        self.available_plugins = []
        for name in self.pkg_env:
            log.debug("Found plugin: %s %s at %s",
                self.pkg_env[name][0].project_name,
                self.pkg_env[name][0].version,
                self.pkg_env[name][0].location)
            self.available_plugins.append(self.pkg_env[name][0].project_name)

    def enable_plugin(self, plugin_name):
        """Enables a plugin"""
        if plugin_name not in self.available_plugins:
            log.warning("Cannot enable non-existant plugin %s", plugin_name)
            return

        if plugin_name in self.plugins:
            log.warning("Cannot enable already enabled plugin %s", plugin_name)
            return

        plugin_name = plugin_name.replace(" ", "-")
        egg = self.pkg_env[plugin_name][0]
        egg.activate()
        for name in egg.get_entry_map(self.entry_name):
            entry_point = egg.get_entry_info(self.entry_name, name)
            try:
                cls = entry_point.load()
                instance = cls(plugin_name.replace("-", "_"))
            except Exception, e:
                log.error("Unable to instantiate plugin!")
                log.exception(e)
                continue
            instance.enable()
            if self._component_state == "Started":
                component.start([instance.plugin._component_name])
            plugin_name = plugin_name.replace("-", " ")
            self.plugins[plugin_name] = instance
            if plugin_name not in self.config["enabled_plugins"]:
                log.debug("Adding %s to enabled_plugins list in config",
                    plugin_name)
                self.config["enabled_plugins"].append(plugin_name)
            log.info("Plugin %s enabled..", plugin_name)

    def disable_plugin(self, name):
        """Disables a plugin"""
        try:
            self.plugins[name].disable()
            component.deregister(self.plugins[name].plugin._component_name)
            del self.plugins[name]
            self.config["enabled_plugins"].remove(name)
        except KeyError:
            log.warning("Plugin %s is not enabled..", name)

        log.info("Plugin %s disabled..", name)

    def get_plugin_info(self, name):
        """Returns a dictionary of plugin info from the metadata"""
        info = {}.fromkeys(METADATA_KEYS)
        last_header = ""
        cont_lines = []
        # Missing plugin info
        if not self.pkg_env[name]:
            log.warn("Failed to retrive info for plugin '%s'" % name)
            for k in info:
                info[k] = _("Not available")
            return info
        for line in self.pkg_env[name][0].get_metadata("PKG-INFO").splitlines():
            if not line:
                continue
            if line[0] in ' \t' and (len(line.split(":", 1)) == 1 or line.split(":", 1)[0] not in info.keys()):
                # This is a continuation
                cont_lines.append(line.strip())
            else:
                if cont_lines:
                    info[last_header] = "\n".join(cont_lines).strip()
                    cont_lines = []
                if line.split(":", 1)[0] in info.keys():
                    last_header = line.split(":", 1)[0]
                    info[last_header] = line.split(":", 1)[1].strip()
        return info
