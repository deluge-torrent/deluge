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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

from deluge.configmanager import ConfigManager
import deluge.configmanager
import deluge.common
from deluge.log import LOG as log

from gobject import signal_new, SIGNAL_RUN_LAST, TYPE_NONE
from gtk import gdk
signal_new('button-press-event', gtk.TreeViewColumn,
           SIGNAL_RUN_LAST, TYPE_NONE, (gdk.Event,))


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
    date = model.get_value(row, data)
    if date <= 0:
        date_str = ""
    else:
        date_str = deluge.common.fdate(date)

    cell.set_property('text', date_str)

def cell_data_speed_limit(column, cell, model, row, data):
    """Display value as a speed, eg. 2 KiB/s"""
    speed = model.get_value(row, data)
    speed_str = ""
    if speed > 0:
        speed_str = deluge.common.fspeed(speed * 1024)

    cell.set_property('text', speed_str)

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
            # Values needed to update TreeViewColumns
            self.column_type = None
            self.renderer = None
            self.text_index = 0
            self.value_index = 0
            self.pixbuf_index = 0
            self.data_func = None

    class TreeviewColumn(gtk.TreeViewColumn):
        """
            TreeViewColumn does not signal right-click events, and we need them
            This subclass is equivalent to TreeViewColumn, but it signals these events

            Most of the code of this class comes from Quod Libet (http://www.sacredchao.net/quodlibet)
        """

        def __init__(self, title=None, cell_renderer=None, ** args):
            """ Constructor, see gtk.TreeViewColumn """
            gtk.TreeViewColumn.__init__(self, title, cell_renderer, ** args)
            label = gtk.Label(title)
            self.set_widget(label)
            label.show()
            label.__realize = label.connect('realize', self.onRealize)

        def onRealize(self, widget):
            widget.disconnect(widget.__realize)
            del widget.__realize
            button = widget.get_ancestor(gtk.Button)
            if button is not None:
                button.connect('button-press-event', self.onButtonPressed)

        def onButtonPressed(self, widget, event):
            self.emit('button-press-event', event)

        def set_col_attributes(self, renderer, add=True, **kw):
            """Helper function to add and set attributes"""
            if add is True:
                for attr, value in kw.iteritems():
                    self.add_attribute(renderer, attr, value)
            else:
                self.set_attributes(renderer, **kw)

    def __init__(self, treeview_widget=None, state_file=None):
        log.debug("ListView initialized..")

        if treeview_widget is not None:
            # User supplied a treeview widget
            self.treeview = treeview_widget
        else:
            self.treeview = gtk.TreeView()

        self.treeview.set_enable_search(True)
        self.treeview.set_search_equal_func(self.on_keypress_search_by_name)

        if state_file:
            self.load_state(state_file)

        self.liststore = None
        self.model_filter = None

        self.treeview.set_rules_hint(True)
        self.treeview.set_reorderable(False)
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

        # Store removed columns state.  This is needed for plugins that remove
        # their columns prior to having the state list saved on shutdown.
        self.removed_columns_state = []

        # Create the model filter and column
        self.add_bool_column("filter", hidden=True)

    def create_model_filter(self):
        """create new filter-model
        must be called after listview.create_new_liststore
        """
        model_filter = self.liststore.filter_new()
        model_filter.set_visible_column(
            self.columns["filter"].column_indices[0])
        self.model_filter = gtk.TreeModelSort(model_filter)
        self.treeview.set_model(self.model_filter)
        self.set_sort_functions()
        self.set_model_sort()

    def set_model_sort(self):
        if self.state is not None:
            for column_state in self.state:
                if column_state.sort is not None and column_state.sort > -1:
                    self.treeview.get_model().set_sort_column_id(column_state.sort, column_state.sort_order)
                    break

    def stabilize_sort_func(self, sort_func):
        def stabilized(model, iter1, iter2, data):
            result = sort_func(model, iter1, iter2, data)
            if result == 0:
                # Compare by hash if main column values are equal
                return cmp(model[iter1][1], model[iter2][1])
            return result
        return stabilized

    def generic_sort_func(self, model, iter1, iter2, data):
        return cmp(model[iter1][data], model[iter2][data])

    def set_sort_functions(self):
        for column in self.columns.values():
            sort_func = column.sort_func or self.generic_sort_func
            self.model_filter.set_sort_func(
                column.sort_id,
                self.stabilize_sort_func(sort_func),
                column.sort_id)

    def create_column_state(self, column, position=None):
        if not position:
            # Find the position
            for index, c in enumerate(self.treeview.get_columns()):
                if column.get_title() == c.get_title():
                    position = index
                    break
        sort = None
        if self.model_filter: # Will be None if no list was ever loaded (never connected to server)
            sort_id, order = self.model_filter.get_sort_column_id()
            if self.get_column_name(sort_id) == column.get_title():
                sort = sort_id
        return ListViewColumnState(column.get_title(), position,
            column.get_width(), column.get_visible(),
            sort, int(column.get_sort_order()))

    def save_state(self, filename):
        """Saves the listview state (column positions and visibility) to
            filename."""
        # A list of ListViewColumnStates
        state = []

        # Workaround for all zero widths after removing column on shutdown
        if not any(c.get_width() for c in self.treeview.get_columns()): return

        # Get the list of TreeViewColumns from the TreeView
        for counter, column in enumerate(self.treeview.get_columns()):
            # Append a new column state to the state list
            state.append(self.create_column_state(column, counter))

        state += self.removed_columns_state

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
        except (EOFError, IOError, cPickle.UnpicklingError), e:
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
        try:
            self.columns[name].column.set_visible(widget.get_active())
        except KeyError:
            self.columns[unicode(name)].column.set_visible(widget.get_active())
        return

    def on_treeview_header_right_clicked(self, column, event):
        if event.button == 3:
            self.menu.popup(None, None, None, event.button, event.get_time())


    def register_checklist_menu(self, menu):
        """Register a checklist menu with the listview.  It will automatically
        attach any new checklist menu it makes to this menu.
        """
        self.checklist_menus.append(menu)

    def create_checklist_menu(self):
        """Creates a menu used for toggling the display of columns."""
        menu = self.menu = gtk.Menu()
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

    def update_treeview_column(self, header, add=True):
        """Update TreeViewColumn based on ListView column mappings"""
        column = self.columns[header]
        tree_column = self.columns[header].column

        if column.column_type == "text":
            if add:
                tree_column.pack_start(column.renderer)
            tree_column.set_col_attributes(column.renderer, add=add,
                                           text=column.column_indices[column.text_index])
        elif column.column_type == "bool":
            if add:
                tree_column.pack_start(column.renderer)
            tree_column.set_col_attributes(column.renderer, active=column.column_indices[0])
        elif column.column_type == "func":
            if add:
                tree_column.pack_start(column.renderer, True)
            indice_arg = column.column_indices[0]
            if len(column.column_indices) > 1:
                indice_arg = tuple(column.column_indices)
            tree_column.set_cell_data_func(column.renderer, column.data_func, indice_arg)
        elif column.column_type == "progress":
            if add:
                tree_column.pack_start(column.renderer)
            if column.data_func is None:
                tree_column.set_col_attributes(column.renderer, add=add,
                                               text=column.column_indices[column.text_index],
                                               value=column.column_indices[column.value_index])
            else:
                tree_column.set_cell_data_func(column.renderer, column.data_func,
                                               tuple(column.column_indices))
        elif column.column_type == "texticon":
            if add:
                tree_column.pack_start(column.renderer[column.pixbuf_index], False)
                tree_column.pack_start(column.renderer[column.text_index], True)
            tree_column.set_col_attributes(column.renderer[column.text_index], add=add,
                                           text=column.column_indices[column.text_index])
            if column.data_func is not None:
                tree_column.set_cell_data_func(
                    column.renderer[column.pixbuf_index], column.data_func,
                    column.column_indices[column.pixbuf_index])
        return True

    def remove_column(self, header):
        """Removes the column with the name 'header' from the listview"""
        # Store a copy of this columns state in case it's re-added
        state = self.create_column_state(self.columns[header].column)
        self.removed_columns_state.append(state)

        # Start by removing this column from the treeview
        self.treeview.remove_column(self.columns[header].column)
        # Get the column indices
        column_indices = self.columns[header].column_indices
        # Delete the column
        del self.columns[header]
        self.column_index.remove(header)
        # Shift the column_indices values of those columns affected by the
        # removal. Any column_indices > the one removed.
        for column in self.columns.values():
            if column.column_indices[0] > column_indices[0]:
                # We need to shift this column_indices
                for i, index in enumerate(column.column_indices):
                    column.column_indices[i] = index - len(column_indices)
                # Update the associated TreeViewColumn
                self.update_treeview_column(column.name, add=False)

        # Remove from the liststore columns list
        for index in sorted(column_indices, reverse=True):
            del self.liststore_columns[index]
        # Create a new liststore
        self.create_new_liststore()
        # Create new model for the treeview
        self.create_model_filter()

        # Re-create the menu
        self.create_checklist_menu()

        return

    def add_column(self, header, render, col_types, hidden, position,
            status_field, sortid, text=0, value=0, pixbuf=0, function=None,
            column_type=None, sort_func=None, default=True):
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
        column = self.TreeviewColumn(header)
        self.columns[header] = self.ListViewColumn(header, column_indices)
        self.columns[header].column = column
        self.columns[header].status_field = status_field
        self.columns[header].sort_func = sort_func
        self.columns[header].sort_id = column_indices[sortid]
        # Store creation details
        self.columns[header].column_type = column_type
        self.columns[header].renderer = render
        self.columns[header].text_index = text
        self.columns[header].value_index = value
        self.columns[header].pixbuf_index = pixbuf
        self.columns[header].data_func = function

        # Create a new list with the added column
        self.create_new_liststore()

        # Happens only on columns added after the torrent list has been loaded
        if self.model_filter:
            self.create_model_filter()

        if column_type is None:
            return

        self.update_treeview_column(header)

        column.set_sort_column_id(self.columns[header].column_indices[sortid])
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(10)
        column.set_reorderable(True)
        column.set_visible(not hidden)
        column.connect('button-press-event',
                       self.on_treeview_header_right_clicked)

        # Check for loaded state and apply
        column_in_state = False
        if self.state != None:
            for column_state in self.state:
                if header == column_state.name:
                    # We found a loaded state
                    column_in_state = True
                    if column_state.width > 0:
                        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                        column.set_fixed_width(column_state.width)
                    column.set_visible(column_state.visible)
                    position = column_state.position
                    break

        # Set this column to not visible if its not in the state and
        # its not supposed to be shown by default
        if not column_in_state and not default and not hidden:
            column.set_visible(False)

        if position is not None:
            self.treeview.insert_column(column, position)
        else:
            self.treeview.append_column(column)

        # Set hidden in the column
        self.columns[header].hidden = hidden
        # Re-create the menu item because of the new column
        self.create_checklist_menu()

        return True

    def add_text_column(self, header, col_type=str, hidden=False, position=None,
                        status_field=None, sortid=0, column_type="text",
                        sort_func=None, default=True):
        """Add a text column to the listview.  Only the header name is required.
        """
        render = gtk.CellRendererText()
        self.add_column(header, render, col_type, hidden, position,
                        status_field, sortid, column_type=column_type,
                        sort_func=sort_func, default=default)

        return True

    def add_bool_column(self, header, col_type=bool, hidden=False,
                        position=None, status_field=None, sortid=0,
                        column_type="bool", default=True):
        """Add a bool column to the listview"""
        render = gtk.CellRendererToggle()
        self.add_column(header, render, col_type, hidden, position,
                        status_field, sortid, column_type=column_type,
                        default=default)

    def add_func_column(self, header, function, col_types, sortid=0,
                        hidden=False, position=None, status_field=None,
                        column_type="func", sort_func=None, default=True):
        """Add a function column to the listview.  Need a header name, the
        function and the column types."""

        render = gtk.CellRendererText()
        self.add_column(header, render, col_types, hidden, position,
                        status_field, sortid, column_type=column_type,
                        function=function, sort_func=sort_func, default=default)

        return True

    def add_progress_column(self, header, col_types=[float, str], sortid=0,
                            hidden=False, position=None, status_field=None,
                            function=None, column_type="progress",
                            sort_func=None, default=True):
        """Add a progress column to the listview."""

        render = gtk.CellRendererProgress()
        self.add_column(header, render, col_types, hidden, position,
                        status_field, sortid, function=function,
                        column_type=column_type, value=0, text=1,
                        sort_func=sort_func, default=default)
        return True

    def add_texticon_column(self, header, col_types=[str, str], sortid=1,
                            hidden=False, position=None, status_field=None,
                            column_type="texticon", function=None, sort_func=None,
                            default=True):
        """Adds a texticon column to the listview."""
        render1 = gtk.CellRendererPixbuf()
        render2 = gtk.CellRendererText()

        self.add_column(header, (render1, render2), col_types, hidden, position,
                        status_field, sortid, column_type=column_type,
                        function=function, sort_func=sort_func, pixbuf=0,
                        text=1, default=default)
        return True

    def on_keypress_search_by_name(self, model, columnn, key, iter):
        TORRENT_NAME_COL = 5
        return not model[iter][TORRENT_NAME_COL].lower().startswith(key.lower())

    def restore_columns_order_from_state(self):
        if self.state is None:
            # No state file exists, so, no reordering can be done
            return
        columns = self.treeview.get_columns()
        def find_column(header):
            for column in columns:
                if column.get_title() == header:
                    return column

        restored_columns = []
        for col_state in self.state:
            if col_state.name in restored_columns:
                # Duplicate column in state!?!?!?
                continue
            elif not col_state.visible:
                # Column is not visible, no need to reposition
                continue

            try:
                column_at_position = columns[col_state.position]
            except IndexError:
                # Extra columns in loaded state, likely from plugins, so just skip them.
                continue
            if col_state.name == column_at_position.get_title():
                # It's in the right position
                continue
            column = find_column(col_state.name)
            if not column:
                log.debug("Could not find column matching \"%s\" on state." %
                          col_state.name)
                # The cases where I've found that the column could not be found
                # is when not using the english locale, ie, the default one, or
                # when changing locales between runs.
                # On the next load, all should be fine
                continue
            self.treeview.move_column_after(column, column_at_position)
            # Get columns again to keep reordering since positions have changed
            columns = self.treeview.get_columns()
            restored_columns.append(col_state.name)
        self.create_new_liststore()
