#
# status.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from optparse import make_option
from twisted.internet import defer
from deluge.ui.console.main import BaseCommand
from deluge.ui.client import client
import deluge.common
import deluge.component as component


class Command(BaseCommand):
    """Shows a various status information from the daemon."""
    option_list = BaseCommand.option_list + (
        make_option('-r', '--raw', action='store_true', default=False, dest='raw',
                    help='Don\'t format upload/download rates in KiB/s \
(useful for scripts that want to do their own parsing)'),
        make_option('-n', '--no-torrents', action='store_false', default=True, dest='show_torrents',
                    help='Don\'t show torrent status (this will make the command a bit faster)'),
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
            self.console.write("{!info!}Total upload: %s" % deluge.common.fspeed(self.status["payload_upload_rate"]))
            self.console.write("{!info!}Total download: %s" %
                               deluge.common.fspeed(self.status["payload_download_rate"]))
        self.console.write("{!info!}DHT Nodes: %i" % self.status["dht_nodes"])
        self.console.write("{!info!}Total connections: %i" % self.connections)
        if self.torrents == -1:
            self.console.write("{!error!}Error getting torrent info")
        elif self.torrents != -2:
            self.console.write("{!info!}Total torrents: %i" % len(self.torrents))
            states = ["Downloading", "Seeding", "Paused", "Checking", "Error", "Queued"]
            state_counts = {}
            for state in states:
                state_counts[state] = 0
            for t in self.torrents:
                s = self.torrents[t]
                state_counts[s["state"]] += 1
            for state in states:
                self.console.write("{!info!} %s: %i" % (state, state_counts[state]))

        self.console.set_batch_write(False)
