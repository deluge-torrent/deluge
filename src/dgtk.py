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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.

# Similar to dcommon, this contains any common functions
# related to gtk that are needed by the client

import dcommon
import gettext
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

## Browse for .torrent files
def show_file_open_dialog(parent=None):
	chooser = gtk.FileChooserDialog(_("Choose a .torrent file"), parent, gtk.FILE_CHOOSER_ACTION_OPEN,
			buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
	
	f0 = gtk.FileFilter()
	f0.set_name(_("Torrent files"))
	f0.add_pattern("*." + "torrent")
	chooser.add_filter(f0)
	f1 = gtk.FileFilter()
	f1.set_name(_("All files"))
	f1.add_pattern("*")
	chooser.add_filter(f1)
	
	chooser.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
	chooser.set_property("skip-taskbar-hint", True)
		
	response = chooser.run()
	if response == gtk.RESPONSE_OK:
		result = chooser.get_filename()
	else:
		result = None
	chooser.destroy()
	return result

def show_directory_chooser_dialog(parent=None):
	chooser = gtk.FileChooserDialog(_("Choose a download directory"), parent, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
				buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
	chooser.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
	chooser.set_property("skip-taskbar-hint", True)
	if chooser.run() == gtk.RESPONSE_OK:
		result = chooser.get_filename()
	else:
		result = None
	chooser.destroy()
	return result

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
	view.append_column(column)
	return column
	

def add_text_column(view, header, cid):
	render = gtk.CellRendererText()
	column = gtk.TreeViewColumn(header, render, text=cid)
	column.set_clickable(True)
	column.set_sort_column_id(cid)
	column.set_resizable(True)
	column.set_expand(False)
	view.append_column(column)
	return column

def add_progress_column(view, header, pid, mid):
	render = gtk.CellRendererProgress()
	column = gtk.TreeViewColumn(header, render, value=pid, text=mid)
	column.set_clickable(True)
	column.set_sort_column_id(pid)
	column.set_resizable(True)
	column.set_expand(False)
	view.append_column(column)
	return column

def add_toggle_column(view, header, cid, toggled_signal=None):
	render = gtk.CellRendererToggle()
	render.set_property('activatable', True)
	column = gtk.TreeViewColumn(header, render, active=cid)
	column.set_clickable(True)
	column.set_resizable(True)
	column.set_expand(False)
	view.append_column(column)
	if toggled_signal is not None:
		render.connect("toggled", toggled_signal)
	return column
