# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os

from deluge import component
from deluge.configmanager import ConfigManager
from deluge.pluginmanagerbase import PluginManagerBase
from deluge.ui.client import client

log = logging.getLogger(__name__)


def gather_info(plugin):
    # Get the scripts for the plugin
    scripts = getattr(plugin, "scripts", ())
    debug_scripts = getattr(plugin, "debug_scripts") or scripts

    directories = []
    for script in scripts + debug_scripts:
        if os.path.dirname(script) not in directories:
            directories.append(os.path.dirname(script))

    return {
        "scripts": scripts,
        "debug_scripts": debug_scripts,
        "script_directories": directories
    }


class PluginManager(PluginManagerBase, component.Component):
    def __init__(self):
        component.Component.__init__(self, "Web.PluginManager")
        self.config = ConfigManager("web.conf")
        PluginManagerBase.__init__(self, "web.conf", "deluge.plugin.web")

        client.register_event_handler("PluginEnabledEvent", self._on_plugin_enabled_event)
        client.register_event_handler("PluginDisabledEvent", self._on_plugin_disabled_event)

    def _on_get_enabled_plugins(self, plugins):
        for plugin in plugins:
            self.enable_plugin(plugin)

    def _on_plugin_enabled_event(self, name):
        self.enable_plugin(name)

    def _on_plugin_disabled_event(self, name):
        self.disable_plugin(name)

    def disable_plugin(self, name):
        # Get the plugin instance
        try:
            plugin = component.get("WebPlugin." + name)
        except KeyError:
            log.info("Plugin has no web ui")
            return

        info = gather_info(plugin)

        scripts = component.get("Scripts")
        for script in info["scripts"]:
            scripts.remove_script("%s/%s" % (name.lower(), os.path.basename(script).lower()))

        for script in info["debug_scripts"]:
            scripts.remove_script("%s/%s" % (name.lower(), os.path.basename(script).lower()), "debug")
            scripts.remove_script("%s/%s" % (name.lower(), os.path.basename(script).lower()), "dev")

        super(PluginManager, self).disable_plugin(name)

    def enable_plugin(self, name):
        super(PluginManager, self).enable_plugin(name)

        # Get the plugin instance
        try:
            plugin = component.get("WebPlugin." + name)
        except KeyError:
            log.info("Plugin has no web ui")
            return

        info = gather_info(plugin)

        scripts = component.get("Scripts")
        for script in info["scripts"]:
            log.debug("adding script %s for %s", name, os.path.basename(script))
            scripts.add_script("%s/%s" % (name.lower(), os.path.basename(script)), script)

        for script in info["debug_scripts"]:
            log.debug("adding debug script %s for %s", name, os.path.basename(script))
            scripts.add_script("%s/%s" % (name.lower(), os.path.basename(script)), script, "debug")
            scripts.add_script("%s/%s" % (name.lower(), os.path.basename(script)), script, "dev")

    def start(self):
        """
        Start up the plugin manager
        """
        # Update the enabled plugins from the core
        d = client.core.get_enabled_plugins()
        d.addCallback(self._on_get_enabled_plugins)

    def stop(self):
        """
        Stop the plugin manager
        """
        self.disable_plugins()

    def update(self):
        pass

    def get_plugin_resources(self, name):
        # Get the plugin instance
        try:
            plugin = component.get("WebPlugin." + name)
        except KeyError:
            log.info("Plugin has no web ui")
            return
        info = gather_info(plugin)
        info["name"] = name
        info["scripts"] = ["js/%s/%s" % (name.lower(), os.path.basename(s)) for s in info["scripts"]]
        info["debug_scripts"] = ["js/%s/%s" % (name.lower(), os.path.basename(s)) for s in info["debug_scripts"]]
        del info["script_directories"]
        return info
