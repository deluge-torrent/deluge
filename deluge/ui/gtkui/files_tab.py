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
        # country, filename, size, priority
        self.liststore = gtk.ListStore(str, gobject.TYPE_UINT64, str, int, str)
        
        # Filename column        
        column = gtk.TreeViewColumn(_("Filename"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 0)
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
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 4)
        column.set_sort_column_id(4)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.listview.append_column(column)

        self.listview.set_model(self.liststore)
        
        self.listview.connect("row-activated", self.open_file)

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

    def open_file(self, tree, path, view_column):
        if client.is_localhost:
            client.get_torrent_status(self._on_open_file, self.torrent_id, ["save_path", "files", "num_files"])
            client.force_call(False)

    def _on_open_file(self, status):
        selected = self.listview.get_selection().get_selected()[1]
        file_name = self.liststore.get_value(selected, 0)
        if status["num_files"] > 1:
            file_path = os.path.join(status["save_path"],
                status["files"][0]["path"].split("/", 1)[0], file_name)
        else:
            file_path = os.path.join(status["save_path"], file_name)
        log.debug("Open file '%s'", file_name)
        deluge.common.open_file(file_path)

    def update_files(self):
        # Updates the filename and size columns based on info in self.files_list
        # This assumes the list is currently empty.
        for file in self.files_list[self.torrent_id]:
            row = self.liststore.append()
            # Store the torrent id
            self.liststore.set_value(row, 0, 
                    os.path.split(file["path"])[1])
            self.liststore.set_value(row, 1, file["size"])
        
    def _on_get_torrent_files(self, status):
        self.files_list[self.torrent_id] = status["files"]
        self.update_files()
        self._on_get_torrent_status(status)
        
    def _on_get_torrent_status(self, status):
        for index, row in enumerate(self.liststore):
            row[2] = "%.2f%%" % (status["file_progress"][index] * 100)
            row[3] = status["file_progress"][index] * 100
            row[4] = status["file_priorities"][index]
           
    def clear(self):
        self.liststore.clear()
