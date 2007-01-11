#!/usr/bin/env python
#
# delugegtk.py
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

import deluge

import dcommon, dgtk

import sys, os, gettext
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject

import xdg, xdg.BaseDirectory


class DelugeGTK:
	def __init__(self):
		#Start the Deluge Manager:
		self.manager = deluge.Manager("DL", "0500", "Deluge 0.5.0",
			 os.path.expanduser("~") + "/Temp")
			 #xdg.BaseDirectory.save_config_path("deluge-svn"))
		#Set up the interface:
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
		self.view.set_rules_hint(True)
		
		
		## Initializes the columns for the torrent_view
		
		self.queue_column 	= 	dgtk.add_text_column(self.view, "#", 1)
		self.name_column 	=	dgtk.add_text_column(self.view, "Name", 2)
		self.size_column 	=	dgtk.add_text_column(self.view, "Size", 3)
		self.status_column 	= 	dgtk.add_progress_column(self.view, "Status", 4, 5)
		self.seed_column 	=	dgtk.add_text_column(self.view, "Seeders", 6)
		self.peer_column 	=	dgtk.add_text_column(self.view, "Peers", 7)
		self.dl_column 		=	dgtk.add_text_column(self.view, "Download", 8)
		self.ul_column 		=	dgtk.add_text_column(self.view, "Upload", 9)
		self.eta_column 	=	dgtk.add_text_column(self.view, "ETA", 10)
		self.share_column 	= 	dgtk.add_text_column(self.view, "Share Ratio", 11)
		
		self.status_column.set_expand(True)
		
		self.file_view = self.wtree.get_widget("file_view")
		self.file_store = gtk.ListStore(str, bool)
		self.file_view.set_model(self.file_store)
		
		self.filename_column 	=	dgtk.add_text_column(self.file_view, "Filename", 0)
		self.filetoggle_column 	=	dgtk.add_toggle_column(self.file_view, "DL?", 0)

		self.filename_column.set_expand(True)
		
		## Should probably use rules-hint for other treevies as well
		
		self.peer_view = self.wtree.get_widget("peer_view")
		self.peer_store = gtk.ListStore(str, str, str, str, str)
		self.peer_view.set_model(self.peer_store)
		
		self.peer_ip_column			=	dgtk.add_text_column(self.peer_view, "IP Address", 0)
		self.peer_client_column		=	dgtk.add_text_column(self.peer_view, "Client", 1)
		## Note: change this column to use a progress column before 0.5 is released
		self.peer_complete_column	=	dgtk.add_text_column(self.peer_view, "Percent Complete", 2)
		self.peer_download_column	=	dgtk.add_text_column(self.peer_view, "Download Rate", 3)
		self.peer_upload_column		=	dgtk.add_text_column(self.peer_view, "Upload Rate", 4)
	
		## Interface created
		
		## add torrents in manager to interface
		for uid in self.manager.get_unique_IDs():
			self.store.append(self.get_list_from_uid(uid))
		
		
	## Start the timer that updates the interface
	def start(self):
		gobject.timeout_add(1000, self.update)

	## Call via a timer to update the interface
	def update(self):
		itr = self.store.get_iter_first()
		
		while itr is not None:
			uid = self.store.get_value(itr, 0)
			tlist = self.get_list_from_uid(uid)
			for i in range(12):
				self.store.set_value(itr, i, tlist[i])
			itr = self.store.iter_next(itr)
		return True
	
	# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
	def get_list_from_uid(self, unique_id):
		state = self.manager.get_torrent_state(unique_id)
		return [unique_id, state['queue_pos'], state['name'], state['total_size'], 
				int(state['progress'] * 100), deluge.STATE_MESSAGES[state['state']], state['total_seeds'], 
				state['total_peers'], state['download_rate'], state['upload_rate'], 
				"NULL", "NULL"]
		
	def new_torrent(self, obj=None):
		pass
		
	def add_torrent(self, obj=None):
		torrent = dgtk.show_file_open_dialog()
		if torrent is not None:
			uid = self.manager.add_torrent(torrent, ".", True)
			self.store.append(self.get_list_from_uid(uid))
		
	def quit(self, obj=None):
		self.manager.quit()
		self.window.destroy()
	


		
## For testing purposes, create a copy of the interface
if __name__ == "__main__":
	interface = DelugeGTK()
	interface.start()
	
	gtk.main()