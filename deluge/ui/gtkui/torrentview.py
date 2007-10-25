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

"""The torrent view component that lists all torrents in the session."""

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gettext
import gobject

import deluge.common
import deluge.ui.component as component
import deluge.ui.client as client
from deluge.log import LOG as log
import deluge.ui.gtkui.listview as listview

def cell_data_statusicon(column, cell, model, row, data):
    """Display text with an icon"""
    state = model.get_value(row, data)
    if state == deluge.common.TORRENT_STATE.index("Connecting"):
        fname = "downloading16.png"
    if state == deluge.common.TORRENT_STATE.index("Downloading"):
        fname = "downloading16.png"
    if state == deluge.common.TORRENT_STATE.index("Downloading Metadata"):
        fname = "downloading16.png"
    if state == deluge.common.TORRENT_STATE.index("Queued"):
        fname = "inactive16.png"
    if state == deluge.common.TORRENT_STATE.index("Paused"):
        fname = "inactive16.png"
    if state == deluge.common.TORRENT_STATE.index("Checking"):
        fname = "downloading16.png"
    if state == deluge.common.TORRENT_STATE.index("Allocating"):
        fname = "downloading16.png"
    if state == deluge.common.TORRENT_STATE.index("Finished"):
        fname = "seeding16.png"
    if state == deluge.common.TORRENT_STATE.index("Seeding"):
        fname = "seeding16.png"
        
    icon = gtk.gdk.pixbuf_new_from_file(deluge.common.get_pixmap(fname))
    cell.set_property("pixbuf", icon)

def cell_data_progress(column, cell, model, row, data):
    """Display progress bar with text"""
    # Translated state strings
    TORRENT_STATE = [
        _("Queued"),
        _("Checking"),
        _("Connecting"),
        _("Downloading Metadata"),
        _("Downloading"),
        _("Finished"),
        _("Seeding"),
        _("Allocating"),
        _("Paused")
    ]
    column1, column2 = data
    value = model.get_value(row, column1)
    text = model.get_value(row, column2)
    cell.set_property("value", value)
    textstr = "%s" % TORRENT_STATE[text]
    if TORRENT_STATE[text] == "Downloading" or\
            TORRENT_STATE[text] == "Downloading Metadata" or\
            TORRENT_STATE[text] == "Checking" or\
            TORRENT_STATE[text] == "Allocating" or\
            (TORRENT_STATE[text] == "Paused" and value < 100):
        textstr = textstr + " %.2f%%" % value
    cell.set_property("text", textstr)
    
class TorrentView(listview.ListView, component.Component):
    """TorrentView handles the listing of torrents."""
    def __init__(self):
        component.Component.__init__(self, "TorrentView")
        self.window = component.get("MainWindow")
        # Call the ListView constructor
        listview.ListView.__init__(self, 
                            self.window.main_glade.get_widget("torrent_view"))
        log.debug("TorrentView Init..")

        # Register the columns menu with the listview so it gets updated
        # accordingly.
        self.register_checklist_menu(
                            self.window.main_glade.get_widget("menu_columns"))
        
        # Add the columns to the listview
        self.add_text_column("torrent_id", hidden=True)
        self.add_texticon_column(_("Name"), status_field=["state", "name"], 
                                            function=cell_data_statusicon)
        self.add_func_column(_("Size"), 
                                            listview.cell_data_size, 
                                            [gobject.TYPE_UINT64],
                                            status_field=["total_size"])
        self.add_progress_column(_("Progress"), 
                                    status_field=["progress", "state"],
                                    col_types=[float, int],
                                    function=cell_data_progress)
        self.add_func_column(_("Seeders"),
                                        listview.cell_data_peer,
                                        [int, int],
                                        status_field=["num_seeds", 
                                                        "total_seeds"])
        self.add_func_column(_("Peers"),
                                        listview.cell_data_peer,
                                        [int, int],
                                        status_field=["num_peers", 
                                                        "total_peers"])
        self.add_func_column(_("Down Speed"),
                                        listview.cell_data_speed,
                                        [float],
                                        status_field=["download_payload_rate"])
        self.add_func_column(_("Up Speed"),
                                        listview.cell_data_speed,
                                        [float],
                                        status_field=["upload_payload_rate"])
        self.add_func_column(_("ETA"),
                                            listview.cell_data_time,
                                            [int],
                                            status_field=["eta"])
        self.add_func_column(_("Ratio"),
                                            listview.cell_data_ratio,
                                            [float],
                                            status_field=["ratio"])
        self.add_func_column(_("Avail"),
                                            listview.cell_data_ratio,
                                            [float],
                                            status_field=["distributed_copies"])
                        
        ### Connect Signals ###
        # Connect to the 'button-press-event' to know when to bring up the
        # torrent menu popup.
        self.treeview.connect("button-press-event",
                                    self.on_button_press_event)
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect("changed", 
                                    self.on_selection_changed)
                                    
    def start(self):
        """Start the torrentview"""
        # We need to get the core session state to know which torrents are in
        # the session so we can add them to our list.
        session_state = client.get_session_state()
        for torrent_id in session_state:
            self.add_row(torrent_id)
    
    def stop(self):
        """Stops the torrentview"""
        # We need to clear the liststore
        self.liststore.clear()
            
    def update(self, columns=None):
        """Update the view.  If columns is not None, it will attempt to only
        update those columns selected.
        """
        # Iterates through every row and updates them accordingly
        if self.liststore is not None:
            self.liststore.foreach(self.update_row, columns)
            
    def update_row(self, model=None, path=None, row=None, columns=None):
        """Updates the column values for 'row'.  If columns is None it will
        update all visible columns."""
    
        torrent_id = model.get_value(row, 
                                self.columns["torrent_id"].column_indices[0])
        # Store the 'status_fields' we need to send to core
        status_keys = []
        # Store the actual columns we will be updating
        columns_to_update = []
        
        if columns is None:
            # We need to iterate through all columns
            columns = self.columns.keys()
        
        # Iterate through supplied list of columns to update
        for column in columns:
            # Make sure column is visible and has 'status_field' set.
            # If not, we can ignore it.
            if self.columns[column].column.get_visible() is True \
                and self.columns[column].hidden is False \
                and self.columns[column].status_field is not None:
                for field in self.columns[column].status_field:
                    status_keys.append(field)
                    columns_to_update.append(column)
        
        # Remove duplicate keys
        columns_to_update = list(set(columns_to_update))

        # If there is nothing in status_keys then we must not continue
        if status_keys is []:
            return
            
        # Remove duplicates from status_key list
        status_keys = list(set(status_keys))
        status = client.get_torrent_status(torrent_id,
                status_keys)

        # Set values for each column in the row
        for column in columns_to_update:
            column_index = self.get_column_index(column)
            if type(column_index) is not list:
                # We only have a single list store column we need to update
                try:
                    model.set_value(row,
                            column_index,
                            status[self.columns[column].status_field[0]])
                except TypeError:
                    log.warning("Unable to update column %s with value: %s", 
                        column, status[self.columns[column].status_field[0]])
            else:
                # We have more than 1 liststore column to update
                for index in column_index:
                    # Only update the column if the status field exists
                    try:
                        model.set_value(row,
                            index,
                            status[self.columns[column].status_field[
                                                    column_index.index(index)]])
                    except:
                        pass
                        
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
        self.update_row(model=self.liststore, row=row)
        
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
        try:
            paths = self.treeview.get_selection().get_selected_rows()[1]
        except AttributeError:
            # paths is likely None .. so lets return None
            return None
        try:
            for path in paths:
                torrent_ids.append(
                    self.liststore.get_value(
                        self.liststore.get_iter(path), 0))
            
            if len(torrent_ids) is 0:
                # Only return a list if there is something in it.
                return None
            
            return torrent_ids
        except ValueError:
            return None
                
    ### Callbacks ###                             
    def on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu."""
        log.debug("on_button_press_event")
        # We only care about right-clicks
        if event.button == 3:
            # Show the Torrent menu from the MenuBar
            torrentmenu = component.get("MenuBar").torrentmenu
            torrentmenu.popup(None, None, None, event.button, event.time)
    
    def on_selection_changed(self, treeselection):
        """This callback is know when the selection has changed."""
        log.debug("on_selection_changed")
        component.get("TorrentDetails").update()
        component.get("ToolBar").update_buttons()
        
        
