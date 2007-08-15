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

import deluge.common

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
            # Name is how a column is identified and is also the header
            self.name = name
            # Column_indices holds the indexes to the liststore_columns that 
            # this column utilizes. It is stored as a list.      
            self.column_indices = column_indices
            # Column is a reference to the GtkTreeViewColumn object
            self.column = None
            # If column is 'hidden' then it will not be visible and will not
            # show up in any menu listing;  it cannot be shown ever.
            self.hidden = False
            
    
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

        # Dictionary of 'header' or 'name' to ListViewColumn object
        self.columns = {}
        # Column_index will keep track of the order that the visible columns
        # are in.
        self.column_index = []
        # The column types for the list store.. this may have more entries than
        # visible columns due to some columns utilizing more than 1 liststore
        # column and some columns being hidden.
        self.liststore_columns = []
        # The GtkMenu that is created after every addition, removal or reorder
        self.menu = None
    
    def set_treeview(self, treeview_widget):
        self.treeview = treeview_widget
        return
        
    def get_column_index(self, name):
        # Only return as list if needed
        if len(self.columns[name].column_indices) > 1:
            return self.columns[name].column_indices
        else:
            return self.columns[name].column_indices[0]
    
    def create_checklist_menu(self):
        self.menu = gtk.Menu()
        # Iterate through the column_index list to preserve order
        for name in self.column_index:
            column = self.columns[name]
            # If the column is hidden, then we do not want to show it in the
            # menu.
            if column.hidden is True:
                continue
            menuitem = gtk.CheckMenuItem(column.name)
            # If the column is currently visible, make sure it's set active
            # (or checked) in the menu.
            if column.column.get_visible() is True:
                menuitem.set_active(True)
            # Add the new checkmenuitem to the menu
            self.menu.append(menuitem)
        return self.menu
    
    def create_new_liststore(self):
        # Create a new liststore with added column and move the data from the 
        # old one to the new one.
        new_list = gtk.ListStore(*tuple(self.liststore_columns))

        # This function is used in the liststore.foreach method with user_data
        # being the new liststore and the columns list
        def copy_row(model, path, row, user_data):
            new_list, columns = user_data
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
    
    def add_text_column(self, header, hidden=False):
        # Create a new column object and add it to the list
        self.liststore_columns.append(str)
        # Add to the index list so we know the order of the visible columns.
        self.column_index.append(header)
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
        column.set_visible(not hidden)
        self.treeview.append_column(column)
        # Set hidden in the column
        self.columns[header].hidden = hidden
        self.columns[header].column = column
        # Re-create the menu item because of the new column
        self.create_checklist_menu()
        
        return True
        
    def add_func_column(self, header, function, column_types, sortid=0, 
                                                            hidden=False):
        # Add the new column types to the list and keep track of the liststore
        # columns that this column object uses.
        # Set sortid to the column index relative the to column_types used.
        # Default is 0.
        
        column_indices = []
        for column_type in column_types:
            self.liststore_columns.append(column_type)
            column_indices.append(len(self.liststore_columns) - 1)
        
        # Add to the index list so we know the order of the visible columns.
        self.column_index.append(header)
        # Create a new column object and add it to the list    
        self.columns[header] = self.ListViewColumn(header, column_indices)
        
        # Create new list with the added columns
        self.create_new_liststore()
        
        column = gtk.TreeViewColumn(header)
        render = gtk.CellRendererText()
        column.pack_start(render, True)
        if len(self.columns[header].column_indices) > 1:
            column.set_cell_data_func(render, function, 
                                    tuple(self.columns[header].column_indices))
        else:
            column.set_cell_data_func(render, function,
                                    self.columns[header].column_indices[0])
        column.set_clickable(True)
        column.set_sort_column_id(column_indices[sortid])
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        column.set_visible(not hidden)
        self.treeview.append_column(column)
        # Set hidden in the column
        self.columns[header].hidden = hidden
        self.columns[header].column = column
        # Re-create the menu item because of the new column
        self.create_checklist_menu()
                
        return True

    def add_progress_column(self, header, hidden=False):
        # For the progress value
        self.liststore_columns.append(float)
        # For the text
        self.liststore_columns.append(str)
        column_indices = [len(self.liststore_columns) - 2, 
                                            len(self.liststore_columns) - 1]
        # Add to the index list so we know the order of the visible columns.
        self.column_index.append(header)
        
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
        column.set_visible(not hidden)
        self.treeview.append_column(column)
        # Set hidden in the column
        self.columns[header].hidden = hidden
        self.columns[header].column = column
        # Re-create the menu item because of the new column
        self.create_checklist_menu()
                
        return True
        
    def add_texticon_column(self, header, hidden=False):
        # For icon
        self.liststore_columns.append(gtk.gdk.Pixbuf)
        # For text
        self.liststore_columns.append(str)
        column_indices = [len(self.liststore_columns) - 2, 
                                            len(self.liststore_columns) - 1]
        # Add to the index list so we know the order of the visible columns.
        self.column_index.append(header)
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
        column.set_visible(not hidden)
        self.treeview.append_column(column)
        # Set hidden in the column
        self.columns[header].hidden = hidden
        self.columns[header].column = column
        # Re-create the menu item because of the new column
        self.create_checklist_menu()
                
        return True
