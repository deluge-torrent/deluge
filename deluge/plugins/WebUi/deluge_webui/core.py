# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from twisted.internet import defer
from twisted.internet.error import CannotListenError

import deluge.component as component
from deluge import configmanager
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

try:
    from deluge.ui.web import server
except ImportError:
    server = False

log = logging.getLogger(__name__)

DEFAULT_PREFS = {'enabled': False, 'ssl': False, 'port': 8112}


class Core(CorePluginBase):
    server = None

    def enable(self):
        self.config = configmanager.ConfigManager('web_plugin.conf', DEFAULT_PREFS)
        if self.config['enabled']:
            self.start_server()

    def disable(self):
        self.stop_server()

    def update(self):
        pass

    def _on_stop(self, *args):
        return self.start_server()

    @export
    def got_deluge_web(self):
        """Status of deluge-web module installation.

        Check if deluge.ui.web.server modulge is installed and has been successfully imported.

        Returns:
            bool: True is deluge-web is installed and available, otherwise False.

        """

        return bool(server)

    def start_server(self):
        if not self.server:
            if not self.got_deluge_web():
                return False

            try:
                self.server = component.get('DelugeWeb')
            except KeyError:
                self.server = server.DelugeWeb(daemon=False)

        self.server.port = self.config['port']
        self.server.https = self.config['ssl']
        try:
            self.server.start()
        except CannotListenError as ex:
            log.warning('Failed to start WebUI server: %s', ex)
            raise
        return True

    def stop_server(self):
        if self.server:
            return self.server.stop()
        return defer.succeed(True)

    def restart_server(self):
        return self.stop_server().addCallback(self._on_stop)

    @export
    def set_config(self, config):
        """Sets the config dictionary."""

        action = None
        if 'enabled' in config:
            if config['enabled'] != self.config['enabled']:
                action = config['enabled'] and 'start' or 'stop'

        if 'ssl' in config:
            if not action:
                action = 'restart'

        for key in config:
            self.config[key] = config[key]
        self.config.save()

        if action == 'start':
            return self.start_server()
        elif action == 'stop':
            return self.stop_server()
        elif action == 'restart':
            return self.restart_server()

    @export
    def get_config(self):
        """Returns the config dictionary."""
        return self.config.config
