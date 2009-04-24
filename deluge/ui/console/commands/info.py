#
# info.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
#

from optparse import make_option
import sys

from deluge.ui.console.main import BaseCommand
import deluge.ui.console.colors as colors
from deluge.ui.client import client
import deluge.common as common
import deluge.component as component

status_keys = ["state",
        "save_path",
        "tracker",
        "next_announce",
        "name",
        "total_size",
        "progress",
        "num_seeds",
        "total_seeds",
        "num_peers",
        "total_peers",
        "eta",
        "download_payload_rate",
        "upload_payload_rate",
        "ratio",
        "distributed_copies",
        "num_pieces",
        "piece_length",
        "total_done",
        "files",
        "file_priorities",
        "file_progress",
        "peers",
        "is_seed",
        "is_finished"
        ]


def format_progressbar(progress, width):
    """
    Returns a string of a progress bar.

    :param progress: float, a value between 0-100

    :returns: str, a progress bar based on width

    """

    w = width - 2 # we use a [] for the beginning and end
    s = "["
    p = int(round((progress/100) * w))
    s += "#" * p
    s += "~" * (w - p)
    s += "]"
    return s


class Command(BaseCommand):
    """Show information about the torrents"""

    option_list = BaseCommand.option_list + (
            make_option('-v', '--verbose', action='store_true', default=False, dest='verbose',
                        help='shows more information per torrent'),
            make_option('-i', '--id', action='store_true', default=False, dest='tid',
                        help='use internal id instead of torrent name'),
    )

    usage =  "Usage: info [<torrent-id> [<torrent-id> ...]]\n"\
             "       You can give the first few characters of a torrent-id to identify the torrent."


    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        # Compile a list of torrent_ids to request the status of
        torrent_ids = []
        for arg in args:
            torrent_ids.extend(self.console.match_torrent(arg))

        def on_torrents_status(status):
            # Print out the information for each torrent
            for key, value in status.items():
                self.show_info(key, value, options["verbose"])

        def on_torrents_status_fail(reason):
            self.console.write("{{error}}Error getting torrent info: %s" % reason)

        d = client.core.get_torrents_status({"id": torrent_ids}, status_keys)
        d.addCallback(on_torrents_status)
        d.addErrback(on_torrents_status_fail)

    def show_info(self, torrent_id, status, verbose=False):
        """
        Writes out the torrents information to the screen.

        :param torrent_id: str, the torrent_id
        :param status: dict, the torrents status, this should have the same keys
            as status_keys
        :param verbose: bool, if true, we print out more information about the
            the torrent
        """
        self.console.write(" ")
        self.console.write("{{info}}Name: {{input}}%s" % (status["name"]))
        self.console.write("{{info}}ID: {{input}}%s" % (torrent_id))
        s = "{{info}}State: %s%s" % (colors.state_color[status["state"]], status["state"])
        # Only show speed if active
        if status["state"] in ("Seeding", "Downloading"):
            if status["state"] != "Seeding":
                s += " {{info}}Down Speed: {{input}}%s" % common.fspeed(status["download_payload_rate"])
            s += " {{info}}Up Speed: {{input}}%s" % common.fspeed(status["upload_payload_rate"])

            if common.ftime(status["eta"]):
                s += " {{info}}ETA: {{input}}%s" % common.ftime(status["eta"])

        self.console.write(s)

        if status["state"] in ("Seeding", "Downloading", "Queued"):
            s = "{{info}}Seeds: {{input}}%s (%s)" % (status["num_seeds"], status["total_seeds"])
            s += " {{info}}Peers: {{input}}%s (%s)" % (status["num_peers"], status["total_peers"])
            s += " {{info}}Availibility: {{input}}%.2f" % status["distributed_copies"]
            self.console.write(s)

        s = "{{info}}Size: {{input}}%s/%s" % (common.fsize(status["total_done"]), common.fsize(status["total_size"]))
        s += " {{info}}Ratio: {{input}}%.3f" % status["ratio"]
        self.console.write(s)

        if not status["is_finished"]:
            pbar = format_progressbar(status["progress"], self.console.screen.cols - (13 + len("%.2f%%" % status["progress"])))
            s = "{{info}}Progress: {{input}}%.2f%% %s" % (status["progress"], pbar)
            self.console.write(s)


        if verbose:
            self.console.write("  {{info}}::Files")
            for i, f in enumerate(status["files"]):
                s = "    {{input}}%s (%s)" % (f["path"], common.fsize(f["size"]))
                s += " {{info}}Progress: {{input}}%.2f%%" % (status["file_progress"][i] * 100)
                s += " {{info}}Priority:"
                fp = common.FILE_PRIORITY[status["file_priorities"][i]].replace("Priority", "")
                if fp == "Do Not Download":
                    s += "{{error}}"
                else:
                    s += "{{success}}"

                s += " %s" % (fp)
                self.console.write(s)

            self.console.write("  {{info}}::Peers")
            if len(status["peers"]) == 0:
                self.console.write("    None")
            else:
                s = ""
                for peer in status["peers"]:
                    if peer["seed"]:
                        s += "%sSeed{{input}}" % colors.state_color["Seeding"]
                    else:
                        s += "%sPeer{{input}}" % colors.state_color["Downloading"]

                    s += " " + peer["country"]
                    s += " " + peer["ip"]
                    s += "\t" + peer["client"].encode(sys.getdefaultencoding(), "replace")


                    s += "{{input}}\t%s\t%s" % (common.fspeed(peer["up_speed"]), common.fspeed(peer["down_speed"]))
                    s += "\n"

                self.console.write(s[:-1])
