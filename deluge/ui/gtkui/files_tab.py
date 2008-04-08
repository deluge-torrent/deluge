#
# files_tab.py
#
# Copyright (C) 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import gtk, gtk.glade
import gobject
import gettext
import os.path
import cPickle

from deluge.ui.client import aclient as client
from deluge.configmanager import ConfigManager
import deluge.component as component
import deluge.common

from deluge.log import LOG as log

def cell_priority(column, cell, model, row, data):
    priority = model.get_value(row, data)
    cell.set_property("text", deluge.common.FILE_PRIORITY[priority])

def cell_priority_icon(column, cell, model, row, data):
    priority = model.get_value(row, data)
    if deluge.common.FILE_PRIORITY[priority] == "Do Not Download":
        cell.set_property("stock-id", gtk.STOCK_STOP)
    elif deluge.common.FILE_PRIORITY[priority] == "Normal Priority":
        cell.set_property("stock-id", gtk.STOCK_YES)
    elif deluge.common.FILE_PRIORITY[priority] == "High Priority":
        cell.set_property("stock-id", gtk.STOCK_GO_UP)
    elif deluge.common.FILE_PRIORITY[priority] == "Highest Priority":
        cell.set_property("stock-id", gtk.STOCK_GOTO_TOP)

def cell_filename(column, cell, model, row, data):
    """Only show the tail portion of the file path"""
    filepath = model.get_value(row, data)
    cell.set_property("text", os.path.split(filepath)[1])
        
class ColumnState:
    def __init__(self, name, position, width, sort, sort_order):
        self.name = name
        self.position = position
        self.width = width
        self.sort = sort
        self.sort_order = sort_order

class FilesTab:
    def __init__(self):
        glade = component.get("MainWindow").get_glade()
        self.listview = glade.get_widget("files_listview")
        # filename, size, progress string, progress value, priority, file index
        self.liststore = gtk.ListStore(str, gobject.TYPE_UINT64, str, int, int, int)
        
        # Filename column        
        column = gtk.TreeViewColumn(_("Filename"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, cell_filename, 0)
        column.set_sort_column_id(0)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)

        # Size column        
        column = gtk.TreeViewColumn(_("Size"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, deluge.ui.gtkui.listview.cell_data_size, 1)
        column.set_sort_column_id(1)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)

        # Progress column        
        column = gtk.TreeViewColumn(_("Progress"))
        render = gtk.CellRendererProgress()
        column.pack_start(render)
        column.add_attribute(render, "text", 2)
        column.add_attribute(render, "value", 3)
        column.set_sort_column_id(3)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)
        
        # Priority column        
        column = gtk.TreeViewColumn(_("Priority"))
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, False)
        column.set_cell_data_func(render, cell_priority_icon, 4)
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, cell_priority, 4)
        column.set_sort_column_id(4)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)

        self.listview.set_model(self.liststore)
        
        self.listview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        self.file_menu = glade.get_widget("menu_file_tab")
        self.listview.connect("row-activated", self._on_row_activated)
        self.listview.connect("button-press-event", self._on_button_press_event)

        glade.signal_autoconnect({
            "on_menuitem_open_file_activate": self._on_menuitem_open_file_activate,
            "on_menuitem_donotdownload_activate": self._on_menuitem_donotdownload_activate,
            "on_menuitem_normal_activate": self._on_menuitem_normal_activate,
            "on_menuitem_high_activate": self._on_menuitem_high_activate,
            "on_menuitem_highest_activate": self._on_menuitem_highest_activate
        })
        
        # Attempt to load state
        self.load_state()
        
        # torrent_id: (filepath, size)
        self.files_list = {}
        
        self.torrent_id = None
    
    def save_state(self):
        filename = "files_tab.state"
        state = []
        for index, column in enumerate(self.listview.get_columns()):
            state.append(ColumnState(column.get_title(), index, column.get_width(), 
                column.get_sort_indicator(), int(column.get_sort_order())))
        
        # Get the config location for saving the state file
        config_location = ConfigManager("gtkui.conf")["config_location"]

        try:
            log.debug("Saving FilesTab state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "wb")
            cPickle.dump(state, state_file)
            state_file.close()
        except IOError, e:
            log.warning("Unable to save state file: %s", e)
    
    def load_state(self):
        filename = "files_tab.state"
        # Get the config location for loading the state file
        config_location = ConfigManager("gtkui.conf")["config_location"]
        state = None
        
        try:
            log.debug("Loading FilesTab state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "rb")
            state = cPickle.load(state_file)
            state_file.close()
        except IOError, e:
            log.warning("Unable to load state file: %s", e)
        
        if state == None:
            return
            
        for column_state in state:
            # Find matching columns in the listview
            for (index, column) in enumerate(self.listview.get_columns()):
                if column_state.name == column.get_title():
                    # We have a match, so set options that were saved in state
                    if column_state.width > 0:
                        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                        column.set_fixed_width(column_state.width)
                        column.set_sort_indicator(column_state.sort)
                        column.set_sort_order(column_state.sort_order)
                    if column_state.position != index:
                        # Column is in wrong position
                        if column_state.position == 0:
                            self.listview.move_column_after(column, None)
                        else:
                            self.listview.move_column_after(column, self.listview.get_columns()[column_state.position - 1])
                    
    def update(self):
        # Get the first selected torrent
        torrent_id = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(torrent_id) != 0:
            torrent_id = torrent_id[0]
        else:
            # No torrent is selected in the torrentview
            self.liststore.clear()
            return
        
        if torrent_id != self.torrent_id:
            # We only want to do this if the torrent_id has changed
            self.liststore.clear()
            self.torrent_id = torrent_id
            
            if self.torrent_id not in self.files_list.keys():
                # We need to get the files list
                log.debug("Getting file list from core..")
                client.get_torrent_status(
                    self._on_get_torrent_files, 
                    self.torrent_id, 
                    ["files", "file_progress", "file_priorities"])
                client.force_call(block=True)
            else:
                self.update_files()
                client.get_torrent_status(self._on_get_torrent_status, self.torrent_id, ["file_progress", "file_priorities"])
                client.force_call(True)
        else:
            client.get_torrent_status(self._on_get_torrent_status, self.torrent_id, ["file_progress", "file_priorities"])
            client.force_call(True)

    def clear(self):
        self.liststore.clear()

    def _on_row_activated(self, tree, path, view_column):
        if client.is_localhost:
            client.get_torrent_status(self._on_open_file, self.torrent_id, ["save_path", "files"])
            client.force_call(False)

    def _on_open_file(self, status):
        paths = self.listview.get_selection().get_selected_rows()[1]
        selected = []
        for path in paths:
            selected.append(self.liststore.get_iter(path))
        
        for select in selected:
            filepath = os.path.join(status["save_path"], self.liststore.get_value(select, 0))
            log.debug("Open file '%s'", filepath)
            deluge.common.open_file(filepath)

    def update_files(self):
        # Updates the filename and size columns based on info in self.files_list
        # This assumes the list is currently empty.
        for file in self.files_list[self.torrent_id]:
            row = self.liststore.append()
            # Store the torrent id
            self.liststore.set_value(row, 0, file["path"])
            self.liststore.set_value(row, 1, file["size"])
            self.liststore.set_value(row, 5, file["index"])
    
    def get_selected_files(self):
        """Returns a list of file indexes that are selected"""
        selected = []
        paths = self.listview.get_selection().get_selected_rows()[1]
        for path in paths:
            selected.append(self.liststore.get_value(self.liststore.get_iter(path), 5))

        return selected
        
    def _on_get_torrent_files(self, status):
        self.files_list[self.torrent_id] = status["files"]
        self.update_files()
        self._on_get_torrent_status(status)
        
    def _on_get_torrent_status(self, status):
        for index, row in enumerate(self.liststore):
            row[2] = "%.2f%%" % (status["file_progress"][index] * 100)
            row[3] = status["file_progress"][index] * 100
            row[4] = status["file_priorities"][index]
           
    def _on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu."""
        log.debug("on_button_press_event")
        # We only care about right-clicks
        if self.get_selected_files() and event.button == 3:
            self.file_menu.popup(None, None, None, event.button, event.time)
            return True
            
    def _on_menuitem_open_file_activate(self, menuitem):
        self._on_row_activated(None, None, None)

    def _set_file_priorities_on_user_change(self, selected, priority):
        """Sets the file priorities in the core.  It will change the selected
            with the 'priority'"""
        file_priorities = []
        for row in self.liststore:
            if row[5] in selected:
                # This is a row we're modifying
                file_priorities.append(priority)
            else:
                file_priorities.append(row[4])
                
        client.set_torrent_file_priorities(self.torrent_id, file_priorities)
        
    def _on_menuitem_donotdownload_activate(self, menuitem):
        self._set_file_priorities_on_user_change(
            self.get_selected_files(), 
            deluge.common.FILE_PRIORITY["Do Not Download"])
            
    def _on_menuitem_normal_activate(self, menuitem):
        self._set_file_priorities_on_user_change(
            self.get_selected_files(), 
            deluge.common.FILE_PRIORITY["Normal Priority"])

    def _on_menuitem_high_activate(self, menuitem):
        self._set_file_priorities_on_user_change(
            self.get_selected_files(), 
            deluge.common.FILE_PRIORITY["High Priority"])

    def _on_menuitem_highest_activate(self, menuitem):
        self._set_file_priorities_on_user_change(
            self.get_selected_files(), 
            deluge.common.FILE_PRIORITY["Highest Priority"])

