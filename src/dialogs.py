# -*- coding: utf-8 -*-
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import gtk

import common
import dgtk
import files
import pref

PREFS_FILENAME  = "prefs.state"

class PreferencesDlg:
    def __init__(self, preferences, active_port, plugins, plugin_tab=False):
        self.glade = gtk.glade.XML(common.get_glade_file("preferences_dialog.glade"), domain='deluge')
        self.dialog = self.glade.get_widget("pref_dialog")
        if plugin_tab:
            self.glade.get_widget("notebook").set_current_page(6)
        self.dialog.set_position(gtk.WIN_POS_CENTER)
        if not common.windows_check():
            self.dialog.set_icon(common.get_logo(18))
        self.glade.signal_autoconnect({
                                        'toggle_ui': self.toggle_ui,
                                        'on_btn_testport_clicked': self.TestPort,
                                      })
        
        self.preferences = preferences
        self.active_port = str(active_port)
        #init plugin info
        self.view = self.glade.get_widget("plugin_view")
        self.store = gtk.ListStore(str, bool)
        self.store.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.view.set_model(self.store)
        try:
            self.view.get_selection().set_select_function(self.plugin_clicked, full=True)
        except TypeError:
            self.view.get_selection().set_select_function(self.old_clicked)
        name_col = dgtk.add_text_column(self.view, _("Plugin"), 0)
        name_col.set_expand(True)
        dgtk.add_toggle_column(self.view, _("Enabled"), 1, toggled_signal=self.plugin_toggled)
        signals = {'plugin_pref':      self.plugin_pref,
                   'on_close_clicked': self.close_clicked}
        self.glade.signal_autoconnect(signals)
        self.plugins = plugins

    def show(self, interface, window):
        # Load settings into dialog
        try:
            self.glade.get_widget("combo_encin").set_active(self.preferences.get("encin_state"))
            self.glade.get_widget("combo_encout").set_active(self.preferences.get("encout_state"))
            self.glade.get_widget("combo_enclevel").set_active(self.preferences.get("enclevel_type"))
            self.glade.get_widget("combo_peer_proxy_type").set_active(self.preferences.get("peer_proxy_type"))
            self.glade.get_widget("combo_dht_proxy_type").set_active(self.preferences.get("dht_proxy_type"))
            self.glade.get_widget("combo_tracker_proxy_type").set_active(self.preferences.get("tracker_proxy_type"))
            self.glade.get_widget("combo_web_proxy_type").set_active(self.preferences.get("web_proxy_type"))
            self.glade.get_widget("chk_autoload").set_active(self.preferences.get("autoload"))
            self.glade.get_widget("chk_send_info").set_active(self.preferences.get("send_info"))
            self.glade.get_widget("chk_pref_rc4").set_active(self.preferences.get("pref_rc4"))
            self.glade.get_widget("chk_peer_proxy").set_active(self.preferences.get("peer_proxy"))
            self.glade.get_widget("chk_tracker_proxy").set_active(self.preferences.get("tracker_proxy"))
            self.glade.get_widget("chk_dht_proxy").set_active(self.preferences.get("dht_proxy"))
            self.glade.get_widget("chk_web_proxy").set_active(self.preferences.get("web_proxy"))
            self.glade.get_widget("chk_upnp").set_active(self.preferences.get("use_upnp"))
            self.glade.get_widget("chk_lsd").set_active(self.preferences.get("use_lsd"))
            self.glade.get_widget("chk_random_port").set_active(self.preferences.get("random_port"))
            self.glade.get_widget("chk_natpmp").set_active(self.preferences.get("use_natpmp"))
            self.glade.get_widget("chk_utpex").set_active(self.preferences.get("use_utpex"))
            self.glade.get_widget("chk_new_releases").set_active(self.preferences.get("new_releases"))
            self.glade.get_widget("chk_use_tray").set_active(self.preferences.get("enable_system_tray"))
            self.glade.get_widget("chk_min_on_close").set_active(self.preferences.get("close_to_tray"))
            self.glade.get_widget("chk_start_in_tray").set_active(self.preferences.get("start_in_tray"))
            self.glade.get_widget("chk_lock_tray").set_active(self.preferences.get("lock_tray"))
            self.glade.get_widget("txt_tray_passwd").set_text(self.preferences.get("tray_passwd"))
            self.glade.get_widget("txt_peer_proxy_hostname").set_text(self.preferences.get("peer_proxy_hostname"))
            self.glade.get_widget("txt_peer_proxy_username").set_text(self.preferences.get("peer_proxy_username"))
            self.glade.get_widget("txt_peer_proxy_password").set_text(self.preferences.get("peer_proxy_password"))
            self.glade.get_widget("txt_tracker_proxy_hostname").set_text(self.preferences.get("tracker_proxy_hostname"))
            self.glade.get_widget("txt_tracker_proxy_username").set_text(self.preferences.get("tracker_proxy_username"))
            self.glade.get_widget("txt_tracker_proxy_password").set_text(self.preferences.get("tracker_proxy_password"))
            self.glade.get_widget("txt_dht_proxy_hostname").set_text(self.preferences.get("dht_proxy_hostname"))
            self.glade.get_widget("txt_dht_proxy_username").set_text(self.preferences.get("dht_proxy_username"))
            self.glade.get_widget("txt_dht_proxy_password").set_text(self.preferences.get("dht_proxy_password"))
            self.glade.get_widget("txt_web_proxy_hostname").set_text(self.preferences.get("web_proxy_hostname"))
            self.glade.get_widget("txt_web_proxy_username").set_text(self.preferences.get("web_proxy_username"))
            self.glade.get_widget("txt_web_proxy_password").set_text(self.preferences.get("web_proxy_password"))
            self.glade.get_widget("autoload_path_button").set_filename(self.preferences.get("default_autoload_path"))
            self.glade.get_widget("download_path_button").set_filename(self.preferences.get("default_download_path"))
            self.glade.get_widget("torrent_path_button").set_filename(self.preferences.get("default_torrent_path"))
            self.glade.get_widget("chk_enable_files_dialog").set_active(self.preferences.get("enable_files_dialog"))
            self.glade.get_widget("chk_enable_multi_only").set_active(self.preferences.get("enable_multi_only"))
            self.glade.get_widget("chk_prioritize_first_last_pieces").set_active(self.preferences.get("prioritize_first_last_pieces"))
            self.glade.get_widget("radio_compact_allocation").set_active(self.preferences.get("use_compact_storage"))
            self.glade.get_widget("radio_full_allocation").set_active(not self.preferences.get("use_compact_storage"))
            self.glade.get_widget("active_port_label").set_text(str(self.active_port))
            self.glade.get_widget("spin_port_min").set_value(self.preferences.get("listen_on")[0])
            self.glade.get_widget("spin_port_max").set_value(self.preferences.get("listen_on")[1])
            self.glade.get_widget("spin_max_upload").set_value(self.preferences.get("max_upload_speed"))
            self.glade.get_widget("spin_max_upload_slots_global").set_value(float(self.preferences.get("max_upload_slots_global")))
            self.glade.get_widget("spin_max_upload_slots_per_torrent").set_value(float(self.preferences.get("max_upload_slots_per_torrent")))
            self.glade.get_widget("spin_max_download").set_value(self.preferences.get("max_download_speed"))
            self.glade.get_widget("spin_max_connections_global").set_value(self.preferences.get("max_connections_global"))
            self.glade.get_widget("spin_max_connections_per_torrent").set_value(self.preferences.get("max_connections_per_torrent"))
            self.glade.get_widget("spin_peer_proxy_port").set_value(self.preferences.get("peer_proxy_port"))
            self.glade.get_widget("spin_tracker_proxy_port").set_value(self.preferences.get("tracker_proxy_port"))
            self.glade.get_widget("spin_dht_proxy_port").set_value(self.preferences.get("dht_proxy_port"))
            self.glade.get_widget("spin_web_proxy_port").set_value(self.preferences.get("web_proxy_port"))
            self.glade.get_widget("spin_max_half_open").set_value(float(self.preferences.get("max_half_open")))
            self.glade.get_widget("spin_connection_speed").set_value(float(self.preferences.get("connection_speed")))
            self.glade.get_widget("spin_torrents").set_value(float(self.preferences.get("max_active_torrents")))
            self.glade.get_widget("chk_seedbottom").set_active(self.preferences.get("queue_seeds_to_bottom"))
            self.glade.get_widget("chk_queue_above_completed").set_sensitive(self.preferences.get("queue_seeds_to_bottom"))
            self.glade.get_widget("chk_queue_above_completed").set_active(self.preferences.get("queue_above_completed"))
            self.glade.get_widget("chk_autoseed").set_active(self.preferences.get("auto_end_seeding"))
            self.glade.get_widget("chk_autotime").set_active(self.preferences.get("auto_time_end_seeding"))
            self.glade.get_widget("chk_clear_max_ratio_torrents").set_sensitive(self.preferences.get("auto_end_seeding"))
            self.glade.get_widget("chk_clear_max_ratio_torrents").set_active(self.preferences.get("clear_max_ratio_torrents"))
            self.glade.get_widget("chk_clear_max_time_torrents").set_sensitive(self.preferences.get("auto_time_end_seeding"))
            self.glade.get_widget("chk_clear_max_time_torrents").set_active(self.preferences.get("clear_max_time_torrents"))
            self.glade.get_widget("chk_paused").set_active(self.preferences.get("start_paused"))
            self.glade.get_widget("ratio_spinner").set_value(self.preferences.get("auto_seed_ratio"))
            self.glade.get_widget("time_spinner").set_value(self.preferences.get("auto_seed_time"))
            self.glade.get_widget("chk_dht").set_active(self.preferences.get("enable_dht"))
            self.glade.get_widget("chk_use_advanced_bar").set_active(self.preferences.get("use_advanced_bar"))

            #smart dialog set sensitivities
            if(self.preferences.get("use_default_dir")):
                self.glade.get_widget("radio_save_all_to").set_active(True)
            else:
                self.glade.get_widget("radio_ask_save").set_active(True)
                
            self.glade.get_widget('chk_min_on_close').set_sensitive(
                self.glade.get_widget('chk_use_tray').get_active())
            self.glade.get_widget('chk_enable_multi_only').set_sensitive(
                self.glade.get_widget('chk_enable_files_dialog').get_active())
            self.glade.get_widget('chk_start_in_tray').set_sensitive(
                self.glade.get_widget('chk_use_tray').get_active())
            self.glade.get_widget('chk_lock_tray').set_sensitive(
                self.glade.get_widget('chk_use_tray').get_active())
            self.glade.get_widget('txt_tray_passwd').set_sensitive(
                self.glade.get_widget('chk_use_tray').get_active() and \
                    self.glade.get_widget('chk_lock_tray').get_active())
            
            self.glade.get_widget('spin_port_min').set_sensitive(
                not self.glade.get_widget('chk_random_port').get_active())
            self.glade.get_widget('spin_port_max').set_sensitive(
                not self.glade.get_widget('chk_random_port').get_active())                

            self.glade.get_widget("ok_button").connect("clicked", 
                                                   self.ok_clicked, interface)
            self.glade.get_widget("cancel_button").connect("clicked", 
                                                       self.cancel_clicked)
            
        except KeyError:
            pass
        # plugin tab
        self.store.clear()
        for plugin in self.plugins.get_available_plugins():
            #print plugin
            if plugin in self.plugins.get_enabled_plugins():
                self.store.append( (plugin, True) )
            else:
                self.store.append( (plugin, False) )
        self.glade.get_widget("plugin_text").get_buffer().set_text("")
        self.glade.get_widget("plugin_conf").set_sensitive(False)
        self.dialog.set_transient_for(window)
        self.dialog.show()

    def ok_clicked(self, source, interface):
        self.dialog.hide()
        import sha
        self.preferences.set("encin_state", self.glade.get_widget("combo_encin").get_active())
        self.preferences.set("encout_state", self.glade.get_widget("combo_encout").get_active())
        self.preferences.set("enclevel_type", self.glade.get_widget("combo_enclevel").get_active())
        self.preferences.set("peer_proxy_type", self.glade.get_widget("combo_peer_proxy_type").get_active())
        self.preferences.set("autoload", self.glade.get_widget("chk_autoload").get_active())
        self.preferences.set("send_info", self.glade.get_widget("chk_send_info").get_active())
        self.preferences.set("pref_rc4", self.glade.get_widget("chk_pref_rc4").get_active())
        self.preferences.set("peer_proxy", self.glade.get_widget("chk_peer_proxy").get_active())
        self.preferences.set("tracker_proxy", self.glade.get_widget("chk_tracker_proxy").get_active())
        self.preferences.set("dht_proxy", self.glade.get_widget("chk_dht_proxy").get_active())
        self.preferences.set("web_proxy", self.glade.get_widget("chk_web_proxy").get_active())
        self.preferences.set("use_upnp", self.glade.get_widget("chk_upnp").get_active())
        self.preferences.set("use_lsd", self.glade.get_widget("chk_lsd").get_active())
        self.preferences.set("tracker_proxy_type", self.glade.get_widget("combo_tracker_proxy_type").get_active())
        self.preferences.set("dht_proxy_type", self.glade.get_widget("combo_dht_proxy_type").get_active())
        self.preferences.set("web_proxy_type", self.glade.get_widget("combo_web_proxy_type").get_active())
        self.preferences.set("new_releases", self.glade.get_widget("chk_new_releases").get_active())
        self.preferences.set("random_port", self.glade.get_widget("chk_random_port").get_active())
        self.preferences.set("use_natpmp", self.glade.get_widget("chk_natpmp").get_active())
        self.preferences.set("use_utpex", self.glade.get_widget("chk_utpex").get_active())
        self.preferences.set("enable_system_tray", self.glade.get_widget("chk_use_tray").get_active())
        self.preferences.set("close_to_tray", self.glade.get_widget("chk_min_on_close").get_active())
        self.preferences.set("start_in_tray", self.glade.get_widget("chk_start_in_tray").get_active())
        self.preferences.set("lock_tray", self.glade.get_widget("chk_lock_tray").get_active())
        if len(self.glade.get_widget("txt_tray_passwd").get_text()) != 40:
            password = sha.new(self.glade.get_widget("txt_tray_passwd").get_text()).hexdigest()
        else:
            password = self.glade.get_widget("txt_tray_passwd").get_text()
        self.preferences.set("tray_passwd", password)
        self.preferences.set("tracker_proxy_username", self.glade.get_widget("txt_tracker_proxy_username").get_text())
        self.preferences.set("tracker_proxy_password", self.glade.get_widget("txt_tracker_proxy_password").get_text())
        self.preferences.set("tracker_proxy_hostname", self.glade.get_widget("txt_tracker_proxy_hostname").get_text())
        self.preferences.set("web_proxy_username", self.glade.get_widget("txt_web_proxy_username").get_text())
        self.preferences.set("web_proxy_password", self.glade.get_widget("txt_web_proxy_password").get_text())
        self.preferences.set("web_proxy_hostname", self.glade.get_widget("txt_web_proxy_hostname").get_text())
        self.preferences.set("dht_proxy_username", self.glade.get_widget("txt_dht_proxy_username").get_text())
        self.preferences.set("dht_proxy_password", self.glade.get_widget("txt_dht_proxy_password").get_text())
        self.preferences.set("dht_proxy_hostname", self.glade.get_widget("txt_dht_proxy_hostname").get_text())
        self.preferences.set("peer_proxy_username", self.glade.get_widget("txt_peer_proxy_username").get_text())
        self.preferences.set("peer_proxy_password", self.glade.get_widget("txt_peer_proxy_password").get_text())
        self.preferences.set("peer_proxy_hostname", self.glade.get_widget("txt_peer_proxy_hostname").get_text())
        self.preferences.set("use_default_dir", self.glade.get_widget("radio_save_all_to").get_active())
        self.preferences.set("default_autoload_path", self.glade.get_widget("autoload_path_button").get_filename())
        self.preferences.set("default_download_path", self.glade.get_widget("download_path_button").get_filename())
        self.preferences.set("default_torrent_path", self.glade.get_widget("torrent_path_button").get_filename())
        self.preferences.set("enable_files_dialog", self.glade.get_widget("chk_enable_files_dialog").get_active())
        self.preferences.set("enable_multi_only", self.glade.get_widget("chk_enable_multi_only").get_active())
        self.preferences.set("prioritize_first_last_pieces", self.glade.get_widget("chk_prioritize_first_last_pieces").get_active())
        self.preferences.set("auto_seed_ratio", self.glade.get_widget("ratio_spinner").get_value())
        self.preferences.set("auto_end_seeding", self.glade.get_widget("chk_autoseed").get_active())
        self.preferences.set("auto_time_end_seeding", self.glade.get_widget("chk_autotime").get_active())
        self.preferences.set("auto_seed_time", self.glade.get_widget("time_spinner").get_value())
        self.preferences.set("use_compact_storage", self.glade.get_widget("radio_compact_allocation").get_active())
        self.preferences.set("listen_on", [self.glade.get_widget("spin_port_min").get_value(), self.glade.get_widget("spin_port_max").get_value()])
        self.preferences.set("max_upload_speed", self.glade.get_widget("spin_max_upload").get_value())
        self.preferences.set("max_upload_slots_global", int(self.glade.get_widget("spin_max_upload_slots_global").get_value()))
        self.preferences.set("max_upload_slots_per_torrent", int(self.glade.get_widget("spin_max_upload_slots_per_torrent").get_value()))
        self.preferences.set("max_download_speed", self.glade.get_widget("spin_max_download").get_value())
        self.preferences.set("peer_proxy_port", self.glade.get_widget("spin_peer_proxy_port").get_value())
        self.preferences.set("dht_proxy_port", self.glade.get_widget("spin_dht_proxy_port").get_value())
        self.preferences.set("web_proxy_port", self.glade.get_widget("spin_web_proxy_port").get_value())
        self.preferences.set("tracker_proxy_port", self.glade.get_widget("spin_tracker_proxy_port").get_value())
        self.preferences.set("max_connections_global", int(self.glade.get_widget("spin_max_connections_global").get_value()))
        self.preferences.set("max_connections_per_torrent", int(self.glade.get_widget("spin_max_connections_per_torrent").get_value()))
        self.preferences.set("max_half_open", int(self.glade.get_widget("spin_max_half_open").get_value()))
        self.preferences.set("connection_speed", int(self.glade.get_widget("spin_connection_speed").get_value()))
        self.preferences.set("max_active_torrents", int(self.glade.get_widget("spin_torrents").get_value()))
        self.preferences.set("queue_seeds_to_bottom", self.glade.get_widget("chk_seedbottom").get_active())
        self.preferences.set("enable_dht", self.glade.get_widget("chk_dht").get_active())
        self.preferences.set("clear_max_ratio_torrents", self.glade.get_widget("chk_clear_max_ratio_torrents").get_active())
        self.preferences.set("clear_max_time_torrents", self.glade.get_widget("chk_clear_max_time_torrents").get_active())
        self.preferences.set("queue_above_completed", self.glade.get_widget("chk_queue_above_completed").get_active())
        self.preferences.set("start_paused", self.glade.get_widget("chk_paused").get_active())
        self.preferences.set("use_advanced_bar", self.glade.get_widget("chk_use_advanced_bar").get_active())

        interface.apply_prefs()
        interface.config.save()

    def cancel_clicked(self, source):
        self.dialog.hide()

    def close_clicked(self, source):
        self.dialog.hide()
    
    def old_clicked(self, path):
        return self.plugin_clicked(self.view.get_selection(), self.store, path, False)
    
    def plugin_clicked(self, selection, model, path, is_selected):
        if is_selected:
            return True
        name = model.get_value(model.get_iter(path), 0)
        plugin = self.plugins.get_plugin(name)
        author = plugin.plugin_author
        version = plugin.plugin_version
        description = plugin.plugin_description
        if name in self.plugins.get_enabled_plugins():
            config = self.plugins.configurable_plugin(name)
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
            config = self.plugins.configurable_plugin(plugin_name)
            try:
                self.glade.get_widget("plugin_conf").set_sensitive(config)
            except: 
                pass
        else:
            self.plugins.disable_plugin(plugin_name)
            self.glade.get_widget("plugin_conf").set_sensitive(False)
                
    def plugin_pref(self, widget=None):
        (model, plugin_iter) = self.view.get_selection().get_selected()
        plugin_name = self.store.get_value(plugin_iter, 0)
        self.plugins.configure_plugin(plugin_name, self.dialog)

    def TestPort(self, widget):
        common.open_url_in_browser('http://www.deluge-torrent.org/test-port.php?port=%s' % self.active_port)
    
    def toggle_ui(self, widget):
        value = widget.get_active()
        if widget == self.glade.get_widget('radio_save_all_to'):
            self.glade.get_widget('download_path_button').set_sensitive(value)
            self.glade.get_widget('autoload_path_button').set_sensitive(value)
            self.glade.get_widget('chk_autoload').set_sensitive(value)
        elif widget == self.glade.get_widget('chk_autoseed'):
            self.glade.get_widget('ratio_spinner').set_sensitive(value)
            self.glade.get_widget('chk_clear_max_ratio_torrents').set_sensitive(value)  
        elif widget == self.glade.get_widget('chk_autotime'):
            self.glade.get_widget('time_spinner').set_sensitive(value)
            self.glade.get_widget('chk_clear_max_time_torrents').set_sensitive(value)  
        elif widget == self.glade.get_widget('chk_seedbottom'):
            self.glade.get_widget('chk_queue_above_completed').set_sensitive(value)
        elif widget == self.glade.get_widget('chk_enable_files_dialog'):
            self.glade.get_widget('chk_enable_multi_only').set_sensitive(value)
        elif widget == self.glade.get_widget('chk_peer_proxy'):
                value = self.glade.get_widget('chk_peer_proxy').get_active() 
                for x in ['combo_peer_proxy_type', 'txt_peer_proxy_hostname', 
                          'txt_peer_proxy_username', 'spin_peer_proxy_port', 
                          'txt_peer_proxy_password']:
                    self.glade.get_widget(x).set_sensitive(value)
        elif widget == self.glade.get_widget('chk_tracker_proxy'):
                value = self.glade.get_widget('chk_tracker_proxy').get_active() 
                for x in ['combo_tracker_proxy_type', 'txt_tracker_proxy_hostname', 
                          'txt_tracker_proxy_username', 'spin_tracker_proxy_port', 
                          'txt_tracker_proxy_password']:
                    self.glade.get_widget(x).set_sensitive(value)
        elif widget == self.glade.get_widget('chk_dht_proxy'):
                value = self.glade.get_widget('chk_dht_proxy').get_active() 
                for x in ['combo_dht_proxy_type', 'txt_dht_proxy_hostname', 
                          'txt_dht_proxy_username', 'spin_dht_proxy_port', 
                          'txt_dht_proxy_password']:
                    self.glade.get_widget(x).set_sensitive(value)
        elif widget == self.glade.get_widget('chk_web_proxy'):
                value = self.glade.get_widget('chk_web_proxy').get_active() 
                for x in ['combo_web_proxy_type', 'txt_web_proxy_hostname', 
                          'txt_web_proxy_username', 'spin_web_proxy_port', 
                          'txt_web_proxy_password']:
                    self.glade.get_widget(x).set_sensitive(value)
        elif widget == self.glade.get_widget('chk_use_tray'):
            self.glade.get_widget('chk_min_on_close').set_sensitive(value)
            self.glade.get_widget('chk_start_in_tray').set_sensitive(value)
            self.glade.get_widget('chk_lock_tray').set_sensitive(value)
            self.glade.get_widget('txt_tray_passwd').set_sensitive(value and \
                self.glade.get_widget('chk_lock_tray').get_active())
        elif widget == self.glade.get_widget('chk_lock_tray'):
            self.glade.get_widget('txt_tray_passwd').set_sensitive(value)
        elif widget == self.glade.get_widget('chk_random_port'):
            self.glade.get_widget('spin_port_min').set_sensitive(False)
            self.glade.get_widget('spin_port_max').set_sensitive(False)
            if not value:
                self.glade.get_widget('spin_port_min').set_sensitive(True)
                self.glade.get_widget('spin_port_max').set_sensitive(True)

class MergeDlg:
    def __init__(self):
        self.glade = gtk.glade.XML(common.get_glade_file("merge_dialog.glade"), 
                                   domain='deluge')
        self.dialog = self.glade.get_widget("merge_dialog")
        self.dialog.set_position(gtk.WIN_POS_CENTER)
        if not common.windows_check():
            self.dialog.set_icon(common.get_logo(18))
    
    def show(self, window):
        self.dialog.set_transient_for(window)
        self.dialog.show()
        r = self.dialog.run()
        self.dialog.hide()
        
        return r

class FilesDlg:
    def __init__(self, dumped_torrent):
        self.glade = gtk.glade.XML(common.get_glade_file("files_dialog.glade"), 
                                   domain='deluge')
        self.dialog = self.glade.get_widget("file_dialog")
        self.dialog.set_position(gtk.WIN_POS_CENTER)
        if not common.windows_check():
            self.dialog.set_icon(common.get_logo(18))
        
        self.files_manager = files.FilesDialogManager(
                                 self.glade.get_widget("file_view"),
                                 dumped_torrent)
        self.files_manager.build_file_view()
        self.files_manager.prepare_file_store()
    
    def show(self, window):
        #clear private setting
        self.glade.get_widget("chk_setpriv").set_active(False)
        self.dialog.set_transient_for(window)
        self.dialog.show()
        r = self.dialog.run()
        self.dialog.hide()
        
        return r
    
    def is_private_flag_checked(self):
        return self.glade.get_widget("chk_setpriv").get_active()
    
    def get_priorities(self):
        return self.files_manager.get_priorities()

def show_about_dialog(window):
        def url_hook(dialog, url):
            common.open_url_in_browser(url)

        gtk.about_dialog_set_url_hook(url_hook)
        abt = gtk.glade.XML(common.get_glade_file("aboutdialog.glade")).get_widget("aboutdialog")
        abt.set_transient_for(window)
        abt.set_name(common.PROGRAM_NAME)
        abt.set_version(common.PROGRAM_VERSION)
        abt.set_comments("Deluge is a full-featured BitTorrent\nclient for Linux, Mac OS X and Windows")
        abt.set_documenters(["Marcos Pinto"])
        abt.set_authors(["Zach Tibbitts", "Alon Zakai", "Marcos Pinto", "Andrew Resch", "Alex Dedul"])
        abt.set_artists(["Andrew Wedderburn"])
        abt.set_translator_credits("Ahmad Farghal\nA.Matveev\nAaron Wang Shi\nabbigss\nAbcx\nAccord Tsai\nActam\nAdam\nAdrian Goll\nAhmades\nakira\nAlan Pepelko\nAlberto\nAlberto Ferrer\nalcatr4z\nAleksej Korgenkov\nAlessio Treglia\nAlexander Matveev\nAlexander Taubenkorb\nAlexander Yurtsev\nAlexandre Martani\nAlexandre Rosenfeld\nAlexandre Sapata Carbonell\nAlin Claudiu Radut\nAlSim\nAlvaro Carrillanca P.\nAndrea Ratto\nAndrea Tarocchi\nAndreas Johansson\nAndreas Str\nAndreiF\nandrewh\nAndris Karasz\nAngel Guzman Maeso\nAníbal Deboni Neto\nanimarval\nAnton Yakutovich\nAntonio Cono\nantoniojreyes\nantou\nArkadiusz Kalinowski\nArtin\nartir\nAthanasios Lefteris\nAugusta Carla Klug\naxaard\nAxelRafn\nAyont\nb3rx\nBae Taegil\nBajusz Tamás\nBalaam's Miracle\nBent Ole Fosse\nbeyonet\nbigx\nBjorn Inge Berg\nblackbird\nBlackeyed\nblackmx\nBlutheo\nbob00work\nboenki\nBoone\nBranislav Jovanović\nbronze\nbrownie\nBrus46\nbumper\nbutely\nc0nfidencal\ncassianoleal\nCésar Rubén\nChangHyo Jeong\nchicha\nChien Cheng Wei\nChristian Kopac\nchristooss\nCityAceE\nckaya\nClopy\nClusty\ncnu\nCommandant\nCoolmax\ncosmix\nCostin Chirvasuta\nCoVaLiDiTy\nCrispin Kirchner\nCruster\nCybolic\nDan Bishop\nDanek\nDani\nDaniel Frank\nDaniel Høyer Iversen\nDaniel Marynicz\nDaniel Nylander\nDaniel Patriche\nDaniel Schildt\ndarh00\nDaria Michalska\nDarkenCZ\nDaspah\nDavid Eurenius\nDavid Machakhelidze\ndavidhjelm\nDawid Dziurdzia\ndcruz\nDeady\ndi0rz`\nDialecti Valsamou\nDiego Medeiros\nDkzoffy\ndmig\nDmitry Olyenyov\nDominik Kozaczko\nDominik Lübben\ndoomster\nDorota Król\nDoyen Philippe\nDread Knight\nDreamSonic\nduan\nDuong Thanh An\nDvoglavaZver\ndwori\ndylansmrjones\nEbuntor\nEdgar Alejandro Jarquin Flores\nEetu\nekerazha\neliasj\nelparia\nEmberke\nEmiliano Goday Caneda\nEndelWar\nercangun\nÉric Lassauge\nErlend Finvåg\nEvgeni Spasov\nFabian Ordelmans\nFabio Mazanatti\nFábio Nogueira\nFaCuZ\nFelipe Lerena\nFernando Pereira\nfjetland\nFlorian Schäfer\nFolke\nForce\nfosk\nfragarray\nfreddeg\nFrédéric Perrin\nFredrik Kilegran\nFreeAtMind\nFulvio Ciucci\nGabor Kelemen\nGaussian\ngdevitis\nGeorg Brzyk\nGeorg Sieber\nGeorgi Arabadjiev\nGerd Radecke\ngergo86\nGermán Heusdens\nGianni Vialetto\nGigih Aji Ibrahim\nGiorgio Wicklein\nGiovanni Rapagnani\ngl\nglen\ngranjerox\nGreen Fish\nGreyhound\nguillaume\nGuillaume Pelletier\nGustavo Henrique Klug\ngutocarvalho\nHans Rødtang\nHargas Gábor\nhasardeur\nHeitor Thury Barreiros Barbosa\nhelios91940\nhelix84\nHelton Rodrigues\nHendrik Luup\nHenrique Ferreiro\nHenry Goury-Laffont\nHezy Amiel\nHipi\nhokten\nHolmsss\nhristo.num\nIarwain\nibe\nibear\nId2ndR\nIgor Zubarev\nimen\nInuktitut\nIoannis Koniaris\nIstvan Nyitrai\nIvan Petrovic\nIvan Prignano\nJack Shen\njackmc\nJacques Stadler\nJakub Korbel\nJames Nealon\nJan Kaláb\nJan Niklas Hasse\nJanek Thomaschewski\nJasper Groenewegen\nJavi Rodríguez\njeannich\nJeff Bailes\nJesse Zilstorff\nJoan Duran\nJoão Santos\nJochen Schäfer\nJoe Anderson\nJohn Garland\nJojan\njollyr0ger\nJonas Bo Grimsgaard\nJonas Granqvist\nJonas Slivka\nJonathan Zeppettini\nJørgen\nJørgen Tellnes\njosé\nJosé Geraldo Gouvêa\nJosé Lou C.\nJose Sun\nJr.\nJukka Kauppinen\njulietgolf\nJusic\nJustzupi\nKaarel\nKai Thomsen\nKamil Páral\nKane_F\nKateikyoushii\nkaxhinaz\nKazuhiro NISHIYAMA\nKerberos\nKeresztes Ákos\nkevintyk\nkiersie\nKim Lübbe\nKimbo^\nkitzOgen\nkluon\nkmikz\nkoleoptero\nKőrösi Krisztián\nKostas\nKouta\nKrakatos\nKrešo Kunjas\nkripkenstein\nKristian Øllegaard\nKristoffer Egil Bonarjee\nKrzysztof Janowski\nl3estkunG\nlaughterwym\nLaur Mõtus\nlazka\nlebinh\nLKRaider\nLow Kian Seong\nLuca Ferretti\nLuis Gomes\nLuis Reis\nM.Kitchen\nMaciej Chojnacki\nMads Peter Rommedahl\nMajor Kong\nmalde\nMara Sorella\nmarazmista\nMarcin\nMarcin Falkiewicz\nMarco da Silva\nMarco de Moulin\nMarco Rodrigues\nmarcobra\nMarcos Escalier\nMarcos Pinto\nMarcus Ekstrom\nMario César Señoranis\nMario Munda\nMarius Andersen\nMarius Hudea\nMarius Mihai\nMariusz Cielecki\nMark Krapivner\nmarko-markovic\nMarkus Sutter\nMartin\nMartin Dybdal\nMartin Iglesias\nMartin Lettner\nMartin Pihl\nMasoud Kalali\nmat02\nMatej Urbančič\nMathias-K\nMatrik\nMatteo Renzulli\nMatthias Benkard\nMatthias Mailänder\nMert Dirik\nmhietar\nMichael Budde\nMichal Kaliszka\nMichał Tokarczyk\nMiguel Pires da Rosa\nMihai Capotă\nMikael Fernblad\nMike Sierra\nMike Sierra\nMilan Prvulović\nMilo Casagrande\nMiroslav Matejaš\nmithras\nMitja Pagon\nMohamed Magdy\nmoonkey\nMrBlonde\nmrtbzkrt\nmuczy\nMustafa Temizel\nmvoncken\nNagyMarton\nNeil Lin\nNicklas Larsson\nNicola Piovesan\nNicolaj Wyke\nNicolas Velin\nnik\nNiko_Thien\nNikolai M. Riabov\nnoisemonkey\nnosense\nNuno Estêvão\nNuno Santos\nnxxs\nnyo\noldbeggar\nOlivier FAURAX\nosantana\nOsman Tosun\nOssiR\notypoks\nounn\nOz123\nÖzgür BASKIN\nPablo Ledesma\nPål-Eivind Johnsen\npano\nPaolo Naldini\nPattogoTehen\nPaul Lange\nPavcio\nPaweł Wysocki\nPedro Brites Moita\nPedro Clemente Pereira Neto\nPekka Niemistö\nPenzo\nperdido\nPeter Kotrcka\nPeter Van den Bosch\nPetter Eklund\nPetter Viklund\nphatsphere\nPhilipi\nPhilippides Homer\npidi\nPierre Quillery\nPierre Slamich\nPiotr Strębski\nPittmann Tamás\nPrescott\nPumy\npushpika  \nPY\nqubicllj\nr21vo\nrainofchaos\nRajbir\nras0ir\nRat\nremus\nRenato\nRene Pärts\nRicardo Duarte\nRichard\nRobert Hrovat\nRobert Lundmark\nRoberth Sjonøy\nRobin Jakobsson\nRodrigo Donado\nRoel Groeneveld\nrohmaru\nRolf Christensen\nRoni Kantis\nRonmi\nRostislav Raykov\nroyto\nRui Moura\nRuiAmaro\nRusna\nRytis\nSam Azab\nSami Koskinen\nSamir van de Sand\nSamuel R. C. Vale\nsanafrato\nSanti\nSanti Martínez Cantelli\nSargate Kanogan\nSarmad Jari\nSaša Bodiroža\nsat0shi\nSavvas Radević\nSebastian Krauß\nSebastián Porta\nSedir\nsekolands\nsemsomi\nSergii Golovatiuk\nSergio\nsetarcos\nSheki\nSheki\nshifty\nShironeko\nShlomil\nSimone Tolotti\nSimone Vendemia\nsimonkoco\nskoruppa\nSławomir Więch\nslyon\nsmoke\nSonja\nspin_555\nSpiziuz\nSpyros Theodoritsis\nSqUe\nsrtck\nStefan Horning\nStefano Maggiolo\nStefano Roberto Soleti\nsteinberger\nStephan Klein\nStéphane Travostino\nStian24\nstylius\nSunjae Park\nSusana Pereira\nszymon siglowy\nthamood\nThanos Chatziathanassiou\nThe Jedi\nThéophane Anestis\nTiago Silva\nTiago Sousa\nTikkel\nTim Bordemann\nTim Fuchs\nTim Kornhammar\ntim__b\nTimo\nTimo Jyrinki\nTimothy Babych\nTitkosRejtozo\nTom\nTom Mannerhagen\nTom Verdaat\nTomas Gustavsson\nTomas Valentukevičius\nTomislav Plavčić\nTommy Mikkelsen\nToudi\ntqm_z\nTrapanator\nTribaal\nTuomo Sipola\nturbojugend_gr\nTurtle.net\ntwilight\ntymmej\numarzuki\nunikob\nVadim Gusev\nVagi\nValmantas Palikša\nVASKITTU\nvetal17\nvicedo\nviki\nvillads hamann\nvinchi007\nVinícius de Figueiredo Silva\nvinz\nvirtoo\nVitor Caike\nVitor Lamas Gatti\nWanderlust\nwarddr\nWebCrusader\nwebdr\nWentao Tang\nWorld Sucks\nXabi Ezpeleta\nXavi de Moner\nXavierToo\nXChesser\nXiaodong Xu\nxyb\nYasen Pramatarov\nZanDaTHraX\nzekopeko\nzhuqin\nZissan\nАртём Попов")
        abt.set_license(_("Deluge is free software, you can redistribute it and/or\nmodify it under the terms of the GNU General Public\n License as published by the Free Software Foundation,\neither version 2 of the License, or (at your option) any\nlater version.  Deluge is distributed in the hope that it\nwill be useful, but WITHOUT ANY WARRANTY, without even \nthe implied warranty of MERCHANTABILITY or FITNESS\nFOR A PARTICULAR PURPOSE.  See the GNU General\nPublic License for more details.  You should have received\na copy of the GNU General Public License along with\nDeluge, but if not, write to the Free Software Foundation,\n Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-\n1301 USA"))
        abt.set_website("http://deluge-torrent.org")
        abt.set_website_label("http://deluge-torrent.org")
        if not common.windows_check():
            abt.set_icon(common.get_logo(18))
        abt.set_logo(gtk.gdk.pixbuf_new_from_file(
                common.get_pixmap("deluge-about.png")))
        abt.show_all()
        abt.run()
        abt.hide_all()

def show_popup_warning(window, message):
    warner = gtk.MessageDialog(parent = window,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    buttons= gtk.BUTTONS_OK,
                    message_format=message,
                    type = gtk.MESSAGE_WARNING)
    warner.run()
    warner.destroy()

def show_popup_question(window, message):
    asker = gtk.MessageDialog(parent = window, 
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
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
def show_file_open_dialog(parent, title=None):
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
    config = pref.Preferences()
    chooser.set_current_folder(config.get("open_torrent_dialog_path"))
    chooser.add_filter(f1)
    chooser.set_select_multiple(True)
    if not common.windows_check():
        chooser.set_icon(common.get_logo(18))
        chooser.set_property("skip-taskbar-hint", True)
        
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
        result = chooser.get_filenames()
        config.set("open_torrent_dialog_path", chooser.get_current_folder())
    else:
        result = None
    chooser.destroy()
    return result

def show_directory_chooser_dialog(parent, title):
    chooser = gtk.FileChooserDialog(title, parent, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
    if not common.windows_check():
        chooser.set_icon(common.get_logo(18))
        chooser.set_property("skip-taskbar-hint", True)
    config = pref.Preferences()
    current_folder = config.get("choose_directory_dialog_path")
    if current_folder != None:
        chooser.set_current_folder(current_folder)
    if chooser.run() == gtk.RESPONSE_OK:
        result = chooser.get_filename()
        config.set("choose_directory_dialog_path", result)
    else:
        result = None
    chooser.destroy()
    return result
