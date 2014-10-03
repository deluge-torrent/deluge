# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 bendikro <bro.development@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

def popup_menu_helper(treeview, event, popupmenu, select_if_unselected=True, button=3):
    if event.button != button:
        return None
    cursor_path = treeview.get_path_at_pos(int(event.x), int(event.y))
    if not cursor_path:
        return False
    if select_if_unselected:
        paths = treeview.get_selection().get_selected_rows()[1]
        if cursor_path[0] not in paths:
            row = treeview.get_model().get_iter(cursor_path[0])
            treeview.get_selection().unselect_all()
            treeview.get_selection().select_iter(row)
    it = model.get_iter(cursor_path[0])
    # Only show popup when right clicking a selected file
    if not treeview.get_selection().iter_is_selected(it):
        return False
    return it, cursor_path


def get_treeview_value_in_selected_row(treeview, store, column_index=0):
    """
    Helper to get the value at index 'index_column' of the selected element
    in the given treeview.
    return None of no item is selected.
    """
    tree, tree_id = treeview.get_selection().get_selected()
    if tree_id:
        value = store.get_value(tree_id, column_index)
        return value
    return None
