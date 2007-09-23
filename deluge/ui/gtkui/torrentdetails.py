#
# torrentdetails.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

"""The torrent details component shows info about the selected torrent."""

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gettext

import deluge.ui.functions as functions
import deluge.common
from deluge.log import LOG as log

class TorrentDetails:
    def __init__(self, window):
        self.window = window
        glade = self.window.main_glade
        
        self.core = functions.get_core()
        
        self.notebook = glade.get_widget("torrent_info")
        self.details_tab = glade.get_widget("torrentdetails_tab")
    
        # Get the labels we need to update.
        self.progress_bar = glade.get_widget("progressbar")
        self.name = glade.get_widget("summary_name")
        self.total_size = glade.get_widget("summary_total_size")
        self.num_files = glade.get_widget("summary_num_files")
        self.pieces = glade.get_widget("summary_pieces")
        self.availability = glade.get_widget("summary_availability")
        self.total_downloaded = glade.get_widget("summary_total_downloaded")
        self.total_uploaded = glade.get_widget("summary_total_uploaded")
        self.download_speed = glade.get_widget("summary_download_speed")
        self.upload_speed = glade.get_widget("summary_upload_speed")
        self.seeders = glade.get_widget("summary_seeders")
        self.peers = glade.get_widget("summary_peers")
        self.percentage_done = glade.get_widget("summary_percentage_done")
        self.share_ratio = glade.get_widget("summary_share_ratio")
        self.tracker = glade.get_widget("summary_tracker")
        self.tracker_status = glade.get_widget("summary_tracker_status")
        self.next_announce = glade.get_widget("summary_next_announce")
        self.eta = glade.get_widget("summary_eta")
    
    def update(self):
        # Only update if this page is showing
        if self.notebook.page_num(self.details_tab) is \
                                            self.notebook.get_current_page():
            # Get the first selected torrent
            selected = self.window.torrentview.get_selected_torrents()
            
            # Only use the first torrent in the list or return if None selected
            if selected is not None:
                selected = selected[0]
            else:
                # No torrent is selected in the torrentview
                return
            
            # Get the torrent status
            status_keys = ["progress", "name", "total_size", "num_files",
                "num_pieces", "piece_length", "distributed_copies", 
                "total_done", "total_payload_download", "total_uploaded",
                "total_payload_upload", "download_payload_rate", 
                "upload_payload_rate", "num_peers", "num_seeds", "total_peers",
                "total_seeds", "eta", "ratio", "tracker", "next_announce"]
            status = functions.get_torrent_status(self.core, 
                                                    selected, 
                                                    status_keys)

            # We need to adjust the value core gives us for progress
            progress = status["progress"]/100
            self.progress_bar.set_fraction(progress)
            self.progress_bar.set_text(deluge.common.fpcnt(progress))
            
            self.name.set_text(status["name"])
            self.total_size.set_text(deluge.common.fsize(status["total_size"]))
            self.num_files.set_text(str(status["num_files"]))
            self.pieces.set_text("%s (%s)" % (status["num_pieces"],
                                deluge.common.fsize(status["piece_length"])))
            self.availability.set_text("%.3f" % status["distributed_copies"])
            self.total_downloaded.set_text("%s (%s)" % \
                (deluge.common.fsize(status["total_done"]),
                deluge.common.fsize(status["total_payload_download"])))
            self.total_uploaded.set_text("%s (%s)" % \
                (deluge.common.fsize(status["total_uploaded"]),
                deluge.common.fsize(status["total_payload_upload"])))
            self.download_speed.set_text(
                deluge.common.fspeed(status["download_payload_rate"]))
            self.upload_speed.set_text(
                deluge.common.fspeed(status["upload_payload_rate"]))
            self.seeders.set_text(deluge.common.fpeer(status["num_seeds"],
                                                    status["total_seeds"]))
            self.peers.set_text(deluge.common.fpeer(status["num_peers"],
                                                    status["total_peers"]))
            self.eta.set_text(deluge.common.ftime(status["eta"]))
            self.share_ratio.set_text("%.3f" % status["ratio"])
            self.tracker.set_text(status["tracker"])
            self.next_announce.set_text(
                deluge.common.ftime(status["next_announce"]))

    def clear(self):
        # Only update if this page is showing
        if self.notebook.page_num(self.details_tab) is \
                                            self.notebook.get_current_page():
            self.name.set_text("")
            self.total_size.set_text("")
            self.num_files.set_text("")
            self.pieces.set_text("")
            self.availability.set_text("")
            self.total_downloaded.set_text("")
            self.total_uploaded.set_text("")
            self.download_speed.set_text("")
            self.upload_speed.set_text("")
            self.seeders.set_text("")
            self.peers.set_text("")
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_text("")
            self.share_ratio.set_text("")
            self.tracker.set_text("")
            self.tracker_status.set_text("")
            self.next_announce.set_text("")
            self.eta.set_text("")
