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

import sys, os, os.path, gettext
import deluge, dcommon, dgtk
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject
import xdg, xdg.BaseDirectory
import dbus, dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib 


class DelugeGTK(dbus.service.Object):
	def __init__(self, bus_name=dbus.service.BusName('org.deluge_torrent.Deluge',
			bus=dbus.SessionBus()),	object_path='/org/deluge_torrent/DelugeObject'):
		dbus.service.Object.__init__(self, bus_name, object_path)
		self.is_running = False
		self.torrent_file_queue = []
		#Load up a config file:
		self.conf_file = xdg.BaseDirectory.save_config_path("deluge-svn") + '/deluge.conf'
		if os.path.isdir(self.conf_file):
			print 'Weird, the file I was trying to write to, %s, is an existing directory'%(self.conf_file)
			sys.exit(0)
		if not os.path.isfile(self.conf_file):
			f = open(self.conf_file, mode='w')
			f.flush()
			f.close()
		self.pref = dcommon.DelugePreferences()
		self.pref.load_from_file(self.conf_file)
		#Start the Deluge Manager:
		self.manager = deluge.Manager("DE", "0490", "Deluge 0.4.9",
			 xdg.BaseDirectory.save_config_path("deluge-svn"))
		#Set up the interface:
		self.gladefile = dcommon.get_glade_file("delugegtk.glade")
		self.wtree = gtk.glade.XML(self.gladefile)
		self.window = self.wtree.get_widget("main_window")
		self.window.hide()
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
		
		self.wtree.signal_autoconnect({
					## File Menu
					"new_torrent": self.new_torrent_clicked,
					"add_torrent": self.add_torrent_clicked,
					"remove_torrent" : self.remove_torrent_clicked,
					"menu_quit": self.quit,
					## Edit Menu
					"pref_clicked": self.show_pref,
					"plugins_clicked": self.show_plugins,
					## View Menu
					"infopane_toggle": self.infopane_toggle,
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
					## Toolbar
					"recheck_files": self.recheck_files,
					"update_tracker": self.update_tracker,
					"clear_finished": self.clear_finished,
					"queue_up": self.q_torrent_up,
					"queue_down": self.q_torrent_down,
					## Other events
					"torrentrow_click": self.torrentview_clicked,
					})
		
		## Create the torrent listview
		self.view = self.wtree.get_widget("torrent_view")
		# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
		self.store = gtk.ListStore(int, int, str, str, float, str, str, str, str, str, str, str)
		self.view.set_model(self.store)
		self.view.set_rules_hint(True)
		
		
		## Initializes the columns for the torrent_view
#		Just found out there are built-in pygtk methods with similar functionality
#		to these, perhaps I should look into using those.
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
		
		#Torrent Summary tab
		# Look into glade's widget prefix function
		self.text_summary_title                   = self.wtree.get_widget("summary_title")
		self.text_summary_total_size              = self.wtree.get_widget("summary_total_size")
		self.text_summary_pieces                  = self.wtree.get_widget("summary_pieces")
		self.text_summary_total_downloaded        = self.wtree.get_widget("summary_total_downloaded")
		self.text_summary_total_uploaded          = self.wtree.get_widget("summary_total_uploaded")
		self.text_summary_download_rate			  = self.wtree.get_widget("summary_download_rate")
		self.text_summary_upload_rate			  = self.wtree.get_widget("summary_upload_rate")
		self.text_summary_seeders				  = self.wtree.get_widget("summary_seeders")
		self.text_summary_peers					  = self.wtree.get_widget("summary_peers")
		self.text_summary_percentage_done         = self.wtree.get_widget("summary_percentage_done")
		self.text_summary_share_ratio             = self.wtree.get_widget("summary_share_ratio")
		self.text_summary_downloaded_this_session = self.wtree.get_widget("summary_downloaded_this_session")
		self.text_summary_uplodaded_this_session  = self.wtree.get_widget("summary_uploaded_this_session")
		self.text_summary_tracker                 = self.wtree.get_widget("summary_tracker")
		self.text_summary_tracker_response        = self.wtree.get_widget("summary_tracker_response")
		self.text_summary_tracker_status          = self.wtree.get_widget("summary_tracker_status")
		self.text_summary_next_announce           = self.wtree.get_widget("summary_next_announce")
		self.text_summary_compact_allocation      = self.wtree.get_widget("summary_compact_allocation")
		self.text_summary_eta					  = self.wtree.get_widget("summary_eta")
		
		## Interface created
		self.apply_prefs()
	
	## external_add_torrent should only be called from outside the class	
	@dbus.service.method('org.deluge_torrent.DelugeInterface')
	def external_add_torrent(self, torrent_file):
		print "Ding!"
		print "Got torrent externally:", os.path.basename(torrent_file)
		print "\tNow, what to do with it?"
		if self.is_running:
			print "\t\tthe client seems to already be running, i'll try and add the torrent"
			uid = self.manager.add_torrent(torrent_file, ".", True)
			self.store.append(self.get_list_from_unique_id(uid))
		else:
			print "\t\tthe client hasn't started yet, I'll queue the torrent"
			self.torrent_file_queue.append(torrent_file)
		
		
	## Start the timer that updates the interface
	def start(self, hidden=False):
		if not hidden:
			self.window.show()
		# go through torrent files to add
		#dummy preferences values:
		use_default_download_location = True
		default_download_location = "."
		for torrent_file in self.torrent_file_queue:
			print "adding torrent", torrent_file
			try:
				self.manager.add_torrent(torrent_file, ".", True)
			except deluge.DelugeError:
				print "duplicate torrent found, ignoring", torrent_file
		## add torrents in manager to interface
		for uid in self.manager.get_unique_IDs():
			self.store.append(self.get_list_from_unique_id(uid))
		gobject.timeout_add(1000, self.update)
		try:
			self.is_running = True
			gtk.main()
		except KeyboardInterrupt:
			self.manager.quit()
	
	def show_pref(self, o=None):
		self.pref = self.prf.show_dlg(self.pref)
	
	def show_plugins(self, o=None):
		pass
	
	def apply_prefs(self):
		for k in self.pref.keys():
			print k, self.pref.get(k)
			
	
	# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
	def get_list_from_unique_id(self, unique_id):
		state = self.manager.get_torrent_state(unique_id)
		queue = int(state['queue_pos']) + 1 
		name = state['name']
		size = dcommon.fsize(state['total_size'])
		progress = float(state['progress'] * 100)
		message = deluge.STATE_MESSAGES[state['state']]
		seeds = dcommon.fseed(state)
		peers = dcommon.fpeer(state)
		dlrate = dcommon.frate(state['download_rate'])
		ulrate = dcommon.frate(state['upload_rate'])
		eta = "NULL"
		share = self.calc_share_ratio(unique_id, state)
		return [unique_id, queue, name, size, progress, message,
				seeds, peers, dlrate, ulrate, eta, share]

	## Call via a timer to update the interface
	def update(self):
		# Make sure that the interface still exists
		try:
			tab = self.wtree.get_widget("torrent_info").get_current_page()
		except AttributeError:
			return False
		# If no torrent is selected, select the first torrent:
		(temp, selection) = self.view.get_selection().get_selected()
		if selection is None:
			self.view.get_selection().select_path("0")
		#Torrent List
		itr = self.store.get_iter_first()
		if itr is None:
			return True
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
		if tab == 0: #Details Paneself.text_summary_seeders				  = self.wtree.get_widget("summary_seeders")
		
			state = self.manager.get_torrent_state(self.get_selected_torrent())
			self.text_summary_title.set_text(str(state["name"]))
			self.text_summary_total_size.set_text(dcommon.fsize(state["total_size"]))
			self.text_summary_pieces.set_text(str(state["pieces"]))
			self.text_summary_total_downloaded.set_text(dcommon.fsize(state["total_download"]))
			self.text_summary_total_uploaded.set_text(dcommon.fsize(state["total_upload"]))
			self.text_summary_download_rate.set_text(dcommon.frate(state["download_rate"]))
			self.text_summary_upload_rate.set_text(dcommon.frate(state["upload_rate"]))
			self.text_summary_seeders.set_text(dcommon.fseed(state))
			self.text_summary_peers.set_text(dcommon.fpeer(state))
			self.text_summary_percentage_done.set_text(dcommon.fpcnt(state["progress"]))
			self.text_summary_share_ratio.set_text(self.calc_share_ratio(self.get_selected_torrent(), state))
			#self.text_summary_downloaded_this_session.set_text(str(state[""]))
			#self.text_summary_uplodaded_this_session.set_text(str(state[""]))
			self.text_summary_tracker.set_text(str(state["tracker"]))
			#self.text_summary_tracker_response.set_text(str(state[""]))
			self.text_summary_tracker_status.set_text(str(state["tracker_ok"]))
			self.text_summary_next_announce.set_text(str(state["next_announce"]))
			#self.text_summary_compact_allocation.set_text(str(state[""]))
			#self.text_summary_eta.set_text(str(state[""]))
		elif tab == 1: #Peers List
			uid = self.get_selected_torrent()
			self.peer_store.clear()
			peer_data = self.manager.get_torrent_peer_info(uid)
			for peer in peer_data:
				# ip client percent dl ul
				self.peer_store.append([peer["ip"], unicode(peer["client"], 'Latin-1'), peer["peer_has"], 
						peer["download_speed"], peer["upload_speed"]])
		elif tab == 2: #File List
			pass
		else:
			pass

		return True
	
	def calc_share_ratio(self, unique_id, torrent_state):
		r = self.manager.calc_ratio(unique_id, torrent_state)
		return '%.2f'%(r)
	
	def get_selected_torrent(self):
		try:
			return self.store.get_value(self.view.get_selection().get_selected()[1], 0)
		except TypeError:
			return None

		
	def new_torrent_clicked(self, obj=None):
		pass
		
	def add_torrent_clicked(self, obj=None):
		torrent = dgtk.show_file_open_dialog()
		if torrent is not None:
			uid = self.manager.add_torrent(torrent, ".", True)
			self.store.append(self.get_list_from_unique_id(uid))
	
	def remove_torrent_clicked(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.remove_torrent(torrent, False)
		
	def recheck_files(self, obj=None):
		pass

	def update_tracker(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.update_tracker(torrent)
	
	def clear_finished(self, obj=None):
		self.manager.clear_completed()
	
	def q_torrent_up(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.queue_up(torrent)
	
	def q_torrent_down(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.queue_up(torrent)

	def torrentview_clicked(self, widget, event):
		pass
	
	def infopane_toggle(self, widget):
		if widget.get_active():
			self.wtree.get_widget("torrent_info").show()
		else:
			self.wtree.get_widget("torrent_info").hide()
		
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
