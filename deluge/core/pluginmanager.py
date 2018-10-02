# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


"""PluginManager for Core"""
from __future__ import unicode_literals

import logging

from twisted.internet import defer

import deluge.component as component
import deluge.pluginmanagerbase
from deluge.event import PluginDisabledEvent, PluginEnabledEvent

log = logging.getLogger(__name__)


class PluginManager(deluge.pluginmanagerbase.PluginManagerBase, component.Component):
    """PluginManager handles the loading of plugins and provides plugins with
    functions to access parts of the core."""

    def __init__(self, core):
        component.Component.__init__(self, 'CorePluginManager')

        self.status_fields = {}

        # Call the PluginManagerBase constructor
        deluge.pluginmanagerbase.PluginManagerBase.__init__(
            self, 'core.conf', 'deluge.plugin.core'
        )

    def start(self):
        # Enable plugins that are enabled in the config
        self.enable_plugins()

    def stop(self):
        # Disable all enabled plugins
        self.disable_plugins()

    def shutdown(self):
        self.stop()

    def update_plugins(self):
        for plugin in self.plugins:
            if hasattr(self.plugins[plugin], 'update'):
                try:
                    self.plugins[plugin].update()
                except Exception as ex:
                    log.exception(ex)

    def enable_plugin(self, name):
        d = defer.succeed(True)
        if name not in self.plugins:
            d = deluge.pluginmanagerbase.PluginManagerBase.enable_plugin(self, name)

            def on_enable_plugin(result):
                if result is True and name in self.plugins:
                    component.get('EventManager').emit(PluginEnabledEvent(name))
                return result

            d.addBoth(on_enable_plugin)
        return d

    def disable_plugin(self, name):
        d = defer.succeed(True)
        if name in self.plugins:
            d = deluge.pluginmanagerbase.PluginManagerBase.disable_plugin(self, name)

            def on_disable_plugin(result):
                if name not in self.plugins:
                    component.get('EventManager').emit(PluginDisabledEvent(name))
                return result

            d.addBoth(on_disable_plugin)
        return d

    def get_status(self, torrent_id, fields):
        """Return the value of status fields for the selected torrent_id."""
        status = {}
        if len(fields) == 0:
            fields = list(self.status_fields)
        for field in fields:
            try:
                status[field] = self.status_fields[field](torrent_id)
            except KeyError:
                pass
        return status

    def register_status_field(self, field, function):
        """Register a new status field.  This can be used in the same way the
        client requests other status information from core."""
        log.debug('Registering status field %s with PluginManager', field)
        self.status_fields[field] = function

    def deregister_status_field(self, field):
        """Deregisters a status field"""
        log.debug('Deregistering status field %s with PluginManager', field)
        try:
            del self.status_fields[field]
        except Exception:
            log.warning('Unable to deregister status field %s', field)
