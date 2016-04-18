# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


"""PluginManagerBase"""

import logging
import os.path

import pkg_resources
from twisted.internet import defer
from twisted.python.failure import Failure

import deluge.common
import deluge.component as component
import deluge.configmanager

log = logging.getLogger(__name__)

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

DEPRECATION_WARNING = """
The plugin %s is not using the "deluge.plugins" namespace.
In order to avoid package name clashes between regular python packages and
deluge plugins, the way deluge plugins should be created has changed.
If you're seeing this message and you're not the developer of the plugin which
triggered this warning, please report to it's author.
If you're the developer, please take a look at the plugins hosted on deluge's
git repository to have an idea of what needs to be changed.
"""


class PluginManagerBase(object):
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
        base_plugin_dir = deluge.common.resource_filename("deluge", "plugins")
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
        """Enable a plugin

        Args:
            plugin_name (str): The plugin name

        Returns:
            Deferred: A deferred with callback value True or False indicating
                      whether the plugin is enabled or not.
        """
        if plugin_name not in self.available_plugins:
            log.warning("Cannot enable non-existant plugin %s", plugin_name)
            return defer.succeed(False)

        if plugin_name in self.plugins:
            log.warning("Cannot enable already enabled plugin %s", plugin_name)
            return defer.succeed(True)

        plugin_name = plugin_name.replace(" ", "-")
        egg = self.pkg_env[plugin_name][0]
        egg.activate()
        return_d = defer.succeed(True)

        for name in egg.get_entry_map(self.entry_name):
            entry_point = egg.get_entry_info(self.entry_name, name)
            try:
                cls = entry_point.load()
                instance = cls(plugin_name.replace("-", "_"))
            except component.ComponentAlreadyRegistered as ex:
                log.error(ex)
                return defer.succeed(False)
            except Exception as ex:
                log.error("Unable to instantiate plugin %r from %r!", name, egg.location)
                log.exception(ex)
                continue
            try:
                return_d = defer.maybeDeferred(instance.enable)
            except Exception as ex:
                log.error("Unable to enable plugin '%s'!", name)
                log.exception(ex)
                return_d = defer.fail(False)

            if not instance.__module__.startswith("deluge.plugins."):
                import warnings
                warnings.warn_explicit(
                    DEPRECATION_WARNING % name,
                    DeprecationWarning,
                    instance.__module__, 0
                )
            if self._component_state == "Started":
                def on_enabled(result, instance):
                    return component.start([instance.plugin._component_name])
                return_d.addCallback(on_enabled, instance)

            def on_started(result, instance):
                plugin_name_space = plugin_name.replace("-", " ")
                self.plugins[plugin_name_space] = instance
                if plugin_name_space not in self.config["enabled_plugins"]:
                    log.debug("Adding %s to enabled_plugins list in config", plugin_name_space)
                    self.config["enabled_plugins"].append(plugin_name_space)
                log.info("Plugin %s enabled..", plugin_name_space)
                return True

            def on_started_error(result, instance):
                log.warn("Failed to start plugin '%s': %s", plugin_name, result.getTraceback())
                component.deregister(instance.plugin)
                return False

            return_d.addCallbacks(on_started, on_started_error, callbackArgs=[instance], errbackArgs=[instance])
            return return_d

        return defer.succeed(False)

    def disable_plugin(self, name):
        """
        Disable a plugin

        Args:
            plugin_name (str): The plugin name

        Returns:
            Deferred: A deferred with callback value True or False indicating
                      whether the plugin is disabled or not.
        """
        if name not in self.plugins:
            log.warning("Plugin '%s' is not enabled..", name)
            return defer.succeed(True)

        try:
            d = defer.maybeDeferred(self.plugins[name].disable)
        except Exception as ex:
            log.error("Error when disabling plugin '%s'", self.plugin._component_name)
            log.exception(ex)
            d = defer.succeed(False)

        def on_disabled(result):
            ret = True
            if isinstance(result, Failure):
                log.error("Error when disabling plugin '%s'", name)
                log.exception(result.getTraceback())
                ret = False
            try:
                component.deregister(self.plugins[name].plugin)
                del self.plugins[name]
                self.config["enabled_plugins"].remove(name)
            except Exception as ex:
                log.error("Unable to disable plugin '%s'!", name)
                log.exception(ex)
                ret = False
            else:
                log.info("Plugin %s disabled..", name)
            return ret

        d.addBoth(on_disabled)
        return d

    def get_plugin_info(self, name):
        """Returns a dictionary of plugin info from the metadata"""
        info = {}.fromkeys(METADATA_KEYS)
        last_header = ""
        cont_lines = []
        # Missing plugin info
        if not self.pkg_env[name]:
            log.warn("Failed to retrive info for plugin '%s'", name)
            for k in info:
                info[k] = "not available"
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
