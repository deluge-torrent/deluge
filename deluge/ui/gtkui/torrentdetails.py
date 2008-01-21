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

import deluge.component as component
import deluge.ui.client as client
import deluge.common
from deluge.log import LOG as log

def fpeer_sized(first, second):
    return "%s (%s)" % (deluge.common.fsize(first), deluge.common.fsize(second))

def fpeer_size_second(first, second):
    return "%s (%s)" % (first, deluge.common.fsize(second))

def fratio(value):
    return "%.3f" % value

def fpcnt(value):
    return "%.2f%%" % value
    
class TorrentDetails(component.Component):
    def __init__(self):
        component.Component.__init__(self, "TorrentDetails")
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        
        self.notebook = glade.get_widget("torrent_info")
        self.details_tab = glade.get_widget("torrentdetails_tab")
    
        # Don't show tabs if there is only 1
        if self.notebook.get_n_pages() < 2:
            self.notebook.set_show_tabs(False)
        else:
            self.notebook.set_show_tabs(True)
                
        self.is_visible = True
        
        # Get the labels we need to update.
        # widgetname, modifier function, status keys
        self.label_widgets = [
            (glade.get_widget("summary_name"), None, ("name",)),
            (glade.get_widget("summary_total_size"), deluge.common.fsize, ("total_size",)),
            (glade.get_widget("summary_num_files"), str, ("num_files",)),
            (glade.get_widget("summary_pieces"), fpeer_size_second, ("num_pieces", "piece_length")),
            (glade.get_widget("summary_availability"), fratio, ("distributed_copies",)),
            (glade.get_widget("summary_total_downloaded"), fpeer_sized, ("total_done", "total_payload_download")),
            (glade.get_widget("summary_total_uploaded"), fpeer_sized, ("total_uploaded", "total_payload_upload")),
            (glade.get_widget("summary_download_speed"), deluge.common.fspeed, ("download_payload_rate",)),
            (glade.get_widget("summary_upload_speed"), deluge.common.fspeed, ("upload_payload_rate",)),
            (glade.get_widget("summary_seeders"), deluge.common.fpeer, ("num_seeds", "total_seeds")),
            (glade.get_widget("summary_peers"), deluge.common.fpeer, ("num_peers", "total_peers")),
            (glade.get_widget("summary_eta"), deluge.common.ftime, ("eta",)),
            (glade.get_widget("summary_share_ratio"), fratio, ("ratio",)),
            (glade.get_widget("summary_tracker"), None, ("tracker",)),
            (glade.get_widget("summary_tracker_status"), None, ("tracker_status",)),
            (glade.get_widget("summary_next_announce"), deluge.common.ftime, ("next_announce",)),
            (glade.get_widget("summary_torrent_path"), None, ("save_path",)),
            (glade.get_widget("progressbar"), fpcnt, ("progress",))
        ]
    
    def visible(self, visible):
        if visible:
            self.notebook.show()
        else:
            self.notebook.hide()
            self.window.vpaned.set_position(-1)
        
        self.is_visible = visible
        
    def stop(self):
        self.clear()

    def update(self):
        # Show tabs if more than 1 page
        if self.notebook.get_n_pages() > 1:
            self.notebook.set_show_tabs(True)
            
        # Only update if this page is showing
        if self.notebook.page_num(self.details_tab) is \
            self.notebook.get_current_page() and \
                self.notebook.get_property("visible"):
            # Get the first selected torrent
            selected = component.get("TorrentView").get_selected_torrents()
            
            # Only use the first torrent in the list or return if None selected
            if len(selected) != 0:
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
                "total_seeds", "eta", "ratio", "tracker", "next_announce",
                "tracker_status", "save_path"]
            client.get_torrent_status(
                self._on_get_torrent_status, selected, status_keys)
                    
    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if status is None:
            return
       
        # Update all the label widgets        
        for widget in self.label_widgets:
            if widget[1] != None:
                args = []
                try:
                    for key in widget[2]:
                        args.append(status[key])
                except Exception, e:
                    log.debug("Unable to get status value: %s", e)
                    continue
                    
                txt = widget[1](*args)
            else:
                txt = status[widget[2][0]]

            if widget[0].get_text() != txt:
                widget[0].set_text(txt)
        
        # Do the progress bar because it's a special case (not a label)
        w = self.window.main_glade.get_widget("progressbar")
        fraction = status["progress"] / 100
        if w.get_fraction() != fraction:
            w.set_fraction(fraction)
                    
    def clear(self):
        # Only update if this page is showing
        if self.notebook.page_num(self.details_tab) is \
                                            self.notebook.get_current_page():

            for widget in self.label_widgets:
                widget[0].set_text("")
                
            self.window.main_glade.get_widget("progressbar").set_fraction(0.0)
