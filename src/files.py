# -*- coding: utf-8 -*-
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

from itertools import izip

import gobject
import gtk

import common
import core
import dgtk
import pref

class FilesBaseManager(object):
    def __init__(self, file_view, file_store):
        self.config = pref.Preferences()

        self.file_view = file_view
        
        self.glade = gtk.glade.XML(common.get_glade_file("file_tab_menu.glade"), 
                                   domain='deluge')
        self.file_menu = self.glade.get_widget("file_tab_menu")
        self.glade.signal_autoconnect({
            "open_file" : self.open_file,
            "rename_file" : self.rename_file,
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

    def open_file(self):
        pass

    def rename_file(self):
        pass

    def build_file_view(self):
        def priority(column, cell, model, iter, data):
            priority = common.fpriority(model.get_value(iter, data))
            cell.set_property("text", priority)
            
        filename_column = dgtk.add_text_column(self.file_view, _("Filename"), \
                                 0, width=self.config.get("filename_f_width"))
        filename_column.set_expand(True)
        size_column = dgtk.add_func_column(self.file_view, _("Size"), dgtk.cell_data_size, 
                             1, width=self.config.get("size_f_width"))
        priority_column = dgtk.add_func_column(self.file_view, _("Priority"), \
                priority, 2, width=self.config.get("priority_f_width"))
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
            message_format = (_("File priority can only be set when using full allocation.\nPlease change your preference to disable compact allocation, then remove and re-add this torrent.")))
        msgBox.run()
        msgBox.destroy()
    
    def priority_clicked(self, widget):
        widget_name = widget.get_name()
        priority = {'priority_dont_download': core.PRIORITY_DONT_DOWNLOAD,
                    'priority_normal': core.PRIORITY_NORMAL,
                    'priority_high': core.PRIORITY_HIGH,
                    'priority_highest': core.PRIORITY_HIGHEST}[widget_name]
                
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
            
            path = data[0]
            is_selected = self.file_view.get_selection().path_is_selected(path)
            if not is_selected:
                self.file_view.grab_focus()
                self.file_view.set_cursor(path)
            self.file_menu.popup(None, None, None, event.button, event.time)
            
            return is_selected
        else:
            return False
        
    def update_priorities(self):
        pass

class FilesDialogManager(FilesBaseManager):
    def __init__(self, file_view, dumped_torrent):
        file_store = gtk.ListStore(str, gobject.TYPE_UINT64, 
                                   gobject.TYPE_UINT)
        super(FilesDialogManager, self).__init__(file_view, file_store)
        
        self.dumped_torrent = dumped_torrent
        self.config = pref.Preferences()
        
        # Hide Open File menu item as it's not applicable when torrent is
        # not added yet
        self.glade.get_widget("open_file").hide()
        self.glade.get_widget("open_file_separator").hide()
        self.glade.get_widget("rename_file").hide()
        self.glade.get_widget("rename_file_separator").hide()
    
    def prepare_file_store(self):
        for file in self.dumped_torrent:
            self.file_store.append([file['path'], file['size'], 
                                    core.PRIORITY_NORMAL])

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
