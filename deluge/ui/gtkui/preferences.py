#
# preferences.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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
#
#

from __future__ import with_statement

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import pkg_resources

import deluge.component as component
from deluge.log import LOG as log
from deluge.ui.client import client
import deluge.common
import deluge.error
import common
from deluge.configmanager import ConfigManager
import deluge.configmanager

class Preferences(component.Component):
    def __init__(self):
        component.Component.__init__(self, "Preferences")
        self.glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui",
                                            "glade/preferences_dialog.glade"))
        self.pref_dialog = self.glade.get_widget("pref_dialog")
        self.pref_dialog.set_transient_for(component.get("MainWindow").window)
        self.pref_dialog.set_icon(common.get_deluge_icon())
        self.treeview = self.glade.get_widget("treeview")
        self.notebook = self.glade.get_widget("notebook")
        self.gtkui_config = ConfigManager("gtkui.conf")

        self.load_pref_dialog_state()

        self.glade.get_widget("image_magnet").set_from_file(
            deluge.common.get_pixmap("magnet.png"))

        # Hide the unused associate magnet button on OSX see: #2420
        if deluge.common.osx_check():
            self.glade.get_widget("button_associate_magnet").hide()

        # Setup the liststore for the categories (tab pages)
        self.liststore = gtk.ListStore(int, str)
        self.treeview.set_model(self.liststore)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Categories"), render, text=1)
        self.treeview.append_column(column)
        # Add the default categories
        i = 0
        for category in [_("Downloads"), _("Network"), _("Bandwidth"),
            _("Interface"), _("Other"), _("Daemon"), _("Queue"), _("Proxy"),
            _("Cache"), _("Plugins")]:
            self.liststore.append([i, category])
            i += 1

        # Setup plugin tab listview
        # The third entry is for holding translated plugin names
        self.plugin_liststore = gtk.ListStore(str, bool, str)
        self.plugin_liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.plugin_listview = self.glade.get_widget("plugin_listview")
        self.plugin_listview.set_model(self.plugin_liststore)
        render = gtk.CellRendererToggle()
        render.connect("toggled", self.on_plugin_toggled)
        render.set_property("activatable", True)
        self.plugin_listview.append_column(
            gtk.TreeViewColumn(_("Enabled"), render, active=1))
        self.plugin_listview.append_column(
            gtk.TreeViewColumn(_("Plugin"), gtk.CellRendererText(), text=2))

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
            "on_test_port_clicked": self.on_test_port_clicked,
            "on_button_plugin_install_clicked": self._on_button_plugin_install_clicked,
            "on_button_rescan_plugins_clicked": self._on_button_rescan_plugins_clicked,
            "on_button_find_plugins_clicked": self._on_button_find_plugins_clicked,
            "on_button_cache_refresh_clicked": self._on_button_cache_refresh_clicked,
            "on_combo_proxy_type_changed": self._on_combo_proxy_type_changed,
            "on_button_associate_magnet_clicked": self._on_button_associate_magnet_clicked,
            "on_pref_dialog_configure_event": self.on_pref_dialog_configure_event,
        })

        # These get updated by requests done to the core
        self.all_plugins = []
        self.enabled_plugins = []

    def __del__(self):
        del self.gtkui_config

    def add_page(self, name, widget):
        """Add a another page to the notebook"""
        # Create a header and scrolled window for the preferences tab
        parent = widget.get_parent()
        if parent:
            parent.remove(widget)
        vbox = gtk.VBox()
        label = gtk.Label()
        label.set_use_markup(True)
        label.set_markup("<b><i><big>" + name + "</big></i></b>")
        label.set_alignment(0.00, 0.50)
        label.set_padding(10, 10)
        vbox.pack_start(label, False, True, 0)
        sep = gtk.HSeparator()
        vbox.pack_start(sep, False, True, 0)
        align = gtk.Alignment()
        align.set_padding(5, 0, 0, 0)
        align.set(0, 0, 1, 1)
        align.add(widget)
        vbox.pack_start(align, True, True, 0)
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

        # We need to re-adjust the index values for the remaining pages
        for i, (index, name) in enumerate(self.liststore):
            self.liststore[i][0] = i

    def show(self, page=None):
        """Page should be the string in the left list.. ie, 'Network' or
        'Bandwidth'"""
        if page != None:
            for (index, string) in self.liststore:
                if page == string:
                    self.treeview.get_selection().select_path(index)
                    break

        component.get("PluginManager").run_on_show_prefs()

        # Update the preferences dialog to reflect current config settings
        self.core_config = {}
        if client.connected():
            def _on_get_config(config):
                self.core_config = config
                client.core.get_available_plugins().addCallback(_on_get_available_plugins)

            def _on_get_available_plugins(plugins):
                self.all_plugins = plugins
                client.core.get_enabled_plugins().addCallback(_on_get_enabled_plugins)

            def _on_get_enabled_plugins(plugins):
                self.enabled_plugins = plugins
                client.core.get_listen_port().addCallback(_on_get_listen_port)

            def _on_get_listen_port(port):
                self.active_port = port
                client.core.get_cache_status().addCallback(_on_get_cache_status)

            def _on_get_cache_status(status):
                self.cache_status = status
                self._show()

            # This starts a series of client.core requests prior to showing the window
            client.core.get_config().addCallback(_on_get_config)
        else:
            self._show()

    def _show(self):
        if self.core_config != {} and self.core_config != None:
            core_widgets = {
                "download_path_button": \
                    ("filename", self.core_config["download_location"]),
                "chk_move_completed": \
                    ("active", self.core_config["move_completed"]),
                "move_completed_path_button": \
                    ("filename", self.core_config["move_completed_path"]),
                "chk_copy_torrent_file": \
                    ("active", self.core_config["copy_torrent_file"]),
                "chk_del_copy_torrent_file": \
                    ("active", self.core_config["del_copy_torrent_file"]),
                "torrent_files_button": \
                    ("filename", self.core_config["torrentfiles_location"]),
                "chk_autoadd": \
                    ("active", self.core_config["autoadd_enable"]),
                "folder_autoadd": \
                    ("filename", self.core_config["autoadd_location"]),
                "radio_compact_allocation": \
                    ("active", self.core_config["compact_allocation"]),
                "radio_full_allocation": \
                    ("not_active", self.core_config["compact_allocation"]),
                "chk_prioritize_first_last_pieces": \
                    ("active",
                        self.core_config["prioritize_first_last_pieces"]),
                "chk_add_paused": ("active", self.core_config["add_paused"]),
                "spin_port_min": ("value", self.core_config["listen_ports"][0]),
                "spin_port_max": ("value", self.core_config["listen_ports"][1]),
                "active_port_label": ("text", str(self.active_port)),
                "chk_random_port": ("active", self.core_config["random_port"]),
                "spin_outgoing_port_min": ("value", self.core_config["outgoing_ports"][0]),
                "spin_outgoing_port_max": ("value", self.core_config["outgoing_ports"][1]),
                "chk_random_outgoing_ports": ("active", self.core_config["random_outgoing_ports"]),
                "entry_interface": ("text", self.core_config["listen_interface"]),
                "entry_peer_tos": ("text", self.core_config["peer_tos"]),
                "chk_dht": ("active", self.core_config["dht"]),
                "chk_upnp": ("active", self.core_config["upnp"]),
                "chk_natpmp": ("active", self.core_config["natpmp"]),
                "chk_utpex": ("active", self.core_config["utpex"]),
                "chk_lsd": ("active", self.core_config["lsd"]),
                "chk_new_releases": ("active", self.core_config["new_release_check"]),
                "chk_send_info": ("active", self.core_config["send_info"]),
                "entry_geoip": ("text", self.core_config["geoip_db_location"]),
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
                "spin_max_half_open_connections": \
                    ("value", self.core_config["max_half_open_connections"]),
                "spin_max_connections_per_second": \
                    ("value", self.core_config["max_connections_per_second"]),
                "chk_ignore_limits_on_local_network": \
                    ("active", self.core_config["ignore_limits_on_local_network"]),
                "chk_rate_limit_ip_overhead": \
                    ("active", self.core_config["rate_limit_ip_overhead"]),
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
                "spin_active": ("value", self.core_config["max_active_limit"]),
                "spin_seeding": ("value", self.core_config["max_active_seeding"]),
                "spin_downloading": ("value", self.core_config["max_active_downloading"]),
                "chk_dont_count_slow_torrents": ("active", self.core_config["dont_count_slow_torrents"]),
                "chk_queue_new_top": ("active", self.core_config["queue_new_to_top"]),
                "spin_share_ratio_limit": ("value", self.core_config["share_ratio_limit"]),
                "spin_seed_time_ratio_limit": \
                    ("value", self.core_config["seed_time_ratio_limit"]),
                "spin_seed_time_limit": ("value", self.core_config["seed_time_limit"]),
                "chk_seed_ratio": ("active", self.core_config["stop_seed_at_ratio"]),
                "spin_share_ratio": ("value", self.core_config["stop_seed_ratio"]),
                "chk_remove_ratio": ("active", self.core_config["remove_seed_at_ratio"]),
                "spin_cache_size": ("value", self.core_config["cache_size"]),
                "spin_cache_expiry": ("value", self.core_config["cache_expiry"])
            }
            # Add proxy stuff

            # Display workaround for single proxy in libtorrent >v0.16
            try:
                lt_single_proxy = component.get("PreferencesManager").LT_SINGLE_PROXY
            except AttributeError:
                lt_single_proxy = False

            for t in ("peer", "web_seed", "tracker", "dht"):
                if lt_single_proxy and not t == "peer":
                    widget = self.glade.get_widget("frame_%s" % t)
                    widget.set_sensitive(False)
                core_widgets["spin_proxy_port_%s" % t] = ("value", self.core_config["proxies"][t]["port"])
                core_widgets["combo_proxy_type_%s" % t] = ("active", self.core_config["proxies"][t]["type"])
                core_widgets["txt_proxy_server_%s" % t] = ("text", self.core_config["proxies"][t]["hostname"])
                core_widgets["txt_proxy_username_%s" % t] = ("text", self.core_config["proxies"][t]["username"])
                core_widgets["txt_proxy_password_%s" % t] = ("text", self.core_config["proxies"][t]["password"])

            # Change a few widgets if we're connected to a remote host
            if not client.is_localhost():
                self.glade.get_widget("entry_download_path").show()
                self.glade.get_widget("download_path_button").hide()
                core_widgets.pop("download_path_button")
                core_widgets["entry_download_path"] = ("text", self.core_config["download_location"])

                self.glade.get_widget("entry_move_completed_path").show()
                self.glade.get_widget("move_completed_path_button").hide()
                core_widgets.pop("move_completed_path_button")
                core_widgets["entry_move_completed_path"] = ("text", self.core_config["move_completed_path"])

                self.glade.get_widget("entry_torrents_path").show()
                self.glade.get_widget("torrent_files_button").hide()
                core_widgets.pop("torrent_files_button")
                core_widgets["entry_torrents_path"] = ("text", self.core_config["torrentfiles_location"])

                self.glade.get_widget("entry_autoadd").show()
                self.glade.get_widget("folder_autoadd").hide()
                core_widgets.pop("folder_autoadd")
                core_widgets["entry_autoadd"] = ("text", self.core_config["autoadd_location"])
            else:
                self.glade.get_widget("entry_download_path").hide()
                self.glade.get_widget("download_path_button").show()
                self.glade.get_widget("entry_move_completed_path").hide()
                self.glade.get_widget("move_completed_path_button").show()
                self.glade.get_widget("entry_torrents_path").hide()
                self.glade.get_widget("torrent_files_button").show()
                self.glade.get_widget("entry_autoadd").hide()
                self.glade.get_widget("folder_autoadd").show()

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
                    if value:
                        try:
                            widget.set_current_folder(value)
                        except Exception, e:
                            log.debug("Unable to set_current_folder: %s", e)
                elif modifier == "active":
                    widget.set_active(value)
                elif modifier == "not_active":
                    widget.set_active(not value)
                elif modifier == "value":
                    widget.set_value(float(value))
                elif modifier == "text":
                    if value is None:
                        value = ""
                    widget.set_text(value)

            for key in core_widgets.keys():
                widget = self.glade.get_widget(key)
                # Update the toggle status if necessary
                self.on_toggle(widget)
        else:
            core_widget_list = [
                "download_path_button",
                "chk_move_completed",
                "move_completed_path_button",
                "chk_copy_torrent_file",
                "chk_del_copy_torrent_file",
                "torrent_files_button",
                "chk_autoadd",
                "folder_autoadd",
                "radio_compact_allocation",
                "radio_full_allocation",
                "chk_prioritize_first_last_pieces",
                "chk_add_paused",
                "spin_port_min",
                "spin_port_max",
                "active_port_label",
                "chk_random_port",
                "spin_outgoing_port_min",
                "spin_outgoing_port_max",
                "chk_random_outgoing_ports",
                "entry_interface",
                "entry_peer_tos",
                "chk_dht",
                "chk_upnp",
                "chk_natpmp",
                "chk_utpex",
                "chk_lsd",
                "chk_send_info",
                "chk_new_releases",
                "entry_geoip",
                "combo_encin",
                "combo_encout",
                "combo_enclevel",
                "chk_pref_rc4",
                "spin_max_connections_global",
                "spin_max_download",
                "spin_max_upload",
                "spin_max_upload_slots_global",
                "spin_max_half_open_connections",
                "spin_max_connections_per_second",
                "chk_ignore_limits_on_local_network",
                "chk_rate_limit_ip_overhead",
                "spin_max_connections_per_torrent",
                "spin_max_upload_slots_per_torrent",
                "spin_max_download_per_torrent",
                "spin_max_upload_per_torrent",
                "spin_daemon_port",
                "chk_allow_remote_connections",
                "spin_seeding",
                "spin_downloading",
                "spin_active",
                "chk_dont_count_slow_torrents",
                "chk_queue_new_top",
                "chk_seed_ratio",
                "spin_share_ratio",
                "chk_remove_ratio",
                "spin_share_ratio_limit",
                "spin_seed_time_ratio_limit",
                "spin_seed_time_limit",
                "spin_cache_size",
                "spin_cache_expiry",
                "button_cache_refresh",
                "btn_testport"
            ]
            for t in ("peer", "web_seed", "tracker", "dht"):
                core_widget_list.append("spin_proxy_port_%s" % t)
                core_widget_list.append("combo_proxy_type_%s" % t)
                core_widget_list.append("txt_proxy_username_%s" % t)
                core_widget_list.append("txt_proxy_password_%s" % t)
                core_widget_list.append("txt_proxy_server_%s" % t)

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

        ## Interface tab ##
        self.glade.get_widget("chk_use_tray").set_active(
            self.gtkui_config["enable_system_tray"])
        self.glade.get_widget("chk_min_on_close").set_active(
            self.gtkui_config["close_to_tray"])
        self.glade.get_widget("chk_start_in_tray").set_active(
            self.gtkui_config["start_in_tray"])
        self.glade.get_widget("chk_enable_appindicator").set_active(
            self.gtkui_config["enable_appindicator"])
        self.glade.get_widget("chk_lock_tray").set_active(
            self.gtkui_config["lock_tray"])
        self.glade.get_widget("chk_classic_mode").set_active(
            self.gtkui_config["classic_mode"])
        self.glade.get_widget("chk_show_rate_in_title").set_active(
            self.gtkui_config["show_rate_in_title"])
        self.glade.get_widget("chk_focus_main_window_on_add").set_active(
            self.gtkui_config["focus_main_window_on_add"])

        ## Other tab ##
        self.glade.get_widget("chk_show_new_releases").set_active(
            self.gtkui_config["show_new_releases"])


        ## Cache tab ##
        if client.connected():
            self.__update_cache_status()

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
            self.plugin_liststore.set_value(row, 2, _(plugin))

        # Now show the dialog
        self.pref_dialog.show()

    def set_config(self, hide=False):
        """
        Sets all altered config values in the core.

        :param hide: bool, if True, will not re-show the dialog and will hide it instead
        """
        try:
            from hashlib import sha1 as sha_hash
        except ImportError:
            from sha import new as sha_hash

        # Get the values from the dialog
        new_core_config = {}
        new_gtkui_config = {}

        ## Downloads tab ##
        new_gtkui_config["interactive_add"] = \
            self.glade.get_widget("chk_show_dialog").get_active()
        new_gtkui_config["focus_add_dialog"] = \
            self.glade.get_widget("chk_focus_dialog").get_active()
        new_core_config["copy_torrent_file"] = \
            self.glade.get_widget("chk_copy_torrent_file").get_active()
        new_core_config["del_copy_torrent_file"] = \
            self.glade.get_widget("chk_del_copy_torrent_file").get_active()
        new_core_config["move_completed"] = \
            self.glade.get_widget("chk_move_completed").get_active()
        if client.is_localhost():
            new_core_config["download_location"] = \
                self.glade.get_widget("download_path_button").get_filename()
            new_core_config["move_completed_path"] = \
                self.glade.get_widget("move_completed_path_button").get_filename()
            new_core_config["torrentfiles_location"] = \
                self.glade.get_widget("torrent_files_button").get_filename()
        else:
            new_core_config["download_location"] = \
                self.glade.get_widget("entry_download_path").get_text()
            new_core_config["move_completed_path"] = \
                self.glade.get_widget("entry_move_completed_path").get_text()
            new_core_config["torrentfiles_location"] = \
                self.glade.get_widget("entry_torrents_path").get_text()

        new_core_config["autoadd_enable"] = \
            self.glade.get_widget("chk_autoadd").get_active()
        if client.is_localhost():
            new_core_config["autoadd_location"] = \
                self.glade.get_widget("folder_autoadd").get_filename()
        else:
            new_core_config["autoadd_location"] = \
                self.glade.get_widget("entry_autoadd").get_text()

        new_core_config["compact_allocation"] = \
            self.glade.get_widget("radio_compact_allocation").get_active()
        new_core_config["prioritize_first_last_pieces"] = \
            self.glade.get_widget(
                "chk_prioritize_first_last_pieces").get_active()
        new_core_config["add_paused"] = \
            self.glade.get_widget("chk_add_paused").get_active()

        ## Network tab ##
        listen_ports = (
            self.glade.get_widget("spin_port_min").get_value_as_int(),
            self.glade.get_widget("spin_port_max").get_value_as_int()
        )
        new_core_config["listen_ports"] = listen_ports
        new_core_config["random_port"] = \
            self.glade.get_widget("chk_random_port").get_active()
        outgoing_ports = (
            self.glade.get_widget("spin_outgoing_port_min").get_value_as_int(),
            self.glade.get_widget("spin_outgoing_port_max").get_value_as_int()
        )
        new_core_config["outgoing_ports"] = outgoing_ports
        new_core_config["random_outgoing_ports"] = \
            self.glade.get_widget("chk_random_outgoing_ports").get_active()
        incoming_address = self.glade.get_widget("entry_interface").get_text().strip()
        if deluge.common.is_ip(incoming_address) or not incoming_address:
            new_core_config["listen_interface"] = incoming_address
        new_core_config["peer_tos"] = self.glade.get_widget("entry_peer_tos").get_text()
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
        new_core_config["max_half_open_connections"] = \
            self.glade.get_widget("spin_max_half_open_connections").get_value_as_int()
        new_core_config["max_connections_per_second"] = \
            self.glade.get_widget(
                "spin_max_connections_per_second").get_value_as_int()
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
        new_core_config["ignore_limits_on_local_network"] = \
            self.glade.get_widget("chk_ignore_limits_on_local_network").get_active()
        new_core_config["rate_limit_ip_overhead"] = \
            self.glade.get_widget("chk_rate_limit_ip_overhead").get_active()

        ## Interface tab ##
        new_gtkui_config["enable_system_tray"] = \
            self.glade.get_widget("chk_use_tray").get_active()
        new_gtkui_config["close_to_tray"] = \
            self.glade.get_widget("chk_min_on_close").get_active()
        new_gtkui_config["start_in_tray"] = \
            self.glade.get_widget("chk_start_in_tray").get_active()
        new_gtkui_config["enable_appindicator"] = \
            self.glade.get_widget("chk_enable_appindicator").get_active()
        new_gtkui_config["lock_tray"] = \
            self.glade.get_widget("chk_lock_tray").get_active()
        passhex = sha_hash(\
            self.glade.get_widget("txt_tray_password").get_text()).hexdigest()
        if passhex != "c07eb5a8c0dc7bb81c217b67f11c3b7a5e95ffd7":
            new_gtkui_config["tray_password"] = passhex
        new_gtkui_config["classic_mode"] = \
            self.glade.get_widget("chk_classic_mode").get_active()
        new_gtkui_config["show_rate_in_title"] = \
            self.glade.get_widget("chk_show_rate_in_title").get_active()
        new_gtkui_config["focus_main_window_on_add"] = \
            self.glade.get_widget("chk_focus_main_window_on_add").get_active()

        ## Other tab ##
        new_gtkui_config["show_new_releases"] = \
            self.glade.get_widget("chk_show_new_releases").get_active()
        new_core_config["send_info"] = \
            self.glade.get_widget("chk_send_info").get_active()
        new_core_config["geoip_db_location"] = \
            self.glade.get_widget("entry_geoip").get_text()

        ## Daemon tab ##
        new_core_config["daemon_port"] = \
            self.glade.get_widget("spin_daemon_port").get_value_as_int()
        new_core_config["allow_remote"] = \
            self.glade.get_widget("chk_allow_remote_connections").get_active()
        new_core_config["new_release_check"] = \
            self.glade.get_widget("chk_new_releases").get_active()

        ## Proxy tab ##
        new_core_config["proxies"] = {}
        for t in ("peer", "web_seed", "tracker", "dht"):
            new_core_config["proxies"][t] = {}
            new_core_config["proxies"][t]["type"] = \
                self.glade.get_widget("combo_proxy_type_%s" % t).get_active()
            new_core_config["proxies"][t]["port"] = \
                self.glade.get_widget("spin_proxy_port_%s" % t).get_value_as_int()
            new_core_config["proxies"][t]["username"] = \
                self.glade.get_widget("txt_proxy_username_%s" % t).get_text()
            new_core_config["proxies"][t]["password"] = \
                self.glade.get_widget("txt_proxy_password_%s" % t).get_text()
            new_core_config["proxies"][t]["hostname"] = \
                self.glade.get_widget("txt_proxy_server_%s" % t).get_text()

        ## Queue tab ##
        new_core_config["queue_new_to_top"] = \
            self.glade.get_widget("chk_queue_new_top").get_active()
        new_core_config["max_active_seeding"] = \
            self.glade.get_widget("spin_seeding").get_value_as_int()
        new_core_config["max_active_downloading"] = \
            self.glade.get_widget("spin_downloading").get_value_as_int()
        new_core_config["max_active_limit"] = \
            self.glade.get_widget("spin_active").get_value_as_int()
        new_core_config["dont_count_slow_torrents"] = \
            self.glade.get_widget("chk_dont_count_slow_torrents").get_active()
        new_core_config["stop_seed_at_ratio"] = \
            self.glade.get_widget("chk_seed_ratio").get_active()
        new_core_config["remove_seed_at_ratio"] = \
            self.glade.get_widget("chk_remove_ratio").get_active()
        new_core_config["stop_seed_ratio"] = \
            self.glade.get_widget("spin_share_ratio").get_value()
        new_core_config["share_ratio_limit"] = \
            self.glade.get_widget("spin_share_ratio_limit").get_value()
        new_core_config["seed_time_ratio_limit"] = \
            self.glade.get_widget("spin_seed_time_ratio_limit").get_value()
        new_core_config["seed_time_limit"] = \
            self.glade.get_widget("spin_seed_time_limit").get_value()

        ## Cache tab ##
        new_core_config["cache_size"] = \
            self.glade.get_widget("spin_cache_size").get_value_as_int()
        new_core_config["cache_expiry"] = \
            self.glade.get_widget("spin_cache_expiry").get_value_as_int()

        # Run plugin hook to apply preferences
        component.get("PluginManager").run_on_apply_prefs()

        # GtkUI
        for key in new_gtkui_config.keys():
            # The values do not match so this needs to be updated
            if self.gtkui_config[key] != new_gtkui_config[key]:
                self.gtkui_config[key] = new_gtkui_config[key]

        # Core
        if client.connected():
            # Only do this if we're connected to a daemon
            config_to_set = {}
            for key in new_core_config.keys():
                # The values do not match so this needs to be updated
                try:
                    if self.core_config[key] != new_core_config[key]:
                        config_to_set[key] = new_core_config[key]
                except KeyError:
                    config_to_set[key] = new_core_config[key]

            if config_to_set:
                # Set each changed config value in the core
                client.core.set_config(config_to_set)
                client.force_call(True)
                # Update the configuration
                self.core_config.update(config_to_set)

        if hide:
            self.hide()
        else:
            # Re-show the dialog to make sure everything has been updated
            self.show()

        if client.is_classicmode() != new_gtkui_config["classic_mode"]:
            dialog = gtk.MessageDialog(
                flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                type=gtk.MESSAGE_QUESTION,
                buttons=gtk.BUTTONS_YES_NO,
                message_format=_("You must restart the deluge UI to change classic mode. Quit now?")
            )
            result = dialog.run()
            if result == gtk.RESPONSE_YES:
                shutdown_daemon = (not client.is_classicmode() and
                                   client.connected() and
                                   client.is_localhost())
                component.get("MainWindow").quit(shutdown=shutdown_daemon)
            dialog.destroy()


    def hide(self):
        self.glade.get_widget("port_img").hide()
        self.pref_dialog.hide()

    def __update_cache_status(self):
        # Updates the cache status labels with the info in the dict
        for widget in self.glade.get_widget_prefix("label_cache_"):
            key = widget.get_name()[len("label_cache_"):]
            value = self.cache_status[key]
            if type(value) == float:
                value = "%.2f" % value
            else:
                value = str(value)

            widget.set_text(value)

    def _on_button_cache_refresh_clicked(self, widget):
        def on_get_cache_status(status):
            self.cache_status = status
            self.__update_cache_status()

        client.core.get_cache_status().addCallback(on_get_cache_status)

    def on_pref_dialog_delete_event(self, widget, event):
        self.hide()
        return True

    def load_pref_dialog_state(self):
        w = self.gtkui_config["pref_dialog_width"]
        h = self.gtkui_config["pref_dialog_height"]
        if w != None and h != None:
            self.pref_dialog.resize(w, h)

    def on_pref_dialog_configure_event(self, widget, event):
        self.gtkui_config["pref_dialog_width"] = event.width
        self.gtkui_config["pref_dialog_height"] = event.height

    def on_toggle(self, widget):
        """Handles widget sensitivity based on radio/check button values."""
        try:
            value = widget.get_active()
        except:
            return

        dependents = {
                "chk_show_dialog": {"chk_focus_dialog": True},
                "chk_random_port": {"spin_port_min": False,
                                    "spin_port_max": False},
                "chk_random_outgoing_ports": {"spin_outgoing_port_min": False,
                                              "spin_outgoing_port_max": False},
                "chk_use_tray": {"chk_min_on_close": True,
                                 "chk_start_in_tray": True,
                                 "chk_enable_appindicator": True,
                                 "chk_lock_tray": True},
                "chk_lock_tray": {"txt_tray_password": True,
                                  "password_label": True},
                "radio_open_folder_custom": {"combo_file_manager": False,
                                             "txt_open_folder_location": True},
                "chk_move_completed" : {"move_completed_path_button" : True},
                "chk_copy_torrent_file" : {"torrent_files_button" : True,
                                           "chk_del_copy_torrent_file" : True},
                "chk_autoadd" : {"folder_autoadd" : True},
                "chk_seed_ratio" : {"spin_share_ratio": True,
                                    "chk_remove_ratio" : True}
            }

        def update_dependent_widgets(name, value):
            dependency = dependents[name]
            for dep in dependency.keys():
                depwidget = self.glade.get_widget(dep)
                sensitive = [not value, value][dependency[dep]]
                depwidget.set_sensitive(sensitive)
                if dep in dependents:
                    update_dependent_widgets(dep, depwidget.get_active() and sensitive)

        for key in dependents.keys():
            if widget != self.glade.get_widget(key):
                continue
            update_dependent_widgets(key, value)

    def on_button_ok_clicked(self, data):
        log.debug("on_button_ok_clicked")
        self.set_config(hide=True)
        return True

    def on_button_apply_clicked(self, data):
        log.debug("on_button_apply_clicked")
        self.set_config()

    def on_button_cancel_clicked(self, data):
        log.debug("on_button_cancel_clicked")
        self.hide()
        return True

    def on_selection_changed(self, treeselection):
        # Show the correct notebook page based on what row is selected.
        (model, row) = treeselection.get_selected()
        try:
            self.notebook.set_current_page(model.get_value(row, 0))
        except TypeError:
            pass

    def on_test_port_clicked(self, data):
        log.debug("on_test_port_clicked")
        def on_get_test(status):
            if status:
                self.glade.get_widget("port_img").set_from_stock(gtk.STOCK_YES, 4)
                self.glade.get_widget("port_img").show()
            else:
                self.glade.get_widget("port_img").set_from_stock(gtk.STOCK_DIALOG_WARNING, 4)
                self.glade.get_widget("port_img").show()
        client.core.test_listen_port().addCallback(on_get_test)
        self.glade.get_widget("port_img").set_from_file(
            deluge.common.get_pixmap('loading.gif')
        )
        self.glade.get_widget("port_img").show()
        client.force_call()

    def on_plugin_toggled(self, renderer, path):
        log.debug("on_plugin_toggled")
        row = self.plugin_liststore.get_iter_from_string(path)
        name = self.plugin_liststore.get_value(row, 0)
        value = self.plugin_liststore.get_value(row, 1)
        self.plugin_liststore.set_value(row, 1, not value)
        if not value:
            client.core.enable_plugin(name)
        else:
            client.core.disable_plugin(name)
            component.get("PluginManager").disable_plugin(name)

    def on_plugin_selection_changed(self, treeselection):
        log.debug("on_plugin_selection_changed")
        (model, itr) = treeselection.get_selected()
        if not itr:
            return
        name = model[itr][0]
        plugin_info = component.get("PluginManager").get_plugin_info(name)
        self.glade.get_widget("label_plugin_author").set_text(plugin_info["Author"])
        self.glade.get_widget("label_plugin_version").set_text(plugin_info["Version"])
        self.glade.get_widget("label_plugin_email").set_text(plugin_info["Author-email"])
        self.glade.get_widget("label_plugin_homepage").set_text(plugin_info["Home-page"])
        self.glade.get_widget("label_plugin_details").set_text(plugin_info["Description"])

    def _on_button_plugin_install_clicked(self, widget):
        log.debug("_on_button_plugin_install_clicked")
        chooser = gtk.FileChooserDialog(_("Select the Plugin"),
            self.pref_dialog,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK))

        chooser.set_transient_for(self.pref_dialog)
        chooser.set_select_multiple(False)
        chooser.set_property("skip-taskbar-hint", True)

        file_filter = gtk.FileFilter()
        file_filter.set_name(_("Plugin Eggs"))
        file_filter.add_pattern("*." + "egg")
        chooser.add_filter(file_filter)

        # Run the dialog
        response = chooser.run()

        if response == gtk.RESPONSE_OK:
            filepath = deluge.common.decode_string(chooser.get_filename())
        else:
            chooser.destroy()
            return

        import base64
        import shutil
        import os.path
        filename = os.path.split(filepath)[1]
        shutil.copyfile(
            filepath,
            os.path.join(deluge.configmanager.get_config_dir(), "plugins", filename))

        component.get("PluginManager").scan_for_plugins()

        if not client.is_localhost():
            # We need to send this plugin to the daemon
            with open(filepath, "rb") as _file:
                filedump = base64.encodestring(_file.read())
            client.core.upload_plugin(filename, filedump)

        client.core.rescan_plugins()
        chooser.destroy()
        # We need to re-show the preferences dialog to show the new plugins
        self.show()

    def _on_button_rescan_plugins_clicked(self, widget):
        component.get("PluginManager").scan_for_plugins()
        if client.connected():
            client.core.rescan_plugins()
        self.show()

    def _on_button_find_plugins_clicked(self, widget):
        deluge.common.open_url_in_browser("http://dev.deluge-torrent.org/wiki/Plugins")

    def _on_combo_proxy_type_changed(self, widget):
        name = widget.get_name().replace("combo_proxy_type_", "")
        proxy_type = widget.get_model()[widget.get_active()][0]

        prefixes = ["txt_proxy_", "label_proxy_", "spin_proxy_"]
        hides = []
        shows = []

        if proxy_type == "None":
            hides.extend(["password", "username", "server", "port"])
        elif proxy_type in ("Socksv4", "Socksv5", "HTTP"):
            hides.extend(["password", "username"])
            shows.extend(["server", "port"])
        elif proxy_type in ("Socksv5 W/ Auth", "HTTP W/ Auth"):
            shows.extend(["password", "username", "server", "port"])

        for h in hides:
            for p in prefixes:
                w = self.glade.get_widget(p + h + "_" + name)
                if w:
                    w.hide()
        for s in shows:
            for p in prefixes:
                w = self.glade.get_widget(p + s + "_" + name)
                if w:
                    w.show()

    def _on_button_associate_magnet_clicked(self, widget):
        common.associate_magnet_links(True)
