# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
from hashlib import sha1 as sha

from gi import require_version
from gi.repository import Gtk
from gi.repository.Gdk import Color

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.error import AuthManagerError, NotAuthorizedError
from deluge.i18n import get_languages
from deluge.ui.client import client
from deluge.ui.common import DISK_CACHE_KEYS, PREFS_CATOG_TRANS

from .common import associate_magnet_links, get_clipboard_text, get_deluge_icon
from .dialogs import AccountDialog, ErrorDialog, InformationDialog, YesNoDialog
from .path_chooser import PathChooser

try:
    from urllib.parse import urlparse
except ImportError:
    # PY2 fallback
    from urlparse import urlparse  # pylint: disable=ungrouped-imports

try:
    require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3  # noqa: F401
except (ImportError, ValueError):
    appindicator = False
else:
    appindicator = True

log = logging.getLogger(__name__)

ACCOUNTS_USERNAME, ACCOUNTS_LEVEL, ACCOUNTS_PASSWORD = list(range(3))
COLOR_MISSING, COLOR_WAITING, COLOR_DOWNLOADING, COLOR_COMPLETED = list(range(4))

COLOR_STATES = {
    'missing': COLOR_MISSING,
    'waiting': COLOR_WAITING,
    'downloading': COLOR_DOWNLOADING,
    'completed': COLOR_COMPLETED,
}


class Preferences(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'Preferences')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            deluge.common.resource_filename(
                __package__, os.path.join('glade', 'preferences_dialog.ui')
            )
        )
        self.pref_dialog = self.builder.get_object('pref_dialog')
        self.pref_dialog.set_transient_for(component.get('MainWindow').window)
        self.pref_dialog.set_icon(get_deluge_icon())
        self.treeview = self.builder.get_object('treeview')
        self.notebook = self.builder.get_object('notebook')
        self.gtkui_config = ConfigManager('gtk3ui.conf')
        self.window_open = False

        self.load_pref_dialog_state()

        self.builder.get_object('image_magnet').set_from_file(
            deluge.common.get_pixmap('magnet16.png')
        )

        # Hide the unused associate magnet button on OSX see: #2420
        if deluge.common.osx_check():
            self.builder.get_object('button_associate_magnet').hide()

        # Setup the liststore for the categories (tab pages)
        self.liststore = Gtk.ListStore(int, str, str)
        self.treeview.set_model(self.liststore)
        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(None, render, text=2)
        self.treeview.append_column(column)

        # Add the default categories
        prefs_categories = (
            'interface',
            'downloads',
            'bandwidth',
            'queue',
            'network',
            'proxy',
            'cache',
            'other',
            'daemon',
            'plugins',
        )
        for idx, category in enumerate(prefs_categories):
            self.liststore.append([idx, category, PREFS_CATOG_TRANS[category]])

        # Add and set separator after Plugins.
        def set_separator(model, _iter, data=None):
            entry = deluge.common.decode_bytes(model.get_value(_iter, 1))
            if entry == '_separator_':
                return True

        self.treeview.set_row_separator_func(set_separator, None)
        self.liststore.append([len(self.liststore), '_separator_', ''])
        # Add a dummy notebook page to keep indexing synced with liststore.
        self.notebook.append_page(Gtk.HSeparator())

        # Setup accounts tab lisview
        self.accounts_levels_mapping = None
        self.accounts_authlevel = self.builder.get_object('accounts_authlevel')
        self.accounts_liststore = Gtk.ListStore(str, str, str, int)
        self.accounts_liststore.set_sort_column_id(
            ACCOUNTS_USERNAME, Gtk.SortType.ASCENDING
        )
        self.accounts_listview = self.builder.get_object('accounts_listview')
        self.accounts_listview.append_column(
            Gtk.TreeViewColumn(
                _('Username'), Gtk.CellRendererText(), text=ACCOUNTS_USERNAME
            )
        )
        self.accounts_listview.append_column(
            Gtk.TreeViewColumn(_('Level'), Gtk.CellRendererText(), text=ACCOUNTS_LEVEL)
        )
        password_column = Gtk.TreeViewColumn(
            'password', Gtk.CellRendererText(), text=ACCOUNTS_PASSWORD
        )
        self.accounts_listview.append_column(password_column)
        password_column.set_visible(False)
        self.accounts_listview.set_model(self.accounts_liststore)

        self.accounts_listview.get_selection().connect(
            'changed', self.on_accounts_selection_changed
        )
        self.accounts_frame = self.builder.get_object('AccountsFrame')

        # Setup plugin tab listview
        # The third entry is for holding translated plugin names
        self.plugin_liststore = Gtk.ListStore(str, bool, str)
        self.plugin_liststore.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.plugin_listview = self.builder.get_object('plugin_listview')
        self.plugin_listview.set_model(self.plugin_liststore)
        render = Gtk.CellRendererToggle()
        render.connect('toggled', self.on_plugin_toggled)
        render.set_property('activatable', True)
        self.plugin_listview.append_column(
            Gtk.TreeViewColumn(_('Enabled'), render, active=1)
        )
        self.plugin_listview.append_column(
            Gtk.TreeViewColumn(_('Plugin'), Gtk.CellRendererText(), text=2)
        )

        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect('changed', self.on_selection_changed)

        self.plugin_listview.get_selection().connect(
            'changed', self.on_plugin_selection_changed
        )

        self.builder.connect_signals(self)

        # Radio buttons to choose between systray and appindicator
        self.builder.get_object('alignment_tray_type').set_visible(appindicator)

        from .gtkui import DEFAULT_PREFS

        self.COLOR_DEFAULTS = {}
        for key in ('missing', 'waiting', 'downloading', 'completed'):
            self.COLOR_DEFAULTS[key] = DEFAULT_PREFS['pieces_color_%s' % key][:]
        del DEFAULT_PREFS

        # These get updated by requests done to the core
        self.all_plugins = []
        self.enabled_plugins = []

        self.setup_path_choosers()
        self.load_languages()

    def setup_path_choosers(self):
        self.download_location_hbox = self.builder.get_object(
            'hbox_download_to_path_chooser'
        )
        self.download_location_path_chooser = PathChooser(
            'download_location_paths_list', parent=self.pref_dialog
        )
        self.download_location_hbox.add(self.download_location_path_chooser)
        self.download_location_hbox.show_all()

        self.move_completed_hbox = self.builder.get_object(
            'hbox_move_completed_to_path_chooser'
        )
        self.move_completed_path_chooser = PathChooser(
            'move_completed_paths_list', parent=self.pref_dialog
        )
        self.move_completed_hbox.add(self.move_completed_path_chooser)
        self.move_completed_hbox.show_all()

        self.copy_torrents_to_hbox = self.builder.get_object(
            'hbox_copy_torrent_files_path_chooser'
        )
        self.copy_torrent_files_path_chooser = PathChooser(
            'copy_torrent_files_to_paths_list', parent=self.pref_dialog
        )
        self.copy_torrents_to_hbox.add(self.copy_torrent_files_path_chooser)
        self.copy_torrents_to_hbox.show_all()

    def load_languages(self):
        self.language_combo = self.builder.get_object('combobox_language')
        self.language_checkbox = self.builder.get_object('checkbutton_language')
        lang_model = self.language_combo.get_model()
        langs = get_languages()
        index = -1
        for i, l in enumerate(langs):
            lang_code, name = l
            lang_model.append([lang_code, name])
            if self.gtkui_config['language'] == lang_code:
                index = i

        if self.gtkui_config['language'] is None:
            self.language_checkbox.set_active(True)
            self.language_combo.set_visible(False)
        else:
            self.language_combo.set_visible(True)
            if index != -1:
                self.language_combo.set_active(index)

    def __del__(self):
        del self.gtkui_config

    def add_page(self, name, widget):
        """Add a another page to the notebook"""
        # Create a header and scrolled window for the preferences tab
        parent = widget.get_parent()
        if parent:
            parent.remove(widget)
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=0)
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_markup('<b><i><big>' + name + '</big></i></b>')
        label.set_alignment(0.00, 0.50)
        label.set_padding(10, 10)
        vbox.pack_start(label, False, True, 0)
        sep = Gtk.HSeparator()
        vbox.pack_start(sep, False, True, 0)
        widget.set_margin_top(7)
        widget.set_vexpand(True)
        widget.set_hexpand(True)
        vbox.pack_start(widget, True, True, 0)
        scrolled = Gtk.ScrolledWindow()
        viewport = Gtk.Viewport()
        viewport.set_shadow_type(Gtk.ShadowType.NONE)
        viewport.add(vbox)
        scrolled.add(viewport)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.show_all()
        # Add this page to the notebook
        index = self.notebook.append_page(scrolled, None)
        self.liststore.append([index, name, _(name)])
        return name

    def remove_page(self, name):
        """Removes a page from the notebook"""
        self.page_num_to_remove = None
        self.iter_to_remove = None

        def on_foreach_row(model, path, _iter, user_data):
            row_name = deluge.common.decode_bytes(model.get_value(_iter, 1))
            if row_name == user_data:
                # This is the row we need to remove
                self.page_num_to_remove = model.get_value(_iter, 0)
                self.iter_to_remove = _iter
                # Return True to stop foreach iterating
                return True

        self.liststore.foreach(on_foreach_row, name)

        # Remove the page and row
        if self.page_num_to_remove is not None:
            self.notebook.remove_page(self.page_num_to_remove)
        if self.iter_to_remove is not None:
            self.liststore.remove(self.iter_to_remove)

        # We need to re-adjust the index values for the remaining pages
        for idx, __ in enumerate(self.liststore):
            self.liststore[idx][0] = idx

    def show(self, page=None):
        """Page should be the string in the left list.. ie, 'Network' or
        'Bandwidth'"""
        self.window_open = True
        if page is not None:
            for (index, string, __) in self.liststore:
                if page == string:
                    self.treeview.get_selection().select_path(index)
                    break

        component.get('PluginManager').run_on_show_prefs()

        # Update the preferences dialog to reflect current config settings
        self.core_config = {}
        if client.connected():
            self._get_accounts_tab_data()

            def on_get_config(config):
                self.core_config = config
                client.core.get_available_plugins().addCallback(
                    on_get_available_plugins
                )

            def on_get_available_plugins(plugins):
                self.all_plugins = plugins
                client.core.get_enabled_plugins().addCallback(on_get_enabled_plugins)

            def on_get_enabled_plugins(plugins):
                self.enabled_plugins = plugins
                client.core.get_listen_port().addCallback(on_get_listen_port)

            def on_get_listen_port(port):
                self.active_port = port
                client.core.get_session_status(DISK_CACHE_KEYS).addCallback(
                    on_get_session_status
                )

            def on_get_session_status(status):
                self.cache_status = status
                self._show()

            # This starts a series of client.core requests prior to showing the window
            client.core.get_config().addCallback(on_get_config)
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
            'chk_move_completed': ('active', 'move_completed'),
            'chk_copy_torrent_file': ('active', 'copy_torrent_file'),
            'chk_del_copy_torrent_file': ('active', 'del_copy_torrent_file'),
            'chk_pre_allocation': ('active', 'pre_allocate_storage'),
            'chk_prioritize_first_last_pieces': (
                'active',
                'prioritize_first_last_pieces',
            ),
            'chk_sequential_download': ('active', 'sequential_download'),
            'chk_add_paused': ('active', 'add_paused'),
            'active_port_label': ('text', lambda: str(self.active_port)),
            'spin_incoming_port': (
                'value',
                lambda: self.core_config['listen_ports'][0],
            ),
            'chk_random_incoming_port': ('active', 'random_port'),
            'spin_outgoing_port_min': (
                'value',
                lambda: self.core_config['outgoing_ports'][0],
            ),
            'spin_outgoing_port_max': (
                'value',
                lambda: self.core_config['outgoing_ports'][1],
            ),
            'chk_random_outgoing_ports': ('active', 'random_outgoing_ports'),
            'entry_interface': ('text', 'listen_interface'),
            'entry_outgoing_interface': ('text', 'outgoing_interface'),
            'entry_peer_tos': ('text', 'peer_tos'),
            'chk_dht': ('active', 'dht'),
            'chk_upnp': ('active', 'upnp'),
            'chk_natpmp': ('active', 'natpmp'),
            'chk_utpex': ('active', 'utpex'),
            'chk_lsd': ('active', 'lsd'),
            'chk_new_releases': ('active', 'new_release_check'),
            'chk_send_info': ('active', 'send_info'),
            'entry_geoip': ('text', 'geoip_db_location'),
            'combo_encin': ('active', 'enc_in_policy'),
            'combo_encout': ('active', 'enc_out_policy'),
            'combo_enclevel': ('active', 'enc_level'),
            'spin_max_connections_global': ('value', 'max_connections_global'),
            'spin_max_download': ('value', 'max_download_speed'),
            'spin_max_upload': ('value', 'max_upload_speed'),
            'spin_max_upload_slots_global': ('value', 'max_upload_slots_global'),
            'spin_max_half_open_connections': ('value', 'max_connections_per_second'),
            'spin_max_connections_per_second': ('value', 'max_connections_per_second'),
            'chk_ignore_limits_on_local_network': (
                'active',
                'ignore_limits_on_local_network',
            ),
            'chk_rate_limit_ip_overhead': ('active', 'rate_limit_ip_overhead'),
            'spin_max_connections_per_torrent': (
                'value',
                'max_connections_per_torrent',
            ),
            'spin_max_upload_slots_per_torrent': (
                'value',
                'max_upload_slots_per_torrent',
            ),
            'spin_max_download_per_torrent': (
                'value',
                'max_download_speed_per_torrent',
            ),
            'spin_max_upload_per_torrent': ('value', 'max_upload_speed_per_torrent'),
            'spin_daemon_port': ('value', 'daemon_port'),
            'chk_allow_remote_connections': ('active', 'allow_remote'),
            'spin_active': ('value', 'max_active_limit'),
            'spin_seeding': ('value', 'max_active_seeding'),
            'spin_downloading': ('value', 'max_active_downloading'),
            'chk_dont_count_slow_torrents': ('active', 'dont_count_slow_torrents'),
            'chk_auto_manage_prefer_seeds': ('active', 'auto_manage_prefer_seeds'),
            'chk_queue_new_top': ('active', 'queue_new_to_top'),
            'spin_share_ratio_limit': ('value', 'share_ratio_limit'),
            'spin_seed_time_ratio_limit': ('value', 'seed_time_ratio_limit'),
            'spin_seed_time_limit': ('value', 'seed_time_limit'),
            'chk_share_ratio': ('active', 'stop_seed_at_ratio'),
            'spin_share_ratio': ('value', 'stop_seed_ratio'),
            'radio_pause_ratio': ('active', 'stop_seed_at_ratio'),
            'radio_remove_ratio': ('active', 'remove_seed_at_ratio'),
            'spin_cache_size': ('value', 'cache_size'),
            'spin_cache_expiry': ('value', 'cache_expiry'),
            'combo_proxy_type': ('active', lambda: self.core_config['proxy']['type']),
            'entry_proxy_user': ('text', lambda: self.core_config['proxy']['username']),
            'entry_proxy_pass': ('text', lambda: self.core_config['proxy']['password']),
            'entry_proxy_host': ('text', lambda: self.core_config['proxy']['hostname']),
            'spin_proxy_port': ('value', lambda: self.core_config['proxy']['port']),
            'chk_proxy_host_resolve': (
                'active',
                lambda: self.core_config['proxy']['proxy_hostnames'],
            ),
            'chk_proxy_peer_conn': (
                'active',
                lambda: self.core_config['proxy']['proxy_peer_connections'],
            ),
            'chk_proxy_tracker_conn': (
                'active',
                lambda: self.core_config['proxy']['proxy_tracker_connections'],
            ),
            'chk_force_proxy': (
                'active',
                lambda: self.core_config['proxy']['force_proxy'],
            ),
            'chk_anonymous_mode': (
                'active',
                lambda: self.core_config['proxy']['anonymous_mode'],
            ),
            'accounts_add': (None, None),
            'accounts_listview': (None, None),
            'button_cache_refresh': (None, None),
            'button_plugin_install': (None, None),
            'button_rescan_plugins': (None, None),
            'button_find_plugins': (None, None),
            'button_testport': (None, None),
            'plugin_listview': (None, None),
        }

        core_widgets[self.download_location_path_chooser] = (
            'path_chooser',
            'download_location',
        )
        core_widgets[self.move_completed_path_chooser] = (
            'path_chooser',
            'move_completed_path',
        )
        core_widgets[self.copy_torrent_files_path_chooser] = (
            'path_chooser',
            'torrentfiles_location',
        )

        # Update the widgets accordingly
        for key in core_widgets:
            modifier = core_widgets[key][0]
            try:
                widget = self.builder.get_object(key)
            except TypeError:
                widget = key

            widget.set_sensitive(self.is_connected)

            if self.is_connected:
                value = core_widgets[key][1]
                try:
                    value = self.core_config[value]
                except KeyError:
                    if callable(value):
                        value = value()
            elif modifier:
                value = {
                    'active': False,
                    'not_active': False,
                    'value': 0,
                    'text': '',
                    'path_chooser': '',
                }[modifier]

            if modifier == 'active':
                widget.set_active(value)
            elif modifier == 'not_active':
                widget.set_active(not value)
            elif modifier == 'value':
                widget.set_value(float(value))
            elif modifier == 'text':
                if value is None:
                    value = ''
                widget.set_text(value)
            elif modifier == 'path_chooser':
                widget.set_text(value, cursor_end=False, default_text=True)

        if self.is_connected:
            for key in core_widgets:
                try:
                    widget = self.builder.get_object(key)
                except TypeError:
                    widget = key
                # Update the toggle status if necessary
                self.on_toggle(widget)

        # Downloads tab #
        self.builder.get_object('chk_show_dialog').set_active(
            self.gtkui_config['interactive_add']
        )
        self.builder.get_object('chk_focus_dialog').set_active(
            self.gtkui_config['focus_add_dialog']
        )

        # Interface tab #
        self.builder.get_object('chk_use_tray').set_active(
            self.gtkui_config['enable_system_tray']
        )
        self.builder.get_object('chk_min_on_close').set_active(
            self.gtkui_config['close_to_tray']
        )
        self.builder.get_object('chk_start_in_tray').set_active(
            self.gtkui_config['start_in_tray']
        )
        self.builder.get_object('radio_appind').set_active(
            self.gtkui_config['enable_appindicator']
        )
        self.builder.get_object('chk_lock_tray').set_active(
            self.gtkui_config['lock_tray']
        )
        self.builder.get_object('radio_standalone').set_active(
            self.gtkui_config['standalone']
        )
        self.builder.get_object('radio_thinclient').set_active(
            not self.gtkui_config['standalone']
        )
        self.builder.get_object('chk_show_rate_in_title').set_active(
            self.gtkui_config['show_rate_in_title']
        )
        self.builder.get_object('chk_focus_main_window_on_add').set_active(
            self.gtkui_config['focus_main_window_on_add']
        )
        self.builder.get_object('piecesbar_toggle').set_active(
            self.gtkui_config['show_piecesbar']
        )
        self.__set_color('completed', from_config=True)
        self.__set_color('downloading', from_config=True)
        self.__set_color('waiting', from_config=True)
        self.__set_color('missing', from_config=True)

        # Other tab #
        self.builder.get_object('chk_show_new_releases').set_active(
            self.gtkui_config['show_new_releases']
        )

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
            enabled = plugin in enabled_plugins
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

        # Get the values from the dialog
        new_core_config = {}
        new_gtkui_config = {}

        # Downloads tab #
        new_gtkui_config['interactive_add'] = self.builder.get_object(
            'chk_show_dialog'
        ).get_active()
        new_gtkui_config['focus_add_dialog'] = self.builder.get_object(
            'chk_focus_dialog'
        ).get_active()

        for state in ('missing', 'waiting', 'downloading', 'completed'):
            color = self.builder.get_object('%s_color' % state).get_color()
            new_gtkui_config['pieces_color_%s' % state] = [
                color.red,
                color.green,
                color.blue,
            ]

        new_core_config['copy_torrent_file'] = self.builder.get_object(
            'chk_copy_torrent_file'
        ).get_active()
        new_core_config['del_copy_torrent_file'] = self.builder.get_object(
            'chk_del_copy_torrent_file'
        ).get_active()
        new_core_config['move_completed'] = self.builder.get_object(
            'chk_move_completed'
        ).get_active()

        new_core_config[
            'download_location'
        ] = self.download_location_path_chooser.get_text()
        new_core_config[
            'move_completed_path'
        ] = self.move_completed_path_chooser.get_text()
        new_core_config[
            'torrentfiles_location'
        ] = self.copy_torrent_files_path_chooser.get_text()
        new_core_config['prioritize_first_last_pieces'] = self.builder.get_object(
            'chk_prioritize_first_last_pieces'
        ).get_active()
        new_core_config['sequential_download'] = self.builder.get_object(
            'chk_sequential_download'
        ).get_active()
        new_core_config['add_paused'] = self.builder.get_object(
            'chk_add_paused'
        ).get_active()
        new_core_config['pre_allocate_storage'] = self.builder.get_object(
            'chk_pre_allocation'
        ).get_active()

        # Network tab #
        listen_ports = [
            self.builder.get_object('spin_incoming_port').get_value_as_int()
        ] * 2
        new_core_config['listen_ports'] = listen_ports
        new_core_config['random_port'] = self.builder.get_object(
            'chk_random_incoming_port'
        ).get_active()
        outgoing_ports = (
            self.builder.get_object('spin_outgoing_port_min').get_value_as_int(),
            self.builder.get_object('spin_outgoing_port_max').get_value_as_int(),
        )
        new_core_config['outgoing_ports'] = outgoing_ports
        new_core_config['random_outgoing_ports'] = self.builder.get_object(
            'chk_random_outgoing_ports'
        ).get_active()
        incoming_address = self.builder.get_object('entry_interface').get_text().strip()
        if deluge.common.is_ip(incoming_address) or not incoming_address:
            new_core_config['listen_interface'] = incoming_address
        new_core_config['outgoing_interface'] = (
            self.builder.get_object('entry_outgoing_interface').get_text().strip()
        )
        new_core_config['peer_tos'] = self.builder.get_object(
            'entry_peer_tos'
        ).get_text()
        new_core_config['dht'] = self.builder.get_object('chk_dht').get_active()
        new_core_config['upnp'] = self.builder.get_object('chk_upnp').get_active()
        new_core_config['natpmp'] = self.builder.get_object('chk_natpmp').get_active()
        new_core_config['utpex'] = self.builder.get_object('chk_utpex').get_active()
        new_core_config['lsd'] = self.builder.get_object('chk_lsd').get_active()
        new_core_config['enc_in_policy'] = self.builder.get_object(
            'combo_encin'
        ).get_active()
        new_core_config['enc_out_policy'] = self.builder.get_object(
            'combo_encout'
        ).get_active()
        new_core_config['enc_level'] = self.builder.get_object(
            'combo_enclevel'
        ).get_active()

        # Bandwidth tab #
        new_core_config['max_connections_global'] = self.builder.get_object(
            'spin_max_connections_global'
        ).get_value_as_int()
        new_core_config['max_download_speed'] = self.builder.get_object(
            'spin_max_download'
        ).get_value()
        new_core_config['max_upload_speed'] = self.builder.get_object(
            'spin_max_upload'
        ).get_value()
        new_core_config['max_upload_slots_global'] = self.builder.get_object(
            'spin_max_upload_slots_global'
        ).get_value_as_int()
        new_core_config['max_half_open_connections'] = self.builder.get_object(
            'spin_max_half_open_connections'
        ).get_value_as_int()
        new_core_config['max_connections_per_second'] = self.builder.get_object(
            'spin_max_connections_per_second'
        ).get_value_as_int()
        new_core_config['max_connections_per_torrent'] = self.builder.get_object(
            'spin_max_connections_per_torrent'
        ).get_value_as_int()
        new_core_config['max_upload_slots_per_torrent'] = self.builder.get_object(
            'spin_max_upload_slots_per_torrent'
        ).get_value_as_int()
        new_core_config['max_upload_speed_per_torrent'] = self.builder.get_object(
            'spin_max_upload_per_torrent'
        ).get_value()
        new_core_config['max_download_speed_per_torrent'] = self.builder.get_object(
            'spin_max_download_per_torrent'
        ).get_value()
        new_core_config['ignore_limits_on_local_network'] = self.builder.get_object(
            'chk_ignore_limits_on_local_network'
        ).get_active()
        new_core_config['rate_limit_ip_overhead'] = self.builder.get_object(
            'chk_rate_limit_ip_overhead'
        ).get_active()

        # Interface tab #
        new_gtkui_config['enable_system_tray'] = self.builder.get_object(
            'chk_use_tray'
        ).get_active()
        new_gtkui_config['close_to_tray'] = self.builder.get_object(
            'chk_min_on_close'
        ).get_active()
        new_gtkui_config['start_in_tray'] = self.builder.get_object(
            'chk_start_in_tray'
        ).get_active()
        new_gtkui_config['enable_appindicator'] = self.builder.get_object(
            'radio_appind'
        ).get_active()
        new_gtkui_config['lock_tray'] = self.builder.get_object(
            'chk_lock_tray'
        ).get_active()
        passhex = sha(
            deluge.common.decode_bytes(
                self.builder.get_object('txt_tray_password').get_text()
            ).encode()
        ).hexdigest()
        if passhex != 'c07eb5a8c0dc7bb81c217b67f11c3b7a5e95ffd7':
            new_gtkui_config['tray_password'] = passhex

        was_standalone = self.gtkui_config['standalone']
        new_gtkui_standalone = self.builder.get_object('radio_standalone').get_active()
        new_gtkui_config['standalone'] = new_gtkui_standalone

        new_gtkui_config['show_rate_in_title'] = self.builder.get_object(
            'chk_show_rate_in_title'
        ).get_active()
        new_gtkui_config['focus_main_window_on_add'] = self.builder.get_object(
            'chk_focus_main_window_on_add'
        ).get_active()

        # Other tab #
        new_gtkui_config['show_new_releases'] = self.builder.get_object(
            'chk_show_new_releases'
        ).get_active()
        new_core_config['send_info'] = self.builder.get_object(
            'chk_send_info'
        ).get_active()
        new_core_config['geoip_db_location'] = self.builder.get_object(
            'entry_geoip'
        ).get_text()

        # Daemon tab #
        new_core_config['daemon_port'] = self.builder.get_object(
            'spin_daemon_port'
        ).get_value_as_int()
        new_core_config['allow_remote'] = self.builder.get_object(
            'chk_allow_remote_connections'
        ).get_active()
        new_core_config['new_release_check'] = self.builder.get_object(
            'chk_new_releases'
        ).get_active()

        # Proxy tab #
        new_core_config['proxy'] = {
            'type': self.builder.get_object('combo_proxy_type').get_active(),
            'username': self.builder.get_object('entry_proxy_user').get_text(),
            'password': self.builder.get_object('entry_proxy_pass').get_text(),
            'hostname': self.builder.get_object('entry_proxy_host').get_text(),
            'port': self.builder.get_object('spin_proxy_port').get_value_as_int(),
            'proxy_hostnames': self.builder.get_object(
                'chk_proxy_host_resolve'
            ).get_active(),
            'proxy_peer_connections': self.builder.get_object(
                'chk_proxy_peer_conn'
            ).get_active(),
            'proxy_tracker_connections': self.builder.get_object(
                'chk_proxy_tracker_conn'
            ).get_active(),
            'force_proxy': self.builder.get_object('chk_force_proxy').get_active(),
            'anonymous_mode': self.builder.get_object(
                'chk_anonymous_mode'
            ).get_active(),
        }

        # Queue tab #
        new_core_config['queue_new_to_top'] = self.builder.get_object(
            'chk_queue_new_top'
        ).get_active()
        new_core_config['max_active_seeding'] = self.builder.get_object(
            'spin_seeding'
        ).get_value_as_int()
        new_core_config['max_active_downloading'] = self.builder.get_object(
            'spin_downloading'
        ).get_value_as_int()
        new_core_config['max_active_limit'] = self.builder.get_object(
            'spin_active'
        ).get_value_as_int()
        new_core_config['dont_count_slow_torrents'] = self.builder.get_object(
            'chk_dont_count_slow_torrents'
        ).get_active()
        new_core_config['auto_manage_prefer_seeds'] = self.builder.get_object(
            'chk_auto_manage_prefer_seeds'
        ).get_active()
        new_core_config['stop_seed_at_ratio'] = self.builder.get_object(
            'chk_share_ratio'
        ).get_active()
        new_core_config['remove_seed_at_ratio'] = self.builder.get_object(
            'radio_remove_ratio'
        ).get_active()
        new_core_config['stop_seed_ratio'] = self.builder.get_object(
            'spin_share_ratio'
        ).get_value()
        new_core_config['share_ratio_limit'] = self.builder.get_object(
            'spin_share_ratio_limit'
        ).get_value()
        new_core_config['seed_time_ratio_limit'] = self.builder.get_object(
            'spin_seed_time_ratio_limit'
        ).get_value()
        new_core_config['seed_time_limit'] = self.builder.get_object(
            'spin_seed_time_limit'
        ).get_value()

        # Cache tab #
        new_core_config['cache_size'] = self.builder.get_object(
            'spin_cache_size'
        ).get_value_as_int()
        new_core_config['cache_expiry'] = self.builder.get_object(
            'spin_cache_expiry'
        ).get_value_as_int()

        # Run plugin hook to apply preferences
        component.get('PluginManager').run_on_apply_prefs()

        # Language
        if self.language_checkbox.get_active():
            new_gtkui_config['language'] = None
        else:
            active = self.language_combo.get_active()
            if active == -1:
                dialog = InformationDialog(
                    _('Attention'), _('You must choose a language')
                )
                dialog.run()
                return
            else:
                model = self.language_combo.get_model()
                new_gtkui_config['language'] = model.get(model.get_iter(active), 0)[0]

        if new_gtkui_config['language'] != self.gtkui_config['language']:
            dialog = InformationDialog(
                _('Attention'),
                _('You must now restart the deluge UI for the changes to take effect.'),
            )
            dialog.run()

        # GtkUI
        for key in new_gtkui_config:
            # The values do not match so this needs to be updated
            if self.gtkui_config[key] != new_gtkui_config[key]:
                self.gtkui_config[key] = new_gtkui_config[key]

        # Core
        if client.connected():
            # Only do this if we're connected to a daemon
            config_to_set = {}
            for key in new_core_config:
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

        if was_standalone != new_gtkui_standalone:

            def on_response(response):
                if response == Gtk.ResponseType.YES:
                    shutdown_daemon = (
                        not client.is_standalone()
                        and client.connected()
                        and client.is_localhost()
                    )
                    component.get('MainWindow').quit(
                        shutdown=shutdown_daemon, restart=True
                    )
                else:
                    self.gtkui_config['standalone'] = not new_gtkui_standalone
                    self.builder.get_object('radio_standalone').set_active(
                        self.gtkui_config['standalone']
                    )
                    self.builder.get_object('radio_thinclient').set_active(
                        not self.gtkui_config['standalone']
                    )

            mode = _('Thinclient') if was_standalone else _('Standalone')
            dialog = YesNoDialog(
                _('Switching Deluge Client Mode...'),
                _('Do you want to restart to use %s mode?' % mode),
            )
            dialog.run().addCallback(on_response)

    def hide(self):
        self.window_open = False
        self.builder.get_object('port_img').hide()
        self.pref_dialog.hide()

    def __update_cache_status(self):
        # Updates the cache status labels with the info in the dict
        cache_labels = (
            'label_cache_read_ops',
            'label_cache_write_ops',
            'label_cache_num_blocks_read',
            'label_cache_num_blocks_written',
            'label_cache_read_hit_ratio',
            'label_cache_write_hit_ratio',
            'label_cache_num_blocks_cache_hits',
            'label_cache_disk_blocks_in_use',
            'label_cache_read_cache_blocks',
        )

        for widget_name in cache_labels:
            widget = self.builder.get_object(widget_name)
            key = widget_name[len('label_cache_') :]
            if not widget_name.endswith('ratio'):
                key = 'disk.' + key
            value = self.cache_status.get(key, 0)
            if isinstance(value, float):
                value = '%.2f' % value
            else:
                value = str(value)

            widget.set_text(value)

    def on_button_cache_refresh_clicked(self, widget):
        def on_get_session_status(status):
            self.cache_status = status
            self.__update_cache_status()

        client.core.get_session_status(DISK_CACHE_KEYS).addCallback(
            on_get_session_status
        )

    def on_pref_dialog_delete_event(self, widget, event):
        self.hide()
        return True

    def load_pref_dialog_state(self):
        w = self.gtkui_config['pref_dialog_width']
        h = self.gtkui_config['pref_dialog_height']
        if w is not None and h is not None:
            self.pref_dialog.resize(w, h)

    def on_pref_dialog_configure_event(self, widget, event):
        self.gtkui_config['pref_dialog_width'] = event.width
        self.gtkui_config['pref_dialog_height'] = event.height

    def on_toggle(self, widget):
        """Handles widget sensitivity based on radio/check button values."""
        try:
            value = widget.get_active()
        except Exception:
            return

        path_choosers = {
            'download_location_path_chooser': self.download_location_path_chooser,
            'move_completed_path_chooser': self.move_completed_path_chooser,
            'torrentfiles_location_path_chooser': self.copy_torrent_files_path_chooser,
        }

        dependents = {
            'chk_show_dialog': {'chk_focus_dialog': True},
            'chk_random_incoming_port': {'spin_incoming_port': False},
            'chk_random_outgoing_ports': {
                'spin_outgoing_port_min': False,
                'spin_outgoing_port_max': False,
            },
            'chk_use_tray': {
                'radio_appind': True,
                'radio_systray': True,
                'chk_min_on_close': True,
                'chk_start_in_tray': True,
                'alignment_tray_type': True,
                'chk_lock_tray': True,
            },
            'chk_lock_tray': {'txt_tray_password': True, 'password_label': True},
            'radio_open_folder_custom': {
                'combo_file_manager': False,
                'txt_open_folder_location': True,
            },
            'chk_move_completed': {'move_completed_path_chooser': True},
            'chk_copy_torrent_file': {
                'torrentfiles_location_path_chooser': True,
                'chk_del_copy_torrent_file': True,
            },
            'chk_share_ratio': {
                'spin_share_ratio': True,
                'radio_pause_ratio': True,
                'radio_remove_ratio': True,
            },
        }

        def update_dependent_widgets(name, value):
            dependency = dependents[name]
            for dep in dependency:
                if dep in path_choosers:
                    depwidget = path_choosers[dep]
                else:
                    depwidget = self.builder.get_object(dep)
                sensitive = [not value, value][dependency[dep]]
                depwidget.set_sensitive(sensitive)
                if dep in dependents:
                    update_dependent_widgets(dep, depwidget.get_active() and sensitive)

        for key in dependents:
            if widget != self.builder.get_object(key):
                continue
            update_dependent_widgets(key, value)

    def on_button_ok_clicked(self, data):
        log.debug('on_button_ok_clicked')
        self.set_config(hide=True)
        return True

    def on_button_apply_clicked(self, data):
        log.debug('on_button_apply_clicked')
        self.set_config()

    def on_button_cancel_clicked(self, data):
        log.debug('on_button_cancel_clicked')
        self.hide()
        return True

    def on_selection_changed(self, treeselection):
        # Show the correct notebook page based on what row is selected.
        (model, row) = treeselection.get_selected()
        try:
            if model.get_value(row, 1) == 'daemon':
                # Let's see update the accounts related stuff
                if client.connected():
                    self._get_accounts_tab_data()
            self.notebook.set_current_page(model.get_value(row, 0))
        except TypeError:
            pass

    def on_test_port_clicked(self, data):
        log.debug('on_test_port_clicked')

        def on_get_test(status):
            if status:
                self.builder.get_object('port_img').set_from_icon_name(
                    'emblem-ok-symbolic', Gtk.IconSize.MENU
                )
                self.builder.get_object('port_img').show()
            else:
                self.builder.get_object('port_img').set_from_icon_name(
                    'dialog-warning-symbolic', Gtk.IconSize.MENU
                )
                self.builder.get_object('port_img').show()

        client.core.test_listen_port().addCallback(on_get_test)
        # XXX: Consider using gtk.Spinner() instead of the loading gif
        #      It requires gtk.ver > 2.12
        self.builder.get_object('port_img').set_from_file(
            deluge.common.get_pixmap('loading.gif')
        )
        self.builder.get_object('port_img').show()
        client.force_call()

    def on_plugin_toggled(self, renderer, path):
        row = self.plugin_liststore.get_iter_from_string(path)
        name = self.plugin_liststore.get_value(row, 0)
        value = self.plugin_liststore.get_value(row, 1)
        log.debug('on_plugin_toggled - %s: %s', name, value)
        self.plugin_liststore.set_value(row, 1, not value)
        if not value:
            d = client.core.enable_plugin(name)
        else:
            d = client.core.disable_plugin(name)

        def on_plugin_action(arg):
            if not value and arg is False:
                log.warning('Failed to enable plugin: %s', name)
                self.plugin_liststore.set_value(row, 1, False)

        d.addBoth(on_plugin_action)

    def on_plugin_selection_changed(self, treeselection):
        log.debug('on_plugin_selection_changed')
        (model, itr) = treeselection.get_selected()
        if not itr:
            return
        name = model[itr][0]
        plugin_info = component.get('PluginManager').get_plugin_info(name)
        self.builder.get_object('label_plugin_author').set_text(plugin_info['Author'])
        self.builder.get_object('label_plugin_version').set_text(plugin_info['Version'])
        self.builder.get_object('label_plugin_email').set_text(
            plugin_info['Author-email']
        )
        self.builder.get_object('label_plugin_homepage').set_text(
            plugin_info['Home-page']
        )
        self.builder.get_object('label_plugin_details').set_text(
            plugin_info['Description']
        )

    def on_button_plugin_install_clicked(self, widget):
        log.debug('on_button_plugin_install_clicked')
        chooser = Gtk.FileChooserDialog(
            _('Select the Plugin'),
            self.pref_dialog,
            Gtk.FileChooserAction.OPEN,
            buttons=(
                _('_Cancel'),
                Gtk.ResponseType.CANCEL,
                _('_Open'),
                Gtk.ResponseType.OK,
            ),
        )

        chooser.set_transient_for(self.pref_dialog)
        chooser.set_select_multiple(False)
        chooser.set_property('skip-taskbar-hint', True)

        file_filter = Gtk.FileFilter()
        file_filter.set_name(_('Plugin Eggs'))
        file_filter.add_pattern('*.' + 'egg')
        chooser.add_filter(file_filter)

        # Run the dialog
        response = chooser.run()

        if response == Gtk.ResponseType.OK:
            filepath = deluge.common.decode_bytes(chooser.get_filename())
        else:
            chooser.destroy()
            return

        import shutil
        from base64 import b64encode

        filename = os.path.split(filepath)[1]
        shutil.copyfile(filepath, os.path.join(get_config_dir(), 'plugins', filename))

        component.get('PluginManager').scan_for_plugins()

        if not client.is_localhost():
            # We need to send this plugin to the daemon
            with open(filepath, 'rb') as _file:
                filedump = b64encode(_file.read())
            client.core.upload_plugin(filename, filedump)

        client.core.rescan_plugins()
        chooser.destroy()
        # We need to re-show the preferences dialog to show the new plugins
        self.show()

    def on_button_rescan_plugins_clicked(self, widget):
        component.get('PluginManager').scan_for_plugins()
        if client.connected():
            client.core.rescan_plugins()
        self.show()

    def on_button_find_plugins_clicked(self, widget):
        deluge.common.open_url_in_browser('http://dev.deluge-torrent.org/wiki/Plugins')

    def on_combo_encryption_changed(self, widget):
        combo_encin = self.builder.get_object('combo_encin').get_active()
        combo_encout = self.builder.get_object('combo_encout').get_active()
        combo_enclevel = self.builder.get_object('combo_enclevel')

        # If incoming and outgoing both set to disabled, disable level combobox
        if combo_encin == 2 and combo_encout == 2:
            combo_enclevel.set_sensitive(False)
        elif self.is_connected:
            combo_enclevel.set_sensitive(True)

    def on_combo_proxy_type_changed(self, widget):
        proxy_type = self.builder.get_object('combo_proxy_type').get_active()
        proxy_entries = [
            'label_proxy_host',
            'entry_proxy_host',
            'label_proxy_port',
            'spin_proxy_port',
            'label_proxy_pass',
            'entry_proxy_pass',
            'label_proxy_user',
            'entry_proxy_user',
            'chk_proxy_host_resolve',
            'chk_proxy_peer_conn',
            'chk_proxy_tracker_conn',
        ]

        # 0: None, 1: Socks4, 2: Socks5, 3: Socks5 Auth, 4: HTTP, 5: HTTP Auth, 6: I2P
        show_entries = []
        if proxy_type > 0:
            show_entries.extend(
                [
                    'label_proxy_host',
                    'entry_proxy_host',
                    'label_proxy_port',
                    'spin_proxy_port',
                    'chk_proxy_peer_conn',
                    'chk_proxy_tracker_conn',
                ]
            )
            if proxy_type in (3, 5):
                show_entries.extend(
                    [
                        'label_proxy_pass',
                        'entry_proxy_pass',
                        'label_proxy_user',
                        'entry_proxy_user',
                    ]
                )
            if proxy_type in (2, 3, 4, 5):
                show_entries.extend(['chk_proxy_host_resolve'])

        for entry in proxy_entries:
            if entry in show_entries:
                self.builder.get_object(entry).show()
            else:
                self.builder.get_object(entry).hide()

    def on_entry_proxy_host_paste_clipboard(self, widget):
        text = get_clipboard_text()
        log.debug('on_entry_proxy_host_paste-clipboard: got paste: %s', text)
        text = text if '//' in text else '//' + text
        parsed = urlparse(text)
        if parsed.hostname:
            widget.set_text(parsed.hostname)
            widget.emit_stop_by_name('paste-clipboard')
        if parsed.port:
            self.builder.get_object('spin_proxy_port').set_value(parsed.port)
        if parsed.username:
            self.builder.get_object('entry_proxy_user').set_text(parsed.username)
        if parsed.password:
            self.builder.get_object('entry_proxy_pass').set_text(parsed.password)

    def on_button_associate_magnet_clicked(self, widget):
        associate_magnet_links(True)

    def _get_accounts_tab_data(self):
        def on_ok(accounts):
            self.accounts_frame.show()
            self.on_get_known_accounts(accounts)

        def on_fail(failure):
            if failure.type == NotAuthorizedError:
                self.accounts_frame.hide()
            else:
                ErrorDialog(
                    _('Server Side Error'),
                    _('An error occurred on the server'),
                    parent=self.pref_dialog,
                    details=failure.getErrorMessage(),
                ).run()

        client.core.get_known_accounts().addCallback(on_ok).addErrback(on_fail)

    def on_get_known_accounts(self, known_accounts):
        known_accounts_to_log = []
        for account in known_accounts:
            account_to_log = {}
            for key, value in account.copy().items():
                if key == 'password':
                    value = '*' * len(value)
                account_to_log[key] = value
            known_accounts_to_log.append(account_to_log)
        log.debug('on_known_accounts: %s', known_accounts_to_log)

        self.accounts_liststore.clear()

        for account in known_accounts:
            accounts_iter = self.accounts_liststore.append()
            self.accounts_liststore.set_value(
                accounts_iter, ACCOUNTS_USERNAME, account['username']
            )
            self.accounts_liststore.set_value(
                accounts_iter, ACCOUNTS_LEVEL, account['authlevel']
            )
            self.accounts_liststore.set_value(
                accounts_iter, ACCOUNTS_PASSWORD, account['password']
            )

    def on_accounts_selection_changed(self, treeselection):
        log.debug('on_accounts_selection_changed')
        (model, itr) = treeselection.get_selected()
        if not itr:
            return
        username = model[itr][0]
        if username:
            self.builder.get_object('accounts_edit').set_sensitive(True)
            self.builder.get_object('accounts_delete').set_sensitive(True)
        else:
            self.builder.get_object('accounts_edit').set_sensitive(False)
            self.builder.get_object('accounts_delete').set_sensitive(False)

    def on_accounts_add_clicked(self, widget):
        dialog = AccountDialog(
            levels_mapping=client.auth_levels_mapping, parent=self.pref_dialog
        )

        def dialog_finished(response_id):
            username = dialog.get_username()
            password = dialog.get_password()
            authlevel = dialog.get_authlevel()

            def add_ok(rv):
                accounts_iter = self.accounts_liststore.append()
                self.accounts_liststore.set_value(
                    accounts_iter, ACCOUNTS_USERNAME, username
                )
                self.accounts_liststore.set_value(
                    accounts_iter, ACCOUNTS_LEVEL, authlevel
                )
                self.accounts_liststore.set_value(
                    accounts_iter, ACCOUNTS_PASSWORD, password
                )

            def add_fail(failure):
                if failure.type == AuthManagerError:
                    ErrorDialog(
                        _('Error Adding Account'),
                        _('Authentication failed'),
                        parent=self.pref_dialog,
                        details=failure.getErrorMessage(),
                    ).run()
                else:
                    ErrorDialog(
                        _('Error Adding Account'),
                        _('An error occurred while adding account'),
                        parent=self.pref_dialog,
                        details=failure.getErrorMessage(),
                    ).run()

            if response_id == Gtk.ResponseType.OK:
                client.core.create_account(username, password, authlevel).addCallback(
                    add_ok
                ).addErrback(add_fail)

        dialog.run().addCallback(dialog_finished)

    def on_accounts_edit_clicked(self, widget):
        (model, itr) = self.accounts_listview.get_selection().get_selected()
        if not itr:
            return

        dialog = AccountDialog(
            model[itr][ACCOUNTS_USERNAME],
            model[itr][ACCOUNTS_PASSWORD],
            model[itr][ACCOUNTS_LEVEL],
            levels_mapping=client.auth_levels_mapping,
            parent=self.pref_dialog,
        )

        def dialog_finished(response_id):
            def update_ok(rc):
                model.set_value(itr, ACCOUNTS_PASSWORD, dialog.get_username())
                model.set_value(itr, ACCOUNTS_LEVEL, dialog.get_authlevel())

            def update_fail(failure):
                ErrorDialog(
                    _('Error Updating Account'),
                    _('An error occurred while updating account'),
                    parent=self.pref_dialog,
                    details=failure.getErrorMessage(),
                ).run()

            if response_id == Gtk.ResponseType.OK:
                client.core.update_account(
                    dialog.get_username(), dialog.get_password(), dialog.get_authlevel()
                ).addCallback(update_ok).addErrback(update_fail)

        dialog.run().addCallback(dialog_finished)

    def on_accounts_delete_clicked(self, widget):
        (model, itr) = self.accounts_listview.get_selection().get_selected()
        if not itr:
            return

        username = model[itr][0]
        header = _('Remove Account')
        text = _(
            'Are you sure you want to remove the account with the '
            'username "%(username)s"?' % {'username': username}
        )
        dialog = YesNoDialog(header, text, parent=self.pref_dialog)

        def dialog_finished(response_id):
            def remove_ok(rc):
                model.remove(itr)

            def remove_fail(failure):
                if failure.type == AuthManagerError:
                    ErrorDialog(
                        _('Error Removing Account'),
                        _('Auhentication failed'),
                        parent=self.pref_dialog,
                        details=failure.getErrorMessage(),
                    ).run()
                else:
                    ErrorDialog(
                        _('Error Removing Account'),
                        _('An error occurred while removing account'),
                        parent=self.pref_dialog,
                        details=failure.getErrorMessage(),
                    ).run()

            if response_id == Gtk.ResponseType.YES:
                client.core.remove_account(username).addCallback(remove_ok).addErrback(
                    remove_fail
                )

        dialog.run().addCallback(dialog_finished)

    def on_piecesbar_toggle_toggled(self, widget):
        self.gtkui_config['show_piecesbar'] = widget.get_active()
        colors_widget = self.builder.get_object('piecebar_colors_expander')
        colors_widget.set_visible(widget.get_active())

    def on_checkbutton_language_toggled(self, widget):
        self.language_combo.set_visible(not self.language_checkbox.get_active())

    def on_completed_color_set(self, widget):
        self.__set_color('completed')

    def on_revert_color_completed_clicked(self, widget):
        self.__revert_color('completed')

    def on_downloading_color_set(self, widget):
        self.__set_color('downloading')

    def on_revert_color_downloading_clicked(self, widget):
        self.__revert_color('downloading')

    def on_waiting_color_set(self, widget):
        self.__set_color('waiting')

    def on_revert_color_waiting_clicked(self, widget):
        self.__revert_color('waiting')

    def on_missing_color_set(self, widget):
        self.__set_color('missing')

    def on_revert_color_missing_clicked(self, widget):
        self.__revert_color('missing')

    def __set_color(self, state, from_config=False):
        if from_config:
            color = Color(*self.gtkui_config['pieces_color_%s' % state])
            log.debug(
                'Setting %r color state from config to %s',
                state,
                (color.red, color.green, color.blue),
            )
            self.builder.get_object('%s_color' % state).set_color(color)
        else:
            color = self.builder.get_object('%s_color' % state).get_color()
            log.debug(
                'Setting %r color state to %s',
                state,
                (color.red, color.green, color.blue),
            )
            self.gtkui_config['pieces_color_%s' % state] = [
                color.red,
                color.green,
                color.blue,
            ]
            self.gtkui_config.save()
            self.gtkui_config.apply_set_functions('pieces_colors')

        self.builder.get_object('revert_color_%s' % state).set_sensitive(
            [color.red, color.green, color.blue] != self.COLOR_DEFAULTS[state]
        )

    def __revert_color(self, state, from_config=False):
        log.debug('Reverting %r color state', state)
        self.builder.get_object('%s_color' % state).set_color(
            Color(*self.COLOR_DEFAULTS[state])
        )
        self.builder.get_object('revert_color_%s' % state).set_sensitive(False)
        self.gtkui_config.apply_set_functions('pieces_colors')
