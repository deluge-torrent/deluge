#
# preferences.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import pkg_resources

import deluge.component as component
from deluge.log import LOG as log
from deluge.ui.client import aclient as client
import deluge.common
from deluge.configmanager import ConfigManager

class Preferences(component.Component):
    def __init__(self):
        component.Component.__init__(self, "Preferences")
        self.window = component.get("MainWindow")
        self.glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui",
                                            "glade/preferences_dialog.glade"))
        self.pref_dialog = self.glade.get_widget("pref_dialog")
        self.pref_dialog.set_icon(deluge.common.get_logo(32))
        self.treeview = self.glade.get_widget("treeview")
        self.notebook = self.glade.get_widget("notebook")
        self.gtkui_config = ConfigManager("gtkui.conf")
        # Setup the liststore for the categories (tab pages)
        self.liststore = gtk.ListStore(int, str)
        self.treeview.set_model(self.liststore)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Categories", render, text=1)
        self.treeview.append_column(column)
        # Add the default categories
        i = 0
        for category in ["Downloads", "Network", "Bandwidth", "Interface", 
            "Other", "Daemon", "Queue", "Plugins"]:
            self.liststore.append([i, category])
            i += 1

        # Setup plugin tab listview
        self.plugin_liststore = gtk.ListStore(str, bool)
        self.plugin_listview = self.glade.get_widget("plugin_listview")
        self.plugin_listview.set_model(self.plugin_liststore)
        render = gtk.CellRendererToggle()
        render.connect("toggled", self.on_plugin_toggled)
        render.set_property("activatable", True)
        self.plugin_listview.append_column(
            gtk.TreeViewColumn(_("Enabled"), render, active=1))
        self.plugin_listview.append_column(
            gtk.TreeViewColumn(_("Plugin"), gtk.CellRendererText(), text=0))
        
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect("changed", 
                                    self.on_selection_changed)
        
        self.plugin_listview.get_selection().connect("changed",
            self.on_plugin_selection_changed)
            
        self.glade.signal_autoconnect({
            "on_pref_dialog_delete_event": self.on_pref_dialog_delete_event,
            "on_button_ok_clicked": self.on_button_ok_clicked,
            "on_button_apply_clicked": self.on_button_apply_clicked,
            "on_button_cancel_clicked": self.on_button_cancel_clicked,
            "on_toggle": self.on_toggle,
            "on_test_port_clicked": self.on_test_port_clicked
        })

        # These get updated by requests done to the core        
        self.all_plugins = []
        self.enabled_plugins = []
    
    def __del__(self):
        del self.gtkui_config

    def add_page(self, name, widget):
        """Add a another page to the notebook"""
        # Create a header and scrolled window for the preferences tab
        widget.unparent()
        vbox = gtk.VBox()
        label = gtk.Label()
        label.set_use_markup(True)
        label.set_markup("<b><i><big>" + name + "</big></i></b>")
        label.set_alignment(0.05, 0.50)
        label.set_padding(0, 10)
        vbox.pack_start(label, False, True, 0)
        sep = gtk.HSeparator()
        vbox.pack_start(sep, False, True, 0)
        align = gtk.Alignment()
        align.set_padding(5, 0, 0, 0)
        align.add(widget)
        vbox.pack_start(align, False, False, 0)
        scrolled = gtk.ScrolledWindow()
        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)       
        viewport.add(vbox)
        scrolled.add(viewport)        
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.show_all()
        # Add this page to the notebook
        index = self.notebook.append_page(scrolled)
        self.liststore.append([index, name])
        return name

    def remove_page(self, name):
        """Removes a page from the notebook"""
        self.page_num_to_remove = None
        self.iter_to_remove = None
        
        def check_row(model, path, iter, user_data):
            row_name = model.get_value(iter, 1)
            if row_name == user_data:
                # This is the row we need to remove
                self.page_num_to_remove = model.get_value(iter, 0)
                self.iter_to_remove = iter
                return
                
        self.liststore.foreach(check_row, name)
        # Remove the page and row
        if self.page_num_to_remove != None:
            self.notebook.remove_page(self.page_num_to_remove)
        if self.iter_to_remove != None:
            self.liststore.remove(self.iter_to_remove)
    
    def _on_get_config(self, config):
        self.core_config = config
    
    def _on_get_available_plugins(self, plugins):
        self.all_plugins = plugins
    
    def _on_get_enabled_plugins(self, plugins):
        self.enabled_plugins = plugins
    
    def _on_get_listen_port(self, port):
        self.active_port = port
                    
    def show(self):
        # Update the preferences dialog to reflect current config settings
        self.core_config = {}
        client.get_config(self._on_get_config)
        client.get_available_plugins(self._on_get_available_plugins)
        client.get_enabled_plugins(self._on_get_enabled_plugins)
        client.get_listen_port(self._on_get_listen_port)
        # Force these calls and block until we've done them all
        client.force_call()

        if self.core_config != {} and self.core_config != None:
            core_widgets = {
                "download_path_button": \
                    ("filename", self.core_config["download_location"]),
                "torrent_files_button": \
                    ("filename", self.core_config["torrentfiles_location"]),
                "chk_autoadd_daemon": \
                    ("active", self.core_config["autoadd_enable"]),
                "entry_autoadd_daemon": \
                    ("text", self.core_config["autoadd_location"]),
                "radio_compact_allocation": \
                    ("active", self.core_config["compact_allocation"]),
                "radio_full_allocation": \
                    ("not_active", self.core_config["compact_allocation"]),
                "chk_prioritize_first_last_pieces": \
                    ("active", 
                        self.core_config["prioritize_first_last_pieces"]),
                "chk_private": \
                    ("active", self.core_config["default_private"]),
                "spin_port_min": ("value", self.core_config["listen_ports"][0]),
                "spin_port_max": ("value", self.core_config["listen_ports"][1]),
                "active_port_label": ("text", str(self.active_port)),
                "chk_random_port": ("active", self.core_config["random_port"]),
                "chk_dht": ("active", self.core_config["dht"]),
                "chk_upnp": ("active", self.core_config["upnp"]),
                "chk_natpmp": ("active", self.core_config["natpmp"]),
                "chk_utpex": ("active", self.core_config["utpex"]),
                "chk_lsd": ("active", self.core_config["lsd"]),
                "combo_encin": ("active", self.core_config["enc_in_policy"]),
                "combo_encout": ("active", self.core_config["enc_out_policy"]),
                "combo_enclevel": ("active", self.core_config["enc_level"]),
                "chk_pref_rc4": ("active", self.core_config["enc_prefer_rc4"]),
                "spin_max_connections_global": \
                    ("value", self.core_config["max_connections_global"]),
                "spin_max_download": \
                    ("value", self.core_config["max_download_speed"]),
                "spin_max_upload": \
                    ("value", self.core_config["max_upload_speed"]),
                "spin_max_upload_slots_global": \
                    ("value", self.core_config["max_upload_slots_global"]),
                "spin_max_connections_per_torrent": \
                    ("value", self.core_config["max_connections_per_torrent"]),
                "spin_max_upload_slots_per_torrent": \
                    ("value", self.core_config["max_upload_slots_per_torrent"]),
                "spin_max_download_per_torrent": \
                    ("value", self.core_config["max_download_speed_per_torrent"]),
                "spin_max_upload_per_torrent": \
                    ("value", self.core_config["max_upload_speed_per_torrent"]),
                "spin_daemon_port": \
                    ("value", self.core_config["daemon_port"]),
                "chk_allow_remote_connections": \
                    ("active", self.core_config["allow_remote"]),
                "spin_seeding": ("value", self.core_config["max_active_seeding"]),
                "spin_downloading": ("value", self.core_config["max_active_downloading"]),
                "chk_queue_new_top": ("active", self.core_config["queue_new_to_top"]),
                "chk_finished_bottom": ("active", self.core_config["queue_finished_to_bottom"]),
                "chk_seed_ratio": ("active", self.core_config["stop_seed_at_ratio"]),
                "spin_share_ratio": ("value", self.core_config["stop_seed_ratio"]),
                "chk_remove_ratio": ("active", self.core_config["remove_seed_at_ratio"])
            }

            # Update the widgets accordingly
            for key in core_widgets.keys():
                modifier = core_widgets[key][0]
                value = core_widgets[key][1]
                widget = self.glade.get_widget(key)
                if type(widget) == gtk.FileChooserButton:
                    for child in widget.get_children():
                        child.set_sensitive(True)
                widget.set_sensitive(True)
                
                if modifier == "filename":
                    widget.set_filename(value)
                elif modifier == "active":
                    widget.set_active(value)
                elif modifier == "not_active":
                    widget.set_active(not value)
                elif modifier == "value":
                    widget.set_value(value)
                elif modifier == "text":
                    widget.set_text(value)
        else:
            core_widget_list = [
                "download_path_button",
                "torrent_files_button",
                "chk_autoadd_daemon",
                "entry_autoadd_daemon",
                "radio_compact_allocation",
                "radio_full_allocation",
                "chk_prioritize_first_last_pieces",
                "chk_private",
                "spin_port_min",
                "spin_port_max",
                "active_port_label",
                "chk_random_port",
                "chk_dht",
                "chk_upnp",
                "chk_natpmp",
                "chk_utpex",
                "chk_lsd",
                "combo_encin",
                "combo_encout",
                "combo_enclevel",
                "chk_pref_rc4",
                "spin_max_connections_global",
                "spin_max_download",
                "spin_max_upload",
                "spin_max_upload_slots_global",
                "spin_max_connections_per_torrent",
                "spin_max_upload_slots_per_torrent",
                "spin_max_download_per_torrent",
                "spin_max_upload_per_torrent",
                "spin_daemon_port",
                "chk_allow_remote_connections",
                "spin_seeding",
                "spin_downloading",
                "chk_queue_new_top",
                "chk_finished_bottom",
                "chk_seed_ratio",
                "spin_share_ratio",
                "chk_remove_ratio"
            ]
            # We don't appear to be connected to a daemon
            for key in core_widget_list:
                widget = self.glade.get_widget(key)
                if type(widget) == gtk.FileChooserButton:
                    for child in widget.get_children():
                        child.set_sensitive(False)
                widget.set_sensitive(False)

        ## Downloads tab ##
        self.glade.get_widget("chk_show_dialog").set_active(
            self.gtkui_config["interactive_add"])
        self.glade.get_widget("chk_focus_dialog").set_active(
            self.gtkui_config["focus_add_dialog"])
        self.glade.get_widget("chk_autoadd_folder").set_active(
            self.gtkui_config["autoadd_enable"])
        self.glade.get_widget("autoadd_folder_button").set_filename(    
            self.gtkui_config["autoadd_location"])

        ## Interface tab ##
        self.glade.get_widget("chk_use_tray").set_active(
            self.gtkui_config["enable_system_tray"])
        self.glade.get_widget("chk_min_on_close").set_active(
            self.gtkui_config["close_to_tray"])
        self.glade.get_widget("chk_start_in_tray").set_active(
            self.gtkui_config["start_in_tray"])
        self.glade.get_widget("chk_lock_tray").set_active(
            self.gtkui_config["lock_tray"])
        self.glade.get_widget("combo_file_manager").set_active(
            self.gtkui_config["stock_file_manager"])
        self.glade.get_widget("txt_open_folder_location").set_text(
            self.gtkui_config["open_folder_location"])
        self.glade.get_widget("radio_open_folder_stock").set_active(
            self.gtkui_config["open_folder_stock"])
        self.glade.get_widget("radio_open_folder_custom").set_active(
            not self.gtkui_config["open_folder_stock"])

        ## Other tab ##
        self.glade.get_widget("chk_new_releases").set_active(
            self.gtkui_config["check_new_releases"])
            
        self.glade.get_widget("chk_send_info").set_active(
            self.gtkui_config["send_info"])
        
        ## Plugins tab ##
        all_plugins = self.all_plugins
        enabled_plugins = self.enabled_plugins
        # Clear the existing list so we don't duplicate entries.
        self.plugin_liststore.clear()
        # Iterate through the lists and add them to the liststore
        for plugin in all_plugins:
            if plugin in enabled_plugins:
                enabled = True
            else:
                enabled = False
            row = self.plugin_liststore.append()
            self.plugin_liststore.set_value(row, 0, plugin)
            self.plugin_liststore.set_value(row, 1, enabled)
            
        # Now show the dialog
        self.pref_dialog.show()
    
    def set_config(self):
        """Sets all altered config values in the core"""
        import sha
        # Get the values from the dialog
        new_core_config = {}
        new_gtkui_config = {}
        
        ## Downloads tab ##
        new_gtkui_config["interactive_add"] = \
            self.glade.get_widget("chk_show_dialog").get_active()
        new_gtkui_config["focus_add_dialog"] = \
            self.glade.get_widget("chk_focus_dialog").get_active()
        new_core_config["download_location"] = \
            self.glade.get_widget("download_path_button").get_filename()
        new_core_config["torrentfiles_location"] = \
            self.glade.get_widget("torrent_files_button").get_filename()
        new_gtkui_config["autoadd_enable"] = \
            self.glade.get_widget("chk_autoadd_folder").get_active()
        new_gtkui_config["autoadd_location"] = \
            self.glade.get_widget("autoadd_folder_button").get_filename()
        new_core_config["autoadd_enable"] = \
            self.glade.get_widget("chk_autoadd_daemon").get_active()
        new_core_config["autoadd_location"] = \
            self.glade.get_widget("entry_autoadd_daemon").get_text()
        new_core_config["compact_allocation"] = \
            self.glade.get_widget("radio_compact_allocation").get_active()
        new_core_config["prioritize_first_last_pieces"] = \
            self.glade.get_widget(
                "chk_prioritize_first_last_pieces").get_active()
        new_core_config["default_private"] = \
            self.glade.get_widget("chk_private").get_active()

        ## Network tab ##
        listen_ports = []
        listen_ports.append(
            self.glade.get_widget("spin_port_min").get_value_as_int())
        listen_ports.append(
            self.glade.get_widget("spin_port_max").get_value_as_int())
        new_core_config["listen_ports"] = listen_ports
        new_core_config["random_port"] = \
            self.glade.get_widget("chk_random_port").get_active()
        new_core_config["dht"] = self.glade.get_widget("chk_dht").get_active()
        new_core_config["upnp"] = self.glade.get_widget("chk_upnp").get_active()
        new_core_config["natpmp"] = \
            self.glade.get_widget("chk_natpmp").get_active()
        new_core_config["utpex"] = \
            self.glade.get_widget("chk_utpex").get_active()
        new_core_config["lsd"] = \
            self.glade.get_widget("chk_lsd").get_active()
        new_core_config["enc_in_policy"] = \
            self.glade.get_widget("combo_encin").get_active()
        new_core_config["enc_out_policy"] = \
            self.glade.get_widget("combo_encout").get_active()
        new_core_config["enc_level"] = \
            self.glade.get_widget("combo_enclevel").get_active()
        new_core_config["enc_prefer_rc4"] = \
            self.glade.get_widget("chk_pref_rc4").get_active()
        
        ## Bandwidth tab ##
        new_core_config["max_connections_global"] = \
            self.glade.get_widget(
                "spin_max_connections_global").get_value_as_int()
        new_core_config["max_download_speed"] = \
            self.glade.get_widget("spin_max_download").get_value()
        new_core_config["max_upload_speed"] = \
            self.glade.get_widget("spin_max_upload").get_value()
        new_core_config["max_upload_slots_global"] = \
            self.glade.get_widget(
                "spin_max_upload_slots_global").get_value_as_int()
        new_core_config["max_connections_per_torrent"] = \
            self.glade.get_widget(
                "spin_max_connections_per_torrent").get_value_as_int()
        new_core_config["max_upload_slots_per_torrent"] = \
            self.glade.get_widget(
                "spin_max_upload_slots_per_torrent").get_value_as_int()
        new_core_config["max_upload_speed_per_torrent"] = \
            self.glade.get_widget(
                "spin_max_upload_per_torrent").get_value()
        new_core_config["max_download_speed_per_torrent"] = \
            self.glade.get_widget(
                "spin_max_download_per_torrent").get_value()
        
        ## Interface tab ##
        new_gtkui_config["enable_system_tray"] = \
            self.glade.get_widget("chk_use_tray").get_active()
        new_gtkui_config["close_to_tray"] = \
            self.glade.get_widget("chk_min_on_close").get_active()
        new_gtkui_config["start_in_tray"] = \
            self.glade.get_widget("chk_start_in_tray").get_active()
        new_gtkui_config["lock_tray"] = \
            self.glade.get_widget("chk_lock_tray").get_active()
        passhex = sha.new(self.glade.get_widget("txt_tray_password").get_text())\
            .hexdigest()
        if passhex != "c07eb5a8c0dc7bb81c217b67f11c3b7a5e95ffd7":
            new_gtkui_config["tray_password"] = passhex
        new_gtkui_config["stock_file_manager"] = \
            self.glade.get_widget("combo_file_manager").get_active()
        new_gtkui_config["open_folder_location"] = \
            self.glade.get_widget("txt_open_folder_location").get_text()
        new_gtkui_config["open_folder_stock"] = \
            self.glade.get_widget("radio_open_folder_stock").get_active()
        
        ## Other tab ##    
        new_gtkui_config["check_new_releases"] = \
            self.glade.get_widget("chk_new_releases").get_active()
            
        new_gtkui_config["send_info"] = \
            self.glade.get_widget("chk_send_info").get_active()

        ## Daemon tab ##
        new_core_config["daemon_port"] = \
            self.glade.get_widget("spin_daemon_port").get_value_as_int()
        new_core_config["allow_remote"] = \
            self.glade.get_widget("chk_allow_remote_connections").get_active()
        
        ## Queue tab ##
        new_core_config["queue_new_to_top"] = \
            self.glade.get_widget("chk_queue_new_top").get_active()
        new_core_config["max_active_seeding"] = \
            self.glade.get_widget("spin_seeding").get_value_as_int()
        new_core_config["max_active_downloading"] = \
            self.glade.get_widget("spin_downloading").get_value_as_int()
        new_core_config["queue_finished_to_bottom"] = \
            self.glade.get_widget("chk_finished_bottom").get_active()
        new_core_config["stop_seed_at_ratio"] = \
            self.glade.get_widget("chk_seed_ratio").get_active()
        new_core_config["remove_seed_at_ratio"] = \
            self.glade.get_widget("chk_remove_ratio").get_active()
        new_core_config["stop_seed_ratio"] = \
            self.glade.get_widget("spin_share_ratio").get_value()
            
        # GtkUI
        for key in new_gtkui_config.keys():
            # The values do not match so this needs to be updated
            if self.gtkui_config[key] != new_gtkui_config[key]:
                self.gtkui_config[key] = new_gtkui_config[key]
        
        # Core
        if client.get_core_uri() != None:
            # Only do this if we're connected to a daemon
            config_to_set = {}
            for key in new_core_config.keys():
                # The values do not match so this needs to be updated
                if self.core_config[key] != new_core_config[key]:
                    config_to_set[key] = new_core_config[key]

            # Set each changed config value in the core
            client.set_config(config_to_set)

            # Update the configuration
            self.core_config.update(config_to_set)
        
        # Re-show the dialog to make sure everything has been updated
        self.show()
        
    def hide(self):
        self.pref_dialog.hide()
    
    def on_pref_dialog_delete_event(self, widget, event):
        self.hide()
        return True
    
    def on_toggle(self, widget):
        """Handles widget sensitivity based on radio/check button values."""
        value = widget.get_active()

        # Disable the focus dialog checkbox if the show dialog isn't active.        
        if widget == self.glade.get_widget("chk_show_dialog"):
            self.glade.get_widget("chk_focus_dialog").set_sensitive(value)
            
        # Disable the port spinners if random ports is selected.
        if widget == self.glade.get_widget("chk_random_port"):
            log.debug("chk_random_port set to: %s", value)
            self.glade.get_widget("spin_port_min").set_sensitive(not value)
            self.glade.get_widget("spin_port_max").set_sensitive(not value)
        
        # Disable all the tray options if tray is not used.
        if widget == self.glade.get_widget("chk_use_tray"):
            self.glade.get_widget("chk_min_on_close").set_sensitive(value)
            self.glade.get_widget("chk_start_in_tray").set_sensitive(value)
            self.glade.get_widget("chk_lock_tray").set_sensitive(value)
            if value == True:
                lock = self.glade.get_widget("chk_lock_tray").get_active()
                self.glade.get_widget("txt_tray_password").set_sensitive(lock)
                self.glade.get_widget("password_label").set_sensitive(lock)
            else:
                self.glade.get_widget("txt_tray_password").set_sensitive(value)
                self.glade.get_widget("password_label").set_sensitive(value)
            
        if widget == self.glade.get_widget("chk_lock_tray"):
            self.glade.get_widget("txt_tray_password").set_sensitive(value)
            self.glade.get_widget("password_label").set_sensitive(value)
                        
        # Disable the file manager combo box if custom is selected.
        if widget == self.glade.get_widget("radio_open_folder_custom"):
            self.glade.get_widget("combo_file_manager").set_sensitive(not value)
            self.glade.get_widget("txt_open_folder_location").set_sensitive(
                                                                        value)
       
    def on_button_ok_clicked(self, data):
        log.debug("on_button_ok_clicked")
        self.set_config()
        component.get("PluginManager").run_on_apply_prefs()
        self.hide()
        return True

    def on_button_apply_clicked(self, data):
        log.debug("on_button_apply_clicked")
        self.set_config()
        component.get("PluginManager").run_on_apply_prefs()

    def on_button_cancel_clicked(self, data):
        log.debug("on_button_cancel_clicked")
        self.hide()
        return True
        
    def on_selection_changed(self, treeselection):
        # Show the correct notebook page based on what row is selected.
        (model, row) = treeselection.get_selected()
        self.notebook.set_current_page(model.get_value(row, 0))

    def on_test_port_clicked(self, data):
        log.debug("on_test_port_clicked")
        def on_get_listen_port(port):
            deluge.common.open_url_in_browser(
                "http://deluge-torrent.org/test-port.php?port=%s" % port)
        client.get_listen_port(on_get_listen_port)
        client.force_call()
    
    def on_plugin_toggled(self, renderer, path):
        log.debug("on_plugin_toggled")
        row = self.plugin_liststore.get_iter_from_string(path)
        name = self.plugin_liststore.get_value(row, 0)
        value = self.plugin_liststore.get_value(row, 1)
        self.plugin_liststore.set_value(row, 1, not value)
        if not value:
            client.enable_plugin(name)
            component.get("PluginManager").enable_plugin(name)
        else:
            client.disable_plugin(name)
            component.get("PluginManager").disable_plugin(name)
        
    def on_plugin_selection_changed(self, treeselection):
        log.debug("on_plugin_selection_changed")
        
