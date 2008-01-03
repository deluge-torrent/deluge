# -*- coding: utf-8 -*-
# dgtk.py
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

# Similar to common, this contains any common functions
# related to gtk that are needed by the client

from itertools import izip

import common
import pygtk
pygtk.require('2.0')
import gtk

## Cell data functions to pass to add_func_column()

def cell_data_speed(column, cell, model, iter, data):
    speed = model.get_value(iter, data)
    if speed<100: speed_str = ""
    else: speed_str = common.fspeed(speed)
    cell.set_property('text', speed_str)

def cell_data_size(column, cell, model, iter, data):
	size = model.get_value(iter, data)
	size_str = common.fsize(size)
	cell.set_property('text', size_str)

## Functions to create columns

def add_func_column(view, header, func, data, sortid=None, width=None):
    column = gtk.TreeViewColumn(header)
    render = gtk.CellRendererText()
    column.pack_start(render, True)
    column.set_cell_data_func(render, func, data)
    if sortid is not None:
        column.set_clickable(True)
        column.set_sort_column_id(sortid)
    else:
        try:
            if len(data) == 1:
                column.set_clickable(True)
                column.set_sort_column_id(data[0])
        except TypeError:
            column.set_clickable(True)
            column.set_sort_column_id(data)
    column.set_resizable(True)
    column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
    if width:
        column.set_fixed_width(width)
    column.set_expand(False)
    column.set_min_width(10)
    column.set_reorderable(True)
    view.append_column(column)
    return column
    

def add_text_column(view, header, cid, width=None):
    render = gtk.CellRendererText()
    column = gtk.TreeViewColumn(header, render, text=cid)
    column.set_clickable(True)
    column.set_sort_column_id(cid)
    column.set_resizable(True)
    column.set_expand(False)
    if width:
        column.set_fixed_width(width)
    column.set_min_width(10)
    column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
    column.set_reorderable(True)
    view.append_column(column)
    return column

def add_progress_column(view, header, pid, mid, width=None):
    render = gtk.CellRendererProgress()
    column = gtk.TreeViewColumn(header, render, value=pid, text=mid)
    column.set_clickable(True)
    column.set_sort_column_id(pid)
    column.set_resizable(True)
    column.set_expand(False)
    column.set_min_width(10)
    if width:
        column.set_fixed_width(width)
    column.set_reorderable(True)
    column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
    view.append_column(column)
    return column

def add_toggle_column(view, header, cid, toggled_signal=None, width=None):
    render = gtk.CellRendererToggle()
    render.set_property('activatable', True)
    column = gtk.TreeViewColumn(header, render, active=cid)
    column.set_clickable(True)
    column.set_resizable(True)
    column.set_expand(False)
    if width:
        column.set_fixed_width(width)
    column.set_min_width(10)
    column.set_reorderable(True)
    view.append_column(column)
    if toggled_signal is not None:
        render.connect("toggled", toggled_signal)
    return column

def add_texticon_column(view, header, icon_col, text_col, width=None):
    column = gtk.TreeViewColumn(header)
    column.set_clickable(True)
    column.set_resizable(True)
    column.set_expand(False)
    if width:
        column.set_fixed_width(width)
    column.set_min_width(10)
    column.set_reorderable(True)
    render = gtk.CellRendererPixbuf()
    column.pack_start(render, expand=False)
    column.add_attribute(render, 'pixbuf', icon_col)
    render = gtk.CellRendererText()
    column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
    column.pack_start(render, expand=True)
    column.add_attribute(render, 'text', text_col)
    view.append_column(column)
    return column

def update_store(store, iter, cols, new_values):
    """gtk.ListStore update function
    
    Arguments:
    store - gtk.ListStore instance
    iter - a valid gtk.TreeIter for the row being modified
    cols - iterable containing indexes of columns to change
    new_values - iterable with new values for specified columns
    
    Example:
    update_store(file_store, iter, (1, 3), ('test.txt', 9940))
    
    """

    old_values = store.get(iter, *cols)
    
    for col, old_value, new_value in izip(cols, old_values, new_values):
        try:
            # equality check because formatting and cell renderer functions 
            # called on self.torrent_model.set_value() are expensive
            if old_value != new_value:
                store.set_value(iter, col, new_value)
        except:
            print "ERR", col, type(new_value), new_value
