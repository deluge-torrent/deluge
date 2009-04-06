# -*- coding: utf-8 -*-
#
# listview.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
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
# 	Boston, MA  02110-1301, USA.
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
#

#


import cPickle
import os.path

import pygtk
pygtk.require('2.0')
import gtk
import gettext

import deluge.configmanager
from deluge.configmanager import ConfigManager
import deluge.common
from deluge.log import LOG as log

# Cell data functions to pass to add_func_column()
def cell_data_speed(column, cell, model, row, data):
    """Display value as a speed, eg. 2 KiB/s"""
    speed = model.get_value(row, data)
    speed_str = ""
    if speed > 0:
        speed_str = deluge.common.fspeed(speed)

    cell.set_property('text', speed_str)

def cell_data_size(column, cell, model, row, data):
    """Display value in terms of size, eg. 2 MB"""
    size = model.get_value(row, data)
    size_str = deluge.common.fsize(size)
    cell.set_property('text', size_str)

def cell_data_peer(column, cell, model, row, data):
    """Display values as 'value1 (value2)'"""
    (first, second) = model.get(row, *data)
    # Only display a (total) if second is greater than -1
    if second > -1:
        cell.set_property('text', '%d (%d)' % (first, second))
    else:
        cell.set_property('text', '%d' % first)

def cell_data_time(column, cell, model, row, data):
    """Display value as time, eg 1m10s"""
    time = model.get_value(row, data)
    if time <= 0:
        time_str = ""
    else:
        time_str = deluge.common.ftime(time)
    cell.set_property('text', time_str)

def cell_data_ratio(column, cell, model, row, data):
    """Display value as a ratio with a precision of 3."""
    ratio = model.get_value(row, data)
    if ratio < 0:
        ratio_str = "∞"
    else:
        ratio_str = "%.3f" % ratio

    cell.set_property('text', ratio_str)

def cell_data_date(column, cell, model, row, data):
    """Display value as date, eg 05/05/08"""
    cell.set_property('text', deluge.common.fdate(model.get_value(row, data)))

class ListViewColumnState:
    """Used for saving/loading column state"""
    def __init__(self, name, position, width, visible, sort, sort_order):
        self.name = name
        self.position = position
        self.width = width
        self.visible = visible
        self.sort = sort
        self.sort_order = sort_order

class ListView:
    """ListView is used to make custom GtkTreeViews.  It supports the adding
    and removing of columns, creating a menu for a column toggle list and
    support for 'status_field's which are used while updating the columns data.
    """

    class ListViewColumn:
        """Holds information regarding a column in the ListView"""
        def __init__(self, name, column_indices):
            # Name is how a column is identified and is also the header
            self.name = name
            # Column_indices holds the indexes to the liststore_columns that
            # this column utilizes. It is stored as a list.
            self.column_indices = column_indices
            # Column is a reference to the GtkTreeViewColumn object
            self.column = None
            # This is the name of the status field that the column will query
            # the core for if an update is called.
            self.status_field = None
            # If column is 'hidden' then it will not be visible and will not
            # show up in any menu listing;  it cannot be shown ever.
            self.hidden = False
            # If this is set, it is used to sort the model
            self.sort_func = None
            self.sort_id = None

    def __init__(self, treeview_widget=None, state_file=None):
        log.debug("ListView initialized..")

        if treeview_widget is not None:
            # User supplied a treeview widget
            self.treeview = treeview_widget
        else:
            self.treeview = gtk.TreeView()

        if state_file:
            self.load_state(state_file)

        self.liststore = None
        self.model_filter = None

        self.treeview.set_rules_hint(True)
        self.treeview.set_reorderable(True)
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        # Dictionary of 'header' or 'name' to ListViewColumn object
        self.columns = {}
        # Column_index keeps track of the order of the visible columns.
        self.column_index = []
        # The column types for the list store.. this may have more entries than
        # visible columns due to some columns utilizing more than 1 liststore
        # column and some columns being hidden.
        self.liststore_columns = []
        # The GtkMenu that is created after every addition, removal or reorder
        self.menu = None
        # A list of menus that self.menu will be a submenu of everytime it is
        # created.
        self.checklist_menus = []

        # Create the model filter and column
        self.add_bool_column("filter", hidden=True)

    def create_model_filter(self):
        """create new filter-model
        must be called after listview.create_new_liststore
        """
        model_filter = self.liststore.filter_new()
        model_filter.set_visible_column(
            self.columns["filter"].column_indices[0])
        sort_info = None
        if self.model_filter:
            sort_info = self.model_filter.get_sort_column_id()

        self.model_filter = gtk.TreeModelSort(model_filter)
        if sort_info and sort_info[0] and sort_info[1] > -1:
            self.model_filter.set_sort_column_id(sort_info[0], sort_info[1])
        self.set_sort_functions()
        self.treeview.set_model(self.model_filter)

    def set_sort_functions(self):
        for column in self.columns.values():
            if column.sort_func:
                self.model_filter.set_sort_func(
                    column.sort_id,
                    column.sort_func,
                    column.sort_id)

    def save_state(self, filename):
        """Saves the listview state (column positions and visibility) to
            filename."""
        # A list of ListViewColumnStates
        state = []

        # Get the list of TreeViewColumns from the TreeView
        treeview_columns = self.treeview.get_columns()
        counter = 0
        for column in treeview_columns:
            sort = None
            id, order = self.model_filter.get_sort_column_id()
            if self.get_column_name(id) == column.get_title():
                sort = id
            # Append a new column state to the state list
            state.append(ListViewColumnState(column.get_title(), counter,
                column.get_width(), column.get_visible(),
                sort, int(column.get_sort_order())))
            # Increase the counter because this is how we determine position
            counter += 1

        # Get the config location for saving the state file
        config_location = deluge.configmanager.get_config_dir()

        try:
            log.debug("Saving ListView state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "wb")
            cPickle.dump(state, state_file)
            state_file.close()
        except IOError, e:
            log.warning("Unable to save state file: %s", e)

    def load_state(self, filename):
        """Load the listview state from filename."""
        # Get the config location for loading the state file
        config_location = deluge.configmanager.get_config_dir()
        state = None

        try:
            log.debug("Loading ListView state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "rb")
            state = cPickle.load(state_file)
            state_file.close()
        except (EOFError, IOError), e:
            log.warning("Unable to load state file: %s", e)

        # Keep the state in self.state so we can access it as we add new columns
        self.state = state

    def set_treeview(self, treeview_widget):
        """Set the treeview widget that this listview uses."""
        self.treeview = treeview_widget
        self.treeview.set_model(self.liststore)
        return

    def get_column_index(self, name):
        """Get the liststore column indices belonging to this column.
        Will return a list.
        """
        return self.columns[name].column_indices

    def get_column_name(self, index):
        """Get the header name for a liststore column index"""
        for key, value in self.columns.items():
            if index in value.column_indices:
                return key

    def get_state_field_column(self, field):
        """Returns the column number for the state field"""
        for column in self.columns.keys():
            if self.columns[column].status_field == None:
                continue

            for f in self.columns[column].status_field:
                if field == f:
                    return self.columns[column].column_indices[
                        self.columns[column].status_field.index(f)]

    def on_menuitem_toggled(self, widget):
        """Callback for the generated column menuitems."""
        # Get the column name from the widget
        name = widget.get_child().get_text()

        # Set the column's visibility based on the widgets active state
        self.columns[name].column.set_visible(widget.get_active())
        return

    def register_checklist_menu(self, menu):
        """Register a checklist menu with the listview.  It will automatically
        attach any new checklist menu it makes to this menu.
        """
        self.checklist_menus.append(menu)

    def create_checklist_menu(self):
        """Creates a menu used for toggling the display of columns."""
        menu = gtk.Menu()
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
            # Connect to the 'toggled' event
            menuitem.connect("toggled", self.on_menuitem_toggled)
            # Add the new checkmenuitem to the menu
            menu.append(menuitem)

        # Attach this new menu to all the checklist_menus
        for _menu in self.checklist_menus:
            _menu.set_submenu(menu)
            _menu.show_all()

        return menu

    def create_new_liststore(self):
        """Creates a new GtkListStore based on the liststore_columns list"""
        # Create a new liststore with added column and move the data from the
        # old one to the new one.
        new_list = gtk.ListStore(*tuple(self.liststore_columns))

        # This function is used in the liststore.foreach method with user_data
        # being the new liststore and the columns list
        def copy_row(model, path, row, user_data):
            new_list, columns = user_data
            new_row = new_list.append()
            for column in range(len(columns)):
                # Get the current value of the column for this row
                value = model.get_value(row, column)
                # Set the value of this row and column in the new liststore
                new_list.set_value(new_row, column, value)

        # Do the actual row copy
        if self.liststore is not None:
            self.liststore.foreach(copy_row, (new_list, self.columns))

        self.liststore = new_list
        # Create the model
        self.create_model_filter()

        return

    def remove_column(self, header):
        """Removes the column with the name 'header' from the listview"""
        # Start by removing this column from the treeview
        self.treeview.remove_column(self.columns[header].column)
        # Get the column indices
        column_indices = self.columns[header].column_indices
        # Delete the column
        del self.columns[header]
        self.column_index.remove(header)
        # Shift the column_indices values of those columns effected by the
        # removal.  Any column_indices > the one removed.
        for column in self.columns.values():
            if column.column_indices[0] > column_indices[0]:
                # We need to shift this column_indices
                for index in column.column_indices:
                    index = index - len(column_indices)

        # Remove from the liststore columns list
        for index in column_indices:
            del self.liststore_columns[index]

        # Create a new liststore
        self.create_new_liststore()

        # Re-create the menu
        self.create_checklist_menu()

        return

    def add_column(self, header, render, col_types, hidden, position,
            status_field, sortid, text=0, value=0, pixbuf=0, function=None,
            column_type=None, sort_func=None):
        """Adds a column to the ListView"""
        # Add the column types to liststore_columns
        column_indices = []
        if type(col_types) is list:
            for col_type in col_types:
                self.liststore_columns.append(col_type)
                column_indices.append(len(self.liststore_columns) - 1)
        else:
            self.liststore_columns.append(col_types)
            column_indices.append(len(self.liststore_columns) - 1)

        # Add to the index list so we know the order of the visible columns.
        if position is not None:
            self.column_index.insert(position, header)
        else:
            self.column_index.append(header)

        # Create a new column object and add it to the list
        self.columns[header] = self.ListViewColumn(header, column_indices)

        self.columns[header].status_field = status_field
        self.columns[header].sort_func = sort_func
        self.columns[header].sort_id = column_indices[sortid]

        # Create a new list with the added column
        self.create_new_liststore()

        column = gtk.TreeViewColumn(header)
        if column_type == "text":
            column.pack_start(render)
            column.add_attribute(render, "text",
                    self.columns[header].column_indices[text])
        elif column_type == "bool":
            column.pack_start(render)
            column.add_attribute(render, "active",
                    self.columns[header].column_indices[0])
        elif column_type == "func":
            column.pack_start(render, True)
            if len(self.columns[header].column_indices) > 1:
                column.set_cell_data_func(render, function,
                        tuple(self.columns[header].column_indices))
            else:
                column.set_cell_data_func(render, function,
                            self.columns[header].column_indices[0])
        elif column_type == "progress":
            column.pack_start(render)
            if function is None:
                column.add_attribute(render, "text",
                    self.columns[header].column_indices[text])
                column.add_attribute(render, "value",
                    self.columns[header].column_indices[value])
            else:
                column.set_cell_data_func(render, function,
                    tuple(self.columns[header].column_indices))
        elif column_type == "texticon":
            column.pack_start(render[pixbuf], False)
            if function is not None:
                column.set_cell_data_func(render[pixbuf], function,
                            self.columns[header].column_indices[pixbuf])
            column.pack_start(render[text], True)
            column.add_attribute(render[text], "text",
                    self.columns[header].column_indices[text])
        elif column_type == None:
            return

        column.set_sort_column_id(self.columns[header].column_indices[sortid])
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        column.set_visible(not hidden)

        # Check for loaded state and apply
        if self.state != None:
            for column_state in self.state:
                if header == column_state.name:
                    # We found a loaded state
                    if column_state.width > 0:
                        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                        column.set_fixed_width(column_state.width)

                    if column_state.sort is not None and column_state.sort > -1:
                        self.model_filter.set_sort_column_id(column_state.sort, column_state.sort_order)
                    column.set_visible(column_state.visible)
                    position = column_state.position

        if position is not None:
            self.treeview.insert_column(column, position)
        else:
            self.treeview.append_column(column)

        # Set hidden in the column
        self.columns[header].hidden = hidden
        self.columns[header].column = column
        # Re-create the menu item because of the new column
        self.create_checklist_menu()

        return True

    def add_text_column(self, header, col_type=str, hidden=False,
                                            position=None,
                                            status_field=None,
                                            sortid=0,
                                            column_type="text",
                                            sort_func=None):
        """Add a text column to the listview.  Only the header name is required.
        """
        render = gtk.CellRendererText()
        self.add_column(header, render, col_type, hidden, position,
                    status_field, sortid, column_type=column_type, sort_func=sort_func)

        return True

    def add_bool_column(self, header, col_type=bool, hidden=False,
                                            position=None,
                                            status_field=None,
                                            sortid=0,
                                            column_type="bool"):

        """Add a bool column to the listview"""
        render = gtk.CellRendererToggle()
        self.add_column(header, render, col_type, hidden, position,
                    status_field, sortid, column_type=column_type)

    def add_func_column(self, header, function, col_types, sortid=0,
                                hidden=False, position=None, status_field=None,
                                column_type="func", sort_func=None):
        """Add a function column to the listview.  Need a header name, the
        function and the column types."""

        render = gtk.CellRendererText()
        self.add_column(header, render, col_types, hidden, position,
                            status_field, sortid, column_type=column_type,
                            function=function, sort_func=sort_func)

        return True

    def add_progress_column(self, header, col_types=[float, str],
                                            sortid=0,
                                            hidden=False,
                                            position=None,
                                            status_field=None,
                                            function=None,
                                            column_type="progress"):
        """Add a progress column to the listview."""

        render = gtk.CellRendererProgress()
        self.add_column(header, render, col_types, hidden, position,
                            status_field, sortid, function=function,
                            column_type=column_type,
                            value=0, text=1)

        return True

    def add_texticon_column(self, header, col_types=[str, str],
                                            sortid=1,
                                            hidden=False,
                                            position=None,
                                            status_field=None,
                                            column_type="texticon",
                                            function=None):
        """Adds a texticon column to the listview."""
        render1 = gtk.CellRendererPixbuf()
        render2 = gtk.CellRendererText()

        self.add_column(header, (render1, render2), col_types, hidden,
                            position, status_field, sortid,
                            column_type=column_type, function=function,
                            pixbuf=0, text=1)

        return True
