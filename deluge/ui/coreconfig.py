# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.ui.client import client

log = logging.getLogger(__name__)


class CoreConfig(component.Component):
    def __init__(self):
        log.debug('CoreConfig init..')
        component.Component.__init__(self, 'CoreConfig')
        self.config = {}

        def on_configvaluechanged_event(key, value):
            self.config[key] = value

        client.register_event_handler(
            'ConfigValueChangedEvent', on_configvaluechanged_event
        )

    def start(self):
        def on_get_config(config):
            self.config = config
            return config

        return client.core.get_config().addCallback(on_get_config)

    def stop(self):
        self.config = {}

    def __contains__(self, key):
        return key in self.config

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        client.core.set_config({key: value})

    def __getattr__(self, attr):
        # We treat this directly interacting with the dictionary
        return getattr(self.config, attr)
