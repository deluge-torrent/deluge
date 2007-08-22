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
        self.add_text_column("Name", status_field=["name"])
        self.add_func_column("Size", 
                                            listview.cell_data_size, 
                                            [long],
                                            status_field=["total_size"])
        self.add_progress_column("Progress", status_field=["progress", "state"])
        self.add_func_column("Seeders",
                                        listview.cell_data_peer,
                                        [int, int],
                                        status_field=["num_seeds", "num_seeds"])
        self.add_func_column("Peers",
                                        listview.cell_data_peer,
                                        [int, int],
                                        status_field=["num_peers", "num_peers"])
        self.add_func_column("Down Speed",
                                        listview.cell_data_speed,
                                        [float],
                                        status_field=["download_payload_rate"])
        self.add_func_column("Up Speed",
                                        listview.cell_data_speed,
                                        [float],
                                        status_field=["upload_payload_rate"])
        self.add_func_column("ETA",
                                            listview.cell_data_time,
                                            [int],
                                            status_field=["eta"])
        self.add_func_column("Ratio",
                                            listview.cell_data_ratio,
                                            [float],
                                            status_field=["ratio"])

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
    
    def update(self, columns=None):
        """Update the view.  If columns is not None, it will attempt to only
        update those columns selected.
        """
        # Iterates through every row and updates them accordingly
        if self.liststore is not None:
            self.liststore.foreach(self.update_row, columns)
            
    def update_row(self, model, path, row, columns=None):
        torrent_id = self.liststore.get_value(row, 
                                self.columns["torrent_id"].column_indices[0])
        # Store the 'status_fields' we need to send to core
        status_keys = []
        # Store the actual columns we will be updating
        columns_to_update = []
        if columns is None:
            # Iterate through the list of columns and only add the 
            # 'status-fields' of the visible ones.
            for column in self.columns.values():
                # Make sure column is visible and has 'status_field' set.
                # If not, we can ignore it.
                if column.column.get_visible() is True \
                    and column.hidden is False \
                        and column.status_field is not None:
                    for field in column.status_field:
                        status_keys.append(field)
                        columns_to_update.append(column.name)                           
        else:
            # Iterate through supplied list of columns to update
            for column in columns:
                if self.columns[column].column.get_visible() is True \
                    and self.columns[column].hidden is False \
                    and self.columns[column].status_field is not None:
                    for field in self.columns[column].status_field:
                        status_keys.append(field)
                        columns_to_update.append(column)
        
        # If there is nothing in status_keys then we must not continue
        if status_keys is []:
            return
            
        # Remove duplicates from status_key list
        status_keys = list(set(status_keys))
        status = functions.get_torrent_status(self.core, torrent_id,
                status_keys)

        # Set values for each column in the row
        for column in columns_to_update:
            if type(self.get_column_index(column)) is not list:
                # We only have a single list store column we need to update
                self.liststore.set_value(row,
                            self.get_column_index(column),
                            status[self.columns[column].status_field[0]])
            else:
                # We have more than 1 liststore column to update
                i = 0
                for index in self.get_column_index(column):
                    # Only update the column if the status field exists
                    try:
                        self.liststore.set_value(row,
                            index,
                            status[self.columns[column].status_field[i]])
                    except:
                        pass
                    i = i + 1
                        
    def add_row(self, torrent_id):
        """Adds a new torrent row to the treeview"""
        # Insert a new row to the liststore
        row = self.liststore.append()
        # Store the torrent id
        self.liststore.set_value(
                    row,
                    self.columns["torrent_id"].column_indices[0], 
                    torrent_id)
        # Update the new row so 
        self.update_row(None, None, row)
        
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
        
