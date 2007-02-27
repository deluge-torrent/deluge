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

import sys, os, os.path, gettext, urllib
import deluge, dcommon, dgtk, ipc_manager
import delugeplugins, pref
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject
import xdg, xdg.BaseDirectory


class DelugeGTK:

	def __init__(self):
		self.is_running = False
		self.ipc_manager = ipc_manager.Manager(self)
		self.torrent_file_queue = []
		#Load up a config file:
		self.conf_file = dcommon.CONFIG_DIR + '/deluge.conf'
		if os.path.isdir(self.conf_file):
			print 'Weird, the file I was trying to write to, %s, is an existing directory'%(self.conf_file)
			sys.exit(0)
		if not os.path.isfile(self.conf_file):
			f = open(self.conf_file, mode='w')
			f.flush()
			f.close()
		#Start the Deluge Manager:
		self.manager = deluge.Manager("DE", "0490", "Deluge 0.4.90.1", dcommon.CONFIG_DIR)
		self.plugins = delugeplugins.PluginManager(self.manager, self)
		self.plugins.add_plugin_dir(dcommon.PLUGIN_DIR)
		if os.path.isdir(dcommon.CONFIG_DIR + '/plugins'):
			self.plugins.add_plugin_dir(dcommon.CONFIG_DIR + '/plugins')
		self.plugins.scan_for_plugins()
		self.config = pref.Preferences()
		self.config.load_from_file(self.conf_file)
		#Set up the interface:
		self.wtree = gtk.glade.XML(dcommon.get_glade_file("delugegtk.glade"))
		self.window = self.wtree.get_widget("main_window")
		self.window.hide()
		self.toolbar = self.wtree.get_widget("tb_middle")
		self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL,[('text/uri-list', 0, 80)], gtk.gdk.ACTION_COPY)
		self.window.connect("delete_event", self.close)
		self.window.connect("drag_data_received", self.on_drag_data)
		self.window.set_title('%s %s'%(dcommon.PROGRAM_NAME, dcommon.PROGRAM_VERSION))
		self.window.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.statusbar = self.wtree.get_widget("statusbar")
		
		
		## Construct the Interface
		self.build_tray_icon()
		self.build_about_dialog()
		self.build_pref_dialog()
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
		self.tray = gtk.StatusIcon()
		self.tray.set_from_file(dcommon.get_pixmap("deluge32.png"))
		self.tray.set_tooltip("Deluge BitTorrent Client")
		tray_glade = gtk.glade.XML(dcommon.get_glade_file("dgtkpopups.glade"))
		self.tray_menu = tray_glade.get_widget("tray_menu")
		dic = {	"show_hide_window": self.force_show_hide,
				"add_torrent":  self.add_torrent_clicked,
				"clear_finished": self.clear_finished,
				"preferences": self.show_pref_dialog,
				"plugins": self.show_plugin_dialog,
				"quit": self.quit,
				}
		tray_glade.signal_autoconnect(dic)
		self.tray.connect("popup-menu", self.tray_popup, None)
		self.tray.connect("activate", self.tray_clicked, None)
		
	def tray_popup(self, status_icon, button, activate_time, arg0=None):
		print "Tray Clicked"
		self.tray_menu.popup(None, None, gtk.status_icon_position_menu, button, activate_time, self.tray)
	
	def tray_clicked(self, status_icon=None, arg=None):
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
	
	
			
	
	def build_about_dialog(self):
		gtk.about_dialog_set_url_hook(dcommon.open_url_in_browser)
		self.abt = gtk.glade.XML(dcommon.get_glade_file("aboutdialog.glade")).get_widget("aboutdialog")
		self.abt.set_name(dcommon.PROGRAM_NAME)
		self.abt.set_version(dcommon.PROGRAM_VERSION)
		self.abt.set_authors(["Zach Tibbits", "A. Zakai"])
		self.abt.set_artists(["Andrew Wedderburn"])
		self.abt.set_website("http://deluge-torrent.org")
		self.abt.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.abt.set_logo(gtk.gdk.pixbuf_new_from_file(
				dcommon.get_pixmap("deluge-about.png")))
	
	def build_pref_dialog(self):
		self.prf_glade = gtk.glade.XML(dcommon.get_glade_file("dgtkpref.glade"))
		self.prf = self.prf_glade.get_widget("pref_dialog")
		self.prf.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.prf_glade.signal_autoconnect({"tray_toggle": self.tray_toggle,})
		self.plugin_dlg = self.prf_glade.get_widget("plugin_dialog")
		self.plugin_dlg.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.plugin_view = self.prf_glade.get_widget("plugin_view")
		self.plugin_store = gtk.ListStore(str, bool)
		self.plugin_view.set_model(self.plugin_store)
		self.plugin_view.get_selection().set_select_function(self.plugin_clicked, full=True)
		name_col = dgtk.add_text_column(self.plugin_view, _("Plugin"), 0)
		name_col.set_expand(True)
		dgtk.add_toggle_column(self.plugin_view, _("Enabled"), 1, toggled_signal=self.plugin_toggled)
		self.prf_glade.signal_autoconnect({'plugin_pref': self.plugin_pref})
	
	def plugin_clicked(self, selection, model, path, is_selected):
		if is_selected:
			return True
		name = model.get_value(model.get_iter(path), 0)
		plugin = self.plugins.get_plugin(name)
		version = plugin['version']
		config = plugin['config']
		description = plugin['description']
		if name in self.plugins.get_enabled_plugins():
			self.prf_glade.get_widget("plugin_conf").set_sensitive(config)
		else:
			self.prf_glade.get_widget("plugin_conf").set_sensitive(False)
		self.prf_glade.get_widget("plugin_text").get_buffer(
			).set_text("%s\nVersion: %s\n\n%s"%
			(name, version, description))
		return True

	def plugin_toggled(self, renderer, path):
		plugin_iter = self.plugin_store.get_iter_from_string(path)
		plugin_name = self.plugin_store.get_value(plugin_iter, 0)
		plugin_value = not self.plugin_store.get_value(plugin_iter, 1)
		self.plugin_store.set_value(plugin_iter, 1, plugin_value)
		if plugin_value:
			self.plugins.enable_plugin(plugin_name)
			self.prf_glade.get_widget("plugin_conf").set_sensitive(
				self.plugins.get_plugin(plugin_name)['config'])
		else:
			self.plugins.disable_plugin(plugin_name)
				
	def plugin_pref(self, widget=None):
		(model, plugin_iter) = self.plugin_view.get_selection().get_selected()
		plugin_name = self.plugin_store.get_value(plugin_iter, 0)
		self.plugins.configure_plugin(plugin_name)

	def build_torrent_table(self):
		## Create the torrent listview
		self.torrent_view = self.wtree.get_widget("torrent_view")
		self.torrent_glade = gtk.glade.XML(dcommon.get_glade_file("torrent_menu.glade"))
		self.torrent_menu = self.torrent_glade.get_widget("torrent_menu")		
		self.torrent_glade.signal_autoconnect({"update_tracker": self.update_tracker,
					"clear_finished": self.clear_finished,
					"queue_up": self.q_torrent_up,
					"queue_down": self.q_torrent_down,
					"queue_bottom": self.q_to_bottom,
					})
		# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
		self.torrent_model = gtk.ListStore(int, int, str, str, float, str, str, str, str, str, str, str)
		self.torrent_view.set_model(self.torrent_model)
		self.torrent_view.set_rules_hint(True)
		self.torrent_view.set_reorderable(True)

		
		## Initializes the columns for the torrent_view
		self.queue_column 	= 	dgtk.add_text_column(self.torrent_view, "#", 1)
		self.name_column 	=	dgtk.add_text_column(self.torrent_view, _("Name"), 2)
		self.size_column 	=	dgtk.add_text_column(self.torrent_view, _("Size"), 3)
		self.status_column 	= 	dgtk.add_progress_column(self.torrent_view, _("Status"), 4, 5)
		self.seed_column 	=	dgtk.add_text_column(self.torrent_view, _("Seeders"), 6)
		self.peer_column 	=	dgtk.add_text_column(self.torrent_view, _("Peers"), 7)
		self.dl_column 		=	dgtk.add_text_column(self.torrent_view, _("Download"), 8)
		self.ul_column 		=	dgtk.add_text_column(self.torrent_view, _("Upload"), 9)
		self.eta_column 	=	dgtk.add_text_column(self.torrent_view, _("Time Remaining"), 10)
		self.share_column 	= 	dgtk.add_text_column(self.torrent_view, _("Ratio"), 11)
		
		self.status_column.set_expand(True)
		
		self.torrent_view.get_selection().set_select_function(self.torrent_clicked, full=True)
		self.torrent_view.connect("button-press-event", self.torrent_view_clicked)
		
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
			
			self.torrent_menu.popup(None, None, None, event.button, event.time)
			
			return True
		else:
			return False
	
	def start_pause(self, widget):
		print "Pause btn clicked"
		unique_id = self.get_selected_torrent()
		self.manager.set_user_pause(unique_id, not self.manager.is_user_paused(unique_id))
	
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
		self.abt.show_all()
		self.abt.run()
		self.abt.hide_all()
	
	def show_pref_dialog(self, arg=None):
		#Try to get current settings from pref, if an error occurs, the default settings will be used:
		try:
			# Page 1
			self.prf_glade.get_widget("chk_use_tray").set_active(self.config.get("enable_system_tray", bool, default=True))
			self.prf_glade.get_widget("chk_min_on_close").set_active(self.config.get("close_to_tray", bool, default=False))
			if(self.config.get("use_default_dir", bool, False)):
				self.prf_glade.get_widget("radio_save_all_to").set_active(True)
			else:
				self.prf_glade.get_widget("radio_ask_save").set_active(True)
			self.prf_glade.get_widget("download_path_button").set_filename(self.config.get("default_download_path", 
																	str, default=os.path.expandvars('$HOME')))
			self.prf_glade.get_widget("chk_autoseed").set_active(self.config.get("auto_end_seeding", bool, default=False))
			self.prf_glade.get_widget("ratio_spinner").set_value(self.config.get("end_seed_ratio", float, default=0.0))
			# self.prf_glade.get_widget("chk_compact").set_active(self.config.get("use_compact_storage", bool, default=False))
			self.prf_glade.get_widget("chk_compact").set_active(False)
			self.prf_glade.get_widget("chk_compact").set_sensitive(False)
			# Page 2
			self.prf_glade.get_widget("active_port_label").set_text(str(self.manager.get_state()['port']))
			self.prf_glade.get_widget("spin_port_min").set_value(self.config.get("tcp_port_range_lower", int, default=6881))
			self.prf_glade.get_widget("spin_port_max").set_value(self.config.get("tcp_port_range_upper", int, default=6889))
			self.prf_glade.get_widget("spin_max_upload").set_value(self.config.get("max_upload_rate", int, default=-1))
			self.prf_glade.get_widget("spin_num_upload").set_value(self.config.get("max_number_uploads", int, default=-1))
			self.prf_glade.get_widget("spin_max_download").set_value(self.config.get("max_download_rate", int, default=-1))
			self.prf_glade.get_widget("spin_num_download").set_value(self.config.get("max_number_downloads", int, default=-1))
		except KeyError:
			pass
		self.prf.show()		
		result = self.prf.run()
		self.prf.hide()
		print result
		if result == 1:
			self.config.set("enable_system_tray", self.prf_glade.get_widget("chk_use_tray").get_active())
			self.config.set("close_to_tray", self.prf_glade.get_widget("chk_min_on_close").get_active())
			self.config.set("use_default_dir", self.prf_glade.get_widget("radio_save_all_to").get_active())
			self.config.set("default_download_path", self.prf_glade.get_widget("download_path_button").get_filename())
			self.config.set("auto_end_seeding", self.prf_glade.get_widget("chk_autoseed").get_active())
			self.config.set("end_seed_ratio", self.prf_glade.get_widget("ratio_spinner").get_value())
			self.config.set("use_compact_storage", self.prf_glade.get_widget("chk_compact").get_active())
			
			self.config.set("tcp_port_range_lower", self.prf_glade.get_widget("spin_port_min").get_value())
			self.config.set("tcp_port_range_upper", self.prf_glade.get_widget("spin_port_max").get_value())
			self.config.set("max_upload_rate", self.prf_glade.get_widget("spin_max_upload").get_value())
			self.config.set("max_number_uploads", self.prf_glade.get_widget("spin_num_upload").get_value())
			self.config.set("max_download_rate", self.prf_glade.get_widget("spin_max_download").get_value())
			self.config.set("max_number_downloads", self.prf_glade.get_widget("spin_num_download").get_value())
			
			self.config.save_to_file(self.conf_file)
		self.apply_prefs()
	
	def show_plugin_dialog(self, arg=None):
		self.plugin_store.clear()
		for plugin in self.plugins.get_available_plugins():
			if plugin in self.plugins.get_enabled_plugins():
				self.plugin_store.append( (plugin, True) )
			else:
				self.plugin_store.append( (plugin, False) )
		self.prf_glade.get_widget("plugin_text").get_buffer().set_text("")
		self.prf_glade.get_widget("plugin_conf").set_sensitive(False)
		self.plugin_dlg.show()
		self.plugin_dlg.run()
		self.plugin_dlg.hide()
		
		
	def tray_toggle(self, obj):
		if obj.get_active():
			self.prf_glade.get_widget("chk_min_on_close").set_sensitive(True)
		else:
			self.prf_glade.get_widget("chk_min_on_close").set_sensitive(False)

	
	def apply_prefs(self):
		ulrate = self.config.get("max_upload_rate", int, default=-1)
		dlrate = self.config.get("max_download_rate", int, default=-1)
		if not (ulrate == -1):
			ulrate *= 1024
		if not (dlrate == -1):
			ulrate *= 1024
		ports = [self.config.get("tcp_port_range_lower", int, default=6881), 
					self.config.get("tcp_port_range_upper", int, default=6889)]
		self.tray.set_visible(self.config.get("enable_system_tray", bool, default=True))
		self.manager.set_pref("listen_on", ports)
		self.manager.set_pref("max_upload_rate", ulrate)
		self.manager.set_pref("max_download_rate", dlrate)
		self.manager.set_pref("max_uploads", self.config.get("max_number_uploads", int, default=-1))
		self.manager.set_pref("max_connections", self.config.get("max_number_downloads", int, default=-1))
			
	
	# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
	def get_list_from_unique_id(self, unique_id):
		state = self.manager.get_torrent_state(unique_id)
		queue = int(state['queue_pos']) + 1 
		name = state['name']
		size = dcommon.fsize(state['total_size'])
		progress = float(state['progress'] * 100)
		message = '%s %d%%'%(deluge.STATE_MESSAGES[state['state']], int(state['progress'] * 100))
		seeds = dcommon.fseed(state)
		peers = dcommon.fpeer(state)
		dlrate = dcommon.frate(state['download_rate'])
		ulrate = dcommon.frate(state['upload_rate'])
		eta = dcommon.estimate_eta(state)
		share = self.calc_share_ratio(unique_id, state)
		return [unique_id, queue, name, size, progress, message,
				seeds, peers, dlrate, ulrate, eta, share]	
	

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
			except deluge.DelugeError:
				print "duplicate torrent found, ignoring", torrent_file
		## add torrents in manager to interface
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
		
		self.tray.set_tooltip(msg)		

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
				for i in range(12):
					self.torrent_model.set_value(itr, i, tlist[i])
				itr = self.torrent_model.iter_next(itr)
			except deluge.InvalidUniqueIDError:
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
		self.saved_peer_info = None
		

		
		if tab == 0: #Details Pane	
			try:		
				state = self.manager.get_torrent_state(self.get_selected_torrent())
			except deluge.InvalidUniqueIDError:
				return True
			self.wtree.get_widget("progressbar").set_text('%s %s'%(str(state["name"]), dcommon.fpcnt(state["progress"])))
			self.text_summary_total_size.set_text(dcommon.fsize(state["total_size"]))
			self.text_summary_pieces.set_text(str(state["pieces"]))
			self.text_summary_total_downloaded.set_text(dcommon.fsize(state["total_done"]))
			#self.text_summary_total_uploaded.set_text()
			self.text_summary_download_rate.set_text(dcommon.frate(state["download_rate"]))
			self.text_summary_upload_rate.set_text(dcommon.frate(state["upload_rate"]))
			self.text_summary_seeders.set_text(dcommon.fseed(state))
			self.text_summary_peers.set_text(dcommon.fpeer(state))
			self.wtree.get_widget("progressbar").set_fraction(float(state['progress']))
			self.text_summary_share_ratio.set_text(self.calc_share_ratio(self.get_selected_torrent(), state))
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
			
			self.saved_peer_info = self.manager.get_torrent_peer_info(unique_id)
			
			
			new_peer_info = self.saved_peer_info
			
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
			path = dgtk.show_directory_chooser_dialog(self.window)
			if path is None:
				return
		unique_id = self.manager.add_torrent(torrent, path, self.config.get('use_compact_storage', bool, default=False))
		if append:
			self.torrent_model.append(self.get_list_from_unique_id(unique_id))
		
		
		
	def add_torrent_clicked(self, obj=None):
		torrent = dgtk.show_file_open_dialog()
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
			glade     = gtk.glade.XML(dcommon.get_glade_file("dgtkpopups.glade"))
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

	def close(self, widget, event):
		if self.config.get("close_to_tray", bool, default=False) and self.config.get("enable_system_tray", bool, default=True):
			self.window.hide()
			return True
		else:
			self.quit()
		
	def quit(self, widget=None):
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
