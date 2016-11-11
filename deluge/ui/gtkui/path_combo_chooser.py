#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Bro <bro.development@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, print_function, unicode_literals

import os

# FIXME: use this as fallback to get_introspection_module?
from gi.importer import modules
# from gi.module import get_introspection_module
from gi.repository import Gdk, GObject, Gtk

import deluge.component as component
from deluge.common import resource_filename
from deluge.path_chooser_common import get_completion_paths


def is_ascii_value(keyval, ascii_key):
    try:
        # Set show/hide hidden files
        if chr(keyval) == ascii_key:
            return True
    except ValueError:
        # Not in ascii range
        pass
    return False


def key_is_up(keyval):
    return keyval == keysyms.Up or keyval == keysyms.KP_Up


def key_is_down(keyval):
    return keyval == keysyms.Down or keyval == keysyms.KP_Down


def key_is_up_or_down(keyval):
    return key_is_up(keyval) or key_is_down(keyval)


def key_is_pgup_or_pgdown(keyval):
    return keyval == keysyms.Page_Down or keyval == keysyms.Page_Up


def key_is_enter(keyval):
    return keyval == keysyms.Return or keyval == keysyms.KP_Enter


def path_without_trailing_path_sep(path):
    while path.endswith('/') or path.endswith('\\'):
        if path == '/':
            return path
        path = path[0:-1]
    return path


class ValueList(object):

    paths_without_trailing_path_sep = False

    def get_values_count(self):
        return len(self.tree_store)

    def get_values(self):
        """
        Returns the values in the list.
        """
        values = []
        for row in self.tree_store:
            values.append(row[0])
        return values

    def add_values(
        self, paths, append=True, scroll_to_row=False,
        clear=False, emit_signal=False,
    ):
        """
        Add paths to the liststore

        :param paths: the paths to add
        :type  paths: list
        :param append: if the values should be appended or inserted
        :type  append: boolean
        :param scroll_to_row: if the treeview should scroll to the new row
        :type  scroll_to_row: boolean

        """
        if clear:
            self.tree_store.clear()

        for path in paths:
            if self.paths_without_trailing_path_sep:
                path = path_without_trailing_path_sep(path)
            if append:
                tree_iter = self.tree_store.append([path])
            else:
                tree_iter = self.tree_store.insert(0, [path])

            if scroll_to_row:
                self.treeview.grab_focus()
                tree_path = self.tree_store.get_path(tree_iter)
                # Scroll to path
                self.handle_list_scroll(path=tree_path)

        if emit_signal:
            self.emit('list-value-added', paths)
            self.emit('list-values-changed', self.get_values())

    def set_values(self, paths, scroll_to_row=False, preserve_selection=True):
        """
        Add paths to the liststore

        :param paths: the paths to add
        :type  paths: list
        :param scroll_to_row: if the treeview should scroll to the new row
        :type  scroll_to_row: boolean

        """
        if not (isinstance(paths, list) or isinstance(paths, tuple)):
            return
        sel = None
        if preserve_selection:
            sel = self.get_selection_path()
        self.add_values(paths, scroll_to_row=scroll_to_row, clear=True)
        if sel:
            self.treeview.get_selection().select_path(sel)

    def get_selection_path(self):
        """Returns the (first) selected path from a treeview"""
        tree_selection = self.treeview.get_selection()
        model, tree_paths = tree_selection.get_selected_rows()
        if len(tree_paths) > 0:
            return tree_paths[0]
        return None

    def get_selected_value(self):
        path = self.get_selection_path()
        if path:
            return self.tree_store[path][0]
        return None

    def remove_selected_path(self):
        path = self.get_selection_path()
        if path:
            path_value = self.tree_store[path][0]
            del self.tree_store[path]
            index = path[0]
            # The last row was deleted
            if index == len(self.tree_store):
                index -= 1
            if index >= 0:
                path = (index, )
            self.treeview.set_cursor(path)
            self.set_path_selected(path)
            self.emit('list-value-removed', path_value)
            self.emit('list-values-changed', self.get_values())

    def set_selected_value(self, value, select_first=False):
        """
        Select the row of the list with value

        :param value: the value to be selected
        :type  value: str
        :param select_first: if the first item should be selected if the value if not found.
        :type  select_first: boolean

        """
        for i, row in enumerate(self.tree_store):
            if row[0] == value:
                self.treeview.set_cursor((i))
                return
        # The value was not found
        if select_first:
            self.treeview.set_cursor((0,))
        else:
            self.treeview.get_selection().unselect_all()

    def set_path_selected(self, path):
        self.treeview.get_selection().select_path(path)

    def on_value_list_treeview_key_press_event(self, widget, event):
        """
        Mimics Combobox behavior

        Escape or Alt+Up: Close
        Enter or Return : Select
        """
        keyval = event.keyval
        state = event.get_state() & gtk.accelerator_get_default_mod_mask()

        if keyval == keysyms.Escape or\
                (
                    key_is_up(keyval) and
                    state == gdk.MOD1_MASK
                ):  # ALT Key
            self.popdown()
            return True
        # Set entry value to the selected row
        elif key_is_enter(keyval):
            path = self.get_selection_path()
            if path:
                self.set_entry_value(path, popdown=True)
            return True
        return False

    def on_treeview_mouse_button_press_event(self, treeview, event, double_click=False):
        """
        When left clicking twice, the row value is set for the text entry
        and the popup is closed.

        """
        # This is left click
        if event.button != 3:
            # Double clicked a row, set this as the entry value
            # and close the popup
            if (double_click and event.type == gdk._2BUTTON_PRESS) or\
                    (not double_click and event.type == gdk.BUTTON_PRESS):
                path = self.get_selection_path()
                if path:
                    self.set_entry_value(path, popdown=True)
                    return True
        return False

    def handle_list_scroll(self, _next=None, path=None, set_entry=False, swap=False, scroll_window=False):
        """
        Handles changes to the row selection.

        :param _next: the direction to change selection. True means down and False means up.
            None means no change.
        :type  _next: boolean/None
        :param path: the current path. If None, the currently selected path is used.
        :type  path: tuple
        :param set_entry: if the new value should be set in the text entry.
        :type  set_entry: boolean
        :param swap: if the old and new value should be swapped
        :type  swap: boolean

        """
        if scroll_window:
            adjustment = self.completion_scrolled_window.get_vadjustment()

            visible_rows_height = self.get_values_count()
            if visible_rows_height > self.max_visible_rows:
                visible_rows_height = self.max_visible_rows

            visible_rows_height *= self.row_height
            value = adjustment.get_value()

            # Max adjustment value
            max_value = adjustment.get_upper() - visible_rows_height
            # Set adjustment increment to 3 times the row height
            adjustment.set_step_increment(self.row_height * 3)

            if _next:
                # If number of values is less than max rows, no scroll
                if self.get_values_count() < self.max_visible_rows:
                    return
                value += adjustment.get_step_increment()
                if value > max_value:
                    value = max_value
            else:
                value -= adjustment.get_step_increment()
                if value < 0:
                    value = 0
            adjustment.set_value(value)
            return

        if path is None:
            path = self.get_selection_path()
            if not path:
                # These options require a selected path
                if set_entry or swap:
                    return
                # This is a regular scroll, not setting value in entry or swapping rows,
                # so we find a path value anyways
                path = (0, )
                cursor = self.treeview.get_cursor()
                if cursor is not None and cursor[0] is not None:
                    path = cursor[0]
                else:
                    # Since cursor is none, we won't advance the index
                    _next = None

        # If _next is None, we won't change the selection
        if _next is not None:
            # We move the selection either one up or down.
            # If we reach end of list, we wrap
            index = path[0] if path else 0
            index = index + 1 if _next else index - 1
            if index >= len(self.tree_store):
                index = 0
            elif index < 0:
                index = len(self.tree_store) - 1

            # We have the index for the new path
            new_path = (index)
            if swap:
                p1 = self.tree_store[path][0]
                p2 = self.tree_store[new_path][0]
                self.tree_store.swap(
                    self.tree_store.get_iter(path),
                    self.tree_store.get_iter(new_path),
                )
                self.emit('list-values-reordered', [p1, p2])
                self.emit('list-values-changed', self.get_values())
            path = new_path

        self.treeview.set_cursor(path)
        self.treeview.get_selection().select_path(path)
        if set_entry:
            self.set_entry_value(path)


class StoredValuesList(ValueList):

    def __init__(self):
        self.tree_store = self.builder.get_object('stored_values_tree_store')
        self.tree_column = self.builder.get_object('stored_values_treeview_column')
        self.rendererText = self.builder.get_object('stored_values_cellrenderertext')
        self.paths_without_trailing_path_sep = False

        # Add signal handlers
        self.signal_handlers['on_stored_values_treeview_mouse_button_press_event'] = \
            self.on_treeview_mouse_button_press_event

        self.signal_handlers['on_stored_values_treeview_key_press_event'] = \
            self.on_stored_values_treeview_key_press_event
        self.signal_handlers['on_stored_values_treeview_key_release_event'] = \
            self.on_stored_values_treeview_key_release_event

        self.signal_handlers['on_cellrenderertext_edited'] = self.on_cellrenderertext_edited

    def on_cellrenderertext_edited(self, cellrenderertext, path, new_text):
        """
        Callback on the 'edited' signal.

        Sets the new text in the path and disables editing on the renderer.
        """
        new_text = path_without_trailing_path_sep(new_text)
        self.tree_store[path][0] = new_text
        self.rendererText.set_property('editable', False)

    def on_edit_path(self, path, column):
        """
        Starts editing on the provided path

        :param path: the paths to edit
        :type  path: tuple
        :param column: the column to edit
        :type  column: gtk.TreeViewColumn

        """
        self.rendererText.set_property('editable', True)
        self.treeview.grab_focus()
        self.treeview.set_cursor(path, focus_column=column, start_editing=True)

    def on_treeview_mouse_button_press_event(self, treeview, event):
        """
        Shows popup on selected row when right clicking
        When left clicking twice, the row value is set for the text entry
        and the popup is closed.

        """
        # This is left click
        if event.button != 3:
            super(StoredValuesList, self).on_treeview_mouse_button_press_event(treeview, event, double_click=True)
            return False

        # This is right click, create popup menu for this row
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = treeview.get_path_at_pos(x, y)
        if pthinfo is not None:
            path, col, cellx, celly = pthinfo
            treeview.grab_focus()
            treeview.set_cursor(path, col, 0)

            self.path_list_popup = gtk.Menu()
            menuitem_edit = gtk.MenuItem('Edit path')
            self.path_list_popup.append(menuitem_edit)
            menuitem_remove = gtk.MenuItem('Remove path')
            self.path_list_popup.append(menuitem_remove)

            def on_edit_clicked(widget, path):
                self.on_edit_path(path, self.tree_column)

            def on_remove_clicked(widget, path):
                self.remove_selected_path()

            menuitem_edit.connect('activate', on_edit_clicked, path)
            menuitem_remove.connect('activate', on_remove_clicked, path)
            self.path_list_popup.popup(None, None, None, event.button, time, data=path)
            self.path_list_popup.show_all()

    def remove_selected_path(self):
        ValueList.remove_selected_path(self)
        # Resize popup
        PathChooserPopup.popup(self)

    def on_stored_values_treeview_key_press_event(self, widget, event):
        super(StoredValuesList, self).on_value_list_treeview_key_press_event(widget, event)
        # Prevent the default event handler to move the cursor in the list
        if key_is_up_or_down(event.keyval):
            return True

    def on_stored_values_treeview_key_release_event(self, widget, event):
        """
        Mimics Combobox behavior

        Escape or Alt+Up: Close
        Enter or Return : Select

        """
        keyval = event.keyval
        ctrl = event.get_state() & gdk.CONTROL_MASK

        # Edit selected row
        if (keyval in [keysyms.Left, keysyms.Right, keysyms.space]):
            path = self.get_selection_path()
            if path:
                self.on_edit_path(path, self.tree_column)
        elif key_is_up_or_down(keyval):
            # Swap the row value
            if event.get_state() & gdk.CONTROL_MASK:
                self.handle_list_scroll(
                    _next=key_is_down(keyval),
                    swap=True,
                )
            else:
                self.handle_list_scroll(_next=key_is_down(keyval))
        elif key_is_pgup_or_pgdown(event.keyval):
            # The cursor has been changed by the default key-press-event handler
            # so set the path of the cursor selected
            self.set_path_selected(self.treeview.get_cursor()[0])
        elif ctrl:
            # Handle key bindings for manipulating the list
            # Remove the selected entry
            if is_ascii_value(keyval, 'r'):
                self.remove_selected_path()
                return True
            # Add current value to saved list
            elif is_ascii_value(keyval, 's'):
                super(PathChooserComboBox, self).add_current_value_to_saved_list()  # pylint: disable=bad-super-call
                return True
            # Edit selected value
            elif is_ascii_value(keyval, 'e'):
                self.edit_selected_path()
                return True


class CompletionList(ValueList):

    def __init__(self):
        self.tree_store = self.builder.get_object('completion_tree_store')
        self.tree_column = self.builder.get_object('completion_treeview_column')
        self.rendererText = self.builder.get_object('completion_cellrenderertext')
        self.completion_scrolled_window = self.builder.get_object('completion_scrolled_window')
        self.signal_handlers['on_completion_treeview_key_press_event'] = \
            self.on_completion_treeview_key_press_event
        self.signal_handlers['on_completion_treeview_motion_notify_event'] = \
            self.on_completion_treeview_motion_notify_event

        # Add super class signal handler
        self.signal_handlers['on_completion_treeview_mouse_button_press_event'] = \
            super(CompletionList, self).on_treeview_mouse_button_press_event

    def reduce_values(self, prefix):
        """
        Reduce the values in the liststore to those starting with the prefix.

        :param prefix: the prefix to be matched
        :type  paths: string

        """
        values = self.get_values()
        matching_values = []
        for v in values:
            if v.startswith(prefix):
                matching_values.append(v)
        self.add_values(matching_values, clear=True)

    def on_completion_treeview_key_press_event(self, widget, event):
        ret = super(CompletionList, self).on_value_list_treeview_key_press_event(widget, event)
        if ret:
            return ret
        keyval = event.keyval
        ctrl = event.get_state() & gdk.CONTROL_MASK
        if key_is_up_or_down(keyval):
            self.handle_list_scroll(_next=key_is_down(keyval))
            return True
        elif ctrl:
            # Set show/hide hidden files
            if is_ascii_value(keyval, 'h'):
                self.path_entry.set_show_hidden_files(not self.path_entry.get_show_hidden_files(), do_completion=True)
                return True

    def on_completion_treeview_motion_notify_event(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y

        path = self.treeview.get_path_at_pos(int(x), int(y))
        if path:
            self.handle_list_scroll(path=path[0], _next=None)


class PathChooserPopup(object):
    """This creates the popop window for the ComboEntry."""
    def __init__(self, min_visible_rows, max_visible_rows, popup_alignment_widget):
        self.min_visible_rows = min_visible_rows
        # Maximum number of rows to display without scrolling
        self.set_max_popup_rows(max_visible_rows)
        self.popup_window.realize()
        self.alignment_widget = popup_alignment_widget
        self.popup_buttonbox = None  # If set, the height of this widget is the minimum height

    def popup(self):
        """Make the popup visible."""
        # Entry is not yet visible
        if not self.path_entry.get_realized():
            return
        self.set_window_position_and_size()

    def popdown(self):
        if not self.is_popped_up():
            return
        if not self.path_entry.get_realized():
            return
        self.popup_window.grab_remove()
        self.popup_window.hide_all()

    def is_popped_up(self):
        """Check if window is popped up.

        Returns:
            bool: True if popped up, False otherwise.

        """
        return self.popup_window.get_mapped()

    def set_window_position_and_size(self):
        if len(self.tree_store) < self.min_visible_rows:
            return False
        x, y, width, height = self.get_position()
        self.popup_window.set_size_request(width, height)
        self.popup_window.resize(width, height)
        self.popup_window.move(x, y)
        self.popup_window.show_all()

    def get_position(self):
        """
        Returns the size of the popup window and the coordinates on the screen.

        """

        # Necessary for the first call, to make treeview.size_request give sensible values
        # self.popup_window.realize()
        self.treeview.realize()

        # We start with the coordinates of the parent window
        x, y = self.path_entry.get_window().get_origin()

        # Add the position of the alignment_widget relative to the parent window.
        x += self.alignment_widget.get_allocation().x
        y += self.alignment_widget.get_allocation().y

        height_extra = 8
        buttonbox_width = 0
        height = self.popup_window.size_request()[1]
        width = self.popup_window.size_request()[0]

        if self.popup_buttonbox:
            buttonbox_height = max(self.popup_buttonbox.size_request()[1], self.popup_buttonbox.get_allocation().height)
            buttonbox_width = max(self.popup_buttonbox.size_request()[0], self.popup_buttonbox.get_allocation().width)
            treeview_width = self.treeview.size_request()[0]
            # After removing an element from the tree store, self.treeview.size_request()[0]
            # returns -1 for some reason, so the requested width cannot be used until the treeview
            # has been displayed once.
            if treeview_width != -1:
                width = treeview_width + buttonbox_width
            # The list is empty, so ignore initial popup width request
            # Will be set to the minimum width next
            elif len(self.tree_store) == 0:
                width = 0

        if width < self.alignment_widget.get_allocation().width:
            width = self.alignment_widget.get_allocation().width

        # 10 is extra spacing
        content_width = self.treeview.size_request()[0] + buttonbox_width + 10

        # Adjust height according to number of list items
        if len(self.tree_store) > 0 and self.max_visible_rows > 0:
            # The height for one row in the list
            self.row_height = self.treeview.size_request()[1] // len(self.tree_store)
            # Set height to number of rows
            height = len(self.tree_store) * self.row_height + height_extra
            # Adjust the height according to the max number of rows
            max_height = self.row_height * self.max_visible_rows
            # Restrict height to max_visible_rows
            if max_height + height_extra < height:
                height = max_height
                height += height_extra
                # Increase width because of vertical scrollbar
                content_width += 15

        if self.popup_buttonbox:
            # Minimum height is the height of the button box
            if height < buttonbox_height + height_extra:
                height = buttonbox_height + height_extra

        if content_width > width:
            width = content_width

        screen = self.path_entry.get_screen()
        monitor_num = screen.get_monitor_at_window(self.path_entry.get_window())
        monitor = screen.get_monitor_geometry(monitor_num)

        if x < monitor.x:
            x = monitor.x
        elif x + width > monitor.x + monitor.width:
            x = monitor.x + monitor.width - width

        # Set the position
        if y + self.path_entry.get_allocation().height + height <= monitor.y + monitor.height:
            y += self.path_entry.get_allocation().height
        # Not enough space downwards on the screen
        elif y - height >= monitor.y:
            y -= height
        elif (
            monitor.y + monitor.height - (y + self.path_entry.get_allocation().height) >
            y - monitor.y
        ):
            y += self.path_entry.get_allocation().height
            height = monitor.y + monitor.height - y
        else:
            height = y - monitor.y
            y = monitor.y

        return x, y, width, height

    def popup_grab_window(self):
        activate_time = 0
        if gdk.pointer_grab(
            self.popup_window.get_window(), True,
            (
                gdk.BUTTON_PRESS_MASK |
                gdk.BUTTON_RELEASE_MASK |
                gdk.POINTER_MOTION_MASK
            ),
            None, None, activate_time,
        ) == 0:
            if gdk.keyboard_grab(self.popup_window.get_window(), True, activate_time) == 0:
                return True
            else:
                self.popup_window.get_window().get_display().pointer_ungrab(activate_time)
                return False
        return False

    def set_entry_value(self, path, popdown=False):
        """

        Sets the text of the entry to the value in path
        """
        self.path_entry.set_text(self.tree_store[path][0], set_file_chooser_folder=True, trigger_event=True)
        if popdown:
            self.popdown()

    def set_max_popup_rows(self, rows):
        try:
            int(rows)
        except Exception:
            self.max_visible_rows = 20
            return
        self.max_visible_rows = rows

    def get_max_popup_rows(self):
        return self.max_visible_rows

#################
# Callbacks
#################

    def on_popup_window_button_press_event(self, window, event):
        # If we're clicking outside of the window close the popup
        hide = False
        # Also if the intersection of self and the event is empty, hide
        # the path_list
        if (tuple(self.popup_window.get_allocation().intersect(
                gdk.Rectangle(
                    x=int(event.x), y=int(event.y),
                    width=1, height=1,
                ),
        )) == (0, 0, 0, 0)):
            hide = True
        # Toplevel is the window that received the event, and parent is the
        # path_list window. If they are not the same, means the popup should
        # be hidden. This is necessary for when the event happens on another
        # widget
        toplevel = event.window.get_toplevel()
        parent = self.popup_window.get_window()

        if toplevel != parent:
            hide = True
        if hide:
            self.popdown()


class StoredValuesPopup(StoredValuesList, PathChooserPopup):
    """

    The stored values popup

    """
    def __init__(self, builder, path_entry, max_visible_rows, popup_alignment_widget):
        self.builder = builder
        self.treeview = self.builder.get_object('stored_values_treeview')
        self.popup_window = self.builder.get_object('stored_values_popup_window')
        self.button_default = self.builder.get_object('button_default')
        self.path_entry = path_entry
        self.text_entry = path_entry.text_entry

        self.signal_handlers = {}
        PathChooserPopup.__init__(self, 0, max_visible_rows, popup_alignment_widget)
        StoredValuesList.__init__(self)

        self.popup_buttonbox = self.builder.get_object('buttonbox')

        # Add signal handlers
        self.signal_handlers['on_buttonbox_key_press_event'] = self.on_buttonbox_key_press_event
        self.signal_handlers['on_stored_values_treeview_scroll_event'] = self.on_scroll_event
        self.signal_handlers['on_button_toggle_dropdown_scroll_event'] = self.on_scroll_event
        self.signal_handlers['on_entry_text_scroll_event'] = self.on_scroll_event
        self.signal_handlers['on_stored_values_popup_window_focus_out_event'] = \
            self.on_stored_values_popup_window_focus_out_event
        # For when clicking outside the popup
        self.signal_handlers['on_stored_values_popup_window_button_press_event'] = \
            self.on_popup_window_button_press_event

        # Buttons for manipulating the list
        self.signal_handlers['on_button_add_clicked'] = self.on_button_add_clicked
        self.signal_handlers['on_button_edit_clicked'] = self.on_button_edit_clicked
        self.signal_handlers['on_button_remove_clicked'] = self.on_button_remove_clicked
        self.signal_handlers['on_button_up_clicked'] = self.on_button_up_clicked
        self.signal_handlers['on_button_down_clicked'] = self.on_button_down_clicked
        self.signal_handlers['on_button_default_clicked'] = self.on_button_default_clicked
        self.signal_handlers['on_button_properties_clicked'] = self.path_entry._on_button_properties_clicked

    def popup(self):
        """
        Makes the popup visible.

        """
        # Calling super popup
        PathChooserPopup.popup(self)
        self.popup_window.grab_focus()

        if not self.treeview.has_focus():
            self.treeview.grab_focus()
        if not self.popup_grab_window():
            self.popup_window.hide()
            return

        self.popup_window.grab_add()
        # Set value selected if it exists
        self.set_selected_value(path_without_trailing_path_sep(self.path_entry.get_text()))

#################
# Callbacks
#################

    def on_stored_values_popup_window_focus_out_event(self, entry, event):
        """
        Popup sometimes loses the focus to the text entry, e.g. when right click
        shows a popup menu on a row. This regains the focus.
        """
        self.popup_grab_window()
        return True

    def on_scroll_event(self, widget, event):
        """
        Handles scroll events from text entry, toggle button and treeview

        """
        swap = event.get_state() & gdk.CONTROL_MASK
        scroll_window = event.get_state() & gdk.SHIFT_MASK
        self.handle_list_scroll(
            _next=event.direction == gdk.SCROLL_DOWN,
            set_entry=widget != self.treeview, swap=swap, scroll_window=scroll_window,
        )
        return True

    def on_buttonbox_key_press_event(self, widget, event):
        """
        Handles when Escape or ALT+arrow up is pressed when focus
        is on any of the buttons in the popup
        """
        keyval = event.keyval
        state = event.get_state() & gtk.accelerator_get_default_mod_mask()
        if keyval == keysyms.Escape or (key_is_up(keyval) and state == gdk.MOD1_MASK):
            self.popdown()
            return True
        return False

# --------------------------------------------------
# Funcs and callbacks on the buttons to manipulate the list
# --------------------------------------------------
    def add_current_value_to_saved_list(self):
        text = self.path_entry.get_text()
        text = path_without_trailing_path_sep(text)
        values = self.get_values()
        if text in values:
            # Make the matching value selected
            self.set_selected_value(text)
            self.handle_list_scroll()
            return True
        self.add_values([text], scroll_to_row=True, append=False, emit_signal=True)

    def edit_selected_path(self):
        path = self.get_selection_path()
        if path:
            self.on_edit_path(path, self.tree_column)

    def on_button_add_clicked(self, widget):
        self.add_current_value_to_saved_list()
        self.popup()

    def on_button_edit_clicked(self, widget):
        self.edit_selected_path()

    def on_button_remove_clicked(self, widget):
        self.remove_selected_path()
        return True

    def on_button_up_clicked(self, widget):
        self.handle_list_scroll(_next=False, swap=True)

    def on_button_down_clicked(self, widget):
        self.handle_list_scroll(_next=True, swap=True)

    def on_button_default_clicked(self, widget):
        if self.default_text:
            self.set_text(self.default_text, trigger_event=True)


class PathCompletionPopup(CompletionList, PathChooserPopup):
    """

    The auto completion popup

    """
    def __init__(self, builder, path_entry, max_visible_rows):
        self.builder = builder
        self.treeview = self.builder.get_object('completion_treeview')
        self.popup_window = self.builder.get_object('completion_popup_window')
        self.path_entry = path_entry
        self.text_entry = path_entry.text_entry
        self.show_hidden_files = False

        self.signal_handlers = {}
        PathChooserPopup.__init__(self, 1, max_visible_rows, self.text_entry)
        CompletionList.__init__(self)

        # Add signal handlers
        self.signal_handlers['on_completion_treeview_scroll_event'] = self.on_scroll_event
        self.signal_handlers['on_completion_popup_window_focus_out_event'] = \
            self.on_completion_popup_window_focus_out_event

        # For when clicking outside the popup
        self.signal_handlers['on_completion_popup_window_button_press_event'] = \
            self.on_popup_window_button_press_event

    def popup(self):
        """
        Makes the popup visible.

        """
        PathChooserPopup.popup(self)
        self.popup_window.grab_focus()

        if not self.treeview.has_focus():
            self.treeview.grab_focus()

        if not self.popup_grab_window():
            self.popup_window.hide()
            return

        self.popup_window.grab_add()
        self.text_entry.grab_focus()
        self.text_entry.set_position(len(self.path_entry.text_entry.get_text()))
        self.set_selected_value(path_without_trailing_path_sep(self.path_entry.get_text()), select_first=True)

#################
# Callbacks
#################

    def on_completion_popup_window_focus_out_event(self, entry, event):
        """
        Popup sometimes loses the focus to the text entry, e.g. when right click
        shows a popup menu on a row. This regains the focus.
        """
        self.popup_grab_window()
        return True

    def on_scroll_event(self, widget, event):
        """
        Handles scroll events from the treeview

        """
        x, y, state = event.window.get_pointer()
        self.handle_list_scroll(
            _next=event.direction == gdk.SCROLL_DOWN,
            set_entry=widget != self.treeview, scroll_window=True,
        )
        path = self.treeview.get_path_at_pos(int(x), int(y))
        if path:
            self.handle_list_scroll(path=path[0], _next=None)
        return True


class PathAutoCompleter(object):

    def __init__(self, builder, path_entry, max_visible_rows):
        self.completion_popup = PathCompletionPopup(builder, path_entry, max_visible_rows)
        self.path_entry = path_entry
        self.dirs_cache = {}
        self.use_popup = False
        self.auto_complete_enabled = True
        self.signal_handlers = self.completion_popup.signal_handlers

        self.signal_handlers['on_completion_popup_window_key_press_event'] = \
            self.on_completion_popup_window_key_press_event
        self.signal_handlers['on_entry_text_delete_text'] = self.on_entry_text_delete_text
        self.signal_handlers['on_entry_text_insert_text'] = self.on_entry_text_insert_text
        self.accelerator_string = gtk.accelerator_name(keysyms.Tab, 0)

    def on_entry_text_insert_text(self, entry, new_text, new_text_length, position):
        if self.path_entry.get_realized():
            cur_text = self.path_entry.get_text()
            pos = entry.get_position()
            new_complete_text = cur_text[:pos] + new_text + cur_text[pos:]
            # Remove all values from the list that do not start with new_complete_text
            self.completion_popup.reduce_values(new_complete_text)
            self.completion_popup.set_selected_value(new_complete_text, select_first=True)
            if self.completion_popup.is_popped_up():
                self.completion_popup.set_window_position_and_size()

    def on_entry_text_delete_text(self, entry, start, end):
        """
        Do completion when characters are removed

        """
        if self.completion_popup.is_popped_up():
            cur_text = self.path_entry.get_text()
            new_complete_text = cur_text[:start] + cur_text[end:]
            self.do_completion(value=new_complete_text, forward_completion=False)

    def set_use_popup(self, use):
        self.use_popup = use

    def on_completion_popup_window_key_press_event(self, entry, event):
        """
        Handles key pressed events on the auto-completion popup window
        """
        # If on_completion_treeview_key_press_event handles the event, do nothing
        ret = self.completion_popup.on_completion_treeview_key_press_event(entry, event)
        if ret:
            return ret
        keyval = event.keyval
        state = event.get_state() & gtk.accelerator_get_default_mod_mask()
        if self.is_auto_completion_accelerator(keyval, state)\
                and self.auto_complete_enabled:
            values_count = self.completion_popup.get_values_count()
            if values_count == 1:
                self.do_completion()
            else:
                self.completion_popup.handle_list_scroll(_next=True)
            return True
        self.path_entry.text_entry.emit('key-press-event', event)

    def is_auto_completion_accelerator(self, keyval, state):
        return gtk.accelerator_name(keyval, state.numerator) == self.accelerator_string

    def do_completion(self, value=None, forward_completion=True):
        if not value:
            value = self.path_entry.get_text()
        self.path_entry.text_entry.set_position(len(value))
        opts = {}
        opts['show_hidden_files'] = self.completion_popup.show_hidden_files
        opts['completion_text'] = value
        opts['forward_completion'] = forward_completion
        self._start_completion(opts)

    def _start_completion(self, args):
        args = get_completion_paths(args)
        self._end_completion(args)

    def _end_completion(self, args):
        value = args['completion_text']
        paths = args['paths']

        if args['forward_completion']:
            common_prefix = os.path.commonprefix(paths)
            if len(common_prefix) > len(value):
                self.path_entry.set_text(common_prefix, set_file_chooser_folder=True, trigger_event=True)

        self.path_entry.text_entry.set_position(len(self.path_entry.get_text()))
        self.completion_popup.set_values(paths, preserve_selection=True)

        if self.use_popup and len(paths) > 1:
            self.completion_popup.popup()
        elif self.completion_popup.is_popped_up() and args['forward_completion']:
            self.completion_popup.popdown()


class PathChooserComboBox(gtk.HBox, StoredValuesPopup, GObject):

    __gsignals__ = {
        b'list-value-added': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'list-value-removed': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'list-values-reordered': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'list-values-changed': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'auto-complete-enabled-toggled': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'show-filechooser-toggled': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'show-path-entry-toggled': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'show-folder-name-on-button': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'show-hidden-files-toggled': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'accelerator-set': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'max-rows-changed': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
        b'text-changed': (SIGNAL_RUN_FIRST, TYPE_NONE, (object, )),
    }

    def __init__(self, max_visible_rows=20, auto_complete=True, use_completer_popup=True):
        gtk.HBox.__init__(self)
        GObject.__init__(self)
        self._stored_values_popping_down = False
        self.filechooser_visible = True
        self.filechooser_enabled = True
        self.path_entry_visible = True
        self.properties_enabled = True
        self.show_folder_name_on_button = False
        self.setting_accelerator_key = False
        self.builder = gtk.Builder()
        self.popup_buttonbox = self.builder.get_object('buttonbox')
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'path_combo_chooser.ui'),
        ))
        self.button_toggle = self.builder.get_object('button_toggle_dropdown')
        self.text_entry = self.builder.get_object('entry_text')
        self.open_filechooser_dialog_button = self.builder.get_object('button_open_dialog')
        self.filechooser_button = self.open_filechooser_dialog_button
        self.filechooserdialog = self.builder.get_object('filechooserdialog')
        self.filechooserdialog.set_transient_for(component.get('MainWindow').window)
        self.folder_name_label = self.builder.get_object('folder_name_label')
        self.default_text = None
        self.button_properties = self.builder.get_object('button_properties')
        self.combo_hbox = self.builder.get_object('entry_combobox_hbox')
        # Change the parent of the hbox from the glade Window to this hbox.
        self.combo_hbox.reparent(self)
        StoredValuesPopup.__init__(self, self.builder, self, max_visible_rows, self.combo_hbox)

        self.auto_completer = PathAutoCompleter(self.builder, self, max_visible_rows)
        self.auto_completer.set_use_popup(use_completer_popup)
        self.auto_completer.auto_complete_enabled = auto_complete
        self._setup_config_dialog()

        signal_handlers = {
            'on_button_toggle_dropdown_toggled': self._on_button_toggle_dropdown_toggled,
            'on_entry_text_key_press_event': self._on_entry_text_key_press_event,
            'on_stored_values_popup_window_hide': self._on_stored_values_popup_window_hide,
            'on_button_toggle_dropdown_button_press_event': self._on_button_toggle_dropdown_button_press_event,
            'on_entry_combobox_hbox_realize': self._on_entry_combobox_hbox_realize,
            'on_button_open_dialog_clicked': self._on_button_open_dialog_clicked,
            'on_entry_text_focus_out_event': self._on_entry_text_focus_out_event,
            'on_entry_text_changed': self.on_entry_text_changed,
        }
        signal_handlers.update(self.signal_handlers)
        signal_handlers.update(self.auto_completer.signal_handlers)
        signal_handlers.update(self.config_dialog_signal_handlers)
        self.builder.connect_signals(signal_handlers)

    def get_text(self):
        """
        Get the current text in the Entry
        """
        return self.text_entry.get_text()

    def set_text(self, text, set_file_chooser_folder=True, cursor_end=True, default_text=False, trigger_event=False):
        """
        Set the text for the entry.

        """
        old_text = self.text_entry.get_text()
        # We must block the "delete-text" signal to avoid the signal handler being called
        self.text_entry.handler_block_by_func(self.auto_completer.on_entry_text_delete_text)
        self.text_entry.set_text(text)
        self.text_entry.handler_unblock_by_func(self.auto_completer.on_entry_text_delete_text)

        self.text_entry.select_region(0, 0)
        self.text_entry.set_position(len(text) if cursor_end else 0)
        self.set_selected_value(text, select_first=True)
        self.combo_hbox.set_tooltip_text(text)
        if default_text:
            self.default_text = text
            self.button_default.set_tooltip_text('Restore the default value in the text entry:\n%s' % self.default_text)
            self.button_default.set_sensitive(True)
        # Set text for the filechooser dialog button
        folder_name = ''
        if self.show_folder_name_on_button or not self.path_entry_visible:
            folder_name = path_without_trailing_path_sep(text)
            if folder_name is not '/' and os.path.basename(folder_name):
                folder_name = os.path.basename(folder_name)
        self.folder_name_label.set_text(folder_name)
        # Only trigger event if text has changed
        if old_text != text and trigger_event:
            self.on_entry_text_changed(self.text_entry)

    def set_sensitive(self, sensitive):
        """
        Set the path chooser widgets sensitive

        :param sensitive: if the widget should be sensitive
        :type  sensitive: bool

        """
        self.text_entry.set_sensitive(sensitive)
        self.filechooser_button.set_sensitive(sensitive)
        self.button_toggle.set_sensitive(sensitive)

    def get_accelerator_string(self):
        return self.auto_completer.accelerator_string

    def set_accelerator_string(self, accelerator):
        """
        Set the accelerator string to trigger auto-completion
        """
        if accelerator is None:
            return
        try:
            # Verify that the accelerator can be parsed
            keyval, mask = gtk.accelerator_parse(self.auto_completer.accelerator_string)
            self.auto_completer.accelerator_string = accelerator
        except TypeError as ex:
            raise TypeError('TypeError when setting accelerator string: %s' % ex)

    def get_auto_complete_enabled(self):
        return self.auto_completer.auto_complete_enabled

    def set_auto_complete_enabled(self, enable):
        if not isinstance(enable, bool):
            return
        self.auto_completer.auto_complete_enabled = enable

    def get_show_folder_name_on_button(self):
        return self.show_folder_name_on_button

    def set_show_folder_name_on_button(self, show):
        if not isinstance(show, bool):
            return
        self.show_folder_name_on_button = show
        self._set_path_entry_filechooser_widths()

    def get_filechooser_button_enabled(self):
        return self.filechooser_enabled

    def set_filechooser_button_enabled(self, enable):
        """
        Enable/disable the filechooser button.

        By setting filechooser disabled, in will not be possible
        to change the settings in the properties.
        """
        if not isinstance(enable, bool):
            return
        self.filechooser_enabled = enable
        if not enable:
            self.set_filechooser_button_visible(False, update=False)

    def get_filechooser_button_visible(self):
        return self.filechooser_visible

    def set_filechooser_button_visible(self, visible, update=True):
        """
        Set file chooser button entry visible
        """
        if not isinstance(visible, bool):
            return
        if update:
            self.filechooser_visible = visible
        if visible and not self.filechooser_enabled:
            return
        if visible:
            self.filechooser_button.show()
        else:
            self.filechooser_button.hide()
        # Update width properties
        self._set_path_entry_filechooser_widths()

    def get_path_entry_visible(self):
        return self.path_entry_visible

    def set_path_entry_visible(self, visible):
        """
        Set the path entry visible
        """
        if not isinstance(visible, bool):
            return
        self.path_entry_visible = visible
        if visible:
            self.text_entry.show()
        else:
            self.text_entry.hide()
        self._set_path_entry_filechooser_widths()

    def get_show_hidden_files(self):
        return self.auto_completer.completion_popup.show_hidden_files

    def set_show_hidden_files(self, show, do_completion=False, emit_event=False):
        """
        Enable/disable showing hidden files on path completion
        """
        if not isinstance(show, bool):
            return
        self.auto_completer.completion_popup.show_hidden_files = show
        if do_completion:
            self.auto_completer.do_completion()
        if emit_event:
            self.emit('show-hidden-files-toggled', show)

    def set_enable_properties(self, enable):
        """
        Enable/disable the config properties
        """
        if not isinstance(enable, bool):
            return
        self.properties_enabled = enable
        if self.properties_enabled:
            self.popup_buttonbox.add(self.button_properties)
        else:
            self.popup_buttonbox.remove(self.button_properties)

    def set_auto_completer_func(self, func):
        """
        Set the function to be called when the auto completion
        accelerator is triggered.
        """
        self.auto_completer._start_completion = func

    def complete(self, args):
        """
        Perform the auto completion with the provided paths
        """
        self.auto_completer._end_completion(args)

##############
# Callbacks and internal functions
##############

    def on_entry_text_changed(self, entry):
        self.emit('text-changed', self.get_text())

    def _on_entry_text_focus_out_event(self, widget, event):
        # Update text on the button label
        self.set_text(self.get_text())

    def _set_path_entry_filechooser_widths(self):
        if self.path_entry_visible:
            self.combo_hbox.set_child_packing(self.filechooser_button, 0, 0, 0, gtk.PACK_START)
            width, height = self.folder_name_label.get_size_request()
            width = 120
            if not self.show_folder_name_on_button:
                width = 0
            self.folder_name_label.set_size_request(width, height)
            self.combo_hbox.set_child_packing(self.filechooser_button, 0, 0, 0, gtk.PACK_START)
        else:
            self.combo_hbox.set_child_packing(self.filechooser_button, 1, 1, 0, gtk.PACK_START)
            self.folder_name_label.set_size_request(-1, -1)
        # Update text on the button label
        self.set_text(self.get_text())

    def _on_entry_combobox_hbox_realize(self, widget):
        """ Must do this when the widget is realized """
        self.set_filechooser_button_visible(self.filechooser_visible)
        self.set_path_entry_visible(self.path_entry_visible)

    def _on_button_open_dialog_clicked(self, widget):
        dialog = self.filechooserdialog
        dialog.set_current_folder(self.get_text())
        response_id = dialog.run()

        if response_id == 0:
            text = self.filechooserdialog.get_filename()
            self.set_text(text, trigger_event=True)
        dialog.hide()

    def _on_entry_text_key_press_event(self, widget, event):
        """
        Listen to key events on the entry widget.

        Arrow up/down will change the value of the entry according to the
        current selection in the list.
        Enter will show the popup.

        Return True whenever we want no other event listeners to be called.

        """
        keyval = event.keyval
        state = event.get_state() & gtk.accelerator_get_default_mod_mask()
        ctrl = event.get_state() & gdk.CONTROL_MASK

        # Select new row with arrow up/down is pressed
        if key_is_up_or_down(keyval):
            self.handle_list_scroll(
                _next=key_is_down(keyval),
                set_entry=True,
            )
            return True
        elif self.auto_completer.is_auto_completion_accelerator(keyval, state):
            if self.auto_completer.auto_complete_enabled:
                self.auto_completer.do_completion()
                return True
        # Show popup when Enter is pressed
        elif key_is_enter(keyval):
            # This sets the toggle active which results in
            # on_button_toggle_dropdown_toggled being called which initiates the popup
            self.button_toggle.set_active(True)
            return True
        elif ctrl:
            # Swap the show hidden files value on CTRL-h
            if is_ascii_value(keyval, 'h'):
                # Set show/hide hidden files
                self.set_show_hidden_files(not self.get_show_hidden_files(), emit_event=True)
                return True
            elif is_ascii_value(keyval, 's'):
                super(PathChooserComboBox, self).add_current_value_to_saved_list()
                return True
            elif is_ascii_value(keyval, 'd'):
                # Set the default value in the text entry
                self.set_text(self.default_text, trigger_event=True)
                return True
        return False

    def _on_button_toggle_dropdown_toggled(self, button):
        """
        Shows the popup when clicking the toggle button.
        """
        if self._stored_values_popping_down:
            return
        self.popup()

    def _on_stored_values_popup_window_hide(self, popup):
        """Make sure the button toggle is removed when popup is closed"""
        self._stored_values_popping_down = True
        self.button_toggle.set_active(False)
        self._stored_values_popping_down = False

##############
# Config dialog
##############

    def _on_button_toggle_dropdown_button_press_event(self, widget, event):
        """Show config when right clicking dropdown toggle button"""
        if not self.properties_enabled:
            return False
        # This is right click
        if event.button == 3:
            self._on_button_properties_clicked(widget)
            return True

    def _on_button_properties_clicked(self, widget):
        self.popdown()
        self.enable_completion.set_active(self.get_auto_complete_enabled())
        # Set the value of the label to the current accelerator
        keyval, mask = gtk.accelerator_parse(self.auto_completer.accelerator_string)
        self.accelerator_label.set_text(gtk.accelerator_get_label(keyval, mask))
        self.visible_rows.set_value(self.get_max_popup_rows())
        self.show_filechooser_checkbutton.set_active(self.get_filechooser_button_visible())
        self.show_path_entry_checkbutton.set_active(self.path_entry_visible)
        self.show_hidden_files_checkbutton.set_active(self.get_show_hidden_files())
        self.show_folder_name_on_button_checkbutton.set_active(self.get_show_folder_name_on_button())
        self._set_properties_widgets_sensitive(True)
        self.config_dialog.show_all()

    def _set_properties_widgets_sensitive(self, val):
        self.enable_completion.set_sensitive(val)
        self.config_short_cuts_frame.set_sensitive(val)
        self.config_general_frame.set_sensitive(val)
        self.show_hidden_files_checkbutton.set_sensitive(val)

    def _setup_config_dialog(self):
        self.config_dialog = self.builder.get_object('completion_config_dialog')
        self.enable_completion = self.builder.get_object('enable_auto_completion_checkbutton')
        self.show_filechooser_checkbutton = self.builder.get_object('show_filechooser_checkbutton')
        self.show_path_entry_checkbutton = self.builder.get_object('show_path_entry_checkbutton')
        set_key_button = self.builder.get_object('set_completion_accelerator_button')
        default_set_accelerator_tooltip = set_key_button.get_tooltip_text()
        self.config_short_cuts_frame = self.builder.get_object('config_short_cuts_frame')
        self.config_general_frame = self.builder.get_object('config_general_frame')
        self.accelerator_label = self.builder.get_object('completion_accelerator_label')
        self.visible_rows = self.builder.get_object('visible_rows_spinbutton')
        self.visible_rows_label = self.builder.get_object('visible_rows_label')
        self.show_hidden_files_checkbutton = self.builder.get_object('show_hidden_files_checkbutton')
        self.show_folder_name_on_button_checkbutton = self.builder.get_object('show_folder_name_on_button_checkbutton')
        self.config_dialog.set_transient_for(component.get('MainWindow').window)

        def on_close(widget, event=None):
            if not self.setting_accelerator_key:
                self.config_dialog.hide()
            else:
                stop_setting_accelerator()
            return True

        def on_enable_completion_toggled(widget):
            self.set_auto_complete_enabled(self.enable_completion.get_active())
            self.emit('auto-complete-enabled-toggled', self.enable_completion.get_active())

        def on_show_filechooser_toggled(widget):
            self.set_filechooser_button_visible(self.show_filechooser_checkbutton.get_active())
            self.emit('show-filechooser-toggled', self.show_filechooser_checkbutton.get_active())
            self.show_folder_name_on_button_checkbutton.set_sensitive(self.show_path_entry_checkbutton.get_active() and
                                                                      self.show_filechooser_checkbutton.get_active())
            if not self.filechooser_visible and not self.path_entry_visible:
                self.show_path_entry_checkbutton.set_active(True)
                on_show_path_entry_toggled(None)

        def on_show_path_entry_toggled(widget):
            self.set_path_entry_visible(self.show_path_entry_checkbutton.get_active())
            self.emit('show-path-entry-toggled', self.show_path_entry_checkbutton.get_active())
            self.show_folder_name_on_button_checkbutton.set_sensitive(self.show_path_entry_checkbutton.get_active() and
                                                                      self.show_filechooser_checkbutton.get_active())
            if not self.filechooser_visible and not self.path_entry_visible:
                self.show_filechooser_checkbutton.set_active(True)
                on_show_filechooser_toggled(None)

        def on_show_folder_name_on_button(widget):
            self.set_show_folder_name_on_button(self.show_folder_name_on_button_checkbutton.get_active())
            self._set_path_entry_filechooser_widths()
            self.emit('show-folder-name-on-button', self.show_folder_name_on_button_checkbutton.get_active())

        def on_show_hidden_files_toggled(widget):
            self.set_show_hidden_files(self.show_hidden_files_checkbutton.get_active(), emit_event=True)

        def on_max_rows_changed(widget):
            self.set_max_popup_rows(self.visible_rows.get_value_as_int())
            self.emit('max-rows-changed', self.visible_rows.get_value_as_int())

        def set_accelerator(widget):
            self.setting_accelerator_key = True
            set_key_button.set_tooltip_text('Press the accelerator keys for triggering auto-completion')
            self._set_properties_widgets_sensitive(False)
            return True

        def stop_setting_accelerator():
            self.setting_accelerator_key = False
            self._set_properties_widgets_sensitive(True)
            set_key_button.set_active(False)
            # Restore default tooltip
            set_key_button.set_tooltip_text(default_set_accelerator_tooltip)

        def on_completion_config_dialog_key_release_event(widget, event):
            # We are listening for a new key
            if set_key_button.get_active():
                state = event.get_state() & gtk.accelerator_get_default_mod_mask()
                accelerator_mask = state.numerator
                # If e.g. only CTRL key is pressed.
                if not gtk.accelerator_valid(event.keyval, accelerator_mask):
                    accelerator_mask = 0
                self.auto_completer.accelerator_string = gtk.accelerator_name(event.keyval, accelerator_mask)
                self.accelerator_label.set_text(gtk.accelerator_get_label(event.keyval, accelerator_mask))
                self.emit('accelerator-set', self.auto_completer.accelerator_string)
                stop_setting_accelerator()
                return True
            else:
                keyval = event.keyval
                ctrl = event.get_state() & gdk.CONTROL_MASK
                if ctrl:
                    # Set show/hide hidden files
                    if is_ascii_value(keyval, 'h'):
                        self.show_hidden_files_checkbutton.set_active(not self.get_show_hidden_files())
                        return True

        def on_set_completion_accelerator_button_clicked(widget):
            if not set_key_button.get_active():
                stop_setting_accelerator()
                return True

        self.config_dialog_signal_handlers = {
            'on_enable_auto_completion_checkbutton_toggled': on_enable_completion_toggled,
            'on_show_filechooser_checkbutton_toggled': on_show_filechooser_toggled,
            'on_show_path_entry_checkbutton_toggled': on_show_path_entry_toggled,
            'on_show_folder_name_on_button_checkbutton_toggled': on_show_folder_name_on_button,
            'on_config_dialog_button_close_clicked': on_close,
            'on_visible_rows_spinbutton_value_changed': on_max_rows_changed,
            'on_completion_config_dialog_delete_event': on_close,
            'on_set_completion_accelerator_button_pressed': set_accelerator,
            'on_completion_config_dialog_key_release_event': on_completion_config_dialog_key_release_event,
            'on_set_completion_accelerator_button_clicked': on_set_completion_accelerator_button_clicked,
            'on_show_hidden_files_checkbutton_toggled': on_show_hidden_files_toggled,
        }


type_register(PathChooserComboBox)


if __name__ == '__main__':
    import sys
    w = gtk.Window()
    w.set_position(gtk.WIN_POS_CENTER)
    w.set_size_request(600, -1)
    w.set_title('ComboEntry example')
    w.connect('delete-event', gtk.main_quit)

    box1 = gtk.VBox(gtk.FALSE, 0)

    def get_resource2(filename):
        return '%s/glade/%s' % (os.path.abspath(os.path.dirname(sys.argv[0])), filename)

    # Override get_resource which fetches from deluge install
    # get_resource = get_resource2

    entry1 = PathChooserComboBox(max_visible_rows=15)
    entry2 = PathChooserComboBox()

    box1.add(entry1)
    box1.add(entry2)

    test_paths = [
        '/home/bro/Downloads',
        '/media/Movies-HD',
        '/media/torrent/in',
        '/media/Live-show/Misc',
        '/media/Live-show/Consert',
        '/media/Series/1/',
        '/media/Series/2',
        '/media/Series/17',
        '/media/Series/18',
        '/media/Series/19',
    ]

    entry1.add_values(test_paths)
    entry1.set_text('/home/bro/', default_text=True)
    entry2.set_text(
        '/home/bro/programmer/deluge/deluge-yarss-plugin/build/lib/yarss2/include/bs4/tests/',
        cursor_end=False,
    )

    entry2.set_filechooser_button_visible(False)
    # entry2.set_enable_properties(False)
    entry2.set_filechooser_button_enabled(False)

    def list_value_added_event(widget, values):
        print('Current list values:', widget.get_values())

    entry1.connect('list-value-added', list_value_added_event)
    entry2.connect('list-value-added', list_value_added_event)
    w.add(box1)
    w.show_all()
    gtk.main()
