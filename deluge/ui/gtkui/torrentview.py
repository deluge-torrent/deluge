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

import deluge.ui.functions as functions
import listview

# Get the logger
log = logging.getLogger("deluge")

class TorrentView(listview.ListView):
    def __init__(self, window):
        self.window = window
        # Call the ListView constructor
        listview.ListView.__init__(self, 
                            self.window.main_glade.get_widget("torrent_view"))
        log.debug("TorrentView Init..")
        self.core = functions.get_core()
        
        # Add the columns to the listview
        self.add_text_column("torrent_id", hidden=True)
        self.add_texticon_column("Name")
        self.add_func_column("Size", 
                                            listview.cell_data_size, 
                                            [long])
        self.add_progress_column("Progress")
        self.add_func_column("Seeders",
                                            listview.cell_data_peer,
                                            [int, int])
        self.add_func_column("Peers",
                                            listview.cell_data_peer,
                                            [int, int])
        self.add_func_column("Down Speed",
                                            listview.cell_data_speed,
                                            [float])
        self.add_func_column("Up Speed",
                                            listview.cell_data_speed,
                                            [float])
        self.add_func_column("ETA",
                                            listview.cell_data_time,
                                            [int])
        self.add_func_column("Ratio",
                                            listview.cell_data_ratio,
                                            [float])

        self.window.main_glade.get_widget("menu_columns").set_submenu(
                        self.menu)
                        
        ### Connect Signals ###
        # Connect to the 'button-press-event' to know when to bring up the
        # torrent menu popup.
        self.treeview.connect("button-press-event",
                                    self.on_button_press_event)
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect("changed", 
                                    self.on_selection_changed)
    
    def update(self):
        """Update the view, this is likely called by a timer"""
        # This function is used for the foreach method of the treemodel
        def update_row(model, path, row, user_data):
            torrent_id = self.liststore.get_value(row, 0)
            status_keys = ["progress", "state", "num_seeds", 
                    "num_peers", "download_payload_rate", "upload_payload_rate",
                    "eta"]
            status = functions.get_torrent_status(self.core, torrent_id,
                    status_keys)
                                       
            # Set values for each column in the row

            self.liststore.set_value(row, 
                            self.get_column_index("Progress")[0], 
                            status["progress"]*100)
            self.liststore.set_value(row,
                            self.get_column_index("Progress")[1],
                            status["state"])
            self.liststore.set_value(row,
                            self.get_column_index("Seeders")[0],  
                            status["num_seeds"])
            self.liststore.set_value(row,
                            self.get_column_index("Seeders")[1],  
                            status["num_seeds"])
            self.liststore.set_value(row,
                            self.get_column_index("Peers")[0],  
                            status["num_peers"])
            self.liststore.set_value(row,
                            self.get_column_index("Peers")[1],  
                            status["num_peers"])
            self.liststore.set_value(row,
                            self.get_column_index("Down Speed"),  
                            status["download_payload_rate"])
            self.liststore.set_value(row,
                            self.get_column_index("Up Speed"),  
                            status["upload_payload_rate"])
            self.liststore.set_value(row,
                            self.get_column_index("ETA"),
                            status["eta"])

        # Iterates through every row and updates them accordingly
        if self.liststore is not None:
            self.liststore.foreach(update_row, None)
    
    def add_row(self, torrent_id):
        """Adds a new torrent row to the treeview"""
        # Get the status and info dictionaries
        status_keys = ["name", "total_size", "progress", "state",
                "num_seeds", "num_peers", "download_payload_rate",
                "upload_payload_rate", "eta"]
        status = functions.get_torrent_status(self.core, torrent_id,
                status_keys)
                
        row_list = [
                torrent_id,
                None,
                status["name"],
                status["total_size"],
                status["progress"]*100,
                status["state"],
                status["num_seeds"],
                status["num_seeds"],
                status["num_peers"],
                status["num_peers"],
                status["download_payload_rate"],
                status["upload_payload_rate"],
                status["eta"],
                0.0
            ]

        # Insert any column info from get_functions.. this is usually from
        # plugins
        for column in self.columns.values():
            if column.get_function is not None:
                if len(column.column_indices) == 1:
                    row_list.insert(column.column_indices[0], 
                                                column.get_function(torrent_id))
                else:
                    result = column.get_function(torrent_id)
                    r_index = 0
                    for index in column.column_indices:
                        row_list.insert(index, result[r_index])
                        r_index = r_index + 1

        # Insert the row with info provided from core
        self.liststore.append(row_list)
            
    def remove_row(self, torrent_id):
        """Removes a row with torrent_id"""
        row = self.liststore.get_iter_first()
        while row is not None:
            # Check if this row is the row we want to remove
            if self.liststore.get_value(row, 0) == torrent_id:
                self.liststore.remove(row)
                # Force an update of the torrentview
                self.update()
                break
            row = self.liststore.iter_next(row)
                    
    def get_selected_torrents(self):
        """Returns a list of selected torrents or None"""
        torrent_ids = []
        paths = self.treeview.get_selection().get_selected_rows()[1]
        
        try:
            for path in paths:
                torrent_ids.append(
                    self.liststore.get_value(
                        self.liststore.get_iter(path), 0))
            return torrent_ids
        except ValueError:
            return None
                
    ### Callbacks ###                             
    def on_button_press_event(self, widget, event):
        log.debug("on_button_press_event")
        # We only care about right-clicks
        if event.button == 3:
            # Show the Torrent menu from the MenuBar
            torrentmenu = self.window.menubar.torrentmenu.get_widget(
                                                                "torrent_menu")
            torrentmenu.popup(None, None, None, event.button, event.time)
    
    def on_selection_changed(self, treeselection):
        log.debug("on_selection_changed")
        
