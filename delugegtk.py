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

import sys, os, gettext
import deluge, dcommon, dgtk
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject
import xdg, xdg.BaseDirectory


class DelugeGTK:
	def __init__(self):
		#Start the Deluge Manager:
		self.manager = deluge.Manager("DE", "0500", "Deluge 0.5.0",
			 os.path.expanduser("~") + "/Temp")
			 #xdg.BaseDirectory.save_config_path("deluge-svn"))
		#Set up the interface:
		self.gladefile = dcommon.get_glade_file("delugegtk.glade")
		self.wtree = gtk.glade.XML(self.gladefile)
		self.window = self.wtree.get_widget("main_window")
		self.toolbar = self.wtree.get_widget("tb_middle")
		if(self.window):
			self.window.connect("destroy", self.quit)
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
					"remove_torrent" : self.remove_torrent,
					"menu_quit": self.quit,
					## Edit Menu
					"pref_clicked": self.prf.show_pref,
					"plugins_clicked": self.prf.show_plugins,
					## View Menu
					"size_toggle": self.size_toggle,
					"status_toggle": self.status_toggle,
					"seeders_toggle": self.seeders_toggle,
					"peers_toggle": self.peers_toggle,
					"dl_toggle": self.dl_toggle,
					"ul_toggle": self.ul_toggle,
					"eta_toggle": self.eta_toggle,
					"share_toggle": self.share_toggle,
					## Help Menu
					"show_about_dialog": self.abt.show,
					## Other events
					"torrentrow_click": self.torrentview_clicked,
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
			self.store.append(self.get_list_from_unique_id(uid))
		
		
	## Start the timer that updates the interface
	def start(self):
		gobject.timeout_add(1000, self.update)

	## Call via a timer to update the interface
	def update(self):
		# Make sure that the interface still exists
		try:
			tab = self.wtree.get_widget("torrent_info").get_current_page()
		except AttributeError:
			return False
		if tab == 0: #Torrent List
			itr = self.store.get_iter_first()
			while itr is not None:
				uid = self.store.get_value(itr, 0)
				try:
					state = self.manager.get_torrent_state(uid)
					tlist = self.get_list_from_unique_id(uid)
					for i in range(12):
						self.store.set_value(itr, i, tlist[i])
					itr = self.store.iter_next(itr)
				except deluge.InvalidUniqueIDError:
					self.store.remove(itr)
					if not self.store.iter_is_valid(itr):
						itr = None
		elif tab == 1: #Details Pane
			pass
		elif tab == 2: #Peers List
			pass
		elif tab == 3: #File List
			pass
		else:
			pass

		return True
	
	def get_selected_torrent(self):
		return self.store.get_value(self.view.get_selection().get_selected()[1], 0)
	
	# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
	def get_list_from_unique_id(self, unique_id):
		state = self.manager.get_torrent_state(unique_id)
		queue = int(state['queue_pos']) + 1 
		name = state['name']
		size = state['total_size']
		progress = int(state['progress'] * 100)
		message = deluge.STATE_MESSAGES[state['state']]
		seeds = str(state['num_seeds']) + " (" + str(state['total_seeds']) + ")"
		peers = str(state['num_peers']) + " (" + str(state['total_peers']) + ")"
		dlrate = state['download_rate']
		ulrate = state['upload_rate']
		eta = "NULL"
		share = "NULL"
		return [unique_id, queue, name, size, progress, message,
				seeds, peers, dlrate, ulrate, eta, share]
		
	def new_torrent(self, obj=None):
		pass
		
	def add_torrent(self, obj=None):
		torrent = dgtk.show_file_open_dialog()
		if torrent is not None:
			uid = self.manager.add_torrent(torrent, ".", True)
			self.store.append(self.get_list_from_unique_id(uid))
	
	def remove_torrent(self, obj=None):
		self.manager.remove_torrent(self.get_selected_torrent(), False)
		
	def torrentview_clicked(self, widget, event):
		pass
		
	def size_toggle(self, obj):
		self.size_column.set_visible(obj.get_active())
			
	
	def status_toggle(self, obj):
		self.status_column.set_visible(obj.get_active())
	
	def seeders_toggle(self, obj):
		self.seed_column.set_visible(obj.get_active())
	
	def peers_toggle(self, obj):
		self.peer_column.set_visible(obj.get_active())
	
	def dl_toggle(self, obj):
		self.dl_column.set_visible(obj.get_active())
	
	def ul_toggle(self, obj):
		self.ul_column.set_visible(obj.get_active())
	
	def eta_toggle(self, obj):
		self.eta_column.set_visible(obj.get_active())
	
	def share_toggle(self, obj):
		self.share_column.set_visible(obj.get_active())
		
	def quit(self, obj=None):
		self.manager.quit()
		gtk.main_quit()
		
	


		
## For testing purposes, create a copy of the interface
if __name__ == "__main__":
	interface = DelugeGTK()
	interface.start()
	gtk.main()