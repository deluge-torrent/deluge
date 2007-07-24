#
# columns.py
#
# Copyright (C) 2006 Zach Tibbitts ('zachtib') <zach@collegegeek.org>
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

import pygtk
pygtk.require('2.0')
import gtk

import deluge.common

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

## Functions to create columns

def add_func_column(view, header, func, data, sortid=None):
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
    column.set_expand(False)
    column.set_min_width(10)
    column.set_reorderable(True)
    view.append_column(column)
    return column
    

def add_text_column(view, header, cid):
    render = gtk.CellRendererText()
    column = gtk.TreeViewColumn(header, render, text=cid)
    column.set_clickable(True)
    column.set_sort_column_id(cid)
    column.set_resizable(True)
    column.set_expand(False)
    column.set_min_width(10)
    column.set_reorderable(True)
    view.append_column(column)
    return column

def add_progress_column(view, header, pid, mid):
    render = gtk.CellRendererProgress()
    column = gtk.TreeViewColumn(header, render, value=pid, text=mid)
    column.set_clickable(True)
    column.set_sort_column_id(pid)
    column.set_resizable(True)
    column.set_expand(False)
    column.set_min_width(10)
    column.set_reorderable(True)
    view.append_column(column)
    return column

def add_toggle_column(view, header, cid, toggled_signal=None):
    render = gtk.CellRendererToggle()
    render.set_property('activatable', True)
    column = gtk.TreeViewColumn(header, render, active=cid)
    column.set_clickable(True)
    column.set_resizable(True)
    column.set_expand(False)
    column.set_min_width(10)
    column.set_reorderable(True)
    view.append_column(column)
    if toggled_signal is not None:
        render.connect("toggled", toggled_signal)
    return column

def add_texticon_column(view, header, icon_col, text_col):
    column = gtk.TreeViewColumn(header)
    column.set_clickable(True)
    column.set_resizable(True)
    column.set_expand(False)
    column.set_min_width(10)
    column.set_reorderable(True)
    render = gtk.CellRendererPixbuf()
    column.pack_start(render, expand=False)
    column.add_attribute(render, 'pixbuf', icon_col)
    render = gtk.CellRendererText()
    column.pack_start(render, expand=True)
    column.add_attribute(render, 'text', text_col)
    view.append_column(column)
    return column
