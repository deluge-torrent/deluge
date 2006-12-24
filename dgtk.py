# dgtk.py
#
# Copyright (C) Zach Tibbitts 2006 <zach@collegegeek.org>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# dgtk.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with main.py.  If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#
# Similar to dcommon, this contains any common functions
# related to gtk

import dcommon
import gettext
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade


## Right now this only supports PyGTK's native 
## tray library.  I will add egg support into
## this class at a later time.
class TrayIcon:
	def __init__(self, parent):
		self.parent = parent
		self.tray = gtk.StatusIcon()
		## uncomment later
		##self.gladefile = dcommon.get_glade_file("dgtkpopups.glade")
		self.tray.set_from_file(dcommon.get_pixmap("deluge32.png"))
		self.tray.set_tooltip("Deluge Bittorrent Client")

class TorrentPopup:
	def __init__(self, parent):
		self.parent = parent
		self.gladefile = dcommon.get_glade_file("dgtkpopups.glade")
		self.wtree = gtk.glade.XML(self.gladefile)
		self.menu = self.wtree.get_widget("torrent_popup")
		dic = {
				"size_toggle": self.size,
				"status_toggle": self.status,
				"seeders_toggle": self.seeders,
				"peers_toggle": self.peers,
				"dl_toggle": self.dl,
				"ul_toggle": self.ul,
				"eta_toggle": self.eta,
				"share_toggle": self.share
				
				}
		self.wtree.signal_autoconnect(dic)
	
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
	
## Functions to create columns

def add_text_column(view, header, cid):
	render = gtk.CellRendererText()
	column = gtk.TreeViewColumn(header, render, text=cid)
	column.set_resizable(True)
	column.set_expand(False)
	view.append_column(column)
	return column

def add_progress_column(view, header, pid, mid):
	render = gtk.CellRendererProgress()
	column = gtk.TreeViewColumn(header, render, value=pid, text=mid)
	column.set_resizable(True)
	column.set_expand(False)
	view.append_column(column)
	return column

def add_toggle_column(view, header, cid, toggled_signal=None):
	render = gtk.CellRendererToggle()
	render.set_property('activatable', True)
	column = gtk.TreeViewColumn(header, render, active=cid)
	column.set_resizable(True)
	column.set_expand(False)
	view.append_column(column)
	if toggled_signal is not None:
		render.connect("toggled", toggled_signal, cid)
	return column