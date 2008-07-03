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

from deluge.ui.gtkui.torrentdetails import Tab
from deluge.ui.client import aclient as client
from deluge.configmanager import ConfigManager
import deluge.component as component
import deluge.common

from deluge.log import LOG as log

def cell_priority(column, cell, model, row, data):
    if model.get_value(row, 5) == -1:
        # This is a folder, so lets just set it blank for now
        cell.set_property("text", "")
        return
    priority = model.get_value(row, data)
    cell.set_property("text", deluge.common.FILE_PRIORITY[priority])

def cell_priority_icon(column, cell, model, row, data):
    if model.get_value(row, 5) == -1:
        # This is a folder, so lets just set it blank for now
        cell.set_property("stock-id", None)
        return
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

def cell_progress(column, cell, model, row, data):
    if model.get_value(row, 5) == -1:
    # This is a folder, so lets just set it blank for now
        cell.set_property("visible", False)
        return
    text = model.get_value(row, data[0])
    value = model.get_value(row, data[1])
    cell.set_property("visible", True)
    cell.set_property("text", text)
    cell.set_property("value", value)

class ColumnState:
    def __init__(self, name, position, width, sort, sort_order):
        self.name = name
        self.position = position
        self.width = width
        self.sort = sort
        self.sort_order = sort_order

class FilesTab(Tab):
    def __init__(self):
        glade = component.get("MainWindow").get_glade()

        self._name = "Files"
        self._child_widget = glade.get_widget("files_tab")
        self._tab_label = glade.get_widget("files_tab_label")

        self.listview = glade.get_widget("files_listview")
        # filename, size, progress string, progress value, priority, file index, icon id
        self.treestore = gtk.TreeStore(str, gobject.TYPE_UINT64, str, int, int, int, str)
        
        # Filename column        
        column = gtk.TreeViewColumn(_("Filename"))
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, False)
        column.add_attribute(render, "stock-id", 6)
        render = gtk.CellRendererText()
        column.pack_start(render, True)
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
        column.set_cell_data_func(render, cell_progress, (2, 3))
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

        self.listview.set_model(self.treestore)
        
        self.listview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        self.file_menu = glade.get_widget("menu_file_tab")
        self.listview.connect("row-activated", self._on_row_activated)
        self.listview.connect("button-press-event", self._on_button_press_event)

        glade.signal_autoconnect({
            "on_menuitem_open_file_activate": self._on_menuitem_open_file_activate,
            "on_menuitem_donotdownload_activate": self._on_menuitem_donotdownload_activate,
            "on_menuitem_normal_activate": self._on_menuitem_normal_activate,
            "on_menuitem_high_activate": self._on_menuitem_high_activate,
            "on_menuitem_highest_activate": self._on_menuitem_highest_activate,
            "on_menuitem_expand_all_activate": self._on_menuitem_expand_all_activate
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
        except (EOFError, IOError), e:
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
            self.treestore.clear()
            return
        
        if torrent_id != self.torrent_id:
            # We only want to do this if the torrent_id has changed
            self.treestore.clear()
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
        self.treestore.clear()

    def _on_row_activated(self, tree, path, view_column):
        if client.is_localhost:
            client.get_torrent_status(self._on_open_file, self.torrent_id, ["save_path", "files"])
            client.force_call(False)

    def get_file_path(self, row, path=""):
        if not row:
            return path
        
        path = self.treestore.get_value(row, 0) + path
        return self.get_file_path(self.treestore.iter_parent(row), path)
        
    def _on_open_file(self, status):
        paths = self.listview.get_selection().get_selected_rows()[1]
        selected = []
        for path in paths:
            selected.append(self.treestore.get_iter(path))
        
        for select in selected:
            path = self.get_file_path(select).split("/")
            filepath = os.path.join(status["save_path"], *path)
            log.debug("Open file '%s'", filepath)
            deluge.common.open_file(filepath)

    ## The following 3 methods create the folder/file view in the treeview        
    def prepare_file_store(self, files):
        split_files = { }
        i = 0
        for file in files:
            self.prepare_file(file, file["path"], i, split_files)
            i += 1
        self.add_files(None, split_files)

    def prepare_file(self, file, file_name, file_num, files_storage):
        first_slash_index = file_name.find("/")
        if first_slash_index == -1:
            files_storage[file_name] = (file_num, file)
        else:
            file_name_chunk = file_name[:first_slash_index+1]
            if file_name_chunk not in files_storage:
                files_storage[file_name_chunk] = { }
            self.prepare_file(file, file_name[first_slash_index+1:],
                              file_num, files_storage[file_name_chunk])
                              
    def add_files(self, parent_iter, split_files):
        ret = 0
        for key,value in split_files.iteritems():
            if key.endswith("/"):
                chunk_iter = self.treestore.append(parent_iter,
                                [key, 0, "", 0, 0, -1, gtk.STOCK_DIRECTORY])
                chunk_size = self.add_files(chunk_iter, value)
                self.treestore.set(chunk_iter, 1, chunk_size)
                ret += chunk_size
            else:
                self.treestore.append(parent_iter, [key,
                                        value[1]["size"], "", 0, 0, value[0], gtk.STOCK_FILE])
                ret += value[1]["size"]
        return ret
    ###        

    def update_files(self):
        self.prepare_file_store(self.files_list[self.torrent_id])
    
    def get_selected_files(self):
        """Returns a list of file indexes that are selected"""
        selected = []
        paths = self.listview.get_selection().get_selected_rows()[1]
        for path in paths:
            selected.append(self.treestore.get_value(self.treestore.get_iter(path), 5))

        return selected
            
    def _on_get_torrent_files(self, status):
        self.files_list[self.torrent_id] = status["files"]
        self.update_files()
        self._on_get_torrent_status(status)
    
    def get_files_from_tree(self, rows, files_list, indent):
        if not rows:
            return None
        
        for row in rows:
            if row[5] > -1:
                files_list.append((row[5], row))
            self.get_files_from_tree(row.iterchildren(), files_list, indent+1)
        return None
        
    def _on_get_torrent_status(self, status):
        # (index, iter)
        files_list = []
        self.get_files_from_tree(self.treestore, files_list, 0)
        files_list.sort()
        for index, row in files_list:
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
        def set_file_priority(model, path, iter, data):
            index = model.get_value(iter, 5)
            if index in selected:
                file_priorities.append((index, priority))
            elif index != -1:
                file_priorities.append((index, model.get_value(iter, 4)))

        self.treestore.foreach(set_file_priority, None)
        file_priorities.sort()
        priorities = [p[1] for p in file_priorities]
        log.debug("priorities: %s", priorities)
                        
        client.set_torrent_file_priorities(self.torrent_id, priorities)
        
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

    def _on_menuitem_expand_all_activate(self, menuitem):
        self.listview.expand_all()
