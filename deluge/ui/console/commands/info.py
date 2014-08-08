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

from deluge.ui.console.main import BaseCommand
import deluge.ui.console.colors as colors
from deluge.ui.client import client
import deluge.common as common
import deluge.component as component

from deluge.ui.console.modes import format_utils
strwidth = format_utils.strwidth

from os.path import sep as dirsep

STATUS_KEYS = ["state",
        "download_location",
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

# Add filter specific state to torrent states
STATES = ["Active"] + common.TORRENT_STATE

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
                        help="show torrents with state STATE. "
                        "Possible values are:              %s"%(", ".join(STATES))),
    )

    usage =  "Usage: info [-v | -d | -s <state>] [<torrent-id> [<torrent-id> ...]]\n"\
             "       You can give the first few characters of a torrent-id to identify the torrent.\n"\
             "       info * will list all torrents.\n\n"\
             "       Tab Completion (info *pattern*<tab>):\n"\
             "           | First press of <tab> will output up to 15 matches;\n"\
             "           | hitting <tab> a second time, will print 15 more matches; \n"\
             "           | and a third press will print all remaining matches.\n"\
             "           | (To modify behaviour of third <tab>, set `third_tab_lists_all` to False)"

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
            options["state"] = options["state"].capitalize()
            if options["state"] in STATES:
                status_dict["state"] = options["state"]
            else:
                self.console.write("Invalid state: %s"%options["state"])
                self.console.write("Possible values are: %s."%(", ".join(STATES)))
                return

        d = client.core.get_torrents_status(status_dict, STATUS_KEYS)
        d.addCallback(on_torrents_status)
        d.addErrback(on_torrents_status_fail)
        return d

    def show_file_info(self, torrent_id, status):
        SPACES_PER_LEVEL = 2

        if hasattr(self.console, "screen"):
            cols = self.console.screen.cols
        else:
            cols = 80

        dirs = []
        prevpath = []
        for i, file in enumerate(status["files"]):
            filename = file["path"].split(dirsep)[-1]
            filepath = file["path"].split(dirsep)[:-1]

            for depth, subdir in enumerate(filepath):
                indent = " "*depth*SPACES_PER_LEVEL
                if   depth >= len(prevpath):
                    self.console.write("%s{!cyan!}%s" % (indent, subdir))
                elif subdir != prevpath[depth]:
                    self.console.write("%s{!cyan!}%s" % (indent, subdir))

            depth = len(filepath)

            indent = " " * depth * SPACES_PER_LEVEL

            col_filename = indent + filename
            col_size = " ({!cyan!}%s{!input!})" % common.fsize(file["size"])
            col_progress = " {!input!}%.2f%%" % (status["file_progress"][i] * 100)

            col_priority = " {!info!}Priority: "

            fp = common.FILE_PRIORITY[status["file_priorities"][i]].replace("Priority", "")
            if status["file_progress"][i] != 1.0:
                if fp == "Do Not Download":
                    col_priority += "{!error!}"
                else:
                    col_priority += "{!success!}"
            else:
                col_priority += "{!input!}"
            col_priority+= fp

            rf = format_utils.remove_formatting
            tlen = lambda s: strwidth(rf(s))

            if not isinstance(col_filename, unicode):
                col_filename = unicode(col_filename, 'utf-8')

            col_all_info = col_size + col_progress + col_priority
            #Check how much space we've got left after writing all the info
            space_left = cols - tlen(col_all_info)
            #And how much we will potentially have with the longest possible column
            maxlen_space_left = cols - tlen(" (1000.0 MiB) 100.00% Priority: Do Not Download")
            if   maxlen_space_left > tlen(col_filename) + 1:
                #If there is enough space, pad it all nicely
                col_all_info = ""
                col_all_info += " ("
                spaces_to_add = tlen(" (1000.0 MiB)") - tlen(col_size)
                col_all_info += " " * spaces_to_add
                col_all_info += col_size[2:]
                spaces_to_add = tlen(" 100.00%") - tlen(col_progress)
                col_all_info += " " * spaces_to_add
                col_all_info += col_progress
                spaces_to_add = tlen(" Priority: Do Not Download") - tlen(col_priority)
                col_all_info += col_priority
                col_all_info += " " * spaces_to_add
                #And remember to put it to the left!
                col_filename = format_utils.pad_string(col_filename, maxlen_space_left - 2, side = "right")
            elif space_left > tlen(col_filename) + 1:
                #If there is enough space, put the info to the right
                col_filename = format_utils.pad_string(col_filename, space_left - 2, side = "right")
            else:
                #And if there is not, shorten the name
                col_filename = format_utils.trim_string( col_filename, space_left, True)
            self.console.write(col_filename + col_all_info)


            prevpath = filepath

    def show_peer_info(self, torrent_id, status):
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

            s = "{!info!}Download Folder: {!input!}%s" % status["download_location"]
            self.console.write(s)

            if detailed:
                self.console.write("{!info!}Files in torrent")
                self.show_file_info(torrent_id, status)
                self.console.write("{!info!}Connected peers")
                self.show_peer_info(torrent_id, status)
        else:
            self.console.write(" ")
            up_color = colors.state_color["Seeding"]
            down_color = colors.state_color["Downloading"]

            s = "%s%s" % (colors.state_color[status["state"]], "[" + status["state"][0] + "]")

            s+= " {!info!}" + ("%.2f%%" % status["progress"]).ljust(7, " ")
            s+= " {!input!}%s" % (status["name"])

            #Shorten the ID if it's necessary. Pretty hacky
            #I _REALLY_ should make a nice function for it that can partition and shorten stuff
            space_left = cols - strwidth("[s] 100.00% " + status["name"] + " "*3) - 2

            if space_left >= len(torrent_id) - 2:
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
                if a > 8:
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
