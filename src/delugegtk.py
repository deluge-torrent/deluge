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
import deluge, dcommon, dgtk, delugeplugins
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject
import xdg, xdg.BaseDirectory
import dbus, dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib 

class DelugeGTK(dbus.service.Object):
	## external_add_torrent should only be called from outside the class	
	@dbus.service.method('org.deluge_torrent.DelugeInterface')
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

	def __init__(self, bus_name=dbus.service.BusName('org.deluge_torrent.Deluge',
			bus=dbus.SessionBus()),	object_path='/org/deluge_torrent/DelugeObject'):
		dbus.service.Object.__init__(self, bus_name, object_path)
		self.is_running = False
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
		self.pref = dcommon.DelugePreferences()
		self.load_default_settings()
		self.pref.load_from_file(self.conf_file)
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
		
		enable_plugins = self.pref.get('enabled_plugins').split(':')
		print enable_plugins
		for plugin in enable_plugins:
			try:
				self.plugins.enable_plugin(plugin)
			except KeyError:
				pass
		self.apply_prefs()
	
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
					"update_tracker": self.update_tracker,
					"clear_finished": self.clear_finished,
					"queue_up": self.q_torrent_up,
					"queue_down": self.q_torrent_down,
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
		self.tray_menu.popup(None, None, gtk.status_icon_position_menu,
			button, activate_time, self.tray)
	
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
		self.abt = gtk.AboutDialog()
		self.abt.set_name(dcommon.PROGRAM_NAME)
		self.abt.set_version(dcommon.PROGRAM_VERSION)
		self.abt.set_authors(["Zach Tibbits", "A. Zakai"])
		self.abt.set_artists(["Andrew Wedderburn"])
		self.abt.set_website("http://deluge-torrent.org")
		self.abt.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.abt.set_logo(gtk.gdk.pixbuf_new_from_file(
				dcommon.get_pixmap("deluge32.png")))
	
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
		self.view = self.wtree.get_widget("torrent_view")
		# UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, Share
		self.store = gtk.ListStore(int, int, str, str, float, str, str, str, str, str, str, str)
		self.view.set_model(self.store)
		self.view.set_rules_hint(True)
		self.view.set_reorderable(True)
		
		## Initializes the columns for the torrent_view
		self.queue_column 	= 	dgtk.add_text_column(self.view, "#", 1)
		self.name_column 	=	dgtk.add_text_column(self.view, _("Name"), 2)
		self.size_column 	=	dgtk.add_text_column(self.view, _("Size"), 3)
		self.status_column 	= 	dgtk.add_progress_column(self.view, _("Status"), 4, 5)
		self.seed_column 	=	dgtk.add_text_column(self.view, _("Seeders"), 6)
		self.peer_column 	=	dgtk.add_text_column(self.view, _("Peers"), 7)
		self.dl_column 		=	dgtk.add_text_column(self.view, _("Download"), 8)
		self.ul_column 		=	dgtk.add_text_column(self.view, _("Upload"), 9)
		self.eta_column 	=	dgtk.add_text_column(self.view, _("Time Remaining"), 10)
		self.share_column 	= 	dgtk.add_text_column(self.view, _("Ratio"), 11)
		
		self.status_column.set_expand(True)
		
		self.view.get_selection().set_select_function(self.torrent_clicked, full=True)

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
		for f in all_files:
			self.file_store.append([f['path'], dcommon.fsize(f['size']), 
					f['offset'], '%.2f%%'%f['progress'], True])
		
		return True
		
	
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
		self.text_summary_uplodaded_this_session  = self.wtree.get_widget("summary_uploaded_this_session")
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
		self.file_store = gtk.ListStore(str, str, str, str, bool)
		self.file_view.set_model(self.file_store)
		
		filename_col = dgtk.add_text_column(self.file_view, _("Filename"), 0)
		dgtk.add_text_column(self.file_view, _("Size"), 1)
		dgtk.add_text_column(self.file_view, _("Offset"), 2)
		dgtk.add_text_column(self.file_view, _("Progress"), 3)
		dgtk.add_toggle_column(self.file_view, _("Download"), 4)

		filename_col.set_expand(True)
	
	def file_toggled(self, renderer, path):
		file_iter = self.file_store.get_iter_from_string(path)
		value = not renderer.get_active()
		self.file_store.set_value(file_iter, 4, value)
		file_filter = []
		itr = self.file_store.get_iter_first()
		while itr is not None:
			file_filter.append(self.file_store.get_value(itr, 4))
			itr = self.file_store.iter_next(itr)
		self.manager.set_file_filter(self.get_selected_torrent(), file_filter)
		

	def load_default_settings(self):
		self.pref.set("enable_system_tray", True)
		self.pref.set("close_to_tray", False)
		self.pref.set("use_default_dir", False)
		self.pref.set("default_download_path", os.path.expandvars('$HOME'))
		self.pref.set("auto_end_seeding", False)
		self.pref.set("end_seed_ratio", 1.0)
		self.pref.set("use_compact_storage", False)
		
		self.pref.set("tcp_port_range_lower", 6881)
		self.pref.set("tcp_port_range_upper", 6889)
		self.pref.set("max_upload_rate", -1)
		self.pref.set("max_number_uploads", -1)
		self.pref.set("max_download_rate", -1)
		self.pref.set("max_number_downloads", -1)
		default_plugins = []
		for name in self.plugins.get_available_plugins():
			if self.plugins.get_plugin(name)['default']:
				default_plugins.append(name)
		self.pref.set("enabled_plugins", ';'.join(default_plugins))




	def show_about_dialog(self, arg=None):
		self.abt.show_all()
		self.abt.run()
		self.abt.hide_all()
	
	def show_pref_dialog(self, arg=None):
		#Try to get current settings from pref, if an error occurs, the default settings will be used:
		try:
			# Page 1
			self.prf_glade.get_widget("chk_use_tray").set_active(self.pref.get("enable_system_tray", bool))
			self.prf_glade.get_widget("chk_min_on_close").set_active(self.pref.get("close_to_tray", bool))
			if(self.pref.get("use_default_dir", bool)):
				self.prf_glade.get_widget("radio_save_all_to").set_active(True)
			else:
				self.prf_glade.get_widget("radio_ask_save").set_active(True)
			
			self.prf_glade.get_widget("download_path_button").set_filename(self.pref.get("default_download_path", str))
			self.prf_glade.get_widget("chk_autoseed").set_active(self.pref.get("auto_end_seeding", bool))
			self.prf_glade.get_widget("ratio_spinner").set_value(self.pref.get("end_seed_ratio", float))
			self.prf_glade.get_widget("chk_compact").set_active(self.pref.get("use_compact_storage", bool))
			# Page 2
			self.prf_glade.get_widget("spin_port_min").set_value(self.pref.get("tcp_port_range_lower", int))
			self.prf_glade.get_widget("spin_port_max").set_value(self.pref.get("tcp_port_range_upper", int))
			self.prf_glade.get_widget("spin_max_upload").set_value(self.pref.get("max_upload_rate", int))
			self.prf_glade.get_widget("spin_num_upload").set_value(self.pref.get("max_number_uploads", int))
			self.prf_glade.get_widget("spin_max_download").set_value(self.pref.get("max_download_rate", int))
			self.prf_glade.get_widget("spin_num_download").set_value(self.pref.get("max_number_downloads", int))
		except KeyError:
			pass
		self.prf.show()		
		result = self.prf.run()
		self.prf.hide()
		print result
		if result == 1:
			self.pref.set("enable_system_tray", self.prf_glade.get_widget("chk_use_tray").get_active())
			self.pref.set("close_to_tray", self.prf_glade.get_widget("chk_min_on_close").get_active())
			self.pref.set("use_default_dir", self.prf_glade.get_widget("radio_save_all_to").get_active())
			self.pref.set("default_download_path", self.prf_glade.get_widget("download_path_button").get_filename())
			self.pref.set("auto_end_seeding", self.prf_glade.get_widget("chk_autoseed").get_active())
			self.pref.set("end_seed_ratio", self.prf_glade.get_widget("ratio_spinner").get_value())
			self.pref.set("use_compact_storage", self.prf_glade.get_widget("chk_compact").get_active())
			
			self.pref.set("tcp_port_range_lower", self.prf_glade.get_widget("spin_port_min").get_value())
			self.pref.set("tcp_port_range_upper", self.prf_glade.get_widget("spin_port_max").get_value())
			self.pref.set("max_upload_rate", self.prf_glade.get_widget("spin_max_upload").get_value())
			self.pref.set("max_number_uploads", self.prf_glade.get_widget("spin_num_upload").get_value())
			self.pref.set("max_download_rate", self.prf_glade.get_widget("spin_max_download").get_value())
			self.pref.set("max_number_downloads", self.prf_glade.get_widget("spin_num_download").get_value())
			
			self.pref.save_to_file(self.conf_file)
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
		self.tray.set_visible(self.pref.get("enable_system_tray", bool))
		self.manager.set_pref("listen_on", [self.pref.get("tcp_port_range_lower", int), self.pref.get("tcp_port_range_upper", int)])
		self.manager.set_pref("max_uploads", self.pref.get("max_number_uploads", int))
		self.manager.set_pref("max_download_rate", self.pref.get("max_download_rate", int))
		self.manager.set_pref("max_connections", self.pref.get("max_number_downloads", int))
			
	
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
			self.store.append(self.get_list_from_unique_id(uid))
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

		self.plugins.update_active_plugins()

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
		
		self.saved_peer_info = None
		

		
		if tab == 0: #Details Pane	
			try:		
				state = self.manager.get_torrent_state(self.get_selected_torrent())
			except deluge.InvalidUniqueIDError:
				return True
			self.wtree.get_widget("progressbar").set_text('%s %s'%(str(state["name"]), dcommon.fpcnt(state["progress"])))
			self.text_summary_total_size.set_text(dcommon.fsize(state["total_size"]))
			self.text_summary_pieces.set_text(str(state["pieces"]))
			self.text_summary_total_downloaded.set_text(dcommon.fsize(state["total_download"]))
			self.text_summary_total_uploaded.set_text(dcommon.fsize(state["total_upload"]))
			self.text_summary_download_rate.set_text(dcommon.frate(state["download_rate"]))
			self.text_summary_upload_rate.set_text(dcommon.frate(state["upload_rate"]))
			self.text_summary_seeders.set_text(dcommon.fseed(state))
			self.text_summary_peers.set_text(dcommon.fpeer(state))
			self.wtree.get_widget("progressbar").set_fraction(float(state['progress']))
			self.text_summary_share_ratio.set_text(self.calc_share_ratio(self.get_selected_torrent(), state))
			#self.text_summary_downloaded_this_session.set_text(str(state[""]))
			#self.text_summary_uplodaded_this_session.set_text(str(state[""]))
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
											2,	peer['peer_has'],
											3,	peer['download_speed'],
											4,	peer['upload_speed'])
			for peer in new_peer_info:
				if peer['ip'] not in curr_ips.keys() and peer['client'] is not "":
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
		if self.pref.get('use_default_dir', bool):
			path = self.pref.get('default_download_path')
		else:
			path = dgtk.show_directory_chooser_dialog(self.window)
			if path is None:
				return
		unique_id = self.manager.add_torrent(torrent, path, self.pref.get('use_compact_storage', bool))
		if append:
			self.store.append(self.get_list_from_unique_id(unique_id))
		
		
		
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

			warning   =  glade.get_widget("warning")
			warning.set_text(" ")

			data_also  =  glade.get_widget("data_also")
			data_also.connect("toggled", self.remove_toggle_warning, warning)

			response = asker.run()
			asker.destroy()
			if response == 1:
				self.manager.remove_torrent(torrent, data_also.get_active())


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
			self.manager.queue_up(torrent)
	
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
		self.wtree.get_widget("chk_infopane").set_active(self.pref.get("show_infopane", bool))
		self.wtree.get_widget("chk_size").set_active(self.pref.get("show_size", bool))
		self.wtree.get_widget("chk_status").set_active(self.pref.get("show_status", bool))
		self.wtree.get_widget("chk_seed").set_active(self.pref.get("show_seeders", bool))
		self.wtree.get_widget("chk_peer").set_active(self.pref.get("show_peers", bool))
		self.wtree.get_widget("chk_download").set_active(self.pref.get("show_dl", bool))
		self.wtree.get_widget("chk_upload").set_active(self.pref.get("show_ul", bool))
		self.wtree.get_widget("chk_eta").set_active(self.pref.get("show_eta", bool))
		self.wtree.get_widget("chk_ratio").set_active(self.pref.get("show_share", bool))
	
	def save_window_settings(self):
		self.pref.set("show_infopane", self.wtree.get_widget("chk_infopane").get_active())
		self.pref.set("show_size", self.size_column.get_visible())
		self.pref.set("show_status", self.status_column.get_visible())
		self.pref.set("show_seeders", self.seed_column.get_visible())
		self.pref.set("show_peers", self.peer_column.get_visible())
		self.pref.set("show_dl", self.dl_column.get_visible())
		self.pref.set("show_ul", self.ul_column.get_visible())
		self.pref.set("show_eta", self.eta_column.get_visible())
		self.pref.set("show_share", self.share_column.get_visible())

	def close(self, widget, event):
		if self.pref.get("close_to_tray", bool) and self.pref.get("enable_system_tray", bool):
			self.window.hide()
			return True
		else:
			self.quit()
		
	def quit(self, widget=None):
		self.shutdown()
	
	def shutdown(self):
		enabled_plugins = ':'.join(self.plugins.get_enabled_plugins())
		self.pref.set('enabled_plugins', enabled_plugins)
		self.save_window_settings()
		self.pref.save_to_file(self.conf_file)
		self.plugins.shutdown_all_plugins()
		self.manager.quit()
		gtk.main_quit()
	


		
## For testing purposes, create a copy of the interface
if __name__ == "__main__":
	interface = DelugeGTK()
	interface.start()
