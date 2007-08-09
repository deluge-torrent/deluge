from itertools import izip

import gobject
import gtk

from deluge.files import FilesBaseManager
from deluge import dgtk

class FilesTabManager(FilesBaseManager):
    def __init__(self, file_view, manager):
        file_store = gtk.ListStore(str, gobject.TYPE_UINT64, 
                                   gobject.TYPE_UINT, float)
        
        super(FilesTabManager, self).__init__(file_view, file_store)

        self.manager = manager
        self.file_unique_id = None
        
        # Stores file path -> gtk.TreeIter's iter mapping for quick look up 
        # in self.update_file_store()
        self.file_store_dict = {}
        
        self.file_viewer = None
        
    def build_file_view(self):
        super(FilesTabManager, self).build_file_view()
        
        def percent(column, cell, model, iter, data):
            percent = float(model.get_value(iter, data))
            percent_str = "%.2f%%"%percent
            cell.set_property("text", percent_str)
        dgtk.add_func_column(self.file_view, _("Progress"), percent, 3)
    
    def set_unique_id(self, unique_id):
        self.file_unique_id = unique_id
    
    def priority_clicked(self, widget):
        state = self.manager.get_torrent_state(self.file_unique_id)
        if state["compact_mode"]:
            self.compact_allocation_warning()
        else:
            super(FilesTabManager, self).priority_clicked(widget)

    def set_file_viewer(self, file_viewer):
        self.file_viewer = file_viewer

    def open_file(self, widget):
        import os
        
        save_dir = self.manager.unique_IDs[self.file_unique_id].save_dir
        selected_paths = self.file_view.get_selection().get_selected_rows()[1]
        try:
            for path in selected_paths:
                child_path = self.file_store_sorted.\
                                 convert_path_to_child_path(path)
                file_name = self.file_store.get_value(
                                self.file_store.get_iter(child_path), 0)
                os.popen2('%s "%s"' % (self.file_viewer, 
                                       os.path.join(save_dir, file_name)))
        except KeyError:
            pass

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
