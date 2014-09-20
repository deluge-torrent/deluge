# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


"""PluginManager for Core"""

import logging

import deluge.component as component
import deluge.pluginmanagerbase
from deluge.event import PluginDisabledEvent, PluginEnabledEvent

log = logging.getLogger(__name__)


class PluginManager(deluge.pluginmanagerbase.PluginManagerBase, component.Component):
    """PluginManager handles the loading of plugins and provides plugins with
    functions to access parts of the core."""

    def __init__(self, core):
        component.Component.__init__(self, "CorePluginManager")

        self.status_fields = {}

        # Call the PluginManagerBase constructor
        deluge.pluginmanagerbase.PluginManagerBase.__init__(
            self, "core.conf", "deluge.plugin.core")

    def start(self):
        # Enable plugins that are enabled in the config
        self.enable_plugins()

    def stop(self):
        # Disable all enabled plugins
        self.disable_plugins()

    def shutdown(self):
        self.stop()

    def update_plugins(self):
        for plugin in self.plugins.keys():
            if hasattr(self.plugins[plugin], "update"):
                try:
                    self.plugins[plugin].update()
                except Exception as ex:
                    log.exception(ex)

    def enable_plugin(self, name):
        if name not in self.plugins:
            super(PluginManager, self).enable_plugin(name)
            if name in self.plugins:
                component.get("EventManager").emit(PluginEnabledEvent(name))

    def disable_plugin(self, name):
        if name in self.plugins:
            super(PluginManager, self).disable_plugin(name)
            if name not in self.plugins:
                component.get("EventManager").emit(PluginDisabledEvent(name))

    def get_status(self, torrent_id, fields):
        """Return the value of status fields for the selected torrent_id."""
        status = {}
        for field in fields:
            try:
                status[field] = self.status_fields[field](torrent_id)
            except KeyError:
                pass
        return status

    def register_status_field(self, field, function):
        """Register a new status field.  This can be used in the same way the
        client requests other status information from core."""
        log.debug("Registering status field %s with PluginManager", field)
        self.status_fields[field] = function

    def deregister_status_field(self, field):
        """Deregisters a status field"""
        log.debug("Deregistering status field %s with PluginManager", field)
        try:
            del self.status_fields[field]
        except:
            log.warning("Unable to deregister status field %s", field)
