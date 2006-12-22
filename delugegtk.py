#!/usr/bin/env python
#
# delugegtk.py
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
# delugegtk.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with main.py.  If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.

import dcommon, dgtk

import sys, os, gettext
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade


class DelugeGTK:
	def __init__(self):
		self.gladefile = dcommon.get_glade_file("delugegtk.glade")
		self.wtree = gtk.glade.XML(self.gladefile)
		self.window = self.wtree.get_widget("main_window")
		self.toolbar = self.wtree.get_widget("tb_middle")
		if(self.window):
			self.window.connect("destroy", gtk.main_quit)
		self.window.set_title(dcommon.PROGRAM_NAME + " " + dcommon.PROGRAM_VERSION)
		self.window.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))

		## Create the system tray icon
		self.tray = dgtk.TrayIcon(self)
		
		## Create the about dialog
		self.abt = dgtk.AboutDialog()
		
		## Create the preferences dialog
		self.prf = dgtk.PreferencesDialog()
		
		actions = 	{
					## File Menu
					"new_torrent": self.new_torrent,
					"add_torrent": self.add_torrent,
					"menu_quit": self.quit,
					## Edit Menu
					"pref_clicked": self.prf.show_pref,
					"plugins_clicked": self.prf.show_plugins,
					## Torrent Menu
					## Help Menu
					"show_about_dialog": self.abt.show,
					}
		self.wtree.signal_autoconnect(actions)
		
		## Create the torrent listview
		self.view = self.wtree.get_widget("torrent_view")
		# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
		self.store = gtk.ListStore(int, int, str, str, int, str, str, str, str, str, str, str)
		self.view.set_model(self.store)
		
		
		## Still a lot of work to be done here,
		## this column is here as an example of how 
		## to create and add columns.  Perhaps I
		## should create some sort of ColumnsManager
		## object in dgtk to keep the code cleaner
		## and also confine column code to one place.
		## I'm worrying about columns way too much
		## because that was one of the main places
		## Deluge's code (up to 0.4) got way out of
		## hand.
		
		self.queue_column 	= 	dgtk.add_text_column(self.view, "#", 1)
		self.name_column 	=	dgtk.add_text_column(self.view, "Name", 2)
		self.size_column 	=	dgtk.add_text_column(self.view, "Size", 3)
		self.status_column 	= 	dgtk.add_progress_column(self.view, "Status", 4, 5)
		self.seed_column 	=	dgtk.add_text_column(self.view, "Seeders", 6)
		self.peer_column 	=	dgtk.add_text_column(self.view, "Peers", 7)
		self.dl_column 		=	dgtk.add_text_column(self.view, "Download", 8)
		self.ul_column 		=	dgtk.add_text_column(self.view, "Upload", 9)
		self.eta_column 	=	dgtk.add_text_column(self.view, "Time Remaining", 10)
		self.share_column 	= 	dgtk.add_text_column(self.view, "Share Ratio", 11)
		
		## Interface created
	
	def start(self):
		pass
		
	def new_torrent(self, obj=None):
		pass
		
	def add_torrent(self, obj=None):
		pass
		
	def quit(self, obj=None):
		self.window.destroy()
	
	## Call via a timer to update the interface
	def update(self):
		pass

		
## For testing purposes, create a copy of the interface
if __name__ == "__main__":
	d = DelugeGTK()
	## Add an example line
	
	## Test the interface by adding a few fake torrents
	d.store.append([0,1,"Deluge Torrent","700MB",50,"Downloading","10 (50)", "15 (30)", "50 KB/s", "10 KB/s", "2 h", "100%"])
	d.store.append([1,2,"Sample Torrent","350MB",75,"Queued","10 (20)","20 (20)","0 KB/s", "0 KB/s", "und", "0%"])
	
	gtk.main()