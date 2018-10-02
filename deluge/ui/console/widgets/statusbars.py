# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import deluge.common
import deluge.component as component
from deluge.core.preferencesmanager import DEFAULT_PREFS
from deluge.ui.client import client


class StatusBars(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'StatusBars', 2, depend=['CoreConfig'])
        self.config = component.get('CoreConfig')

        # Hold some values we get from the core
        self.connections = 0
        self.download = ''
        self.upload = ''
        self.dht = 0
        self.external_ip = ''

        # Default values
        self.topbar = '{!status!}Deluge %s Console - ' % deluge.common.get_version()
        self.bottombar = '{!status!}C: %s' % self.connections

    def start(self):
        self.update()

    def update(self):
        def on_get_session_status(status):
            self.upload = deluge.common.fsize(status['payload_upload_rate'])
            self.download = deluge.common.fsize(status['payload_download_rate'])
            self.connections = status['num_peers']
            if 'dht_nodes' in status:
                self.dht = status['dht_nodes']

            self.update_statusbars()

        def on_get_external_ip(external_ip):
            self.external_ip = external_ip

        keys = ['num_peers', 'payload_upload_rate', 'payload_download_rate']

        if self.config['dht']:
            keys.append('dht_nodes')

        client.core.get_session_status(keys).addCallback(on_get_session_status)
        client.core.get_external_ip().addCallback(on_get_external_ip)

    def update_statusbars(self):
        # Update the topbar string
        self.topbar = '{!status!}Deluge %s Console - ' % deluge.common.get_version()

        if client.connected():
            info = client.connection_info()
            connection_info = ''

            # Client name
            if info[2] == 'localclient':
                connection_info += '{!white,blue!}%s'
            else:
                connection_info += '{!green,blue,bold!}%s'

            # Hostname
            if info[0] == '127.0.0.1':
                connection_info += '{!white,blue,bold!}@{!white,blue!}%s'
            else:
                connection_info += '{!white,blue,bold!}@{!red,blue,bold!}%s'

            # Port
            if info[1] == DEFAULT_PREFS['daemon_port']:
                connection_info += '{!white,blue!}:%s'
            else:
                connection_info += '{!status!}:%s'

            # Change color back to normal, just in case
            connection_info += '{!status!}'

            self.topbar += connection_info % (info[2], info[0], info[1])
        else:
            self.topbar += 'Not Connected'

        # Update the bottombar string
        self.bottombar = '{!status!}C: {!white,blue!}%s{!status!}' % self.connections

        if self.config['max_connections_global'] > -1:
            self.bottombar += ' (%s)' % self.config['max_connections_global']

        if self.download != '0.0 KiB':
            self.bottombar += ' D: {!magenta,blue,bold!}%s{!status!}' % self.download
        else:
            self.bottombar += ' D: {!white,blue!}%s{!status!}' % self.download

        if self.config['max_download_speed'] > -1:
            self.bottombar += (
                ' (%s ' % self.config['max_download_speed'] + _('KiB/s') + ')'
            )

        if self.upload != '0.0 KiB':
            self.bottombar += ' U: {!green,blue,bold!}%s{!status!}' % self.upload
        else:
            self.bottombar += ' U: {!white,blue!}%s{!status!}' % self.upload

        if self.config['max_upload_speed'] > -1:
            self.bottombar += (
                ' (%s ' % self.config['max_upload_speed'] + _('KiB/s') + ')'
            )

        if self.config['dht']:
            self.bottombar += ' ' + _('DHT') + ': {!white,blue!}%s{!status!}' % self.dht

        self.bottombar += ' ' + _('IP {!white,blue!}%s{!status!}') % (
            self.external_ip if self.external_ip else _('n/a')
        )
