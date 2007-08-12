#
# listview.py
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
import gtk
import gettext

# Get the logger
log = logging.getLogger("deluge")

# Cell data functions to pass to add_func_column()

def cell_data_speed(column, cell, model, iter, data):
    speed = int(model.get_value(iter, data))
    speed_str = deluge.common.fspeed(speed)
    cell.set_property('text', speed_str)

def cell_data_size(column, cell, model, iter, data):
	size = long(model.get_value(iter, data))
	size_str = deluge.common.fsize(size)
	cell.set_property('text', size_str)

def cell_data_peer(column, cell, model, iter, data):
    c1, c2 = data
    a = int(model.get_value(iter, c1))
    b = int(model.get_value(iter, c2))
    cell.set_property('text', '%d (%d)'%(a, b))
        
def cell_data_time(column, cell, model, iter, data):
    time = int(model.get_value(iter, data))
    if time < 0 or time == 0:
        time_str = _("Infinity")
    else:
        time_str = deluge.common.ftime(time)
    cell.set_property('text', time_str)
            
def cell_data_ratio(column, cell, model, iter, data):
    ratio = float(model.get_value(iter, data))
    if ratio == -1:
        ratio_str = _("Unknown")
    else:
        ratio_str = "%.3f"%ratio
        cell.set_property('text', ratio_str)

class ListView:
    class ListViewColumn:
        def __init__(self, name, column_indices):
            self.name = name
            # self.column_types = column_types
            self.column_indices = column_indices
    
    def __init__(self, treeview_widget=None):
        log.debug("ListView initialized..")
        
        if treeview_widget is not None:
            # User supplied a treeview widget
            self.treeview = treeview_widget
        else:
            self.treeview = gtk.TreeView()
            
        self.liststore = None
        
        self.treeview.set_model(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_reorderable(True)
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        self.columns = {}
        self.liststore_columns = []
    
    def create_new_liststore(self):
        # Create a new liststore with added column and move the data from the 
        # old one to the new one.
        new_list = gtk.ListStore(*tuple(self.liststore_columns))

        # This function is used in the liststore.foreach method with user_data
        # being the new liststore and the columns list
        def copy_row(model, path, row, user_data):
            new_list, columns = user_data
            # Iterate over the columns except the last one.  This one would have
            # been just added and no need to copy it from the old list.
            for column in range(model.get_n_columns()):
                # Get the current value of the column for this row
                value = model.get_value(row, column)
                # Set the value of this row and column in the new liststore
                new_list.set_value(row, column, value)
        
        # Do the actual row copy
        if self.liststore is not None:
            self.liststore.foreach(copy_row, (new_list, self.columns))
        
        self.liststore = new_list
        self.treeview.set_model(self.liststore)
        
        return
    
    def add_text_column(self, header, visible=True):
        # Create a new column object and add it to the list
        self.liststore_columns.append(str)
        self.columns[header] = self.ListViewColumn(header, 
                                            [len(self.liststore_columns) - 1])
      
        # Create a new list with the added column
        self.create_new_liststore()
        
        # Now add the column to the treeview so the user can see it
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(header, render, 
                                    text=self.columns[header].column_indices[0])
        column.set_clickable(True)
        column.set_sort_column_id(self.columns[header].column_indices[0])
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        column.set_visible(visible)
        self.treeview.append_column(column)

        return True
        
    def add_func_column(self, header, function, column_types, sortid=0):
        # Add the new column types to the list and keep track of the liststore
        # columns that this column object uses.
        # Set sortid to the column index relative the to column_types used.
        # Default is 0.
        
        column_indices = []
        for column_type in column_types:
            self.liststore_columns.append(column_type)
            column_indices.append(len(self.liststore_columns) - 1)

        # Create a new column object and add it to the list    
        self.columns[header] = self.ListViewColumn(header, column_indices)
        
        # Create new list with the added columns
        self.create_new_liststore()
        
        column = gtk.TreeViewColumn(header)
        render = gtk.CellRendererText()
        column.pack_start(render, True)
        column.set_cell_data_func(render, function, 
                                    tuple(self.columns[header].column_indices))
        column.set_clickable(True)
        column.set_sort_column_id(column_indices[sortid])
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.treeview.append_column(column)
        
        return True

    def add_progress_column(self, header):
        # For the progress value
        self.liststore_columns.append(float)
        # For the text
        self.liststore_columns.append(str)
        column_indices = [len(self.liststore_columns) - 2, 
                                            len(self.liststore_columns) - 1]
        # Create a new column object and add it to the list
        self.columns[header] = self.ListViewColumn(header, column_indices)
        
        # Create new list with the added columns
        self.create_new_liststore()
        
        render = gtk.CellRendererProgress()
        column = gtk.TreeViewColumn(header, render, 
                            value=self.columns[header].column_indices[0], 
                            text=self.columns[header].column_indices[1])
        column.set_clickable(True)
        column.set_sort_column_id(self.columns[header].column_indices[0])
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        self.treeview.append_column(column)
        
        return True
        
    def add_texticon_column(self, header):
        # For icon
        self.liststore_columns.append(gtk.gdk.Pixbuf)
        # For text
        self.liststore_columns.append(str)
        column_indices = [len(self.liststore_columns) - 2, 
                                            len(self.liststore_columns) - 1]
        self.columns[header] = self.ListViewColumn(header, column_indices)

        # Create new list with the added columns
        self.create_new_liststore()
        
        column = gtk.TreeViewColumn(header)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, expand=False)
        column.add_attribute(render, 'pixbuf', 
                                        self.columns[header].column_indices[0])
        render = gtk.CellRendererText()
        column.pack_start(render, expand=True)
        column.add_attribute(render, 'text', 
                                        self.columns[header].column_indices[1])
        self.treeview.append_column(column)
        
        return True
