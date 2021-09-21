# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from gi.repository import GObject, Gtk

from deluge.common import PY2, decode_bytes

from .common import cmp, load_pickled_state_file, save_pickled_state_file

log = logging.getLogger(__name__)


class ListViewColumnState(object):
    """Class used for saving/loading column state."""

    def __init__(self, name, position, width, visible, sort, sort_order):
        self.name = name
        self.position = position
        self.width = width
        self.visible = visible
        self.sort = sort
        self.sort_order = sort_order


class ListView(object):
    """ListView is used to make custom GtkTreeViews.  It supports the adding
    and removing of columns, creating a menu for a column toggle list and
    support for 'status_field's which are used while updating the columns data.
    """

    class ListViewColumn(object):
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

    class TreeviewColumn(Gtk.TreeViewColumn, object):
        """
        TreeViewColumn does not signal right-click events, and we need them
        This subclass is equivalent to TreeViewColumn, but it signals these events

        Most of the code of this class comes from Quod Libet (http://www.sacredchao.net/quodlibet)
        """

        __gsignals__ = {
            'button-press-event'
            if not PY2
            else b'button-press-event': (GObject.SIGNAL_RUN_LAST, None, (object,))
        }

        def __init__(self, title=None, cell_renderer=None, **args):
            """ Constructor, see Gtk.TreeViewColumn """
            Gtk.TreeViewColumn.__init__(self, title, cell_renderer, **args)
            label = Gtk.Label(label=title)
            self.set_widget(label)
            label.show()
            label.__realize = label.connect('realize', self.on_realize)
            self.title = title
            self.data_func = None
            self.data_func_data = None
            self.cell_renderer = None

        def on_realize(self, widget):
            widget.disconnect(widget.__realize)
            del widget.__realize
            button = widget.get_ancestor(Gtk.Button)
            if button is not None:
                button.connect('button-press-event', self.on_button_pressed)

        def on_button_pressed(self, widget, event):
            self.emit('button-press-event', event)

        def set_cell_data_func_attributes(self, cell_renderer, func, func_data=None):
            """Store the values to be set by set_cell_data_func"""
            self.data_func = func
            self.data_func_data = func_data
            self.cell_renderer = cell_renderer

        def set_visible(self, visible):
            Gtk.TreeViewColumn.set_visible(self, visible)
            if self.data_func:
                if not visible:
                    # Set data function to None to prevent unnecessary calls when column is hidden
                    self.set_cell_data_func(self.cell_renderer, None, func_data=None)
                else:
                    self.set_cell_data_func(
                        self.cell_renderer, self.data_func, self.data_func_data
                    )

        def set_col_attributes(self, renderer, add=True, **kw):
            if add is True:
                for attr, value in kw.items():
                    self.add_attribute(renderer, attr, value)
            else:
                self.set_attributes(renderer, **kw)

    def __init__(self, treeview_widget=None, state_file=None):
        log.debug('ListView initialized..')

        if treeview_widget is not None:
            # User supplied a treeview widget
            self.treeview = treeview_widget
        else:
            self.treeview = Gtk.TreeView()

        self.treeview.set_enable_search(True)
        self.treeview.set_search_equal_func(self.on_keypress_search_by_name, None)

        if state_file:
            self.load_state(state_file)

        self.liststore = None
        self.model_filter = None

        self.treeview.set_reorderable(False)
        self.treeview.set_rubber_banding(True)  # Enable mouse multi-row selection.
        self.treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

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

        # Since gtk TreeModelSort doesn't do stable sort, remember last sort order so we can
        self.last_sort_order = {}
        self.unique_column_id = None
        self.default_sort_column_id = None

        # Create the model filter and column
        self.add_bool_column('filter', hidden=True)

    def create_model_filter(self):
        """create new filter-model
        must be called after listview.create_new_liststore
        """
        model_filter = self.liststore.filter_new()
        model_filter.set_visible_column(self.columns['filter'].column_indices[0])
        self.model_filter = Gtk.TreeModelSort(model=model_filter)
        self.model_filter.connect('sort-column-changed', self.on_model_sort_changed)
        self.model_filter.connect('row-inserted', self.on_model_row_inserted)
        self.treeview.set_model(self.model_filter)
        self.set_sort_functions()
        self.set_model_sort()

    def set_model_sort(self):
        column_state = self.get_sort_column_from_state()
        if column_state:
            self.treeview.get_model().set_sort_column_id(
                column_state.sort, column_state.sort_order
            )
        # Using the default sort column
        elif self.default_sort_column_id:
            self.model_filter.set_sort_column_id(
                self.default_sort_column_id, Gtk.SortType.ASCENDING
            )
        self.model_filter.set_default_sort_func(
            self.generic_sort_func, self.get_column_index(_('Added'))[0]
        )

    def get_sort_column_from_state(self):
        """Find the first (should only be one) state with sort enabled"""
        if self.state is None:
            return None
        for column_state in self.state:
            if column_state.sort is not None and column_state.sort > -1:
                return column_state
        return None

    def on_model_sort_changed(self, model):
        if self.unique_column_id:
            self.last_sort_order = {}

            def record_position(model, path, _iter, data):
                unique_id = model[_iter][self.unique_column_id]
                self.last_sort_order[unique_id] = int(str(path))

            model.foreach(record_position, None)

    def on_model_row_inserted(self, model, path, _iter):
        if self.unique_column_id:
            self.last_sort_order.setdefault(
                model[_iter][self.unique_column_id], len(model) - 1
            )

    def stabilize_sort_func(self, sort_func):
        def stabilized(model, iter1, iter2, data):
            result = sort_func(model, iter1, iter2, data)
            if result == 0 and self.unique_column_id:
                unique1 = model[iter1][self.unique_column_id]
                unique2 = model[iter2][self.unique_column_id]
                if unique1 in self.last_sort_order and unique2 in self.last_sort_order:
                    result = cmp(
                        self.last_sort_order[unique1], self.last_sort_order[unique2]
                    )
                # If all else fails, fall back to sorting by unique column
                if result == 0:
                    result = cmp(unique1, unique2)

            return result

        return stabilized

    def generic_sort_func(self, model, iter1, iter2, data):
        return cmp(model[iter1][data], model[iter2][data])

    def set_sort_functions(self):
        for column in self.columns.values():
            sort_func = column.sort_func or self.generic_sort_func
            self.model_filter.set_sort_func(
                column.sort_id, self.stabilize_sort_func(sort_func), column.sort_id
            )

    def create_column_state(self, column, position=None):
        if not position:
            # Find the position
            for index, c in enumerate(self.treeview.get_columns()):
                if column.get_title() == c.get_title():
                    position = index
                    break
        sort = None
        if self.model_filter:
            sort_id, order = self.model_filter.get_sort_column_id()
            col_title = decode_bytes(column.get_title())
            if self.get_column_name(sort_id) == col_title:
                sort = sort_id

        return ListViewColumnState(
            column.get_title(),
            position,
            column.get_width(),
            column.get_visible(),
            sort,
            int(column.get_sort_order()),
        )

    def save_state(self, filename):
        """Saves the listview state (column positions and visibility) to
        filename."""
        # A list of ListViewColumnStates
        state = []

        # Workaround for all zero widths after removing column on shutdown
        if not any(c.get_width() for c in self.treeview.get_columns()):
            return

        # Get the list of TreeViewColumns from the TreeView
        for counter, column in enumerate(self.treeview.get_columns()):
            # Append a new column state to the state list
            state.append(self.create_column_state(column, counter))

        state += self.removed_columns_state

        self.state = state
        save_pickled_state_file(filename, state)

    def load_state(self, filename):
        """Load the listview state from filename."""
        self.state = load_pickled_state_file(filename)

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
        for column in self.columns:
            if self.columns[column].status_field is None:
                continue

            for f in self.columns[column].status_field:
                if field == f:
                    return self.columns[column].column_indices[
                        self.columns[column].status_field.index(f)
                    ]

    def on_menuitem_toggled(self, widget):
        """Callback for the generated column menuitems."""
        # Get the column name from the widget
        name = widget.get_child().get_text()

        # Set the column's visibility based on the widgets active state
        try:
            self.columns[name].column.set_visible(widget.get_active())
        except KeyError:
            self.columns[decode_bytes(name)].column.set_visible(widget.get_active())
        return

    def on_treeview_header_right_clicked(self, column, event):
        if event.button == 3:
            self.menu.popup(None, None, None, None, event.button, event.get_time())

    def register_checklist_menu(self, menu):
        """Register a checklist menu with the listview.  It will automatically
        attach any new checklist menu it makes to this menu.
        """
        self.checklist_menus.append(menu)

    def create_checklist_menu(self):
        """Creates a menu used for toggling the display of columns."""
        menu = self.menu = Gtk.Menu()
        # Iterate through the column_index list to preserve order
        for name in self.column_index:
            column = self.columns[name]
            # If the column is hidden, then we do not want to show it in the
            # menu.
            if column.hidden is True:
                continue
            menuitem = Gtk.CheckMenuItem.new_with_label(column.name)
            # If the column is currently visible, make sure it's set active
            # (or checked) in the menu.
            if column.column.get_visible() is True:
                menuitem.set_active(True)
            # Connect to the 'toggled' event
            menuitem.connect('toggled', self.on_menuitem_toggled)
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
        new_list = Gtk.ListStore(*tuple(self.liststore_columns))

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

        if column.column_type == 'text':
            if add:
                tree_column.pack_start(column.renderer, True)
            tree_column.set_col_attributes(
                column.renderer, add=add, text=column.column_indices[column.text_index]
            )
        elif column.column_type == 'bool':
            if add:
                tree_column.pack_start(column.renderer, True)
            tree_column.set_col_attributes(
                column.renderer, active=column.column_indices[0]
            )
        elif column.column_type == 'func':
            if add:
                tree_column.pack_start(column.renderer, True)
            indice_arg = column.column_indices[0]
            if len(column.column_indices) > 1:
                indice_arg = tuple(column.column_indices)
            tree_column.set_cell_data_func(
                column.renderer, column.data_func, indice_arg
            )
        elif column.column_type == 'progress':
            if add:
                tree_column.pack_start(column.renderer, True)
            if column.data_func is None:
                tree_column.set_col_attributes(
                    column.renderer,
                    add=add,
                    text=column.column_indices[column.text_index],
                    value=column.column_indices[column.value_index],
                )
            else:
                tree_column.set_cell_data_func(
                    column.renderer, column.data_func, tuple(column.column_indices)
                )
        elif column.column_type == 'texticon':
            if add:
                tree_column.pack_start(column.renderer[column.pixbuf_index], False)
                tree_column.pack_start(column.renderer[column.text_index], True)
            tree_column.set_col_attributes(
                column.renderer[column.text_index],
                add=add,
                text=column.column_indices[column.text_index],
            )
            if column.data_func is not None:
                tree_column.set_cell_data_func(
                    column.renderer[column.pixbuf_index],
                    column.data_func,
                    column.column_indices[column.pixbuf_index],
                )
        return True

    def remove_column(self, header):
        """Removes the column with the name 'header' from the listview"""
        # Store a copy of this columns state in case it's re-added
        state = self.create_column_state(self.columns[header].column)
        self.removed_columns_state.append(state)
        # Only remove column if column is associated with the treeview. This avoids
        # warning on shutdown when GTKUI is closed before plugins try to remove columns
        if self.columns[header].column.get_tree_view() is not None:
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

    def add_column(
        self,
        header,
        render,
        col_types,
        hidden,
        position,
        status_field,
        sortid,
        text=0,
        value=0,
        pixbuf=0,
        function=None,
        column_type=None,
        sort_func=None,
        tooltip=None,
        default=True,
        unique=False,
        default_sort=False,
    ):
        """Adds a column to the ListView"""
        # Add the column types to liststore_columns
        column_indices = []
        if isinstance(col_types, list):
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

        if unique:
            self.unique_column_id = column_indices[sortid]
        if default_sort:
            self.default_sort_column_id = column_indices[sortid]

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
        column.set_min_width(20)
        column.set_reorderable(True)
        column.set_visible(not hidden)
        column.connect('button-press-event', self.on_treeview_header_right_clicked)

        if tooltip:
            column.get_widget().set_tooltip_markup(tooltip)

        # Check for loaded state and apply
        column_in_state = False
        if self.state is not None:
            for column_state in self.state:
                if header == decode_bytes(column_state.name):
                    # We found a loaded state
                    column_in_state = True
                    if column_state.width > 0:
                        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
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
        self.columns[header].column = column
        # Re-create the menu item because of the new column
        self.create_checklist_menu()

        return True

    def add_text_column(
        self,
        header,
        col_type=str,
        hidden=False,
        position=None,
        status_field=None,
        sortid=0,
        column_type='text',
        sort_func=None,
        tooltip=None,
        default=True,
        unique=False,
        default_sort=False,
    ):
        """Add a text column to the listview.  Only the header name is required."""
        render = Gtk.CellRendererText()
        self.add_column(
            header,
            render,
            col_type,
            hidden,
            position,
            status_field,
            sortid,
            column_type=column_type,
            sort_func=sort_func,
            tooltip=tooltip,
            default=default,
            unique=unique,
            default_sort=default_sort,
        )

        return True

    def add_bool_column(
        self,
        header,
        col_type=bool,
        hidden=False,
        position=None,
        status_field=None,
        sortid=0,
        column_type='bool',
        tooltip=None,
        default=True,
    ):
        """Add a bool column to the listview"""
        render = Gtk.CellRendererToggle()
        self.add_column(
            header,
            render,
            col_type,
            hidden,
            position,
            status_field,
            sortid,
            column_type=column_type,
            tooltip=tooltip,
            default=default,
        )

    def add_func_column(
        self,
        header,
        function,
        col_types,
        sortid=0,
        hidden=False,
        position=None,
        status_field=None,
        column_type='func',
        sort_func=None,
        tooltip=None,
        default=True,
    ):
        """Add a function column to the listview.  Need a header name, the
        function and the column types."""

        render = Gtk.CellRendererText()
        self.add_column(
            header,
            render,
            col_types,
            hidden,
            position,
            status_field,
            sortid,
            column_type=column_type,
            function=function,
            sort_func=sort_func,
            tooltip=tooltip,
            default=default,
        )

        return True

    def add_progress_column(
        self,
        header,
        col_types=None,
        sortid=0,
        hidden=False,
        position=None,
        status_field=None,
        function=None,
        column_type='progress',
        tooltip=None,
        sort_func=None,
        default=True,
    ):
        """Add a progress column to the listview."""

        if col_types is None:
            col_types = [float, str]
        render = Gtk.CellRendererProgress()
        self.add_column(
            header,
            render,
            col_types,
            hidden,
            position,
            status_field,
            sortid,
            function=function,
            column_type=column_type,
            value=0,
            text=1,
            tooltip=tooltip,
            sort_func=sort_func,
            default=default,
        )

        return True

    def add_texticon_column(
        self,
        header,
        col_types=None,
        sortid=1,
        hidden=False,
        position=None,
        status_field=None,
        column_type='texticon',
        function=None,
        sort_func=None,
        tooltip=None,
        default=True,
        default_sort=False,
    ):
        """Adds a texticon column to the listview."""
        if col_types is None:
            col_types = [str, str]
        render1 = Gtk.CellRendererPixbuf()
        render2 = Gtk.CellRendererText()

        self.add_column(
            header,
            (render1, render2),
            col_types,
            hidden,
            position,
            status_field,
            sortid,
            column_type=column_type,
            function=function,
            pixbuf=0,
            text=1,
            tooltip=tooltip,
            sort_func=sort_func,
            default=default,
            default_sort=default_sort,
        )

        return True

    def on_keypress_search_by_name(self, model, column, key, _iter):
        torrent_name_col = self.columns[_('Name')].column_indices[1]
        return not model[_iter][torrent_name_col].lower().startswith(key.lower())

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
                # Ignore extra columns from Plugins in col_state
                continue
            if col_state.name == column_at_position.get_title():
                # It's in the right position
                continue
            column = find_column(col_state.name)
            if not column:
                log.debug(
                    'Could not find column matching "%s" on state.', col_state.name
                )
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
