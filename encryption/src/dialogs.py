# dialogs.py
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

import common, dgtk
import gtk, gtk.glade
import os, os.path



class PreferencesDlg:
	def __init__(self, parent, preferences):
		self.glade = gtk.glade.XML(common.get_glade_file("preferences_dialog.glade"), domain='deluge')
		self.dialog = self.glade.get_widget("pref_dialog")
		self.dialog.set_icon_from_file(common.get_pixmap("deluge32.png"))
		self.glade.signal_autoconnect({
										'tray_toggle': self.tray_toggle,
									  })
		self.parent = parent
		self.preferences = preferences
		
	def show(self):
		# Load settings into dialog
		try:
			if(self.preferences.get("encin_disabled") == "True"):
				self.glade.get_widget("chk_encin_disabled").set_active(True)
				self.glade.get_widget("chk_encin_enabled").set_active(False)
				self.glade.get_widget("chk_encin_forced").set_active(False)
			elif(self.preferences.get("encin_enabled") == "True"):
				self.glade.get_widget("chk_encin_enabled").set_active(True)
				self.glade.get_widget("chk_encin_disabled").set_active(False)
				self.glade.get_widget("chk_encin_forced").set_active(False)
			elif(self.preferences.get("encin_forced") == "True"):
				self.glade.get_widget("chk_encin_forced").set_active(True)
				self.glade.get_widget("chk_encin_enabled").set_active(False)
				self.glade.get_widget("chk_encin_disabled").set_active(False)
			if(self.preferences.get("encout_disabled") == "True"):
				self.glade.get_widget("chk_encout_disabled").set_active(True)
				self.glade.get_widget("chk_encout_enabled").set_active(False)
				self.glade.get_widget("chk_encout_forced").set_active(False)
			elif(self.preferences.get("encout_enabled") == "True"):
				self.glade.get_widget("chk_encout_enabled").set_active(True)
				self.glade.get_widget("chk_encout_disabled").set_active(False)
				self.glade.get_widget("chk_encout_forced").set_active(False)
			elif(self.preferences.get("encout_forced") == "True"):
				self.glade.get_widget("chk_encout_forced").set_active(True)
				self.glade.get_widget("chk_encout_enabled").set_active(False)
				self.glade.get_widget("chk_encout_disabled").set_active(False)
			if(self.preferences.get("level_plaintext") == "True"):
				self.glade.get_widget("chk_level_plaintext").set_active(True)
				self.glade.get_widget("chk_level_rc4").set_active(False)
				self.glade.get_widget("chk_level_both").set_active(False)
			elif(self.preferences.get("level_both") == "True"):
				self.glade.get_widget("chk_level_both").set_active(True)
				self.glade.get_widget("chk_level_plaintext").set_active(False)
				self.glade.get_widget("chk_level_rc4").set_active(False)
			elif(self.preferences.get("level_rc4") == "True"):
				self.glade.get_widget("chk_level_rc4").set_active(True)
				self.glade.get_widget("chk_level_both").set_active(False)
				self.glade.get_widget("chk_level_plaintext").set_active(False)

			self.glade.get_widget("chk_prefer_rc4").set_active(self.preferences.get("prefer_rc4", bool, default=False))

			self.glade.get_widget("chk_use_tray").set_active(self.preferences.get("enable_system_tray", bool, default=True))
			self.glade.get_widget("chk_min_on_close").set_active(self.preferences.get("close_to_tray", bool, default=False))
                        self.glade.get_widget("chk_lock_tray").set_active(self.preferences.get("lock_tray", bool, default=False))
                        self.glade.get_widget("txt_tray_passwd").set_text(self.preferences.get("tray_passwd", default=""))
			if(self.preferences.get("use_default_dir", bool, False)):
				self.glade.get_widget("radio_save_all_to").set_active(True)
			else:
				self.glade.get_widget("radio_ask_save").set_active(True)
			self.glade.get_widget("download_path_button").set_filename(self.preferences.get("default_download_path", str, default=os.path.expandvars('$HOME')))
			self.glade.get_widget("chk_compact").set_active(self.preferences.get("use_compact_storage", bool, default=False))
			self.glade.get_widget("active_port_label").set_text(str(self.parent.manager.get_state()['port']))
			self.glade.get_widget("spin_port_min").set_value(self.preferences.get("tcp_port_range_lower", int, default=6881))
			self.glade.get_widget("spin_port_max").set_value(self.preferences.get("tcp_port_range_upper", int, default=6889))
			self.glade.get_widget("spin_max_upload").set_value(self.preferences.get("max_upload_rate", int, default=-1))
			self.glade.get_widget("spin_num_upload").set_value(self.preferences.get("max_number_uploads", int, default=-1))
			self.glade.get_widget("spin_max_download").set_value(self.preferences.get("max_download_rate", int, default=-1))
			self.glade.get_widget("spin_num_download").set_value(self.preferences.get("max_number_downloads", int, default=-1))
			self.glade.get_widget("spin_torrents").set_value(self.preferences.get("max_number_torrents", int, default=-1))
			self.glade.get_widget("chk_seedbottom").set_active(self.preferences.get("queue_seeds_to_bottom", bool, default=False))
			self.glade.get_widget("chk_dht").set_active(self.preferences.get("enable_dht", bool, default=True))
			self.glade.get_widget("spin_dht").set_value(self.preferences.get("dht_connections", int, default=80))
			self.glade.get_widget("spin_gui").set_value(self.preferences.get("gui_update_interval", float, default=1.0))
		except KeyError:
			pass
		# Now, show the dialog
		self.dialog.show()
		r = self.dialog.run()
		self.dialog.hide()
		# Now, get the settings from the dialog
		if r == 1:
                        self.preferences.set("encin_disabled", self.glade.get_widget("chk_encin_disabled").get_active())
                        self.preferences.set("encin_enabled", self.glade.get_widget("chk_encin_enabled").get_active())
                        self.preferences.set("encin_forced", self.glade.get_widget("chk_encin_forced").get_active())
                        self.preferences.set("encout_disabled", self.glade.get_widget("chk_encout_disabled").get_active())
                        self.preferences.set("encout_enabled", self.glade.get_widget("chk_encout_enabled").get_active())
                        self.preferences.set("encout_forced", self.glade.get_widget("chk_encout_forced").get_active())
		        self.preferences.set("level_plaintext", self.glade.get_widget("chk_level_plaintext").get_active())
                        self.preferences.set("level_rc4", self.glade.get_widget("chk_level_rc4").get_active())
                        self.preferences.set("level_both", self.glade.get_widget("chk_level_both").get_active())
                        self.preferences.set("prefer_rc4", self.glade.get_widget("chk_prefer_rc4").get_active())
			self.preferences.set("system_tray", self.glade.get_widget("chk_use_tray").get_active())
			self.preferences.set("close_to_tray", self.glade.get_widget("chk_min_on_close").get_active())
                        self.preferences.set("lock_tray", self.glade.get_widget("chk_lock_tray").get_active())
                        self.preferences.set("tray_passwd", self.glade.get_widget("txt_tray_passwd").get_text())
			self.preferences.set("use_default_dir", self.glade.get_widget("radio_save_all_to").get_active())
			self.preferences.set("default_download_path", self.glade.get_widget("download_path_button").get_filename())
			self.preferences.set("auto_end_seeding", self.glade.get_widget("chk_autoseed").get_active())
			self.preferences.set("end_seed_ratio", self.glade.get_widget("ratio_spinner").get_value())
			self.preferences.set("use_compact_storage", self.glade.get_widget("chk_compact").get_active())
			self.preferences.set("tcp_port_range_lower", self.glade.get_widget("spin_port_min").get_value())
			self.preferences.set("tcp_port_range_upper", self.glade.get_widget("spin_port_max").get_value())
			self.preferences.set("max_upload_rate", self.glade.get_widget("spin_max_upload").get_value())
			self.preferences.set("max_number_uploads", self.glade.get_widget("spin_num_upload").get_value())
			self.preferences.set("max_download_rate", self.glade.get_widget("spin_max_download").get_value())
			self.preferences.set("max_number_downloads", self.glade.get_widget("spin_num_download").get_value())
			self.preferences.set("max_number_torrents", self.glade.get_widget("spin_torrents").get_value())
			self.preferences.set("queue_seeds_to_bottom", self.glade.get_widget("chk_seedbottom").get_active())
			self.preferences.set("enable_dht", self.glade.get_widget("chk_dht").get_active())
			self.preferences.set("dht_connections", self.glade.get_widget("spin_dht").get_value())
			self.preferences.set("gui_update_interval", self.glade.get_widget("spin_gui").get_value())
		
	def tray_toggle(self, obj):
		if obj.get_active():
			self.glade.get_widget("chk_min_on_close").set_sensitive(True)
		else:
			self.glade.get_widget("chk_min_on_close").set_sensitive(False)

		


class PluginDlg:
	def __init__(self, parent, plugins):
		self.glade = gtk.glade.XML(common.get_glade_file("plugin_dialog.glade"), domain='deluge')
		self.dialog = self.glade.get_widget("plugin_dialog")
		self.dialog.set_icon_from_file(common.get_pixmap("deluge32.png"))
		self.view = self.glade.get_widget("plugin_view")
		self.store = gtk.ListStore(str, bool)
		self.view.set_model(self.store)
		try:
			self.view.get_selection().set_select_function(self.plugin_clicked, full=True)
		except TypeError:
			self.view.get_selection().set_select_function(self.old_clicked)
		name_col = dgtk.add_text_column(self.view, _("Plugin"), 0)
		name_col.set_expand(True)
		dgtk.add_toggle_column(self.view, _("Enabled"), 1, toggled_signal=self.plugin_toggled)
		self.glade.signal_autoconnect({'plugin_pref': self.plugin_pref})
		self.parent = parent
		self.plugins = plugins
		

	def show(self):
		self.store.clear()
		for plugin in self.plugins.get_available_plugins():
			print plugin
			if plugin in self.plugins.get_enabled_plugins():
				self.store.append( (plugin, True) )
			else:
				self.store.append( (plugin, False) )
		self.glade.get_widget("plugin_text").get_buffer().set_text("")
		self.glade.get_widget("plugin_conf").set_sensitive(False)
		self.dialog.show()
		self.dialog.run()
		self.dialog.hide()
	
	def old_clicked(self, path):
		return self.plugin_clicked(self.view.get_selection(), self.store, path, False)
	
	def plugin_clicked(self, selection, model, path, is_selected):
		if is_selected:
			return True
		name = model.get_value(model.get_iter(path), 0)
		plugin = self.plugins.get_plugin(name)
		author = plugin['author']
		version = plugin['version']
		config = plugin['config']
		description = plugin['description']
		if name in self.plugins.get_enabled_plugins():
			self.glade.get_widget("plugin_conf").set_sensitive(config)
		else:
			self.glade.get_widget("plugin_conf").set_sensitive(False)
		self.glade.get_widget("plugin_text").get_buffer(
			).set_text("%s\nBy: %s\nVersion: %s\n\n%s"%
			(name, author, version, description))
		return True

	def plugin_toggled(self, renderer, path):
		plugin_iter = self.store.get_iter_from_string(path)
		plugin_name = self.store.get_value(plugin_iter, 0)
		plugin_value = not self.store.get_value(plugin_iter, 1)
		self.store.set_value(plugin_iter, 1, plugin_value)
		if plugin_value:
			self.plugins.enable_plugin(plugin_name)
			self.glade.get_widget("plugin_conf").set_sensitive(
				self.plugins.get_plugin(plugin_name)['config'])
		else:
			self.plugins.disable_plugin(plugin_name)
			self.glade.get_widget("plugin_conf").set_sensitive(False)
				
	def plugin_pref(self, widget=None):
		(model, plugin_iter) = self.view.get_selection().get_selected()
		plugin_name = self.store.get_value(plugin_iter, 0)
		self.plugins.configure_plugin(plugin_name)


def show_about_dialog(parent=None):
		gtk.about_dialog_set_url_hook(common.open_url_in_browser)
		abt = gtk.glade.XML(common.get_glade_file("aboutdialog.glade")).get_widget("aboutdialog")
		abt.set_name(common.PROGRAM_NAME)
		abt.set_version(common.PROGRAM_VERSION)
		abt.set_authors(["Zach Tibbits", "Alon Zakai", "Marcos Pinto"])
		abt.set_artists(["Andrew Wedderburn"])
		abt.set_website("http://deluge-torrent.org")
		abt.set_website_label("http://deluge-torrent.org")
		abt.set_icon_from_file(common.get_pixmap("deluge32.png"))
		abt.set_logo(gtk.gdk.pixbuf_new_from_file(
				common.get_pixmap("deluge-about.png")))
		abt.show_all()
		abt.run()
		abt.hide_all()

def show_popup_warning(window, message):
	warner = gtk.MessageDialog(parent = window,
					flags  = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
					buttons= gtk.BUTTONS_OK,
					message_format=message,
					type   = gtk.MESSAGE_WARNING)
	warner.run()
	warner.destroy()

def show_popup_question(window, message):
	asker = gtk.MessageDialog(parent = window, 
					flags  = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
					buttons = gtk.BUTTONS_YES_NO,
					message_format=message,
					type=gtk.MESSAGE_QUESTION)
	result = asker.run()
	asker.destroy()
	if result == gtk.RESPONSE_YES:
		return True
	elif result == gtk.RESPONSE_NO:
		return False
	elif result == gtk.RESPONSE_DELETE_EVENT:
		return False
	else:
		return False


## Browse for .torrent files
def show_file_open_dialog(parent=None, title=None):
	if title is None:
		title = _("Choose a .torrent file")
	chooser = gtk.FileChooserDialog(title, parent, gtk.FILE_CHOOSER_ACTION_OPEN,
			buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
	
	f0 = gtk.FileFilter()
	f0.set_name(_("Torrent files"))
	f0.add_pattern("*." + "torrent")
	chooser.add_filter(f0)
	f1 = gtk.FileFilter()
	f1.set_name(_("All files"))
	f1.add_pattern("*")
	chooser.add_filter(f1)
	
	chooser.set_icon_from_file(common.get_pixmap("deluge32.png"))
	chooser.set_property("skip-taskbar-hint", True)
		
	response = chooser.run()
	if response == gtk.RESPONSE_OK:
		result = chooser.get_filename()
	else:
		result = None
	chooser.destroy()
	return result

def show_directory_chooser_dialog(parent=None, title=None):
	if title is None:
		title = _("Choose a download directory")
	chooser = gtk.FileChooserDialog(title, parent, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
				buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
	chooser.set_icon_from_file(common.get_pixmap("deluge32.png"))
	chooser.set_property("skip-taskbar-hint", True)
	if chooser.run() == gtk.RESPONSE_OK:
		result = chooser.get_filename()
	else:
		result = None
	chooser.destroy()
	return result


