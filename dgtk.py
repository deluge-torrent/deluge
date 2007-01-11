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


## Right now this only supports PyGTK's native 
## tray library.  I may add egg support into
## this class at a later time.
class TrayIcon:
	def __init__(self, parent):
		self.parent = parent
		self.tray = gtk.StatusIcon()
		## uncomment later
		##self.gladefile = dcommon.get_glade_file("dgtkpopups.glade")
		self.tray.set_from_file(dcommon.get_pixmap("deluge32.png"))
		self.tray.set_tooltip("Deluge Bittorrent Client")


	
	def popup(self):
		pass
		
	## Toggle functions
	def size(self, obj):
		pass
	
	def status(self, obj):
		pass
	
	def seeders(self, obj):
		pass
	
	def peers(self, obj):
		pass
	
	def dl(self, obj):
		pass
	
	def ul(self, obj):
		pass
	
	def eta(self, obj):
		pass
	
	def share(self, obj):
		pass

class AboutDialog:
	def __init__(self):
		gtk.about_dialog_set_url_hook(dcommon.open_url_in_browser)
		self.abt = gtk.AboutDialog()
		self.abt.set_name(dcommon.PROGRAM_NAME)
		self.abt.set_version(dcommon.PROGRAM_VERSION)
		self.abt.set_website("http://deluge-torrent.org")
		self.abt.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.abt.set_logo(gtk.gdk.pixbuf_new_from_file(
				dcommon.get_pixmap("deluge256.png")))
	
	def show(self, arg=None):
		self.abt.show_all()
		self.abt.run()
		self.abt.hide_all()
		
class PreferencesDialog:
	def __init__(self):
		self.gladefile = dcommon.get_glade_file("dgtkpref.glade")
		self.wtree = gtk.glade.XML(self.gladefile)
		self.prf = self.wtree.get_widget("pref_dialog")
		self.notebook = self.wtree.get_widget("pref_notebook")
		self.prf.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		
		self.plugin_view = self.wtree.get_widget("plugin_view")
		self.plugin_store = gtk.ListStore(str, 'gboolean')
		self.plugin_view.set_model(self.plugin_store)
		self.plugin_name_column = add_text_column(self.plugin_view, "Plugin", 0)
		self.plugin_name_column.set_expand(True)
		self.plugin_toggle_column = add_toggle_column(self.plugin_view, "Enable", 1)
	
	def show_pref(self, arg=None):
		self.prf.show_all()
		self.notebook.set_current_page(0)
		self.prf.run()
		self.prf.hide_all()
	
	def show_plugins(self, arg=None):
		self.prf.show_all()
		self.notebook.set_current_page(2)
		self.prf.run()
		self.prf.hide_all()


## A simple file open dialog.  I'm going to improve it later,
## this is a quick implementation for testing.
def show_file_open_dialog():
	chooser = gtk.FileChooserDialog("Open", None, gtk.FILE_CHOOSER_ACTION_OPEN,
			buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
	response = chooser.run()
	if response == gtk.RESPONSE_OK:
		result = chooser.get_filename()
	else:
		result = None
	chooser.destroy()
	return result
	


## Functions to create columns

def add_text_column(view, header, cid):
	render = gtk.CellRendererText()
	column = gtk.TreeViewColumn(header, render, text=cid)
	column.set_clickable(True)
	column.set_resizable(True)
	column.set_expand(False)
	view.append_column(column)
	return column

def add_progress_column(view, header, pid, mid):
	render = gtk.CellRendererProgress()
	column = gtk.TreeViewColumn(header, render, value=pid, text=mid)
	column.set_clickable(True)
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
		render.connect("toggled", toggled_signal, cid)
	return column