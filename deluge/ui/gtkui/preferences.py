# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os
from hashlib import sha1 as sha

import gtk
import pygtk

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import AuthManagerError, NotAuthorizedError
from deluge.ui.client import client
from deluge.ui.gtkui.common import associate_magnet_links, get_deluge_icon
from deluge.ui.gtkui.dialogs import AccountDialog, ErrorDialog, InformationDialog, YesNoDialog
from deluge.ui.gtkui.path_chooser import PathChooser

pygtk.require('2.0')


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
        self.builder = gtk.Builder()
        self.builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "preferences_dialog.ui")
        ))
        self.pref_dialog = self.builder.get_object("pref_dialog")
        self.pref_dialog.set_transient_for(component.get("MainWindow").window)
        self.pref_dialog.set_icon(get_deluge_icon())
        self.treeview = self.builder.get_object("treeview")
        self.notebook = self.builder.get_object("notebook")
        self.gtkui_config = ConfigManager("gtkui.conf")
        self.window_open = False

        self.load_pref_dialog_state()

        self.builder.get_object("image_magnet").set_from_file(
            deluge.common.get_pixmap("magnet.png"))

        # Hide the unused associate magnet button on OSX see: #2420
        if deluge.common.osx_check():
            self.builder.get_object("button_associate_magnet").hide()

        # Setup the liststore for the categories (tab pages)
        self.liststore = gtk.ListStore(int, str)
        self.treeview.set_model(self.liststore)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Categories"), render, text=1)
        self.treeview.append_column(column)
        # Add the default categories
        i = 0
        for category in (_("Interface"), _("Downloads"), _("Bandwidth"), _("Queue"), _("Network"),
                         _("Proxy"), _("Cache"), _("Other"), _("Daemon"), _("Plugins"), "_separator_"):
            self.liststore.append([i, category])
            i += 1

        def set_separator(model, iter, data=None):
            if "_separator_" == model.get_value(iter, 1):
                return True
        self.treeview.set_row_separator_func(set_separator)

        # Setup accounts tab lisview
        self.accounts_levels_mapping = None
        self.accounts_authlevel = self.builder.get_object("accounts_authlevel")
        self.accounts_liststore = gtk.ListStore(str, str, str, int)
        self.accounts_liststore.set_sort_column_id(ACCOUNTS_USERNAME, gtk.SORT_ASCENDING)
        self.accounts_listview = self.builder.get_object("accounts_listview")
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
        self.accounts_frame = self.builder.get_object("AccountsFrame")

        # Setup plugin tab listview
        # The third entry is for holding translated plugin names
        self.plugin_liststore = gtk.ListStore(str, bool, str)
        self.plugin_liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.plugin_listview = self.builder.get_object("plugin_listview")
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
        self.treeview.get_selection().connect(
            "changed", self.on_selection_changed
        )

        self.plugin_listview.get_selection().connect(
            "changed", self.on_plugin_selection_changed
        )

        self.builder.connect_signals({
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
            "on_combo_encryption_changed": self._on_combo_encryption_changed,
            "on_combo_proxy_type_changed": self._on_combo_proxy_type_changed,
            "on_button_associate_magnet_clicked": self._on_button_associate_magnet_clicked,
            "on_accounts_add_clicked": self._on_accounts_add_clicked,
            "on_accounts_delete_clicked": self._on_accounts_delete_clicked,
            "on_accounts_edit_clicked": self._on_accounts_edit_clicked,
            "on_piecesbar_toggle_toggled": self._on_piecesbar_toggle_toggled,
            "on_completed_color_set": self._on_completed_color_set,
            "on_revert_color_completed_clicked": self._on_revert_color_completed_clicked,
            "on_downloading_color_set": self._on_downloading_color_set,
            "on_revert_color_downloading_clicked": self._on_revert_color_downloading_clicked,
            "on_waiting_color_set": self._on_waiting_color_set,
            "on_revert_color_waiting_clicked": self._on_revert_color_waiting_clicked,
            "on_missing_color_set": self._on_missing_color_set,
            "on_revert_color_missing_clicked": self._on_revert_color_missing_clicked,
            "on_pref_dialog_configure_event": self.on_pref_dialog_configure_event,
            "on_checkbutton_language_toggled": self._on_checkbutton_language_toggled,
        })

        if not deluge.common.osx_check() and not deluge.common.windows_check():
            try:
                import appindicator
                assert appindicator  # silence pyflakes
            except ImportError:
                pass
            else:
                self.builder.get_object("alignment_tray_type").set_visible(True)

        from deluge.ui.gtkui.gtkui import DEFAULT_PREFS
        self.COLOR_DEFAULTS = {}
        for key in ("missing", "waiting", "downloading", "completed"):
            self.COLOR_DEFAULTS[key] = DEFAULT_PREFS["pieces_color_%s" % key][:]
        del DEFAULT_PREFS

        # These get updated by requests done to the core
        self.all_plugins = []
        self.enabled_plugins = []

        self.setup_path_choosers()
        self.load_languages()

    def setup_path_choosers(self):
        self.download_location_hbox = self.builder.get_object("hbox_download_to_path_chooser")
        self.download_location_path_chooser = PathChooser("download_location_paths_list")
        self.download_location_hbox.add(self.download_location_path_chooser)
        self.download_location_hbox.show_all()

        self.move_completed_hbox = self.builder.get_object("hbox_move_completed_to_path_chooser")
        self.move_completed_path_chooser = PathChooser("move_completed_paths_list")
        self.move_completed_hbox.add(self.move_completed_path_chooser)
        self.move_completed_hbox.show_all()

        self.copy_torrents_to_hbox = self.builder.get_object("hbox_copy_torrent_files_path_chooser")
        self.copy_torrent_files_path_chooser = PathChooser("copy_torrent_files_to_paths_list")
        self.copy_torrents_to_hbox.add(self.copy_torrent_files_path_chooser)
        self.copy_torrents_to_hbox.show_all()

    def load_languages(self):
        from deluge.ui import languages  # Import here so that gettext has been setup first
        translations_path = deluge.common.get_translations_path()
        for root, dirs, files in os.walk(translations_path):
            # Get the dirs
            break
        self.language_combo = self.builder.get_object("combobox_language")
        self.language_checkbox = self.builder.get_object("checkbutton_language")
        lang_model = self.language_combo.get_model()

        index = -1
        for i, lang_code in enumerate(sorted(dirs)):
            name = "%s (Language name missing)" % lang_code
            if lang_code in languages.LANGUAGES:
                name = languages.LANGUAGES[lang_code]
            lang_model.append([lang_code, name])
            if self.gtkui_config["language"] == lang_code:
                index = i

        if self.gtkui_config["language"] is None:
            self.language_checkbox.set_active(True)
            self.language_combo.set_visible(False)
        elif index != -1:
            self.language_combo.set_active(index)

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
        if self.page_num_to_remove is not None:
            self.notebook.remove_page(self.page_num_to_remove)
        if self.iter_to_remove is not None:
            self.liststore.remove(self.iter_to_remove)

        # We need to re-adjust the index values for the remaining pages
        for i, (index, name) in enumerate(self.liststore):
            self.liststore[i][0] = i

    def show(self, page=None):
        """Page should be the string in the left list.. ie, 'Network' or
        'Bandwidth'"""
        self.window_open = True
        if page is not None:
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

    def start(self):
        if self.window_open:
            self.show()

    def stop(self):
        self.core_config = None
        if self.window_open:
            self._show()

    def _show(self):
        self.is_connected = self.core_config != {} and self.core_config is not None
        core_widgets = {
            "chk_move_completed": ("active", "move_completed"),
            "chk_copy_torrent_file": ("active", "copy_torrent_file"),
            "chk_del_copy_torrent_file": ("active", "del_copy_torrent_file"),
            "chk_pre_allocation": ("active", "pre_allocate_storage"),
            "chk_prioritize_first_last_pieces": ("active", "prioritize_first_last_pieces"),
            "chk_sequential_download": ("active", "sequential_download"),
            "chk_add_paused": ("active", "add_paused"),
            "active_port_label": ("text", lambda: str(self.active_port)),
            "spin_port_min": ("value", lambda: self.core_config["listen_ports"][0]),
            "spin_port_max": ("value", lambda: self.core_config["listen_ports"][1]),
            "chk_random_port": ("active", "random_port"),
            "spin_outgoing_port_min": ("value", lambda: self.core_config["outgoing_ports"][0]),
            "spin_outgoing_port_max": ("value", lambda: self.core_config["outgoing_ports"][1]),
            "chk_random_outgoing_ports": ("active", "random_outgoing_ports"),
            "entry_interface": ("text", "listen_interface"),
            "entry_peer_tos": ("text", "peer_tos"),
            "chk_dht": ("active", "dht"),
            "chk_upnp": ("active", "upnp"),
            "chk_natpmp": ("active", "natpmp"),
            "chk_utpex": ("active", "utpex"),
            "chk_lt_tex": ("active", "lt_tex"),
            "chk_lsd": ("active", "lsd"),
            "chk_new_releases": ("active", "new_release_check"),
            "chk_send_info": ("active", "send_info"),
            "entry_geoip": ("text", "geoip_db_location"),
            "combo_encin": ("active", "enc_in_policy"),
            "combo_encout": ("active", "enc_out_policy"),
            "combo_enclevel": ("active", "enc_level"),
            "spin_max_connections_global": ("value", "max_connections_global"),
            "spin_max_download": ("value", "max_download_speed"),
            "spin_max_upload": ("value", "max_upload_speed"),
            "spin_max_upload_slots_global": ("value", "max_upload_slots_global"),
            "spin_max_half_open_connections": ("value", "max_connections_per_second"),
            "spin_max_connections_per_second": ("value", "max_connections_per_second"),
            "chk_ignore_limits_on_local_network": ("active", "ignore_limits_on_local_network"),
            "chk_rate_limit_ip_overhead": ("active", "rate_limit_ip_overhead"),
            "chk_anonymous_mode": ("active", "anonymous_mode"),
            "spin_max_connections_per_torrent": ("value", "max_connections_per_torrent"),
            "spin_max_upload_slots_per_torrent": ("value", "max_upload_slots_per_torrent"),
            "spin_max_download_per_torrent": ("value", "max_download_speed_per_torrent"),
            "spin_max_upload_per_torrent": ("value", "max_upload_speed_per_torrent"),
            "spin_daemon_port": ("value", "daemon_port"),
            "chk_allow_remote_connections": ("active", "allow_remote"),
            "spin_active": ("value", "max_active_limit"),
            "spin_seeding": ("value", "max_active_seeding"),
            "spin_downloading": ("value", "max_active_downloading"),
            "chk_dont_count_slow_torrents": ("active", "dont_count_slow_torrents"),
            "chk_auto_manage_prefer_seeds": ("active", "auto_manage_prefer_seeds"),
            "chk_queue_new_top": ("active", "queue_new_to_top"),
            "spin_share_ratio_limit": ("value", "share_ratio_limit"),
            "spin_seed_time_ratio_limit": ("value", "seed_time_ratio_limit"),
            "spin_seed_time_limit": ("value", "seed_time_limit"),
            "chk_seed_ratio": ("active", "stop_seed_at_ratio"),
            "spin_share_ratio": ("value", "stop_seed_ratio"),
            "chk_remove_ratio": ("active", "remove_seed_at_ratio"),
            "spin_cache_size": ("value", "cache_size"),
            "spin_cache_expiry": ("value", "cache_expiry"),
            "combo_proxy_type": ("active", lambda: self.core_config["proxy"]["type"]),
            "entry_proxy_user": ("text", lambda: self.core_config["proxy"]["username"]),
            "entry_proxy_pass": ("text", lambda: self.core_config["proxy"]["password"]),
            "entry_proxy_host": ("text", lambda: self.core_config["proxy"]["hostname"]),
            "spin_proxy_port": ("value", lambda: self.core_config["proxy"]["port"]),
            "chk_proxy_host_resolve": ("active", lambda: self.core_config["proxy"]["proxy_hostnames"]),
            "chk_proxy_peer_conn": ("active", lambda: self.core_config["proxy"]["proxy_peer_connections"]),
            "entry_i2p_host": ("text", lambda: self.core_config["i2p_proxy"]["hostname"]),
            "spin_i2p_port": ("value", lambda: self.core_config["i2p_proxy"]["port"]),
            "accounts_add": (None, None),
            "accounts_listview": (None, None),
            "button_cache_refresh": (None, None),
            "button_plugin_install": (None, None),
            "button_rescan_plugins": (None, None),
            "button_find_plugins": (None, None),
            "button_testport": (None, None),
            "plugin_listview": (None, None),
        }

        core_widgets[self.download_location_path_chooser] = ("path_chooser", "download_location")
        core_widgets[self.move_completed_path_chooser] = ("path_chooser", "move_completed_path")
        core_widgets[self.copy_torrent_files_path_chooser] = ("path_chooser", "torrentfiles_location")

        # Update the widgets accordingly
        for key in core_widgets.keys():
            modifier = core_widgets[key][0]
            if type(key) is str:
                widget = self.builder.get_object(key)
            else:
                widget = key

            widget.set_sensitive(self.is_connected)

            if self.is_connected:
                value = core_widgets[key][1]
                from types import FunctionType
                if type(value) is FunctionType:
                    value = value()
                elif type(value) is str:
                    value = self.core_config[value]
            elif modifier:
                value = {"active": False, "not_active": False, "value": 0, "text": "", "path_chooser": ""}[modifier]

            if modifier == "active":
                widget.set_active(value)
            elif modifier == "not_active":
                widget.set_active(not value)
            elif modifier == "value":
                widget.set_value(float(value))
            elif modifier == "text":
                if value is None:
                    value = ""
                widget.set_text(value)
            elif modifier == "path_chooser":
                widget.set_text(value, cursor_end=False, default_text=True)

        if self.is_connected:
            for key in core_widgets.keys():
                if type(key) is str:
                    widget = self.builder.get_object(key)
                else:
                    widget = key
                # Update the toggle status if necessary
                self.on_toggle(widget)

        # Downloads tab #
        self.builder.get_object("chk_show_dialog").set_active(
            self.gtkui_config["interactive_add"])
        self.builder.get_object("chk_focus_dialog").set_active(
            self.gtkui_config["focus_add_dialog"])

        # Interface tab #
        self.builder.get_object("chk_use_tray").set_active(
            self.gtkui_config["enable_system_tray"])
        self.builder.get_object("chk_min_on_close").set_active(
            self.gtkui_config["close_to_tray"])
        self.builder.get_object("chk_start_in_tray").set_active(
            self.gtkui_config["start_in_tray"])
        self.builder.get_object("radio_appind").set_active(
            self.gtkui_config["enable_appindicator"])
        self.builder.get_object("chk_lock_tray").set_active(
            self.gtkui_config["lock_tray"])
        self.builder.get_object("radio_classic").set_active(
            self.gtkui_config["classic_mode"])
        self.builder.get_object("radio_thinclient").set_active(
            not self.gtkui_config["classic_mode"])
        self.builder.get_object("chk_show_rate_in_title").set_active(
            self.gtkui_config["show_rate_in_title"])
        self.builder.get_object("chk_focus_main_window_on_add").set_active(
            self.gtkui_config["focus_main_window_on_add"])
        self.builder.get_object("piecesbar_toggle").set_active(
            self.gtkui_config["show_piecesbar"]
        )
        self.__set_color("completed", from_config=True)
        self.__set_color("downloading", from_config=True)
        self.__set_color("waiting", from_config=True)
        self.__set_color("missing", from_config=True)

        # Other tab #
        self.builder.get_object("chk_show_new_releases").set_active(
            self.gtkui_config["show_new_releases"])

        # Cache tab #
        if client.connected():
            self.__update_cache_status()

        # Plugins tab #
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
        classic_mode_was_set = self.gtkui_config["classic_mode"]

        # Get the values from the dialog
        new_core_config = {}
        new_gtkui_config = {}

        # Downloads tab #
        new_gtkui_config["interactive_add"] = \
            self.builder.get_object("chk_show_dialog").get_active()
        new_gtkui_config["focus_add_dialog"] = \
            self.builder.get_object("chk_focus_dialog").get_active()

        for state in ("missing", "waiting", "downloading", "completed"):
            color = self.builder.get_object("%s_color" % state).get_color()
            new_gtkui_config["pieces_color_%s" % state] = [
                color.red, color.green, color.blue
            ]

        new_core_config["copy_torrent_file"] = \
            self.builder.get_object("chk_copy_torrent_file").get_active()
        new_core_config["del_copy_torrent_file"] = \
            self.builder.get_object("chk_del_copy_torrent_file").get_active()
        new_core_config["move_completed"] = \
            self.builder.get_object("chk_move_completed").get_active()

        new_core_config["download_location"] = self.download_location_path_chooser.get_text()
        new_core_config["move_completed_path"] = self.move_completed_path_chooser.get_text()
        new_core_config["torrentfiles_location"] = self.copy_torrent_files_path_chooser.get_text()
        new_core_config["prioritize_first_last_pieces"] = \
            self.builder.get_object("chk_prioritize_first_last_pieces").get_active()
        new_core_config["sequential_download"] = \
            self.builder.get_object("chk_sequential_download").get_active()
        new_core_config["add_paused"] = self.builder.get_object("chk_add_paused").get_active()
        new_core_config["pre_allocate_storage"] = self.builder.get_object("chk_pre_allocation").get_active()

        # Network tab #
        listen_ports = (
            self.builder.get_object("spin_port_min").get_value_as_int(),
            self.builder.get_object("spin_port_max").get_value_as_int()
        )
        new_core_config["listen_ports"] = listen_ports
        new_core_config["random_port"] = \
            self.builder.get_object("chk_random_port").get_active()
        outgoing_ports = (
            self.builder.get_object("spin_outgoing_port_min").get_value_as_int(),
            self.builder.get_object("spin_outgoing_port_max").get_value_as_int()
        )
        new_core_config["outgoing_ports"] = outgoing_ports
        new_core_config["random_outgoing_ports"] = \
            self.builder.get_object("chk_random_outgoing_ports").get_active()
        incoming_address = self.builder.get_object("entry_interface").get_text().strip()
        if deluge.common.is_ip(incoming_address) or not incoming_address:
            new_core_config["listen_interface"] = incoming_address
        new_core_config["peer_tos"] = self.builder.get_object("entry_peer_tos").get_text()
        new_core_config["dht"] = self.builder.get_object("chk_dht").get_active()
        new_core_config["upnp"] = self.builder.get_object("chk_upnp").get_active()
        new_core_config["natpmp"] = \
            self.builder.get_object("chk_natpmp").get_active()
        new_core_config["utpex"] = \
            self.builder.get_object("chk_utpex").get_active()
        new_core_config["lt_tex"] = \
            self.builder.get_object("chk_lt_tex").get_active()
        new_core_config["lsd"] = \
            self.builder.get_object("chk_lsd").get_active()
        new_core_config["enc_in_policy"] = \
            self.builder.get_object("combo_encin").get_active()
        new_core_config["enc_out_policy"] = \
            self.builder.get_object("combo_encout").get_active()
        new_core_config["enc_level"] = \
            self.builder.get_object("combo_enclevel").get_active()

        # Bandwidth tab #
        new_core_config["max_connections_global"] = \
            self.builder.get_object(
                "spin_max_connections_global").get_value_as_int()
        new_core_config["max_download_speed"] = \
            self.builder.get_object("spin_max_download").get_value()
        new_core_config["max_upload_speed"] = \
            self.builder.get_object("spin_max_upload").get_value()
        new_core_config["max_upload_slots_global"] = \
            self.builder.get_object(
                "spin_max_upload_slots_global").get_value_as_int()
        new_core_config["max_half_open_connections"] = \
            self.builder.get_object("spin_max_half_open_connections").get_value_as_int()
        new_core_config["max_connections_per_second"] = \
            self.builder.get_object(
                "spin_max_connections_per_second").get_value_as_int()
        new_core_config["max_connections_per_torrent"] = \
            self.builder.get_object(
                "spin_max_connections_per_torrent").get_value_as_int()
        new_core_config["max_upload_slots_per_torrent"] = \
            self.builder.get_object(
                "spin_max_upload_slots_per_torrent").get_value_as_int()
        new_core_config["max_upload_speed_per_torrent"] = \
            self.builder.get_object(
                "spin_max_upload_per_torrent").get_value()
        new_core_config["max_download_speed_per_torrent"] = \
            self.builder.get_object(
                "spin_max_download_per_torrent").get_value()
        new_core_config["ignore_limits_on_local_network"] = \
            self.builder.get_object("chk_ignore_limits_on_local_network").get_active()
        new_core_config["rate_limit_ip_overhead"] = \
            self.builder.get_object("chk_rate_limit_ip_overhead").get_active()

        # Interface tab #
        new_gtkui_config["enable_system_tray"] = \
            self.builder.get_object("chk_use_tray").get_active()
        new_gtkui_config["close_to_tray"] = \
            self.builder.get_object("chk_min_on_close").get_active()
        new_gtkui_config["start_in_tray"] = \
            self.builder.get_object("chk_start_in_tray").get_active()
        new_gtkui_config["enable_appindicator"] = \
            self.builder.get_object("radio_appind").get_active()
        new_gtkui_config["lock_tray"] = \
            self.builder.get_object("chk_lock_tray").get_active()
        passhex = sha(self.builder.get_object("txt_tray_password").get_text()).hexdigest()
        if passhex != "c07eb5a8c0dc7bb81c217b67f11c3b7a5e95ffd7":
            new_gtkui_config["tray_password"] = passhex

        new_gtkui_in_classic_mode = self.builder.get_object("radio_classic").get_active()
        new_gtkui_config["classic_mode"] = new_gtkui_in_classic_mode

        new_gtkui_config["show_rate_in_title"] = \
            self.builder.get_object("chk_show_rate_in_title").get_active()
        new_gtkui_config["focus_main_window_on_add"] = \
            self.builder.get_object("chk_focus_main_window_on_add").get_active()

        # Other tab #
        new_gtkui_config["show_new_releases"] = \
            self.builder.get_object("chk_show_new_releases").get_active()
        new_core_config["send_info"] = \
            self.builder.get_object("chk_send_info").get_active()
        new_core_config["geoip_db_location"] = \
            self.builder.get_object("entry_geoip").get_text()

        # Daemon tab #
        new_core_config["daemon_port"] = \
            self.builder.get_object("spin_daemon_port").get_value_as_int()
        new_core_config["allow_remote"] = \
            self.builder.get_object("chk_allow_remote_connections").get_active()
        new_core_config["new_release_check"] = \
            self.builder.get_object("chk_new_releases").get_active()

        # Proxy tab #
        new_core_config["proxy"] = {}
        new_core_config["proxy"]["type"] = self.builder.get_object("combo_proxy_type").get_active()
        new_core_config["proxy"]["username"] = self.builder.get_object("entry_proxy_user").get_text()
        new_core_config["proxy"]["password"] = self.builder.get_object("entry_proxy_pass").get_text()
        new_core_config["proxy"]["hostname"] = self.builder.get_object("entry_proxy_host").get_text()
        new_core_config["proxy"]["port"] = self.builder.get_object("spin_proxy_port").get_value_as_int()
        new_core_config["proxy"]["proxy_hostnames"] = self.builder.get_object("chk_proxy_host_resolve").get_active()
        new_core_config["proxy"]["proxy_peer_connections"] = self.builder.get_object(
            "chk_proxy_peer_conn").get_active()
        new_core_config["i2p_proxy"] = {}
        new_core_config["i2p_proxy"]["hostname"] = self.builder.get_object("entry_i2p_host").get_text()
        new_core_config["i2p_proxy"]["port"] = self.builder.get_object("spin_i2p_port").get_value_as_int()
        new_core_config["anonymous_mode"] = self.builder.get_object("chk_anonymous_mode").get_active()

        # Queue tab #
        new_core_config["queue_new_to_top"] = \
            self.builder.get_object("chk_queue_new_top").get_active()
        new_core_config["max_active_seeding"] = \
            self.builder.get_object("spin_seeding").get_value_as_int()
        new_core_config["max_active_downloading"] = \
            self.builder.get_object("spin_downloading").get_value_as_int()
        new_core_config["max_active_limit"] = \
            self.builder.get_object("spin_active").get_value_as_int()
        new_core_config["dont_count_slow_torrents"] = \
            self.builder.get_object("chk_dont_count_slow_torrents").get_active()
        new_core_config["auto_manage_prefer_seeds"] = \
            self.builder.get_object("chk_auto_manage_prefer_seeds").get_active()
        new_core_config["stop_seed_at_ratio"] = \
            self.builder.get_object("chk_seed_ratio").get_active()
        new_core_config["remove_seed_at_ratio"] = \
            self.builder.get_object("chk_remove_ratio").get_active()
        new_core_config["stop_seed_ratio"] = \
            self.builder.get_object("spin_share_ratio").get_value()
        new_core_config["share_ratio_limit"] = \
            self.builder.get_object("spin_share_ratio_limit").get_value()
        new_core_config["seed_time_ratio_limit"] = \
            self.builder.get_object("spin_seed_time_ratio_limit").get_value()
        new_core_config["seed_time_limit"] = \
            self.builder.get_object("spin_seed_time_limit").get_value()

        # Cache tab #
        new_core_config["cache_size"] = \
            self.builder.get_object("spin_cache_size").get_value_as_int()
        new_core_config["cache_expiry"] = \
            self.builder.get_object("spin_cache_expiry").get_value_as_int()

        # Run plugin hook to apply preferences
        component.get("PluginManager").run_on_apply_prefs()

        # Lanuage
        if self.language_checkbox.get_active():
            new_gtkui_config["language"] = None
        else:
            active = self.language_combo.get_active()
            if active == -1:
                dialog = InformationDialog(
                    _("Attention"),
                    _("You must choose a language")
                )
                dialog.run()
                return
            else:
                model = self.language_combo.get_model()
                new_gtkui_config["language"] = model.get(model.get_iter(active), 0)[0]

        if new_gtkui_config["language"] != self.gtkui_config["language"]:
            dialog = InformationDialog(
                _("Attention"),
                _("You must now restart the deluge UI for the changes to take effect.")
            )
            dialog.run()

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

        if classic_mode_was_set != new_gtkui_in_classic_mode:
            def on_response(response):
                if response == gtk.RESPONSE_YES:
                    shutdown_daemon = (not client.is_classicmode() and
                                       client.connected() and
                                       client.is_localhost())
                    component.get("MainWindow").quit(shutdown=shutdown_daemon)
                else:
                    self.gtkui_config["classic_mode"] = not new_gtkui_in_classic_mode
                    self.builder.get_object("radio_classic").set_active(self.gtkui_config["classic_mode"])
                    self.builder.get_object("radio_thinclient").set_active(not self.gtkui_config["classic_mode"])
            dialog = YesNoDialog(
                _("Switching client mode..."),
                _("Your current session will be stopped. Do you wish to continue?")
            )
            dialog.run().addCallback(on_response)

    def hide(self):
        self.window_open = False
        self.builder.get_object("port_img").hide()
        self.pref_dialog.hide()

    def __update_cache_status(self):
        # Updates the cache status labels with the info in the dict
        for widget_name in ('label_cache_blocks_written', 'label_cache_writes', 'label_cache_write_hit_ratio',
                            'label_cache_blocks_read', 'label_cache_blocks_read_hit', 'label_cache_read_hit_ratio',
                            'label_cache_reads', 'label_cache_cache_size', 'label_cache_read_cache_size'):
            widget = self.builder.get_object(widget_name)
            key = widget_name[len("label_cache_"):]
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
        if w is not None and h is not None:
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

        path_choosers = {"download_location_path_chooser": self.download_location_path_chooser,
                         "move_completed_path_chooser": self.move_completed_path_chooser,
                         "torrentfiles_location_path_chooser": self.copy_torrent_files_path_chooser
                         }

        dependents = {
            "chk_show_dialog": {"chk_focus_dialog": True},
            "chk_random_port": {"spin_port_min": False,
                                "spin_port_max": False},
            "chk_random_outgoing_ports": {"spin_outgoing_port_min": False,
                                          "spin_outgoing_port_max": False},
            "chk_use_tray": {"radio_appind": True,
                             "radio_systray": True,
                             "chk_min_on_close": True,
                             "chk_start_in_tray": True,
                             "alignment_tray_type": True,
                             "chk_lock_tray": True},
            "chk_lock_tray": {"txt_tray_password": True,
                              "password_label": True},
            "radio_open_folder_custom": {"combo_file_manager": False,
                                         "txt_open_folder_location": True},
            "chk_move_completed": {"move_completed_path_chooser": True},
            "chk_copy_torrent_file": {"torrentfiles_location_path_chooser": True,
                                      "chk_del_copy_torrent_file": True},
            "chk_seed_ratio": {"spin_share_ratio": True,
                               "chk_remove_ratio": True}
        }

        def update_dependent_widgets(name, value):
            dependency = dependents[name]
            for dep in dependency.keys():
                if dep in path_choosers:
                    depwidget = path_choosers[dep]
                else:
                    depwidget = self.builder.get_object(dep)
                sensitive = [not value, value][dependency[dep]]
                depwidget.set_sensitive(sensitive and self.is_connected)
                if dep in dependents:
                    update_dependent_widgets(dep, depwidget.get_active() and sensitive)

        for key in dependents.keys():
            if widget != self.builder.get_object(key):
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
                self.builder.get_object("port_img").set_from_stock(gtk.STOCK_YES, 4)
                self.builder.get_object("port_img").show()
            else:
                self.builder.get_object("port_img").set_from_stock(gtk.STOCK_DIALOG_WARNING, 4)
                self.builder.get_object("port_img").show()
        client.core.test_listen_port().addCallback(on_get_test)
        # XXX: Consider using gtk.Spinner() instead of the loading gif
        #      It requires gtk.ver > 2.12
        self.builder.get_object("port_img").set_from_file(
            deluge.common.get_pixmap('loading.gif')
        )
        self.builder.get_object("port_img").show()
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

    def on_plugin_selection_changed(self, treeselection):
        log.debug("on_plugin_selection_changed")
        (model, itr) = treeselection.get_selected()
        if not itr:
            return
        name = model[itr][0]
        plugin_info = component.get("PluginManager").get_plugin_info(name)
        self.builder.get_object("label_plugin_author").set_text(plugin_info["Author"])
        self.builder.get_object("label_plugin_version").set_text(plugin_info["Version"])
        self.builder.get_object("label_plugin_email").set_text(plugin_info["Author-email"])
        self.builder.get_object("label_plugin_homepage").set_text(plugin_info["Home-page"])
        self.builder.get_object("label_plugin_details").set_text(plugin_info["Description"])

    def _on_button_plugin_install_clicked(self, widget):
        log.debug("_on_button_plugin_install_clicked")
        chooser = gtk.FileChooserDialog(
            _("Select the Plugin"),
            self.pref_dialog,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,
                     gtk.RESPONSE_OK)
        )

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
            os.path.join(get_config_dir(), "plugins", filename))

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

    def _on_combo_encryption_changed(self, widget):
        combo_encin = self.builder.get_object("combo_encin").get_active()
        combo_encout = self.builder.get_object("combo_encout").get_active()
        combo_enclevel = self.builder.get_object("combo_enclevel")

        # If incoming and outgoing both set to disabled, disable level combobox
        if combo_encin == 2 and combo_encout == 2:
            combo_enclevel.set_sensitive(False)
        elif self.is_connected:
            combo_enclevel.set_sensitive(True)

    def _on_combo_proxy_type_changed(self, widget):
        proxy_type = self.builder.get_object("combo_proxy_type").get_active()

        hides = []
        shows = []
        # 0:"None"
        if proxy_type == 0:
            hides.extend(["entry_proxy_pass", "entry_proxy_user", "entry_proxy_host", "spin_proxy_port",
                          "label_proxy_pass", "label_proxy_user", "label_proxy_host", "label_proxy_port",
                          "chk_proxy_host_resolve", "chk_proxy_peer_conn"])
        # 1:"Socks4", 2:"Socks5", 4:"HTTP"
        elif proxy_type in (1, 2, 4):
            if proxy_type in (2, 4):
                shows.extend(["chk_proxy_host_resolve"])
            hides.extend(["entry_proxy_pass", "entry_proxy_user", "label_proxy_pass", "label_proxy_user"])
            shows.extend(["entry_proxy_host", "spin_proxy_port", "label_proxy_host",
                         "label_proxy_port", "chk_proxy_peer_conn"])
        # 3:"Socks5 Auth", 5:"HTTP Auth"
        elif proxy_type in (3, 5):
            shows.extend(["entry_proxy_pass", "entry_proxy_user", "entry_proxy_host", "spin_proxy_port",
                         "label_proxy_pass", "label_proxy_user", "label_proxy_host", "label_proxy_port",
                          "chk_proxy_host_resolve", "chk_proxy_peer_conn"])

        for hide_entry in hides:
            self.builder.get_object(hide_entry).hide()
        for show_entry in shows:
            self.builder.get_object(show_entry).show()

    def _on_button_associate_magnet_clicked(self, widget):
        associate_magnet_links(True)

    def _get_accounts_tab_data(self):
        def on_ok(accounts):
            self.accounts_frame.show()
            self._on_get_known_accounts(accounts)

        def on_fail(failure):
            if failure.type == NotAuthorizedError:
                self.accounts_frame.hide()
            else:
                ErrorDialog(
                    _("Server Side Error"),
                    _("An error ocurred on the server"),
                    parent=self.pref_dialog, details=failure.getErrorMessage()
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
            self.builder.get_object("accounts_edit").set_sensitive(True)
            self.builder.get_object("accounts_delete").set_sensitive(True)
        else:
            self.builder.get_object("accounts_edit").set_sensitive(False)
            self.builder.get_object("accounts_delete").set_sensitive(False)

    def _on_accounts_add_clicked(self, widget):
        dialog = AccountDialog(
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
                if failure.type == AuthManagerError:
                    ErrorDialog(
                        _("Error Adding Account"),
                        _("Authentication failed"),
                        parent=self.pref_dialog, details=failure.getErrorMessage()
                    ).run()
                else:
                    ErrorDialog(
                        _("Error Adding Account"),
                        _("An error ocurred while adding account"),
                        parent=self.pref_dialog, details=failure.getErrorMessage()
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

        dialog = AccountDialog(
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
                ErrorDialog(
                    _("Error Updating Account"),
                    _("An error ocurred while updating account"),
                    parent=self.pref_dialog, details=failure.getErrorMessage()
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
        dialog = YesNoDialog(header, text, parent=self.pref_dialog)

        def dialog_finished(response_id):
            def remove_ok(rc):
                model.remove(itr)

            def remove_fail(failure):
                if failure.type == AuthManagerError:
                    ErrorDialog(
                        _("Error Removing Account"),
                        _("Auhentication failed"),
                        parent=self.pref_dialog, details=failure.getErrorMessage()
                    ).run()
                else:
                    ErrorDialog(
                        _("Error Removing Account"),
                        _("An error ocurred while removing account"),
                        parent=self.pref_dialog, details=failure.getErrorMessage()
                    ).run()
            if response_id == gtk.RESPONSE_YES:
                client.core.remove_account(
                    username
                ).addCallback(remove_ok).addErrback(remove_fail)
        dialog.run().addCallback(dialog_finished)

    def _on_piecesbar_toggle_toggled(self, widget):
        self.gtkui_config['show_piecesbar'] = widget.get_active()
        colors_widget = self.builder.get_object("piecebar_colors_expander")
        colors_widget.set_visible(widget.get_active())

    def _on_checkbutton_language_toggled(self, widget):
        self.language_combo.set_visible(not self.language_checkbox.get_active())

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
            self.builder.get_object("%s_color" % state).set_color(color)
        else:
            color = self.builder.get_object("%s_color" % state).get_color()
            log.debug("Setting %r color state to %s", state,
                      (color.red, color.green, color.blue))
            self.gtkui_config["pieces_color_%s" % state] = [
                color.red, color.green, color.blue
            ]
            self.gtkui_config.save()
            self.gtkui_config.apply_set_functions("pieces_colors")

        self.builder.get_object("revert_color_%s" % state).set_sensitive(
            [color.red, color.green, color.blue] != self.COLOR_DEFAULTS[state]
        )

    def __revert_color(self, state, from_config=False):
        log.debug("Reverting %r color state", state)
        self.builder.get_object("%s_color" % state).set_color(
            gtk.gdk.Color(*self.COLOR_DEFAULTS[state])
        )
        self.builder.get_object("revert_color_%s" % state).set_sensitive(False)
        self.gtkui_config.apply_set_functions("pieces_colors")
