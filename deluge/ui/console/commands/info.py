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

states = ["Active", "Downloading", "Seeding", "Paused", "Checking", "Error", "Queued"]


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
    s += "-" * (w - p)
    s += "]"
    return s


class Command(BaseCommand):
    """Show information about the torrents"""

    option_list = BaseCommand.option_list + (
            make_option('-v', '--verbose', action='store_true', default=False, dest='verbose',
                        help='shows more information per torrent'),
            make_option('-d', '--detailed', action='store_true', default=False, dest='detailed',
                        help='shows detailed information about files and peers. '
                        "Implies -v"),
            make_option('-s', '--state', action='store', dest='state',
                        help="Only retrieve torrents in state STATE. "
                        "Allowable values are: %s "%(", ".join(states))),
    )

    usage =  "Usage: info [-v | -d | -s <state>] [<torrent-id> [<torrent-id> ...]]\n"\
             "       use -v to view more info and -d to view detailed information"\
             "       about files and peers."\
             "       info -s <state> will show only torrents in state <state>\n"\
             "       You can give the first few characters of a torrent-id to identify the torrent."

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        # Compile a list of torrent_ids to request the status of
        torrent_ids = []
        for arg in args:
            torrent_ids.extend(self.console.match_torrent(arg))

        if not args:
            torrent_ids.extend(self.console.match_torrent(""))

        def on_torrents_status(status):
            # Print out the information for each torrent
            for key, value in status.items():
                self.show_info(key, value, options["verbose"], options["detailed"])

        def on_torrents_status_fail(reason):
            self.console.write("{!error!}Error getting torrent info: %s" % reason)

        status_dict = {"id": torrent_ids}

        if options["state"]:
            if options["state"] not in states:
                self.console.write("Invalid state: %s"%options["state"])
                self.console.write("Allowble values are: %s."%(", ".join(states)))
                return
            else:
                status_dict["state"] = options["state"]

        d = client.core.get_torrents_status(status_dict, status_keys)
        d.addCallback(on_torrents_status)
        d.addErrback(on_torrents_status_fail)
        return d

    def show_info(self, torrent_id, status, verbose=False, detailed=False):
        """
        Writes out the torrents information to the screen.

        Format depends on switches given.
        """
        self.console.set_batch_write(True)

        if hasattr(self.console, "screen"):
            cols = self.console.screen.cols
        else:
            cols = 80

        if verbose or detailed:
            self.console.write(" ")
            self.console.write("{!info!}Name: {!input!}%s" % (status["name"]))
            self.console.write("{!info!}ID: {!input!}%s" % (torrent_id))
            s = "{!info!}State: %s%s" % (colors.state_color[status["state"]], status["state"])
            # Only show speed if active
            if status["state"] in ("Seeding", "Downloading"):
                if status["state"] != "Seeding":
                    s += " {!info!}Down Speed: {!input!}%s" % common.fspeed(status["download_payload_rate"])
                s += " {!info!}Up Speed: {!input!}%s" % common.fspeed(status["upload_payload_rate"])

                if common.ftime(status["eta"]):
                    s += " {!info!}ETA: {!input!}%s" % common.ftime(status["eta"])

            self.console.write(s)

            if status["state"] in ("Seeding", "Downloading", "Queued"):
                s = "{!info!}Seeds: {!input!}%s (%s)" % (status["num_seeds"], status["total_seeds"])
                s += " {!info!}Peers: {!input!}%s (%s)" % (status["num_peers"], status["total_peers"])
                s += " {!info!}Availibility: {!input!}%.2f" % status["distributed_copies"]
                self.console.write(s)

            total_done = common.fsize(status["total_done"])
            total_size = common.fsize(status["total_size"])
            if total_done == total_size:
                s = "{!info!}Size: {!input!}%s" % (total_size)
            else:
                s = "{!info!}Size: {!input!}%s/%s" % (total_done, total_size)
            s += " {!info!}Ratio: {!input!}%.3f" % status["ratio"]
            s += " {!info!}Uploaded: {!input!}%s" % common.fsize(status["ratio"] * status["total_done"])
            self.console.write(s)

            s = "{!info!}Tracker: {!input!}%s" % status["tracker"]
            self.console.write(s)


            if not status["is_finished"]:
                pbar = format_progressbar(status["progress"], cols - (13 + len("%.2f%%" % status["progress"])))
                s = "{!info!}Progress: {!input!}%.2f%% %s" % (status["progress"], pbar)
                self.console.write(s)

            s = "{!info!}Download location: {!input!}%s" % status["save_path"]
            self.console.write(s)

            if detailed:
                self.console.write("  {!info!}::Files")
                for i, f in enumerate(status["files"]):
                    s = "    {!input!}%s (%s)" % (f["path"], common.fsize(f["size"]))
                    s += " {!info!}Progress: {!input!}%.2f%%" % (status["file_progress"][i] * 100)
                    s += " {!info!}Priority:"
                    fp = common.FILE_PRIORITY[status["file_priorities"][i]].replace("Priority", "")
                    if fp == "Do Not Download":
                        s += "{!error!}"
                    else:
                        s += "{!success!}"

                    s += " %s" % (fp)
                    # Check if this is too long for the screen and reduce the path
                    # if necessary
                    if hasattr(self.console, "screen"):
                        cols = self.console.screen.cols
                        slen = colors.get_line_length(s, self.console.screen.encoding)
                        if slen > cols:
                            s = s.replace(f["path"], f["path"][slen - cols + 1:])
                    self.console.write(s)

                self.console.write("  {!info!}::Peers")
                if len(status["peers"]) == 0:
                    self.console.write("    None")
                else:
                    s = ""
                    for peer in status["peers"]:
                        if peer["seed"]:
                            s += "%sSeed\t{!input!}" % colors.state_color["Seeding"]
                        else:
                            s += "%sPeer\t{!input!}" % colors.state_color["Downloading"]

                        s += peer["country"] + "\t"

                        if peer["ip"].count(":") == 1:
                            # IPv4
                            s += peer["ip"]
                        else:
                            # IPv6
                            s += "[%s]:%s" % (":".join(peer["ip"].split(":")[:-1]), peer["ip"].split(":")[-1])

                        c = peer["client"]
                        s += "\t" + c

                        if len(c) < 16:
                            s += "\t\t"
                        else:
                            s += "\t"
                        s += "%s%s\t%s%s" % (
                            colors.state_color["Seeding"],
                            common.fspeed(peer["up_speed"]),
                            colors.state_color["Downloading"],
                            common.fspeed(peer["down_speed"]))
                        s += "\n"

                    self.console.write(s[:-1])
        else:
            self.console.write(" ")
            up_color = colors.state_color["Seeding"]
            down_color = colors.state_color["Downloading"]

            s = "%s%s" % (colors.state_color[status["state"]], "[" + status["state"][0] + "]")

            s+= " {!info!}" + ("%.2f%%" % status["progress"]).ljust(7, " ")
            s+= " {!input!}%s" % (status["name"])

            #Shorten the ID if it's necessary. Pretty hacky
            #I _REALLY_ should make a nice function for it that can partition and shorten stuff
            space_left = cols - len("[s] 100.00% " + status["name"] + " "*3) - 2
            if space_left >= len(torrent_id):
                #There's enough space, print it
                s += " {!cyan!}%s" % torrent_id
            else:
                #Shorten the ID
                a = int(space_left * 2/3.0)
                b = space_left - a
                if a < 8:
                    b = b - (8-a)
                    a = 8
                    if b < 0:
                        a+= b
                        b = 0
                if a > 0:
                    #Print the shortened ID
                    s += " {!cyan!}%s" % (torrent_id[0:a] + ".." + torrent_id[-b-1:-1])
                else:
                    #It has wrapped over to the second row anyway
                    s += " {!cyan!}%s" % torrent_id
            self.console.write(s)

            dl_info = "{!info!}DL: {!input!}"
            dl_info+= "%s" % common.fsize(status["total_done"])
            if status["total_done"] != status["total_size"]:
                dl_info+= "/%s" % common.fsize(status["total_size"])
            if status["download_payload_rate"] > 0:
                dl_info += " @ %s%s" % (down_color, common.fspeed(status["download_payload_rate"]))

            ul_info = " {!info!}UL: {!input!}"
            ul_info+= "%s" % common.fsize(status["ratio"] * status["total_done"])
            if status["upload_payload_rate"] > 0:
                ul_info += " @ %s%s" % (up_color, common.fspeed(status["upload_payload_rate"]))

            eta = ""
            if common.ftime(status["eta"]):
                eta = " {!info!}ETA: {!magenta!}%s" % common.ftime(status["eta"])

            self.console.write("    " + dl_info + ul_info + eta)
        self.console.set_batch_write(False)

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get("ConsoleUI").tab_complete_torrent(line)
