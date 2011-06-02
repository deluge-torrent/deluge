#
# preferences.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
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


import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import logging
import pkg_resources

import deluge.component as component
from deluge.ui.client import client
import deluge.common
import common
import dialogs
from deluge.configmanager import ConfigManager
import deluge.configmanager

log = logging.getLogger(__name__)

ACCOUNTS_USERNAME, ACCOUNTS_LEVEL, ACCOUNTS_PASSWORD = range(3)
COLOR_MISSING, COLOR_WAITING, COLOR_DOWNLOADING, COLOR_COMPLETED = range(4)

COLOR_STATES = {
    "missing": COLOR_MISSING,
    "waiting": COLOR_WAITING,
    "downloading": COLOR_DOWNLOADING,
    "completed": COLOR_COMPLETED
}

class Preferences(component.Component):
    def __init__(self):
        component.Component.__init__(self, "Preferences")
        self.window = component.get("MainWindow")
        self.glade = gtk.glade.XML(pkg_resources.resource_filename(
            "deluge.ui.gtkui", "glade/preferences_dialog.glade"
        ))
        self.pref_dialog = self.glade.get_widget("pref_dialog")
        self.pref_dialog.set_icon(common.get_deluge_icon())
        self.treeview = self.glade.get_widget("treeview")
        self.notebook = self.glade.get_widget("notebook")
        self.gtkui_config = ConfigManager("gtkui.conf")

        self.glade.get_widget("image_magnet").set_from_file(
            deluge.common.get_pixmap("magnet.png"))

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

        # Setup accounts tab lisview
        self.accounts_levels_mapping = None
        self.accounts_authlevel = self.glade.get_widget("accounts_authlevel")
        self.accounts_liststore = gtk.ListStore(str, str, str, int)
        self.accounts_liststore.set_sort_column_id(ACCOUNTS_USERNAME,
                                                   gtk.SORT_ASCENDING)
        self.accounts_listview = self.glade.get_widget("accounts_listview")
        self.accounts_listview.append_column(
            gtk.TreeViewColumn(
                _("Username"), gtk.CellRendererText(), text=ACCOUNTS_USERNAME
            )
        )
        self.accounts_listview.append_column(
            gtk.TreeViewColumn(
                _("Level"), gtk.CellRendererText(), text=ACCOUNTS_LEVEL
            )
        )
        password_column = gtk.TreeViewColumn(
            'password', gtk.CellRendererText(), text=ACCOUNTS_PASSWORD
        )
        self.accounts_listview.append_column(password_column)
        password_column.set_visible(False)
        self.accounts_listview.set_model(self.accounts_liststore)

        self.accounts_listview.get_selection().connect(
            "changed", self._on_accounts_selection_changed
        )
        self.accounts_frame = self.glade.get_widget("AccountsFrame")

        # Setup plugin tab listview
        self.plugin_liststore = gtk.ListStore(str, bool)
        self.plugin_liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
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
        self.treeview.get_selection().connect(
            "changed", self.on_selection_changed
        )

        self.plugin_listview.get_selection().connect(
            "changed", self.on_plugin_selection_changed
        )

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
            "on_accounts_add_clicked": self._on_accounts_add_clicked,
            "on_accounts_delete_clicked": self._on_accounts_delete_clicked,
            "on_accounts_edit_clicked": self._on_accounts_edit_clicked,
            "on_alocation_toggled": self._on_alocation_toggled,
            "on_piecesbar_toggle_toggled": self._on_piecesbar_toggle_toggled,
            "on_completed_color_set": self._on_completed_color_set,
            "on_revert_color_completed_clicked": self._on_revert_color_completed_clicked,
            "on_downloading_color_set": self._on_downloading_color_set,
            "on_revert_color_downloading_clicked": self._on_revert_color_downloading_clicked,
            "on_waiting_color_set": self._on_waiting_color_set,
            "on_revert_color_waiting_clicked": self._on_revert_color_waiting_clicked,
            "on_missing_color_set": self._on_missing_color_set,
            "on_revert_color_missing_clicked": self._on_revert_color_missing_clicked
        })

        from deluge.ui.gtkui.gtkui import DEFAULT_PREFS
        self.COLOR_DEFAULTS = {}
        for key in ("missing", "waiting", "downloading", "completed"):
            self.COLOR_DEFAULTS[key] = DEFAULT_PREFS["pieces_color_%s" % key][:]
        del DEFAULT_PREFS

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
            self._get_accounts_tab_data()

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
                "radio_compact_allocation": \
                    ("active", self.core_config["compact_allocation"]),
                "radio_full_allocation": \
                    ("not_active", self.core_config["compact_allocation"]),
                "chk_prioritize_first_last_pieces": \
                    ("active",
                        self.core_config["prioritize_first_last_pieces"]),
                "chk_sequential_download": \
                    ("active",
                        self.core_config["sequential_download"]),
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
            for t in ("peer", "web_seed", "tracker", "dht"):
                core_widgets["spin_proxy_port_%s" % t] = (
                    "value", self.core_config["proxies"][t]["port"]
                )
                core_widgets["combo_proxy_type_%s" % t] = (
                    "active", self.core_config["proxies"][t]["type"]
                )
                core_widgets["txt_proxy_server_%s" % t] = (
                    "text", self.core_config["proxies"][t]["hostname"]
                )
                core_widgets["txt_proxy_username_%s" % t] = (
                    "text", self.core_config["proxies"][t]["username"]
                )
                core_widgets["txt_proxy_password_%s" % t] = (
                    "text", self.core_config["proxies"][t]["password"]
                )

            # Change a few widgets if we're connected to a remote host
            if not client.is_localhost():
                self.glade.get_widget("entry_download_path").show()
                self.glade.get_widget("download_path_button").hide()
                core_widgets.pop("download_path_button")
                core_widgets["entry_download_path"] = (
                    "text", self.core_config["download_location"]
                )

                self.glade.get_widget("entry_move_completed_path").show()
                self.glade.get_widget("move_completed_path_button").hide()
                core_widgets.pop("move_completed_path_button")
                core_widgets["entry_move_completed_path"] = (
                    "text", self.core_config["move_completed_path"]
                )

                self.glade.get_widget("entry_torrents_path").show()
                self.glade.get_widget("torrent_files_button").hide()
                core_widgets.pop("torrent_files_button")
                core_widgets["entry_torrents_path"] = (
                    "text", self.core_config["torrentfiles_location"]
                )
            else:
                self.glade.get_widget("entry_download_path").hide()
                self.glade.get_widget("download_path_button").show()
                self.glade.get_widget("entry_move_completed_path").hide()
                self.glade.get_widget("move_completed_path_button").show()
                self.glade.get_widget("entry_torrents_path").hide()
                self.glade.get_widget("torrent_files_button").show()

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
                "radio_compact_allocation",
                "radio_full_allocation",
                "chk_prioritize_first_last_pieces",
                "chk_sequential_download",
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
        self.glade.get_widget("piecesbar_toggle").set_active(
            self.gtkui_config["show_piecesbar"]
        )
        self.__set_color("completed", from_config=True)
        self.__set_color("downloading", from_config=True)
        self.__set_color("waiting", from_config=True)
        self.__set_color("missing", from_config=True)

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

        # Now show the dialog
        self.pref_dialog.show()

    def set_config(self, hide=False):
        """
        Sets all altered config values in the core.

        :param hide: bool, if True, will not re-show the dialog and will hide
        it instead
        """
        try:
            from hashlib import sha1 as sha_hash
        except ImportError:
            from sha import new as sha_hash

        classic_mode_was_set = self.gtkui_config["classic_mode"]

        # Get the values from the dialog
        new_core_config = {}
        new_gtkui_config = {}

        ## Downloads tab ##
        new_gtkui_config["interactive_add"] = \
            self.glade.get_widget("chk_show_dialog").get_active()
        new_gtkui_config["focus_add_dialog"] = \
            self.glade.get_widget("chk_focus_dialog").get_active()

        for state in ("missing", "waiting", "downloading", "completed"):
            color = self.glade.get_widget("%s_color" % state).get_color()
            new_gtkui_config["pieces_color_%s" % state] = [
                color.red, color.green, color.blue
            ]

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

        new_core_config["compact_allocation"] = \
            self.glade.get_widget("radio_compact_allocation").get_active()
        new_core_config["prioritize_first_last_pieces"] = \
            self.glade.get_widget(
                "chk_prioritize_first_last_pieces").get_active()
        new_core_config["sequential_download"] = \
            self.glade.get_widget("chk_sequential_download").get_active()
        new_core_config["sequential_download"] = \
            self.glade.get_widget("radio_compact_allocation").get_active() and \
            False or self.glade.get_widget("chk_sequential_download").get_active()
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
        new_core_config["listen_interface"] = self.glade.get_widget("entry_interface").get_text()
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

        new_gtkui_in_classic_mode = self.glade.get_widget("chk_classic_mode").get_active()
        new_gtkui_config["classic_mode"] = new_gtkui_in_classic_mode

        new_gtkui_config["show_rate_in_title"] = \
            self.glade.get_widget("chk_show_rate_in_title").get_active()

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
                if self.core_config[key] != new_core_config[key]:
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

        if classic_mode_was_set == True and new_gtkui_in_classic_mode == False:
            def on_response(response):
                if response == gtk.RESPONSE_NO:
                    # Set each changed config value in the core
                    self.gtkui_config["classic_mode"] = True
                    self.glade.get_widget("chk_classic_mode").set_active(True)
                else:
                    client.disconnect()
                    component.stop()
            dialog = dialogs.YesNoDialog(
                _("Attention"),
                _("Your current session will be stopped. Continue?")
            )
            dialog.run().addCallback(on_response)
        elif classic_mode_was_set == False and new_gtkui_in_classic_mode == True:
            dialog = dialogs.InformationDialog(
                _("Attention"),
                _("You must now restart the deluge UI")
            )
            dialog.run()

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
            if model.get_value(row, 1) == _("Daemon"):
                # Let's see update the accounts related stuff
                if client.connected():
                    self._get_accounts_tab_data()
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
        # XXX: Consider using gtk.Spinner() instead of the loading gif
        #      It requires gtk.ver > 2.12
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
            filepath = chooser.get_filename()
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
            filedump = base64.encodestring(open(filepath, "rb").read())
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


    def _get_accounts_tab_data(self):
        def on_ok(accounts):
            self.accounts_frame.show()
            self._on_get_known_accounts(accounts)

        def on_fail(failure):
            if failure.value.exception_type == 'NotAuthorizedError':
                self.accounts_frame.hide()
            else:
                dialogs.ErrorDialog(
                    _("Server Side Error"),
                    _("An error ocurred on the server"),
                    self.pref_dialog, details=failure.value.logable()
                ).run()
        client.core.get_known_accounts().addCallback(on_ok).addErrback(on_fail)

    def _on_get_known_accounts(self, known_accounts):
        known_accounts_to_log = []
        for account in known_accounts:
            account_to_log = {}
            for key, value in account.copy().iteritems():
                if key == 'password':
                    value = '*' * len(value)
                account_to_log[key] = value
            known_accounts_to_log.append(account_to_log)
        log.debug("_on_known_accounts: %s", known_accounts_to_log)

        self.accounts_liststore.clear()

        for account in known_accounts:
            iter = self.accounts_liststore.append()
            self.accounts_liststore.set_value(
                iter, ACCOUNTS_USERNAME, account['username']
            )
            self.accounts_liststore.set_value(
                iter, ACCOUNTS_LEVEL, account['authlevel']
            )
            self.accounts_liststore.set_value(
                iter, ACCOUNTS_PASSWORD, account['password']
            )

    def _on_accounts_selection_changed(self, treeselection):
        log.debug("_on_accounts_selection_changed")
        (model, itr) = treeselection.get_selected()
        if not itr:
            return
        username = model[itr][0]
        if username:
            self.glade.get_widget("accounts_edit").set_sensitive(True)
            self.glade.get_widget("accounts_delete").set_sensitive(True)
        else:
            self.glade.get_widget("accounts_edit").set_sensitive(False)
            self.glade.get_widget("accounts_delete").set_sensitive(False)

    def _on_accounts_add_clicked(self, widget):
        dialog = dialogs.AccountDialog(
            levels_mapping=client.auth_levels_mapping,
            parent=self.pref_dialog
        )

        def dialog_finished(response_id):
            username = dialog.get_username()
            password = dialog.get_password()
            authlevel = dialog.get_authlevel()

            def add_ok(rv):
                iter = self.accounts_liststore.append()
                self.accounts_liststore.set_value(
                    iter, ACCOUNTS_USERNAME, username
                )
                self.accounts_liststore.set_value(
                    iter, ACCOUNTS_LEVEL, authlevel
                )
                self.accounts_liststore.set_value(
                    iter, ACCOUNTS_PASSWORD, password
                )

            def add_fail(failure):
                if failure.value.exception_type == 'AuthManagerError':
                    dialogs.ErrorDialog(
                        _("Error Adding Account"),
                        failure.value.exception_msg
                    ).run()
                else:
                    dialogs.ErrorDialog(
                        _("Error Adding Account"),
                        _("An error ocurred while adding account"),
                          self.pref_dialog, details=failure.value.logable()
                    ).run()

            if response_id == gtk.RESPONSE_OK:
                client.core.create_account(
                    username, password, authlevel
                ).addCallback(add_ok).addErrback(add_fail)

        dialog.run().addCallback(dialog_finished)

    def _on_accounts_edit_clicked(self, widget):
        (model, itr) = self.accounts_listview.get_selection().get_selected()
        if not itr:
            return

        dialog = dialogs.AccountDialog(
            model[itr][ACCOUNTS_USERNAME],
            model[itr][ACCOUNTS_PASSWORD],
            model[itr][ACCOUNTS_LEVEL],
            levels_mapping=client.auth_levels_mapping,
            parent=self.pref_dialog
        )

        def dialog_finished(response_id):

            def update_ok(rc):
                model.set_value(itr, ACCOUNTS_PASSWORD, dialog.get_username())
                model.set_value(itr, ACCOUNTS_LEVEL, dialog.get_authlevel())

            def update_fail(failure):
                dialogs.ErrorDialog(
                    _("Error Updating Account"),
                    _("An error ocurred while updating account"),
                      self.pref_dialog, details=failure.value.logable()
                ).run()

            if response_id == gtk.RESPONSE_OK:
                client.core.update_account(
                    dialog.get_username(),
                    dialog.get_password(),
                    dialog.get_authlevel()
                ).addCallback(update_ok).addErrback(update_fail)

        dialog.run().addCallback(dialog_finished)

    def _on_accounts_delete_clicked(self, widget):
        (model, itr) = self.accounts_listview.get_selection().get_selected()
        if not itr:
            return

        username = model[itr][0]
        header = _("Remove Account")
        text = _("Are you sure you wan't do remove the account with the "
                 "username \"%(username)s\"?" % dict(username=username))
        dialog = dialogs.YesNoDialog(header, text, parent=self.pref_dialog)

        def dialog_finished(response_id):
            def remove_ok(rc):
                model.remove(itr)

            def remove_fail(failure):
                if failure.value.exception_type == 'AuthManagerError':
                    dialogs.ErrorDialog(
                        _("Error Removing Account"),
                        failure.value.exception_msg
                    ).run()
                else:
                    dialogs.ErrorDialog(
                        _("Error Removing Account"),
                        _("An error ocurred while removing account"),
                          self.pref_dialog, details=failure.value.logable()
                    ).run()
            if response_id == gtk.RESPONSE_YES:
                client.core.remove_account(
                    username
                ).addCallback(remove_ok).addErrback(remove_fail)
        dialog.run().addCallback(dialog_finished)

    def _on_alocation_toggled(self, widget):
        full_allocation_active = self.glade.get_widget("radio_full_allocation").get_active()
        self.glade.get_widget("chk_prioritize_first_last_pieces").set_sensitive(full_allocation_active)
        self.glade.get_widget("chk_sequential_download").set_sensitive(full_allocation_active)

    def _on_piecesbar_toggle_toggled(self, widget):
        self.gtkui_config['show_piecesbar'] = widget.get_active()
        colors_widget = self.glade.get_widget("piecebar_colors_expander")
        colors_widget.set_visible(widget.get_active())

    def _on_completed_color_set(self, widget):
        self.__set_color("completed")

    def _on_revert_color_completed_clicked(self, widget):
        self.__revert_color("completed")

    def _on_downloading_color_set(self, widget):
        self.__set_color("downloading")

    def _on_revert_color_downloading_clicked(self, widget):
        self.__revert_color("downloading")

    def _on_waiting_color_set(self, widget):
        self.__set_color("waiting")

    def _on_revert_color_waiting_clicked(self, widget):
        self.__revert_color("waiting")

    def _on_missing_color_set(self, widget):
        self.__set_color("missing")

    def _on_revert_color_missing_clicked(self, widget):
        self.__revert_color("missing")

    def __set_color(self, state, from_config=False):
        if from_config:
            color = gtk.gdk.Color(*self.gtkui_config["pieces_color_%s" % state])
            log.debug("Setting %r color state from config to %s", state,
                      (color.red, color.green, color.blue))
            self.glade.get_widget("%s_color" % state).set_color(color)
        else:
            color = self.glade.get_widget("%s_color" % state).get_color()
            log.debug("Setting %r color state to %s", state,
                      (color.red, color.green, color.blue))
            self.gtkui_config["pieces_color_%s" % state] = [
                color.red, color.green, color.blue
            ]
            self.gtkui_config.save()
            self.gtkui_config.apply_set_functions("pieces_colors")

        self.glade.get_widget("revert_color_%s" % state).set_sensitive(
            [color.red, color.green, color.blue] != self.COLOR_DEFAULTS[state]
        )

    def __revert_color(self, state, from_config=False):
        log.debug("Reverting %r color state", state)
        self.glade.get_widget("%s_color" % state).set_color(
            gtk.gdk.Color(*self.COLOR_DEFAULTS[state])
        )
        self.glade.get_widget("revert_color_%s" % state).set_sensitive(False)
        self.gtkui_config.apply_set_functions("pieces_colors")
