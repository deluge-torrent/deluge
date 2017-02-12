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
from __future__ import unicode_literals

import logging

log = logging.getLogger(__name__)


class PluginInitBase(object):
    _plugin_cls = None

    def __init__(self, plugin_name):
        self.plugin = self._plugin_cls(plugin_name)  # pylint: disable=not-callable

    def enable(self):
        return self.plugin.enable()

    def disable(self):
        return self.plugin.disable()
