#!/usr/bin/env python
#
# files.py
#
# Copyright (C) Zach Tibbitts 2006 <zach@collegegeek.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import gtk
import dgtk
import common
from itertools import izip
import gobject

class FilesBaseManager(object):
    def __init__(self, file_store):
        self.file_glade = gtk.glade.XML(common.get_glade_file("file_tab_menu.glade"), 
                                        domain='deluge')
        self.file_menu = self.file_glade.get_widget("file_tab_menu")
        self.file_glade.signal_autoconnect({
                            "select_all": self.file_select_all,
                            "unselect_all": self.file_unselect_all,
                            "check_selected": self.file_check_selected,
                            "uncheck_selected": self.file_uncheck_selected,
                            })
        
        self.file_store = file_store
        # We need file_store_sorted so original file_store keeps unchanged
        # when file_view is sorted. And from file_store we have to pass 
        # files priorities to manager.prioritize_files() in the exact same 
        # order as we get files from manager.get_torrent_file_info()
        self.file_store_sorted = gtk.TreeModelSort(self.file_store)

    def build_file_view(self, file_view):
        self.file_view = file_view
        self.file_selected = []
        
        dgtk.add_toggle_column(self.file_view, _("Priority"), 0, 
                               toggled_signal=self.file_toggled)
        filename_column = dgtk.add_text_column(self.file_view, _("Filename"), 
                                               1)
        filename_column.set_expand(True)
        dgtk.add_func_column(self.file_view, _("Size"), dgtk.cell_data_size, 
                             2)
        
        self.file_view.set_model(self.file_store_sorted)
        self.file_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.file_view.get_selection().set_select_function(self.file_clicked)
        self.file_view.connect("button-press-event", self.file_view_clicked)

    def clear_file_store(self):
        self.file_store.clear()
        self.file_store_dict = {}
        
    def prepare_file_store(self):
        pass
        
    def file_select_all(self, widget):
        self.file_view.get_selection().select_all()
        
    def file_unselect_all(self, widget):
        self.file_view.get_selection().unselect_all()
    
    def file_check_selected(self, widget):
        self.file_view.get_selection().selected_foreach(self.file_toggle_selected, True)
        self.file_toggled_update_priorities()
    
    def file_uncheck_selected(self, widget):
        self.file_view.get_selection().selected_foreach(self.file_toggle_selected, False)
        self.file_toggled_update_priorities()

    def file_clicked(self, path):
        return not self.file_selected
    
    def file_view_clicked(self, widget, event):
        if event.button == 3:
            self.file_menu.popup(None, None, None, event.button, event.time)
            return True
        else:
            self.file_selected = False
            return False
        
    def file_toggle_selected(self, treemodel, path, selected_iter, value):
        child_iter = self.file_store_sorted.convert_iter_to_child_iter(None,
                         selected_iter)
        if value:
            new_value = 1
        else:
            new_value = 0
        self.file_store_sorted.get_model().set_value(child_iter, 0, new_value)

    def file_toggled(self, renderer, path):
        self.file_selected = True
        
        value = not renderer.get_active()
        if value:
            new_value = 1
        else:
            new_value = 0
            
        file_iter = self.file_store_sorted.get_iter_from_string(path)
        selection = self.file_view.get_selection()
        if selection.iter_is_selected(file_iter):
            selection.selected_foreach(self.file_toggle_selected, value)
        else:
            child_iter = self.file_store_sorted.convert_iter_to_child_iter(
                             None, file_iter)
            self.file_store_sorted.get_model().set_value(child_iter, 0, 
                                                         new_value)
        self.file_toggled_update_priorities()

    def file_toggled_update_priorities(self):
        pass

class FilesTabManager(FilesBaseManager):
    def __init__(self, manager):
        file_store = gtk.ListStore(int, str, gobject.TYPE_UINT64, float)
        
        super(FilesTabManager, self).__init__(file_store)

        self.manager = manager
        self.file_unique_id = None
        
        # Stores file path -> gtk.TreeIter's iter mapping for quick look up 
        # in self.update_file_store()
        self.file_store_dict = {}
        
    def build_file_view(self, file_view):
        super(FilesTabManager, self).build_file_view(file_view)
        
        def percent(column, cell, model, iter, data):
            percent = float(model.get_value(iter, data))
            percent_str = "%.2f%%"%percent
            cell.set_property("text", percent_str)
        dgtk.add_func_column(file_view, _("Progress"), percent, 3)
    
    def set_unique_id(self, unique_id):
        self.file_unique_id = unique_id
    
    def prepare_file_store(self):
        if not self.file_store_dict:
            all_files = self.manager.get_torrent_file_info(self.file_unique_id)
            file_priorities = self.manager.get_priorities(self.file_unique_id)
            for file, priority in izip(all_files, file_priorities):
                iter = self.file_store.append([priority, file['path'],
                           file['size'],
                           round(file['progress'], 2)])
                self.file_store_dict[file['path']] = iter
    
    def update_file_store(self):
        new_file_info = self.manager.get_torrent_file_info(self.file_unique_id)
        for file in new_file_info:
            iter = self.file_store_dict[file['path']]
            if self.file_store.get_value(iter, 3) != round(file['progress'], 2):
                self.file_store.set(iter, 3, file['progress'])
        
    def file_toggled_update_priorities(self):
        file_priorities = []
        for x in self.file_store:
            file_priorities.append(x[0])
        self.manager.prioritize_files(self.file_unique_id, file_priorities)

class FilesDialogManager(FilesBaseManager):
    def __init__(self, dumped_torrent):
        file_store = gtk.ListStore(int, str, gobject.TYPE_UINT64)
        super(FilesDialogManager, self).__init__(file_store)
        
        self.dumped_torrent = dumped_torrent
    
    def prepare_file_store(self):
        for file in self.dumped_torrent:
            self.file_store.append([1, file['path'], file['size']])
                
    def get_priorities(self):
        file_priorities = []
        for x in self.file_store:
            file_priorities.append(x[0])
            
        return file_priorities
