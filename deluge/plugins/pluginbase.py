# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2010 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component

log = logging.getLogger(__name__)


class PluginBase(component.Component):

    update_interval = 1

    def __init__(self, name):
        super(PluginBase, self).__init__(name, self.update_interval)

    def enable(self):
        raise NotImplementedError('Need to define an enable method!')

    def disable(self):
        raise NotImplementedError('Need to define a disable method!')


class CorePluginBase(PluginBase):
    def __init__(self, plugin_name):
        super(CorePluginBase, self).__init__('CorePlugin.' + plugin_name)
        # Register RPC methods
        component.get('RPCServer').register_object(self, plugin_name.lower())
        log.debug('CorePlugin initialized..')

    def __del__(self):
        component.get('RPCServer').deregister_object(self)

    def enable(self):
        super(CorePluginBase, self).enable()

    def disable(self):
        super(CorePluginBase, self).disable()


class Gtk3PluginBase(PluginBase):
    def __init__(self, plugin_name):
        super(Gtk3PluginBase, self).__init__('Gtk3Plugin.' + plugin_name)
        log.debug('Gtk3Plugin initialized..')

    def enable(self):
        super(Gtk3PluginBase, self).enable()

    def disable(self):
        super(Gtk3PluginBase, self).disable()


class WebPluginBase(PluginBase):

    scripts = []
    debug_scripts = []

    stylesheets = []
    debug_stylesheets = []

    def __init__(self, plugin_name):
        super(WebPluginBase, self).__init__('WebPlugin.' + plugin_name)

        # Register JSON rpc methods
        component.get('JSON').register_object(self, plugin_name.lower())
        log.debug('WebPlugin initialized..')

    def __del__(self):
        component.get('JSON').deregister_object(self)

    def enable(self):
        pass

    def disable(self):
        pass
