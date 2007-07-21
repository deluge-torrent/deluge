#
# torrentview.py
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

import logging

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gobject
import gettext

import columns

# Get the logger
log = logging.getLogger("deluge")

class TorrentView:
    def __init__(self, window):
        log.debug("TorrentView Init..")
        self.window = window
        # Get the torrent_view widget
        self.torrent_view = self.window.main_glade.get_widget("torrent_view")
        
        ## TreeModel setup ##
        # UID, Q#, Status Icon, Name, Size, Progress, Message, Seeders, Peers,
        #     DL, UL, ETA, Share
        self.torrent_model = gtk.ListStore(int, gobject.TYPE_UINT, 
            gtk.gdk.Pixbuf, str, gobject.TYPE_UINT64, float, str, int, int, 
            int, int, int, int, gobject.TYPE_UINT, float)
        
        ## TreeView setup ##
        self.torrent_view.set_model(self.torrent_model)
        self.torrent_view.set_rules_hint(True)
        self.torrent_view.set_reorderable(True)
        self.torrent_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        # Initializes the columns for the torrent_view
        (TORRENT_VIEW_COL_UID,
         TORRENT_VIEW_COL_QUEUE,
         TORRENT_VIEW_COL_STATUSICON,
         TORRENT_VIEW_COL_NAME,
         TORRENT_VIEW_COL_SIZE,
         TORRENT_VIEW_COL_PROGRESS,
         TORRENT_VIEW_COL_STATUS,
         TORRENT_VIEW_COL_CONNECTED_SEEDS,
         TORRENT_VIEW_COL_SEEDS,
         TORRENT_VIEW_COL_CONNECTED_PEERS,
         TORRENT_VIEW_COL_PEERS,
         TORRENT_VIEW_COL_DOWNLOAD,
         TORRENT_VIEW_COL_UPLOAD,
         TORRENT_VIEW_COL_ETA,
         TORRENT_VIEW_COL_RATIO) = range(15)
        
        self.queue_column = columns.add_text_column(
            self.torrent_view, "#",
            TORRENT_VIEW_COL_QUEUE)
        self.name_column = columns.add_texticon_column(
            self.torrent_view, 
            _("Name"),
            TORRENT_VIEW_COL_STATUSICON,
            TORRENT_VIEW_COL_NAME)
        self.size_column = columns.add_func_column(
            self.torrent_view,
            _("Size"),
            columns.cell_data_size,
            TORRENT_VIEW_COL_SIZE)
        self.progress_column = columns.add_progress_column(
            self.torrent_view,
            _("Progress"),
            TORRENT_VIEW_COL_PROGRESS,
            TORRENT_VIEW_COL_STATUS)
        self.seed_column = columns.add_func_column(
            self.torrent_view,
            _("Seeders"),
            columns.cell_data_peer,
            (TORRENT_VIEW_COL_CONNECTED_SEEDS, TORRENT_VIEW_COL_SEEDS))
        self.peer_column = columns.add_func_column(
            self.torrent_view,
            _("Peers"),
            columns.cell_data_peer,
            (TORRENT_VIEW_COL_CONNECTED_PEERS, TORRENT_VIEW_COL_PEERS))
        self.dl_column = columns.add_func_column(
            self.torrent_view,
            _("Down Speed"),
            columns.cell_data_speed,
            TORRENT_VIEW_COL_DOWNLOAD)
        self.ul_column = columns.add_func_column(
            self.torrent_view,
            _("Up Speed"),
            columns.cell_data_speed,
            TORRENT_VIEW_COL_UPLOAD)
        self.eta_column = columns.add_func_column(
            self.torrent_view,
            _("ETA"),
            columns.cell_data_time,
            TORRENT_VIEW_COL_ETA)
        self.share_column = columns.add_func_column(
            self.torrent_view,
            _("Ratio"),
            columns.cell_data_ratio,
            TORRENT_VIEW_COL_RATIO)
        
        # Set some column settings
        self.progress_column.set_expand(True)
        self.name_column.set_sort_column_id(TORRENT_VIEW_COL_NAME)
        self.seed_column.set_sort_column_id(TORRENT_VIEW_COL_CONNECTED_SEEDS)
        self.peer_column.set_sort_column_id(TORRENT_VIEW_COL_CONNECTED_PEERS)
        
        # Set the default sort column to the queue column
        self.torrent_model.set_sort_column_id(TORRENT_VIEW_COL_QUEUE, 
                                                gtk.SORT_ASCENDING)
                
        ### Connect Signals ###
        # Connect to the 'button-press-event' to know when to bring up the
        # torrent menu popup.
        self.torrent_view.connect("button-press-event",
                                    self.on_button_press_event)
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.torrent_view.get_selection().connect("changed", 
                                    self.on_selection_changed)
    
    ### Callbacks ###                             
    def on_button_press_event(self, widget, event):
        log.debug("on_button_press_event")
    
    def on_selection_changed(self, treeselection, data):
        log.debug("on_selection_changed")
        
