# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
This base class is used in plugin's __init__ for the plugin entry points.
"""
import logging

log = logging.getLogger(__name__)


class PluginInitBase(object):
    _plugin_cls = None

    def __init__(self, plugin_name):
        self.plugin = self._plugin_cls(plugin_name)

    def enable(self):
        try:
            self.plugin.enable()
        except Exception as ex:
            log.error("Unable to enable plugin \"%s\"!", self.plugin._component_name)
            log.exception(ex)

    def disable(self):
        try:
            self.plugin.disable()
        except Exception as ex:
            log.error("Unable to disable plugin \"%s\"!", self.plugin._component_name)
            log.exception(ex)
