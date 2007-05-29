# -*- coding: utf-8 -*-

# Copyright (C) 2007 - regulate@gmail.com
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import gtk, gtk.glade

class plugin_tcreator:
	
	
	def __init__(self, path, deluge_core, deluge_interface):
		import gtk, gtk.glade 
		self.path = path
		self.interface = deluge_interface
		self.core = deluge_core
		self.dialog = None
		self.glade = None
		# get a toolbar to attach to
		self.toolbar = self.interface.toolbar
		# create a button 
		icon = gtk.image_new_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)
		self.button = gtk.ToolButton(icon_widget=icon)
		self.button.set_label('create torrent')
		self.button.connect("clicked", self.clicked)
		self.toolbar.add(self.button)
		self.button.show_all()

	def unload(self):
		self.toolbar.remove(self.button)
	
	def update(self):
		pass
	
	def clicked(self, button):
		import gtk, gtk.glade
		ret = 0
		self.glade = gtk.glade.XML(self.path + "/tcreator.glade", domain='deluge')
		self.dialog = self.glade.get_widget('tcreator')
		self.dialog.set_title('Deluge Torrent Creator')
		self.dialog.connect('destroy', self.destroy)
		self.dialog.show_all()
		ret = self.dialog.run()

		if ret == 1:
			self.verify_settings()
			self.destroy()

		if ret == 0:
			self.destroy()
		
	def destroy(self, *args):
		self.dialog.hide()
		self.dialog = None
	
	def verify_settings(self):
		import os, gtk, gtk.glade
		self.dest = self.glade.get_widget("dest_file").get_text()
		(dir, fn) = os.path.split(self.dest)
		src_dir =  self.glade.get_widget("src_dir").get_filename()
		trackers = self.glade.get_widget("trackers").get_buffer() 
		(start, end) = trackers.get_bounds()
		trackers = trackers.get_text(start, end)
		comments = self.glade.get_widget("comments").get_buffer()
		(start, end) = comments.get_bounds()
		comments = comments.get_text(start, end)
		size_table = {1:256, 2:512, 3:1024}
		size = self.glade.get_widget("piece_size").get_active()
		author = self.glade.get_widget("author").get_text()

		if 0<size and size<4:
			size = size_table[size]
		else:
			size = 256

		if not callable(getattr(self.core, "create_torrent")):
			print 'Incompatible core.py'
		
		ret = self.core.create_torrent(self.dest, src_dir, trackers, comments, size, author)
		return ret

register_plugin("Deluge Torrent Creator", plugin_tcreator, "regulate", "0.1", "A torrent creator plugin", config=False)

