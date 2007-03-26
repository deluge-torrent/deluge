#!/usr/bin/env python
#
# interface.py
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

import sys, os, os.path, urllib
import core, dcommon, dgtk, ipc_manager, dialogs
import delugeplugins, pref
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject
import xdg, xdg.BaseDirectory
import gettext, locale

DEFAULT_PREFS = {
					"auto_end_seeding" : False,
					"close_to_tray" : False,
					"default_download_path" : "",
					"enable_system_tray" : True,
					"enabled_plugins" : "",
					"end_seed_ratio" : 0.0,
					"max_download_rate" : -1.0,
					"max_number_downloads" : -1.0,
					"max_number_uploads" : -1.0,
					"max_upload_rate" : -1.0,
					"show_dl" : True,
					"show_eta" : True,
					"show_infopane" : True,
					"show_peers" : True,
					"show_seeders" : True,
					"show_share" : True,
					"show_size" : True,
					"show_status" : True,
					"show_toolbar" : True,
					"show_ul" : True,
					"tcp_port_range_lower" : 6881,
					"tcp_port_range_upper" : 6889,
					"use_compact_storage" : False,
					"use_default_dir" : False,
					"window_height" : 480,
					"window_width" : 640,
					"window_x_pos" : 0,
					"window_y_pos" : 0,
				}

class DelugeGTK:
	def __init__(self):
		APP = 'deluge'
		DIR = os.path.join(dcommon.INSTALL_PREFIX, 'share', 'locale')
		locale.setlocale(locale.LC_ALL, '')
		locale.bindtextdomain(APP, DIR)
		locale.textdomain(APP)
		gettext.bindtextdomain(APP, DIR)
		gettext.textdomain(APP)
		gettext.install(APP, DIR)
		
		self.is_running = False
		self.ipc_manager = ipc_manager.Manager(self)
		self.torrent_file_queue = []
		#Load up a config file:
		self.conf_file = os.path.join(dcommon.CONFIG_DIR, 'deluge.conf')
		if os.path.isdir(self.conf_file):
			print 'Weird, the file I was trying to write to, %s, is an existing directory'%(self.conf_file)
			sys.exit(0)
		if not os.path.isfile(self.conf_file):
			f = open(self.conf_file, mode='w')
			f.flush()
			f.close()
		#Start the Deluge Manager:
		p = "DE"
		v = "0500"
		s = "%s %s"%(dcommon.PROGRAM_NAME, dcommon.PROGRAM_VERSION)
		#try:
		#	self.manager = core.Manager(p, v, s, dcommon.CONFIG_DIR)
		#except:
		#	# If something goes wrong while restoring the session, then load
		#	# a blank state rather than crash and exit
		#	self.manager = core.Manager(p, v, s, dcommon.CONFIG_DIR, blank_slate=True)
		#	self.something_screwed_up = True
		self.manager = core.Manager(p, v, s, dcommon.CONFIG_DIR)
		self.something_screwed_up = False
		#else: self.something_screwed_up = False
		self.plugins = delugeplugins.PluginManager(self.manager, self)
		self.plugins.add_plugin_dir(dcommon.PLUGIN_DIR)
		if os.path.isdir(os.path.join(dcommon.CONFIG_DIR , 'plugins')):
			self.plugins.add_plugin_dir(os.path.join(dcommon.CONFIG_DIR, 'plugins'))
		self.plugins.scan_for_plugins()
		self.config = pref.Preferences(self.conf_file, DEFAULT_PREFS)
		#Set up the interface:
		self.wtree = gtk.glade.XML(dcommon.get_glade_file("delugegtk.glade"), domain=APP)
		self.window = self.wtree.get_widget("main_window")
		self.window.hide()
		self.toolbar = self.wtree.get_widget("tb_middle")
		self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL,[('text/uri-list', 0, 80)], gtk.gdk.ACTION_COPY)
		self.window.connect("delete_event", self.close)
		self.window.connect("drag_data_received", self.on_drag_data)
		self.window.set_title(dcommon.PROGRAM_NAME)
		self.window.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.notebook = self.wtree.get_widget("torrent_info")
		self.statusbar = self.wtree.get_widget("statusbar")
		

		
		
		## Construct the Interface
		try:
			self.build_tray_icon()
		except AttributeError:
			#python-pygtk is < 2.9
			self.tray_icon = dgtk.StupidTray()
			self.has_tray = False
		else:
			self.has_tray = True
		
		self.preferences_dialog = dialogs.PreferencesDlg(self, self.config)
		self.plugin_dialog = dialogs.PluginDlg(self, self.plugins)
		self.build_torrent_table()
		self.build_summary_tab()
		self.build_file_tab()
		self.build_peer_tab()
		
		self.connect_signals()
		
		try:
			self.load_window_settings()
		except KeyError:
			pass
		
		enable_plugins = self.config.get('enabled_plugins', str, default="").split(':')
		print enable_plugins
		for plugin in enable_plugins:
			try:
				self.plugins.enable_plugin(plugin)
			except KeyError:
				pass
		self.apply_prefs()
		self.load_window_geometry()

	def external_add_torrent(self, torrent_file):
		print "Ding!"
		print "Got torrent externally:", os.path.basename(torrent_file)
		print "Here's the raw data:", torrent_file
		print "\tNow, what to do with it?"
		if self.is_running:
			print "\t\tthe client seems to already be running, i'll try and add the torrent"
			uid = self.interactive_add_torrent(torrent_file)
		else:
			print "\t\tthe client hasn't started yet, I'll queue the torrent"
			self.torrent_file_queue.append(torrent_file)
	
	def connect_signals(self):
		self.wtree.signal_autoconnect({
					## File Menu
					"add_torrent": self.add_torrent_clicked,
					"add_torrent_url": self.add_torrent_url_clicked,
					"remove_torrent" : self.remove_torrent_clicked,
					"menu_quit": self.quit,
					## Edit Menu
					"pref_clicked": self.show_pref_dialog,
					"plugins_clicked": self.show_plugin_dialog,
					## View Menu
					"toolbar_toggle": self.toolbar_toggle,
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
					"show_about_dialog": self.show_about_dialog,
					## Toolbar
					"start_pause": self.start_pause,
					"update_tracker": self.update_tracker,
					"clear_finished": self.clear_finished,
					"queue_up": self.q_torrent_up,
					"queue_down": self.q_torrent_down,
					"queue_bottom": self.q_to_bottom,
					})
	
	def build_tray_icon(self):
		self.tray_icon = gtk.status_icon_new_from_file(dcommon.get_pixmap("deluge32.png"))
		self.tray_menu = gtk.Menu()
		
		item_show  = gtk.MenuItem(_("Show / Hide Window"))
		item_add   = gtk.ImageMenuItem(_("Add Torrent"))
		item_clear = gtk.ImageMenuItem(_("Clear Finished"))
		item_pref  = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		item_plug  = gtk.ImageMenuItem(_("Plugins"))
		item_quit  = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		
		item_add.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU))
		item_clear.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
		item_plug.set_image(gtk.image_new_from_stock(gtk.STOCK_DISCONNECT, gtk.ICON_SIZE_MENU))
		
		item_show.connect("activate", self.force_show_hide)
		item_add.connect("activate", self.add_torrent_clicked)
		item_clear.connect("activate", self.clear_finished)
		item_pref.connect("activate", self.show_pref_dialog)
		item_plug.connect("activate", self.show_plugin_dialog)
		item_quit.connect("activate", self.quit)
		
		self.tray_menu.append(item_show)
		self.tray_menu.append(item_add)
		self.tray_menu.append(item_clear)
		self.tray_menu.append(gtk.SeparatorMenuItem())
		self.tray_menu.append(item_pref)
		self.tray_menu.append(item_plug)
		self.tray_menu.append(gtk.SeparatorMenuItem())
		self.tray_menu.append(item_quit)
		
		self.tray_menu.show_all()
		
		self.tray_icon.connect("activate", self.tray_clicked)
		self.tray_icon.connect("popup-menu", self.tray_popup)
		
	def tray_popup(self, status_icon, button, activate_time):
		self.tray_menu.popup(None, None, gtk.status_icon_position_menu, 
			button, activate_time, status_icon)
	
	def tray_clicked(self, status_icon):
		if self.window.get_property("visible"):
			if self.window.is_active():
				self.window.hide()
			else:
				self.window.present()
		else:
			self.window.show()
	
	def force_show_hide(self, arg=None):
		if self.window.get_property("visible"):
			self.window.hide()
		else:
			self.window.show()

	def build_torrent_table(self):
		## Create the torrent listview
		self.torrent_view = self.wtree.get_widget("torrent_view")
		self.torrent_glade = gtk.glade.XML(dcommon.get_glade_file("torrent_menu.glade"), domain='deluge')
		self.torrent_menu = self.torrent_glade.get_widget("torrent_menu")		
		self.torrent_glade.signal_autoconnect({"update_tracker": self.update_tracker,
					"clear_finished": self.clear_finished,
					"queue_up": self.q_torrent_up,
					"queue_down": self.q_torrent_down,
					"queue_bottom": self.q_to_bottom,
					})
		# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
		self.torrent_model = gtk.ListStore(int, int, str, str, float, str, int, int, int, int, int, int, str, float)
		self.torrent_view.set_model(self.torrent_model)
		self.torrent_view.set_rules_hint(True)
		self.torrent_view.set_reorderable(True)
		
		def size(column, cell, model, iter, data):
			size = long(model.get_value(iter, data))
			size_str = dcommon.fsize(size)
			cell.set_property('text', size_str)
			
		def rate(column, cell, model, iter, data):
			rate = int(model.get_value(iter, data))
			rate_str = dcommon.frate(rate)
			cell.set_property('text', rate_str)
		
		def peer(column, cell, model, iter, data):
			c1, c2 = data
			a = int(model.get_value(iter, c1))
			b = int(model.get_value(iter, c2))
			cell.set_property('text', '%d (%d)'%(a, b))
		
		def time(column, cell, model, iter, data):
			time = int(model.get_value(iter, data))
			if time < 0:
				time_str = _("Infinity")
			elif time == 0:
				time_str = "-"
			else:
				time_str = dcommon.ftime(time)
			cell.set_property('text', time_str)
			
		def ratio(column, cell, model, iter, data):
			ratio = float(model.get_value(iter, data))
			if ratio == -1:
				ratio_str = _("Unknown")
			else:
				ratio_str = "%.2f"%ratio
			cell.set_property('text', ratio_str)
			
		
		## Initializes the columns for the torrent_view
		self.queue_column 	= 	dgtk.add_text_column(self.torrent_view, "#", 1)
		self.name_column 	=	dgtk.add_text_column(self.torrent_view, _("Name"), 2)
		self.size_column 	=	dgtk.add_func_column(self.torrent_view, _("Size"), size, 3)
		self.status_column 	= 	dgtk.add_progress_column(self.torrent_view, _("Status"), 4, 5)
		self.seed_column 	=	dgtk.add_func_column(self.torrent_view, _("Seeders"), peer, (6, 7))
		self.peer_column 	=	dgtk.add_func_column(self.torrent_view, _("Peers"), peer, (8, 9))
		self.dl_column 		=	dgtk.add_func_column(self.torrent_view, _("Download"), rate, 10)
		self.ul_column 		=	dgtk.add_func_column(self.torrent_view, _("Upload"), rate, 11)
		self.eta_column 	=	dgtk.add_func_column(self.torrent_view, _("Time Remaining"), time, 12)
		self.share_column 	= 	dgtk.add_func_column(self.torrent_view, _("Ratio"), ratio, 13)
		
		self.status_column.set_expand(True)
		self.seed_column.set_sort_column_id(6)
		self.peer_column.set_sort_column_id(8)
		
		def long_sort(model, iter1, iter2, data):
			value1 = long(model.get_value(iter1, data))
			value2 = long(model.get_value(iter2, data))
			if value1 < value2:
				return -1
			elif value1 > value2:
				return 1
			else:
				return 0
		
		self.torrent_model.set_sort_func(3, long_sort, 3)
		self.torrent_model.set_sort_func(12, long_sort, 12)
		try:
			self.torrent_view.get_selection().set_select_function(self.torrent_clicked, full=True)
		except TypeError:
			self.torrent_view.get_selection().set_select_function(self.old_t_click)
		self.torrent_view.connect("button-press-event", self.torrent_view_clicked)

	def old_t_click(self, path):
		return self.torrent_clicked(self.torrent_view.get_selection(), self.torrent_model, path, False)
		
	def torrent_clicked(self, selection, model, path, is_selected):
		if is_selected:
			# Torrent is already selected, we don't need to do anything
			return True
		unique_id = model.get_value(model.get_iter(path), 0)
		state = self.manager.get_torrent_state(unique_id)
		# A new torrent has been selected, need to update parts of interface
		self.text_summary_total_size.set_text(dcommon.fsize(state["total_size"]))
		self.text_summary_pieces.set_text(str(state["pieces"]))
		self.text_summary_tracker.set_text(str(state["tracker"]))
		#self.text_summary_compact_allocation.set_text(str(state[""]))
		# Now for the File tab
		self.file_store.clear()
		all_files = self.manager.get_torrent_file_info(unique_id)
		file_filter = self.manager.get_file_filter(unique_id)
		if file_filter is None:
			file_filter = [False] * len(all_files)
		assert(len(all_files) == len(file_filter))
		i=0
		for f in all_files:
			self.file_store.append([not file_filter[i], f['path'], dcommon.fsize(f['size']), 
					f['offset'], '%.2f%%'%f['progress']])
			i=i+1
		
		return True
	
	def torrent_view_clicked(self, widget, event):
		print widget
		print event
		if event.button == 3:
			x = int(event.x)
			y = int(event.y)
			data = self.torrent_view.get_path_at_pos(x, y)
			if data is None:
				return True
			path, col, cellx, celly = data
			self.torrent_view.grab_focus()
			self.torrent_view.set_cursor(path, col, 0)
			unique_id = self.get_selected_torrent()
			widget = self.torrent_glade.get_widget("menu_pause")
			if(self.manager.is_user_paused(self.get_selected_torrent())):
				widget.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU))
				widget.get_children()[0].set_text(_("Start"))
			else:
				widget.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_MENU))
				widget.get_children()[0].set_text(_("Pause"))
			
			self.torrent_menu.popup(None, None, None, event.button, event.time)
			
			return True
		else:
			return False
	
	def start_pause(self, widget):
		print "Pause btn clicked"
		unique_id = self.get_selected_torrent()
		try:
			self.manager.set_user_pause(unique_id, not self.manager.is_user_paused(unique_id))
		except KeyError:
			pass
	
	def build_summary_tab(self):
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
		self.text_summary_uploaded_this_session	  = self.wtree.get_widget("summary_uploaded_this_session")
		self.text_summary_tracker                 = self.wtree.get_widget("summary_tracker")
		self.text_summary_tracker_response        = self.wtree.get_widget("summary_tracker_response")
		self.text_summary_tracker_status          = self.wtree.get_widget("summary_tracker_status")
		self.text_summary_next_announce           = self.wtree.get_widget("summary_next_announce")
		self.text_summary_compact_allocation      = self.wtree.get_widget("summary_compact_allocation")
		self.text_summary_eta					  = self.wtree.get_widget("summary_eta")

	def build_peer_tab(self):
		self.peer_view = self.wtree.get_widget("peer_view")
		self.peer_store = gtk.ListStore(str, str, str, str, str)
		self.peer_view.set_model(self.peer_store)
		
		self.peer_ip_column			=	dgtk.add_text_column(self.peer_view, _("IP Address"), 0)
		self.peer_client_column		=	dgtk.add_text_column(self.peer_view, _("Client"), 1)
		self.peer_complete_column	=	dgtk.add_text_column(self.peer_view, _("Percent Complete"), 2)
		self.peer_download_column	=	dgtk.add_text_column(self.peer_view, _("Download Rate"), 3)
		self.peer_upload_column		=	dgtk.add_text_column(self.peer_view, _("Upload Rate"), 4)


	def build_file_tab(self):
		self.file_view = self.wtree.get_widget("file_view")
		self.file_store = gtk.ListStore(bool, str, str, str, str)
		self.file_view.set_model(self.file_store)
		
		dgtk.add_toggle_column(self.file_view, _("Download"), 0, toggled_signal=self.file_toggled)
		dgtk.add_text_column(self.file_view, _("Filename"), 1).set_expand(True)
		dgtk.add_text_column(self.file_view, _("Size"), 2)
		dgtk.add_text_column(self.file_view, _("Offset"), 3)
		dgtk.add_text_column(self.file_view, _("Progress"), 4)
		
	
	def file_toggled(self, renderer, path):
		file_iter = self.file_store.get_iter_from_string(path)
		value = not renderer.get_active()
		self.file_store.set_value(file_iter, 0, value)
		file_filter = []
		itr = self.file_store.get_iter_first()
		while itr is not None:
			file_filter.append(not self.file_store.get_value(itr, 0))
			itr = self.file_store.iter_next(itr)
		print file_filter
		self.manager.set_file_filter(self.get_selected_torrent(), file_filter)
		
	def show_about_dialog(self, arg=None):
		dialogs.show_about_dialog()
	
	def show_pref_dialog(self, arg=None):
		self.preferences_dialog.show()
		self.apply_prefs()
		self.config.save_to_file()
	
	def show_plugin_dialog(self, arg=None):
		self.plugin_dialog.show()
	
	def apply_prefs(self):
		ulrate = self.config.get("max_upload_rate", int, default=-1)
		dlrate = self.config.get("max_download_rate", int, default=-1)
		if not (ulrate == -1):
			ulrate *= 1024
		if not (dlrate == -1):
			dlrate *= 1024
		ports = [self.config.get("tcp_port_range_lower", int, default=6881), 
					self.config.get("tcp_port_range_upper", int, default=6889)]
		if self.config.get("auto_end_seeding", bool, default=False):
			auto_seed_ratio = self.config.get("end_seed_ratio", float, default=1.0)
		else:
			auto_seed_ratio = -1
		self.tray_icon.set_visible(self.config.get("enable_system_tray", bool, default=True))
		self.manager.set_pref("listen_on", ports)
		self.manager.set_pref("max_upload_rate", ulrate)
		self.manager.set_pref("max_download_rate", dlrate)
		self.manager.set_pref("max_uploads", self.config.get("max_number_uploads", int, default=-1))
		self.manager.set_pref("max_connections", self.config.get("max_number_downloads", int, default=-1))
		self.manager.set_pref("auto_seed_ratio", auto_seed_ratio)
	
	# '%s %d%%'%(core.STATE_MESSAGES[state['state']], int(state['progress'] * 100))
	def get_message_from_state(self, torrent_state):
		state = torrent_state['state']
		is_paused = torrent_state['is_paused']
		progress = torrent_state['progress']
		progress = '%d%%'%int(progress * 100)
		if is_paused:
			message = 'Paused %s'%progress
		else:
			try:
				message = core.STATE_MESSAGES[state]
				if state in (1, 3, 4, 7):
					message = '%s %s'%(message, progress)
			except IndexError:
				message = ''
		return message
	
	# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
	def get_list_from_unique_id(self, unique_id):
		state = self.manager.get_torrent_state(unique_id)
		
		queue = int(state['queue_pos']) + 1 
		name = state['name']
		size = long(state['total_size'])
		progress = float(state['progress'] * 100)
		message = self.get_message_from_state(state)
		seeds = int(state['num_seeds'])
		seeds_t = int(state['total_seeds'])
		peers = int(state['num_peers'])
		peers_t = int(state['total_peers'])
		dlrate = int(state['download_rate'])
		ulrate = int(state['upload_rate'])
		try:
			eta = dcommon.get_eta(state["total_size"], state["total_done"], state["download_rate"])
		except ZeroDivisionError:
			eta = -1
		share = float(self.calc_share_ratio(unique_id, state))
		rlist =  [int(unique_id), int(queue), str(name), long(size), float(progress), str(message),
				int(seeds), int(seeds_t), int(peers), int(peers_t), int(dlrate), int(ulrate), int(eta), float(share)]	

		return rlist
	

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
				self.interactive_add_torrent(torrent_file, append=False)
			except core.DelugeError:
				print "duplicate torrent found, ignoring", torrent_file
		## add torrents in manager to interface
		# self.torrent_model.append([0, 1, "Hello, World", 2048, 50.0, "Hi", 1, 2, 1, 2, 2048, 2048, 120, 1.0])
		for uid in self.manager.get_unique_IDs():
			self.torrent_model.append(self.get_list_from_unique_id(uid))
		gobject.timeout_add(1000, self.update)
		try:
			self.is_running = True
			gtk.main()
		except KeyboardInterrupt:
			self.manager.quit()
	
	## Call via a timer to update the interface
	def update(self):
		# Make sure that the interface still exists
		try:
			tab = self.wtree.get_widget("torrent_info").get_current_page()
		except AttributeError:
			return False
		
		if self.something_screwed_up:
			dialogs.show_popup_warning(self.window, 
				_("For some reason, the previous state could not be loaded, so a blank state has been loaded for you."))
			restore_torrents = dialogs.show_popup_question(self.window,
				_("Would you like to attempt to reload the previous session's downloads?"))
			if restore_torrents:
				torrent_subdir = os.path.join(self.manager.base_dir, core.TORRENTS_SUBDIR)
				for torrent in os.listdir(torrent_subdir):
					if torrent.endswith('.torrent'):
						self.interactive_add_torrent(torrent)
			self.something_screwed_up = False
		
		# Update Statusbar and Tray Tips
		core_state = self.manager.get_state()
		connections = core_state['num_peers']
		dlrate = dcommon.frate(core_state['download_rate'])
		ulrate = dcommon.frate(core_state['upload_rate'])
		
		self.statusbar_temp_msg = '%s: %s   %s: %s   %s: %s'%(
			_('Connections'), connections, _('Download'), 
			dlrate, _('Upload'), ulrate)
		
		if 'DHT_nodes' in core_state.keys():
			dht_peers = core_state['DHT_nodes']
			if dht_peers == -1:
				dht_peers = '?'
			else:
				dht_peers = str(dht_peers)
			self.statusbar_temp_msg = self.statusbar_temp_msg + '   [DHT: %s]'%(dht_peers)
		
		msg = _("Deluge Bittorrent Client") + "\n" + \
			_("Connections") + ": " + str(connections) + "\n" + _("Download") + ": " + \
			dlrate + "\n" + _("Upload") + ": " + ulrate
		
		self.tray_icon.set_tooltip(msg)		

		#Update any active plugins
		self.plugins.update_active_plugins()
		
		# Put the generated message into the statusbar
		# This gives plugins a chance to write to the 
		# statusbar if they want
		self.statusbar.pop(1)
		self.statusbar.push(1, self.statusbar_temp_msg)

		# If no torrent is selected, select the first torrent:
		(temp, selection) = self.torrent_view.get_selection().get_selected()
		if selection is None:
			self.torrent_view.get_selection().select_path("0")
		#Torrent List
		itr = self.torrent_model.get_iter_first()
		if itr is None:
			return True

		while itr is not None:
			uid = self.torrent_model.get_value(itr, 0)
			try:
				state = self.manager.get_torrent_state(uid)
				tlist = self.get_list_from_unique_id(uid)
				for i in range(len(tlist)):
					try:
						self.torrent_model.set_value(itr, i, tlist[i])
					except:
						print "ERR", i, type(tlist[i]), tlist[i]
				itr = self.torrent_model.iter_next(itr)
			except core.InvalidUniqueIDError:
				self.torrent_model.remove(itr)
				if not self.torrent_model.iter_is_valid(itr):
					itr = None
		try:
			if self.manager.is_user_paused(self.get_selected_torrent()):
				self.wtree.get_widget("toolbutton_pause").set_stock_id(gtk.STOCK_MEDIA_PLAY)
			else:
				self.wtree.get_widget("toolbutton_pause").set_stock_id(gtk.STOCK_MEDIA_PAUSE)
		except KeyError:
			pass
		
		try:		
			state = self.manager.get_torrent_state(self.get_selected_torrent())
		except core.InvalidUniqueIDError:
			return True

		
		if tab == 0: #Details Pane	
			self.wtree.get_widget("summary_name").set_text(state['name'])
			self.text_summary_total_size.set_text(dcommon.fsize(state["total_size"]))
			self.text_summary_pieces.set_text(str(state["pieces"]))
			self.text_summary_total_downloaded.set_text(dcommon.fsize(state["total_done"]))
			#self.text_summary_total_uploaded.set_text()
			self.text_summary_download_rate.set_text(dcommon.frate(state["download_rate"]))
			self.text_summary_upload_rate.set_text(dcommon.frate(state["upload_rate"]))
			self.text_summary_seeders.set_text(dcommon.fseed(state))
			self.text_summary_peers.set_text(dcommon.fpeer(state))
			self.wtree.get_widget("progressbar").set_fraction(float(state['progress']))
			self.wtree.get_widget("progressbar").set_text(dcommon.fpcnt(state["progress"]))
			self.text_summary_share_ratio.set_text(str(self.calc_share_ratio(self.get_selected_torrent(), state)))
			self.text_summary_downloaded_this_session.set_text(dcommon.fsize(state["total_download"]))
			self.text_summary_uploaded_this_session.set_text(dcommon.fsize(state["total_upload"]))
			self.text_summary_tracker.set_text(str(state["tracker"]))
			#self.text_summary_tracker_response.set_text(str(state[""]))
			self.text_summary_tracker_status.set_text(str(state["tracker_ok"]))
			self.text_summary_next_announce.set_text(str(state["next_announce"]))
			#self.text_summary_compact_allocation.set_text(str(state[""]))
			self.text_summary_eta.set_text(dcommon.estimate_eta(state))
		elif tab == 1: #Peers List
			def biographer(model, path, iter, dictionary):
				assert(model.get_value(iter, 0) not in dictionary.keys())
				dictionary[model.get_value(iter, 0)] = model.get_string_from_iter(iter)
			
			class remover_data:
				def __init__(self, new_ips):
					self.new_ips = new_ips
					self.removed = False
			
			def remover(model, path, iter, data):
				if model.get_value(iter, 0) not in data.new_ips:
					model.remove(iter)
					data.removed = True
					return True
				else:
					return False

			unique_id = self.get_selected_torrent()
			
			new_peer_info = self.manager.get_torrent_peer_info(unique_id)
			
			new_ips = {}
			
			for index in range(len(new_peer_info)):
				if not new_peer_info[index]['client'] == "":
					assert(new_peer_info[index]['ip'] not in new_ips.keys())
					new_ips[new_peer_info[index]['ip']] = index
			
			while True:
				data = remover_data(new_ips.keys())
				self.peer_store.foreach(remover, data)
				if not data.removed:
					break
			
			curr_ips = {}
			
			self.peer_store.foreach(biographer, curr_ips)
			
			assert(self.peer_store.iter_n_children(None) == len(curr_ips.keys()))
			
			for peer in new_peer_info:
				if peer['ip'] in curr_ips.keys():
					self.peer_store.set(self.peer_store.get_iter_from_string(curr_ips[peer['ip']]),
											1,	unicode(peer['client'], 'Latin-1'),
											2,	'%.2f%%'%peer["peer_has"],
											3,	dcommon.frate(peer["download_speed"]),
											4,	dcommon.frate(peer["upload_speed"]))
			for peer in new_peer_info:
				if peer['ip'] not in curr_ips.keys() and peer['client'] is not "":
					self.peer_store.append([peer["ip"], 
											unicode(peer["client"], 'Latin-1'), 
											'%.2f%%'%peer["peer_has"], 
											dcommon.frate(peer["download_speed"]), 
											dcommon.frate(peer["upload_speed"])])
			#print new_ips
			#print curr_ips
			#print new_peer_info
			del new_peer_info
			del new_ips
			del curr_ips
			
			
								
		elif tab == 2: #File List
			pass
		else:
			pass

		return True
	
	def calc_share_ratio(self, unique_id, torrent_state):
		r = float(self.manager.calc_ratio(unique_id, torrent_state))
		return r
	
	def get_selected_torrent(self):
		try:
			return self.torrent_model.get_value(self.torrent_view.get_selection().get_selected()[1], 0)
		except TypeError:
			return None
	
	def on_drag_data(self, widget, drag_context, x, y, selection_data, info, timestamp):
		uri_split = selection_data.data.strip().split()
		for uri in uri_split:
			path = urllib.url2pathname(uri).strip('\r\n\x00')
			if path.startswith('file:\\\\\\'):
				path = path[8:]
			elif path.startswith('file://'):
				path = path[7:]
			elif path.startswith('file:'):
				path = path[5:]
			if path.endswith('.torrent'):
				self.interactive_add_torrent(path)
				

		
	def interactive_add_torrent(self, torrent, append=True):
		if self.config.get('use_default_dir', bool, default=False):
			path = self.config.get('default_download_path', default=os.path.expandvars('$HOME'))
		else:
			path = dialogs.show_directory_chooser_dialog(self.window)
			if path is None:
				return
	
		try:
			unique_id = self.manager.add_torrent(torrent, path, self.config.get('use_compact_storage', bool, default=False))
		except core.InsufficientFreeSpaceError, err:	
			nice_need = dcommon.fsize(err.needed_space)
			nice_free = dcommon.fsize(err.free_space)
			
			
		if append:
			self.torrent_model.append(self.get_list_from_unique_id(unique_id))
		
		
		
	def add_torrent_clicked(self, obj=None):
		torrent = dialogs.show_file_open_dialog()
		if torrent is not None:
			self.interactive_add_torrent(torrent)
	
	def add_torrent_url_clicked(self, obj=None):
		dlg = gtk.Dialog(title=_("Add torrent from URL"), parent=self.window,
			buttons=(gtk.STOCK_CANCEL, 0, gtk.STOCK_OK, 1))
		dlg.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		
		label = gtk.Label(_("Enter the URL of the .torrent to download"))
		entry = gtk.Entry()
		dlg.vbox.pack_start(label)
		dlg.vbox.pack_start(entry)
		dlg.show_all()
		result = dlg.run()
		url = entry.get_text()
		dlg.destroy()
		
		if result == 1:
			opener = urllib.URLopener()
			filename, headers = opener.retrieve(url)
			if filename.endswith(".torrent") or headers["content-type"]=="application/x=bittorrent":
				self.interactive_add_torrent(filename)
		
	
	def remove_torrent_clicked(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			glade     = gtk.glade.XML(dcommon.get_glade_file("dgtkpopups.glade"), domain='deluge')
			asker     = glade.get_widget("remove_torrent_dlg")
			
			asker.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))

			warning   =  glade.get_widget("warning")
			warning.set_text(" ")

			data_also  =  glade.get_widget("data_also")
			data_also.connect("toggled", self.remove_toggle_warning, warning)

			response = asker.run()
			asker.destroy()
			if response == 1:
				self.manager.remove_torrent(torrent, data_also.get_active())
				self.clear_details_pane()
	
	def clear_details_pane(self):
		self.wtree.get_widget("progressbar").set_text("")
		self.text_summary_total_size.set_text("")
		self.text_summary_pieces.set_text("")
		self.text_summary_total_downloaded.set_text("")
		self.text_summary_total_uploaded.set_text("")
		self.text_summary_download_rate.set_text("")
		self.text_summary_upload_rate.set_text("")
		self.text_summary_seeders.set_text("")
		self.text_summary_peers.set_text("")
		self.wtree.get_widget("progressbar").set_fraction(0.0)
		self.text_summary_share_ratio.set_text("")
		self.text_summary_downloaded_this_session.set_text("")
		self.text_summary_uploaded_this_session.set_text("")
		self.text_summary_tracker.set_text("")
		self.text_summary_tracker_response.set_text("")
		self.text_summary_tracker_status.set_text("")
		self.text_summary_next_announce.set_text("")
		self.text_summary_compact_allocation.set_text("")
		self.text_summary_eta.set_text("")
		self.peer_store.clear()
		self.file_store.clear()


	def remove_toggle_warning(self, args, warning):
		if not args.get_active():
			warning.set_text(" ")
		else:
			warning.set_markup("<i>" + _("Warning - all downloaded files for this torrent will be deleted!") + "</i>")
		return False

	def update_tracker(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.update_tracker(torrent)
	
	def clear_finished(self, obj=None):
		print "Clearing Completed Torrents"
		self.manager.clear_completed()
	
	def q_torrent_up(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.queue_up(torrent)
				
	def q_torrent_down(self, obj=None):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.queue_down(torrent)

	def q_to_bottom(self, widget):
		torrent = self.get_selected_torrent()
		if torrent is not None:
			self.manager.queue_bottom(torrent)
				
	def toolbar_toggle(self, widget):
		if widget.get_active():
			self.wtree.get_widget("tb_left").show()
			self.wtree.get_widget("tb_middle").show()
			self.wtree.get_widget("tb_right").show()
		else:
			self.wtree.get_widget("tb_left").hide()
			self.wtree.get_widget("tb_middle").hide()
			self.wtree.get_widget("tb_right").hide()
	
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
		
	def load_window_settings(self):
		self.wtree.get_widget("chk_infopane").set_active(self.config.get("show_infopane", bool, default=True))
		self.wtree.get_widget("chk_toolbar").set_active(self.config.get("show_toolbar", bool, default=True))
		self.wtree.get_widget("chk_size").set_active(self.config.get("show_size", bool, default=True))
		self.wtree.get_widget("chk_status").set_active(self.config.get("show_status", bool, default=True))
		self.wtree.get_widget("chk_seed").set_active(self.config.get("show_seeders", bool, default=True))
		self.wtree.get_widget("chk_peer").set_active(self.config.get("show_peers", bool, default=True))
		self.wtree.get_widget("chk_download").set_active(self.config.get("show_dl", bool, default=True))
		self.wtree.get_widget("chk_upload").set_active(self.config.get("show_ul", bool, default=True))
		self.wtree.get_widget("chk_eta").set_active(self.config.get("show_eta", bool, default=True))
		self.wtree.get_widget("chk_ratio").set_active(self.config.get("show_share", bool, default=True))
	
	def save_window_settings(self):
		self.config.set("show_infopane", self.wtree.get_widget("chk_infopane").get_active())
		self.config.set("show_toolbar", self.wtree.get_widget("chk_toolbar").get_active())
		self.config.set("show_size", self.size_column.get_visible())
		self.config.set("show_status", self.status_column.get_visible())
		self.config.set("show_seeders", self.seed_column.get_visible())
		self.config.set("show_peers", self.peer_column.get_visible())
		self.config.set("show_dl", self.dl_column.get_visible())
		self.config.set("show_ul", self.ul_column.get_visible())
		self.config.set("show_eta", self.eta_column.get_visible())
		self.config.set("show_share", self.share_column.get_visible())
	
	def save_window_geometry(self):
		x, y = self.window.get_position()
		w, h = self.window.get_size()
		self.config.set('window_x_pos', x)
		self.config.set('window_y_pos', y)
		self.config.set('window_width', w)
		self.config.set('window_height',h)
		
	def load_window_geometry(self):
		x = self.config.get('window_x_pos', int, default=0)
		y = self.config.get('window_y_pos', int, default=0)
		w = self.config.get('window_width', int, default=640)
		h = self.config.get('window_height',int, default=480)
		self.window.move(x, y)
		self.window.resize(w, h)
		

	def close(self, widget, event):
		if self.config.get("close_to_tray", bool, default=False) and self.config.get("enable_system_tray", bool, default=True) and self.has_tray:
			self.save_window_geometry()
			self.window.hide()
			return True
		else:
			self.quit()
		
	def quit(self, widget=None):
		self.save_window_geometry()
		self.window.hide()
		self.shutdown()
	
	def shutdown(self):
		enabled_plugins = ':'.join(self.plugins.get_enabled_plugins())
		self.config.set('enabled_plugins', enabled_plugins)
		self.save_window_settings()
		self.config.save_to_file(self.conf_file)
		self.plugins.shutdown_all_plugins()
		self.manager.quit()
		gtk.main_quit()
	


		
## For testing purposes, create a copy of the interface
if __name__ == "__main__":
	interface = DelugeGTK()
	interface.start()
