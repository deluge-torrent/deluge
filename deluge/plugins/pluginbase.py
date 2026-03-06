#
# Copyright (C) 2007-2010 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.component as component

log = logging.getLogger(__name__)


def _plugin_rpc_name(plugin_name: str) -> str:
    """Return the RPC namespace for a plugin name (lowercase snake_case)."""
    return plugin_name.lower().replace('-', '_').replace(' ', '_')


class PluginBase(component.Component):
    update_interval = 1

    def __init__(self, name):
        super().__init__(name, self.update_interval)

    def enable(self):
        raise NotImplementedError('Need to define an enable method!')

    def disable(self):
        raise NotImplementedError('Need to define a disable method!')


class CorePluginBase(PluginBase):
    def __init__(self, plugin_name):
        name = _plugin_rpc_name(plugin_name)
        super().__init__('CorePlugin.' + name)
        component.get('RPCServer').register_object(self, name)
        log.debug('CorePlugin.%s initialized..', name)

    def __del__(self):
        try:
            component.get('RPCServer').deregister_object(self)
        except KeyError:
            log.debug('RPCServer already deregistered')

    def enable(self):
        super().enable()

    def disable(self):
        super().disable()


class Gtk3PluginBase(PluginBase):
    def __init__(self, plugin_name):
        name = _plugin_rpc_name(plugin_name)
        super().__init__('Gtk3Plugin.' + name)
        log.debug('Gtk3Plugin.%s initialized..', name)

    def enable(self):
        super().enable()

    def disable(self):
        super().disable()


class WebPluginBase(PluginBase):
    scripts = []
    debug_scripts = []

    stylesheets = []
    debug_stylesheets = []

    def __init__(self, plugin_name):
        name = _plugin_rpc_name(plugin_name)
        super().__init__('WebPlugin.' + name)
        component.get('JSON').register_object(self, name)
        log.debug('WebPlugin.%s initialized..', name)

    def __del__(self):
        component.get('JSON').deregister_object(self)

    def enable(self):
        pass

    def disable(self):
        pass
