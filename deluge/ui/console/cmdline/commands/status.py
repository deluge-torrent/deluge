# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from twisted.internet import defer

import deluge.component as component
from deluge.common import TORRENT_STATE, fspeed
from deluge.ui.client import client

from . import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Shows various status information from the daemon"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-r',
            '--raw',
            action='store_true',
            default=False,
            dest='raw',
            help=_(
                'Raw values for upload/download rates (without KiB/s suffix)'
                '(useful for scripts that want to do their own parsing)'
            ),
        )
        parser.add_argument(
            '-n',
            '--no-torrents',
            action='store_false',
            default=True,
            dest='show_torrents',
            help=_('Do not show torrent status (Improves command speed)'),
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')
        self.status = None
        self.torrents = 1 if options.show_torrents else 0
        self.raw = options.raw

        def on_session_status(status):
            self.status = status

        def on_torrents_status(status):
            self.torrents = status

        def on_torrents_status_fail(reason):
            log.warning('Failed to retrieve session status: %s', reason)
            self.torrents = -2

        deferreds = []

        ds = client.core.get_session_status(
            ['num_peers', 'payload_upload_rate', 'payload_download_rate', 'dht_nodes']
        )
        ds.addCallback(on_session_status)
        deferreds.append(ds)

        if options.show_torrents:
            dt = client.core.get_torrents_status({}, ['state'])
            dt.addCallback(on_torrents_status)
            dt.addErrback(on_torrents_status_fail)
            deferreds.append(dt)

        return defer.DeferredList(deferreds).addCallback(self.print_status)

    def print_status(self, *args):
        self.console.set_batch_write(True)
        if self.raw:
            self.console.write(
                '{!info!}Total upload: %f' % self.status['payload_upload_rate']
            )
            self.console.write(
                '{!info!}Total download: %f' % self.status['payload_download_rate']
            )
        else:
            self.console.write(
                '{!info!}Total upload: %s' % fspeed(self.status['payload_upload_rate'])
            )
            self.console.write(
                '{!info!}Total download: %s'
                % fspeed(self.status['payload_download_rate'])
            )
        self.console.write('{!info!}DHT Nodes: %i' % self.status['dht_nodes'])

        if isinstance(self.torrents, int):
            if self.torrents == -2:
                self.console.write('{!error!}Error getting torrent info')
        else:
            self.console.write('{!info!}Total torrents: %i' % len(self.torrents))
            state_counts = {}
            for state in TORRENT_STATE:
                state_counts[state] = 0
            for t in self.torrents:
                s = self.torrents[t]
                state_counts[s['state']] += 1
            for state in TORRENT_STATE:
                self.console.write('{!info!} %s: %i' % (state, state_counts[state]))

        self.console.set_batch_write(False)
