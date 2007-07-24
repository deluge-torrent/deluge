#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# tab_files.py
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

from itertools import izip

import gobject
import gtk
import gtk.glade

import common
import dgtk
import pref

class FilesBaseManager(object):
    def __init__(self, file_store):
        file_glade = gtk.glade.XML(common.get_glade_file("file_tab_menu.glade"), 
                                   domain='deluge')
        self.file_menu = file_glade.get_widget("file_tab_menu")
        file_glade.signal_autoconnect({
            "select_all": self.file_select_all,
            "unselect_all": self.file_unselect_all,
            "priority_dont_download": self.priority_clicked,
            "priority_normal": self.priority_clicked,
            "priority_high": self.priority_clicked,
            "priority_highest": self.priority_clicked,
        })
        
        self.file_store = file_store
        # We need file_store_sorted so original file_store keeps unchanged
        # when file_view is sorted. And from file_store we have to pass 
        # files priorities to manager.prioritize_files() in the exact same 
        # order as we get files from manager.get_torrent_file_info()
        self.file_store_sorted = gtk.TreeModelSort(self.file_store)

    def build_file_view(self, file_view):
        self.file_view = file_view
        
        def priority(column, cell, model, iter, data):
            priority = common.fpriority(model.get_value(iter, data))
            cell.set_property("text", priority)
            
        filename_column = dgtk.add_text_column(self.file_view, _("Filename"), 
                                               0)
        filename_column.set_expand(True)
        dgtk.add_func_column(self.file_view, _("Size"), dgtk.cell_data_size, 
                             1)
        dgtk.add_func_column(self.file_view, _("Priority"), priority, 2)
        
        self.file_view.set_model(self.file_store_sorted)
        self.file_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        self.file_view.connect("button-press-event", self.mouse_clicked)

    def clear_file_store(self):
        self.file_store.clear()
        self.file_store_dict = {}
        
    def prepare_file_store(self):
        pass
        
    def file_select_all(self, widget):
        self.file_view.get_selection().select_all()
        
    def file_unselect_all(self, widget):
        self.file_view.get_selection().unselect_all()

    def compact_allocation_warning(self):
        msgBox = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_OK, 
            message_format = (_("File priority can only be set when using full allocation.\nPlease change your preference to disable compact allocation, then remove and readd this torrent.")))
        msgBox.run()
        msgBox.destroy()
    
    def priority_clicked(self, widget):
        widget_name = widget.get_name()
        priority = {'priority_dont_download': common.PRIORITY_DONT_DOWNLOAD,
                    'priority_normal': common.PRIORITY_NORMAL,
                    'priority_high': common.PRIORITY_HIGH,
                    'priority_highest': common.PRIORITY_HIGHEST}[widget_name]
                
        selected_paths = self.file_view.get_selection().get_selected_rows()[1]
        for path in selected_paths:
            child_path = self.file_store_sorted.\
                         convert_path_to_child_path(path)
                         
            self.file_store.set_value(self.file_store.get_iter(child_path), 2, 
                                      priority)
        
        self.update_priorities()

    def mouse_clicked(self, widget, event):
        if event.button == 3:
            data = self.file_view.get_path_at_pos(int(event.x), int(event.y))
            if data is None:
                return True
            
            path, col, cellx, celly = data
            is_selected = self.file_view.get_selection().path_is_selected(path)
            if not is_selected:
                self.file_view.grab_focus()
                self.file_view.set_cursor(path, col, 0)
            self.file_menu.popup(None, None, None, event.button, event.time)
            
            return is_selected
        else:
            return False
        
    def update_priorities(self):
        pass

class FilesTabManager(FilesBaseManager):
    def __init__(self, manager):
        file_store = gtk.ListStore(str, gobject.TYPE_UINT64, 
                                   gobject.TYPE_UINT, float)
        
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
    
    def priority_clicked(self, widget):
        state = self.manager.get_torrent_state(self.file_unique_id)
        if state["compact_mode"]:
            self.compact_allocation_warning()
        else:
            super(FilesTabManager, self).priority_clicked(widget)
    
    # From core to UI
    def prepare_file_store(self):
        if not self.file_store_dict:
            all_files = self.manager.get_torrent_file_info(self.file_unique_id)
            file_priorities = self.manager.get_priorities(self.file_unique_id)
            for file, priority in izip(all_files, file_priorities):
                iter = self.file_store.append([file['path'], file['size'],
                           priority, round(file['progress'], 2)])
                self.file_store_dict[file['path']] = iter
    
    # From core to UI
    def update_file_store(self):
        new_file_info = self.manager.get_torrent_file_info(self.file_unique_id)
        for file in new_file_info:
            iter = self.file_store_dict[file['path']]
            dgtk.update_store(self.file_store, iter, (3,), 
                              (round(file['progress'], 2),))

    # From UI to core
    def update_priorities(self):
        file_priorities = [x[2] for x in self.file_store]
        self.manager.prioritize_files(self.file_unique_id, file_priorities)

class FilesDialogManager(FilesBaseManager):
    def __init__(self, dumped_torrent):
        file_store = gtk.ListStore(str, gobject.TYPE_UINT64, 
                                   gobject.TYPE_UINT)
        super(FilesDialogManager, self).__init__(file_store)
        
        self.dumped_torrent = dumped_torrent
        self.config = pref.Preferences()
    
    def prepare_file_store(self):
        for file in self.dumped_torrent:
            self.file_store.append([file['path'], file['size'], 
                                    common.PRIORITY_NORMAL])

    def priority_clicked(self, widget):
        if self.config.get("use_compact_storage"): 
            self.compact_allocation_warning()
        else:
            super(FilesDialogManager, self).priority_clicked(widget)
                
    def get_priorities(self):
        file_priorities = []
        for x in self.file_store:
            file_priorities.append(x[2])
            
        return file_priorities
