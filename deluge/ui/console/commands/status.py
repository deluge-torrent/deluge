# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from optparse import make_option

from twisted.internet import defer

import deluge.component as component
from deluge.common import TORRENT_STATE, fspeed
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """Shows a various status information from the daemon."""
    option_list = BaseCommand.option_list + (
        make_option("-r", "--raw", action="store_true", default=False, dest="raw",
                    help="Don't format upload/download rates in KiB/s \
(useful for scripts that want to do their own parsing)"),
        make_option("-n", "--no-torrents", action="store_false", default=True, dest="show_torrents",
                    help="Don't show torrent status (this will make the command a bit faster)"),
    )

    usage = "Usage: status [-r] [-n]"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        self.status = None
        self.connections = None
        if options["show_torrents"]:
            self.torrents = None
        else:
            self.torrents = -2

        self.raw = options["raw"]

        def on_session_status(status):
            self.status = status
            if self.status is not None and self.connections is not None and self.torrents is not None:
                self.print_status()

        def on_torrents_status(status):
            self.torrents = status
            if self.status is not None and self.connections is not None and self.torrents is not None:
                self.print_status()

        def on_torrents_status_fail(reason):
            self.torrents = -1
            if self.status is not None and self.connections is not None and self.torrents is not None:
                self.print_status()

        deferreds = []

        ds = client.core.get_session_status(["num_peers", "payload_upload_rate", "payload_download_rate", "dht_nodes"])
        ds.addCallback(on_session_status)
        deferreds.append(ds)

        if options["show_torrents"]:
            dt = client.core.get_torrents_status({}, ["state"])
            dt.addCallback(on_torrents_status)
            dt.addErrback(on_torrents_status_fail)
            deferreds.append(dt)

        return defer.DeferredList(deferreds)

    def print_status(self):
        self.console.set_batch_write(True)
        if self.raw:
            self.console.write("{!info!}Total upload: %f" % self.status["payload_upload_rate"])
            self.console.write("{!info!}Total download: %f" % self.status["payload_download_rate"])
        else:
            self.console.write("{!info!}Total upload: %s" % fspeed(self.status["payload_upload_rate"]))
            self.console.write("{!info!}Total download: %s" % fspeed(self.status["payload_download_rate"]))
        self.console.write("{!info!}DHT Nodes: %i" % self.status["dht_nodes"])
        self.console.write("{!info!}Total connections: %i" % self.connections)
        if self.torrents == -1:
            self.console.write("{!error!}Error getting torrent info")
        elif self.torrents != -2:
            self.console.write("{!info!}Total torrents: %i" % len(self.torrents))

            state_counts = {}
            for state in TORRENT_STATE:
                state_counts[state] = 0
            for t in self.torrents:
                s = self.torrents[t]
                state_counts[s["state"]] += 1
            for state in TORRENT_STATE:
                self.console.write("{!info!} %s: %i" % (state, state_counts[state]))

        self.console.set_batch_write(False)
