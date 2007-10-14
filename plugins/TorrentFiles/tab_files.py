# -*- coding: utf-8 -*-
#
# tab_files.py
#
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
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

from deluge.files import FilesBaseManager
from deluge import dgtk, dialogs

class FilesTabManager(FilesBaseManager):
    def __init__(self, file_view, manager):
        file_store = gtk.ListStore(str, gobject.TYPE_UINT64, 
                                   gobject.TYPE_UINT, float, str)
        
        super(FilesTabManager, self).__init__(file_view, file_store)
        self.manager = manager
        self.file_unique_id = None
        
        # Stores file path -> gtk.TreeIter's iter mapping for quick look up 
        # in self.update_file_store()
        self.file_store_dict = {}
        
        self.file_viewer = None
        
    def build_file_view(self):
        super(FilesTabManager, self).build_file_view()
        
        percent_col = dgtk.add_progress_column(self.file_view, _("Progress"),\
                 3, 4, width=150)
        expander_col = gtk.TreeViewColumn()
        expander_col.set_expand(True)
        self.file_view.append_column(expander_col)
        self.file_view.connect("row-activated", self.double_click_file)
    
    def set_unique_id(self, unique_id):
        self.file_unique_id = unique_id
    
    def priority_clicked(self, widget):
        if self.manager.get_pref("use_compact_storage"):
            self.compact_allocation_warning()
        else:
            super(FilesTabManager, self).priority_clicked(widget)

    def set_file_viewer(self, file_viewer):
        self.file_viewer = file_viewer

    def double_click_file(self, tree, path, view_column):
        self.open_file()

    def open_file(self, widget=None):
        import os
        
        from deluge.common import exec_command, windows_check
        
        save_dir = self.manager.unique_IDs[self.file_unique_id].save_dir
        selected_paths = self.file_view.get_selection().get_selected_rows()[1]
        try:
            for path in selected_paths:
                child_path = self.file_store_sorted.\
                                 convert_path_to_child_path(path)
                file_name = self.file_store.get_value(
                                self.file_store.get_iter(child_path), 0)
                if windows_check(): 
                    try:
                        os.startfile(os.path.join(save_dir, file_name))
                    except WindowsError:
                        import gtk
                        gtk.gdk.threads_enter()
                        result = dialogs.show_popup_warning(None, _("There was \
an error trying to launch the file."))
                        gtk.gdk.threads_leave()
                else:    
                    exec_command(self.file_viewer, 
                             os.path.join(save_dir, file_name))
        except KeyError:
            pass

    # From core to UI
    def prepare_file_store(self):
        if not self.file_store_dict:
            all_files = self.manager.get_torrent_file_info(self.file_unique_id)
            file_priorities = self.manager.get_priorities(self.file_unique_id)
            for file, priority in izip(all_files, file_priorities):
                iter = self.file_store.append([file['path'], file['size'],
                            priority, file['progress'],
                            "%.3g%%"%float(file['progress'])])
                self.file_store_dict[file['path']] = iter
    
    # From core to UI
    def update_file_store(self):
        new_file_info = self.manager.get_torrent_file_info(self.file_unique_id)
        for file in new_file_info:
            iter = self.file_store_dict[file['path']]
            dgtk.update_store(self.file_store, iter, (3,4), 
                              (file['progress'],
                               "%.3g%%"%float(file['progress'])))

    # From UI to core
    def update_priorities(self):
        prev_file_priorities = self.manager.get_priorities(self.file_unique_id)
        file_priorities = []
        update = False
        for x, priority in izip(self.file_store, prev_file_priorities):
            file_priorities.append(x[2])
            if x[2] > 0 and priority == 0:
                update = True
            if x[2] == 0:
                update = True
        self.manager.prioritize_files(self.file_unique_id, file_priorities, update_files_removed=update)
