# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 GazpachoKing <chase.sterling@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os

import gi  # isort:skip (Required before Gtk import).

gi.require_version('Gtk', '3.0')  # NOQA: E402

# isort:imports-thirdparty
from gi.repository import Gtk

# isort:imports-firstparty
import deluge.common
import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client
from deluge.ui.gtk3 import dialogs

# isort:imports-localfolder
from .common import get_resource

log = logging.getLogger(__name__)


class IncompatibleOption(Exception):
    pass


class OptionsDialog(object):
    spin_ids = ['max_download_speed', 'max_upload_speed', 'stop_ratio']
    spin_int_ids = ['max_upload_slots', 'max_connections']
    chk_ids = [
        'stop_at_ratio',
        'remove_at_ratio',
        'move_completed',
        'add_paused',
        'auto_managed',
        'queue_to_top',
    ]

    def __init__(self):
        self.accounts = Gtk.ListStore(str)
        self.labels = Gtk.ListStore(str)
        self.core_config = {}

    def show(self, options=None, watchdir_id=None):
        if options is None:
            options = {}
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('autoadd_options.ui'))
        self.builder.connect_signals(
            {
                'on_opts_add': self.on_add,
                'on_opts_apply': self.on_apply,
                'on_opts_cancel': self.on_cancel,
                'on_options_dialog_close': self.on_cancel,
                'on_toggle_toggled': self.on_toggle_toggled,
            }
        )
        self.dialog = self.builder.get_object('options_dialog')
        self.dialog.set_transient_for(component.get('Preferences').pref_dialog)

        if watchdir_id:
            # We have an existing watchdir_id, we are editing
            self.builder.get_object('opts_add_button').hide()
            self.builder.get_object('opts_apply_button').show()
            self.watchdir_id = watchdir_id
        else:
            # We don't have an id, adding
            self.builder.get_object('opts_add_button').show()
            self.builder.get_object('opts_apply_button').hide()
            self.watchdir_id = None

        self.load_options(options)
        self.dialog.run()

    def load_options(self, options):
        self.builder.get_object('enabled').set_active(options.get('enabled', True))
        self.builder.get_object('append_extension_toggle').set_active(
            options.get('append_extension_toggle', False)
        )
        self.builder.get_object('append_extension').set_text(
            options.get('append_extension', '.added')
        )
        self.builder.get_object('download_location_toggle').set_active(
            options.get('download_location_toggle', False)
        )
        self.builder.get_object('copy_torrent_toggle').set_active(
            options.get('copy_torrent_toggle', False)
        )
        self.builder.get_object('delete_copy_torrent_toggle').set_active(
            options.get('delete_copy_torrent_toggle', False)
        )
        self.builder.get_object('seed_mode').set_active(options.get('seed_mode', False))
        self.accounts.clear()
        self.labels.clear()
        combobox = self.builder.get_object('OwnerCombobox')
        combobox_render = Gtk.CellRendererText()
        combobox.pack_start(combobox_render, True)
        combobox.add_attribute(combobox_render, 'text', 0)
        combobox.set_model(self.accounts)

        label_widget = self.builder.get_object('label')
        label_widget.get_child().set_text(options.get('label', ''))
        label_widget.set_model(self.labels)
        label_widget.set_entry_text_column(0)
        self.builder.get_object('label_toggle').set_active(
            options.get('label_toggle', False)
        )

        for spin_id in self.spin_ids + self.spin_int_ids:
            self.builder.get_object(spin_id).set_value(options.get(spin_id, 0))
            self.builder.get_object(spin_id + '_toggle').set_active(
                options.get(spin_id + '_toggle', False)
            )
        for chk_id in self.chk_ids:
            self.builder.get_object(chk_id).set_active(bool(options.get(chk_id, True)))
            self.builder.get_object(chk_id + '_toggle').set_active(
                options.get(chk_id + '_toggle', False)
            )
        if not options.get('add_paused', True):
            self.builder.get_object('isnt_add_paused').set_active(True)
        if not options.get('queue_to_top', True):
            self.builder.get_object('isnt_queue_to_top').set_active(True)
        if not options.get('auto_managed', True):
            self.builder.get_object('isnt_auto_managed').set_active(True)
        for field in [
            'move_completed_path',
            'path',
            'download_location',
            'copy_torrent',
        ]:
            if client.is_localhost():
                self.builder.get_object(field + '_chooser').set_current_folder(
                    options.get(field, os.path.expanduser('~'))
                )
                self.builder.get_object(field + '_chooser').show()
                self.builder.get_object(field + '_entry').hide()
            else:
                self.builder.get_object(field + '_entry').set_text(
                    options.get(field, '')
                )
                self.builder.get_object(field + '_entry').show()
                self.builder.get_object(field + '_chooser').hide()
        self.set_sensitive()

        def on_core_config(config):
            if client.is_localhost():
                self.builder.get_object('download_location_chooser').set_current_folder(
                    options.get('download_location', config['download_location'])
                )
                if options.get('move_completed_toggle', config['move_completed']):
                    self.builder.get_object('move_completed_toggle').set_active(True)
                    self.builder.get_object(
                        'move_completed_path_chooser'
                    ).set_current_folder(
                        options.get(
                            'move_completed_path', config['move_completed_path']
                        )
                    )
                if options.get('copy_torrent_toggle', config['copy_torrent_file']):
                    self.builder.get_object('copy_torrent_toggle').set_active(True)
                    self.builder.get_object('copy_torrent_chooser').set_current_folder(
                        options.get('copy_torrent', config['torrentfiles_location'])
                    )
            else:
                self.builder.get_object('download_location_entry').set_text(
                    options.get('download_location', config['download_location'])
                )
                if options.get('move_completed_toggle', config['move_completed']):
                    self.builder.get_object('move_completed_toggle').set_active(
                        options.get('move_completed_toggle', False)
                    )
                    self.builder.get_object('move_completed_path_entry').set_text(
                        options.get(
                            'move_completed_path', config['move_completed_path']
                        )
                    )
                if options.get('copy_torrent_toggle', config['copy_torrent_file']):
                    self.builder.get_object('copy_torrent_toggle').set_active(True)
                    self.builder.get_object('copy_torrent_entry').set_text(
                        options.get('copy_torrent', config['torrentfiles_location'])
                    )

            if options.get(
                'delete_copy_torrent_toggle', config['del_copy_torrent_file']
            ):
                self.builder.get_object('delete_copy_torrent_toggle').set_active(True)

        if not options:
            client.core.get_config().addCallback(on_core_config)

        def on_accounts(accounts, owner):
            log.debug('Got Accounts')
            selected_iter = None
            for account in accounts:
                acc_iter = self.accounts.append()
                self.accounts.set_value(acc_iter, 0, account['username'])
                if account['username'] == owner:
                    selected_iter = acc_iter
            self.builder.get_object('OwnerCombobox').set_active_iter(selected_iter)

        def on_accounts_failure(failure):
            log.debug('Failed to get accounts!!! %s', failure)
            acc_iter = self.accounts.append()
            self.accounts.set_value(acc_iter, 0, client.get_auth_user())
            self.builder.get_object('OwnerCombobox').set_active(0)
            self.builder.get_object('OwnerCombobox').set_sensitive(False)

        def on_labels(labels):
            log.debug('Got Labels: %s', labels)
            for label in labels:
                self.labels.set_value(self.labels.append(), 0, label)
            label_widget = self.builder.get_object('label')
            label_widget.set_model(self.labels)
            label_widget.set_entry_text_column(0)

        def on_failure(failure):
            log.exception(failure)

        def on_get_enabled_plugins(result):
            if 'Label' in result:
                self.builder.get_object('label_frame').show()
                client.label.get_labels().addCallback(on_labels).addErrback(on_failure)
            else:
                self.builder.get_object('label_frame').hide()
                self.builder.get_object('label_toggle').set_active(False)

        client.core.get_enabled_plugins().addCallback(on_get_enabled_plugins)
        if client.get_auth_level() == deluge.common.AUTH_LEVEL_ADMIN:
            client.core.get_known_accounts().addCallback(
                on_accounts, options.get('owner', client.get_auth_user())
            ).addErrback(on_accounts_failure)
        else:
            acc_iter = self.accounts.append()
            self.accounts.set_value(acc_iter, 0, client.get_auth_user())
            self.builder.get_object('OwnerCombobox').set_active(0)
            self.builder.get_object('OwnerCombobox').set_sensitive(False)

    def set_sensitive(self):
        maintoggles = [
            'download_location',
            'append_extension',
            'move_completed',
            'label',
            'max_download_speed',
            'max_upload_speed',
            'max_connections',
            'max_upload_slots',
            'add_paused',
            'auto_managed',
            'stop_at_ratio',
            'queue_to_top',
            'copy_torrent',
        ]
        for maintoggle in maintoggles:
            self.on_toggle_toggled(self.builder.get_object(maintoggle + '_toggle'))

    def on_toggle_toggled(self, tb):
        toggle = tb.get_name().replace('_toggle', '')
        isactive = tb.get_active()
        if toggle == 'download_location':
            self.builder.get_object('download_location_chooser').set_sensitive(isactive)
            self.builder.get_object('download_location_entry').set_sensitive(isactive)
        elif toggle == 'append_extension':
            self.builder.get_object('append_extension').set_sensitive(isactive)
        elif toggle == 'copy_torrent':
            self.builder.get_object('copy_torrent_entry').set_sensitive(isactive)
            self.builder.get_object('copy_torrent_chooser').set_sensitive(isactive)
            self.builder.get_object('delete_copy_torrent_toggle').set_sensitive(
                isactive
            )
        elif toggle == 'move_completed':
            self.builder.get_object('move_completed_path_chooser').set_sensitive(
                isactive
            )
            self.builder.get_object('move_completed_path_entry').set_sensitive(isactive)
            self.builder.get_object('move_completed').set_active(isactive)
        elif toggle == 'label':
            self.builder.get_object('label').set_sensitive(isactive)
        elif toggle == 'max_download_speed':
            self.builder.get_object('max_download_speed').set_sensitive(isactive)
        elif toggle == 'max_upload_speed':
            self.builder.get_object('max_upload_speed').set_sensitive(isactive)
        elif toggle == 'max_connections':
            self.builder.get_object('max_connections').set_sensitive(isactive)
        elif toggle == 'max_upload_slots':
            self.builder.get_object('max_upload_slots').set_sensitive(isactive)
        elif toggle == 'add_paused':
            self.builder.get_object('add_paused').set_sensitive(isactive)
            self.builder.get_object('isnt_add_paused').set_sensitive(isactive)
        elif toggle == 'queue_to_top':
            self.builder.get_object('queue_to_top').set_sensitive(isactive)
            self.builder.get_object('isnt_queue_to_top').set_sensitive(isactive)
        elif toggle == 'auto_managed':
            self.builder.get_object('auto_managed').set_sensitive(isactive)
            self.builder.get_object('isnt_auto_managed').set_sensitive(isactive)
        elif toggle == 'stop_at_ratio':
            self.builder.get_object('remove_at_ratio_toggle').set_active(isactive)
            self.builder.get_object('stop_ratio_toggle').set_active(isactive)
            self.builder.get_object('stop_at_ratio').set_active(isactive)
            self.builder.get_object('stop_ratio').set_sensitive(isactive)
            self.builder.get_object('remove_at_ratio').set_sensitive(isactive)

    def on_apply(self, event=None):
        try:
            options = self.generate_opts()
            client.autoadd.set_options(str(self.watchdir_id), options).addCallbacks(
                self.on_added, self.on_error_show
            )
        except IncompatibleOption as ex:
            dialogs.ErrorDialog(_('Incompatible Option'), str(ex), self.dialog).run()

    def on_error_show(self, result):
        d = dialogs.ErrorDialog(_('Error'), result.value.exception_msg, self.dialog)
        result.cleanFailure()
        d.run()

    def on_added(self, result):
        self.dialog.destroy()

    def on_add(self, event=None):
        try:
            options = self.generate_opts()
            client.autoadd.add(options).addCallbacks(self.on_added, self.on_error_show)
        except IncompatibleOption as ex:
            dialogs.ErrorDialog(_('Incompatible Option'), str(ex), self.dialog).run()

    def on_cancel(self, event=None):
        self.dialog.destroy()

    def generate_opts(self):
        # generate options dict based on gtk objects
        options = {}
        options['enabled'] = self.builder.get_object('enabled').get_active()
        if client.is_localhost():
            options['path'] = self.builder.get_object('path_chooser').get_filename()
            options['download_location'] = self.builder.get_object(
                'download_location_chooser'
            ).get_filename()
            options['move_completed_path'] = self.builder.get_object(
                'move_completed_path_chooser'
            ).get_filename()
            options['copy_torrent'] = self.builder.get_object(
                'copy_torrent_chooser'
            ).get_filename()
        else:
            options['path'] = self.builder.get_object('path_entry').get_text()
            options['download_location'] = self.builder.get_object(
                'download_location_entry'
            ).get_text()
            options['move_completed_path'] = self.builder.get_object(
                'move_completed_path_entry'
            ).get_text()
            options['copy_torrent'] = self.builder.get_object(
                'copy_torrent_entry'
            ).get_text()

        options['label'] = (
            self.builder.get_object('label').get_child().get_text().lower()
        )
        options['append_extension'] = self.builder.get_object(
            'append_extension'
        ).get_text()
        options['owner'] = self.accounts[
            self.builder.get_object('OwnerCombobox').get_active()
        ][0]

        for key in [
            'append_extension_toggle',
            'download_location_toggle',
            'label_toggle',
            'copy_torrent_toggle',
            'delete_copy_torrent_toggle',
            'seed_mode',
        ]:
            options[key] = self.builder.get_object(key).get_active()

        for spin_id in self.spin_ids:
            options[spin_id] = self.builder.get_object(spin_id).get_value()
            options[spin_id + '_toggle'] = self.builder.get_object(
                spin_id + '_toggle'
            ).get_active()
        for spin_int_id in self.spin_int_ids:
            options[spin_int_id] = self.builder.get_object(
                spin_int_id
            ).get_value_as_int()
            options[spin_int_id + '_toggle'] = self.builder.get_object(
                spin_int_id + '_toggle'
            ).get_active()
        for chk_id in self.chk_ids:
            options[chk_id] = self.builder.get_object(chk_id).get_active()
            options[chk_id + '_toggle'] = self.builder.get_object(
                chk_id + '_toggle'
            ).get_active()

        if (
            options['copy_torrent_toggle']
            and options['path'] == options['copy_torrent']
        ):
            raise IncompatibleOption(
                _(
                    '"Watch Folder" directory and "Copy of .torrent'
                    ' files to" directory cannot be the same!'
                )
            )
        return options


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('config.ui'))
        self.builder.connect_signals(self)
        self.opts_dialog = OptionsDialog()

        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs
        )
        client.register_event_handler(
            'AutoaddOptionsChangedEvent', self.on_options_changed_event
        )

        self.watchdirs = {}

        vbox = self.builder.get_object('watchdirs_vbox')
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        vbox.pack_start(sw, True, True, 0)

        self.store = self.create_model()

        self.treeView = Gtk.TreeView(self.store)
        self.treeView.connect('cursor-changed', self.on_listitem_activated)
        self.treeView.connect('row-activated', self.on_edit_button_clicked)

        self.create_columns(self.treeView)
        sw.add(self.treeView)
        sw.show_all()
        component.get('Preferences').add_page(
            _('AutoAdd'), self.builder.get_object('prefs_box')
        )

    def disable(self):
        component.get('Preferences').remove_page(_('AutoAdd'))
        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )

    def create_model(self):
        store = Gtk.ListStore(str, bool, str, str)
        for watchdir_id, watchdir in self.watchdirs.items():
            store.append(
                [
                    watchdir_id,
                    watchdir['enabled'],
                    watchdir.get('owner', 'localclient'),
                    watchdir['path'],
                ]
            )
        return store

    def create_columns(self, treeview):
        renderer_toggle = Gtk.CellRendererToggle()
        column = Gtk.TreeViewColumn(
            _('Active'), renderer_toggle, activatable=1, active=1
        )
        column.set_sort_column_id(1)
        treeview.append_column(column)
        tt = Gtk.Tooltip()
        tt.set_text(_('Double-click to toggle'))
        treeview.set_tooltip_cell(tt, None, None, renderer_toggle)

        renderertext = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Owner'), renderertext, text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)
        tt2 = Gtk.Tooltip()
        tt2.set_text(_('Double-click to edit'))
        treeview.set_has_tooltip(True)

        renderertext = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Path'), renderertext, text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)
        tt2 = Gtk.Tooltip()
        tt2.set_text(_('Double-click to edit'))
        treeview.set_has_tooltip(True)

    def load_watchdir_list(self):
        pass

    def add_watchdir_entry(self):
        pass

    def on_add_button_clicked(self, event=None):
        # display options_window
        self.opts_dialog.show()

    def on_remove_button_clicked(self, event=None):
        tree, tree_id = self.treeView.get_selection().get_selected()
        watchdir_id = str(self.store.get_value(tree_id, 0))
        if watchdir_id:
            client.autoadd.remove(watchdir_id)

    def on_edit_button_clicked(self, event=None, a=None, col=None):
        tree, tree_id = self.treeView.get_selection().get_selected()
        watchdir_id = str(self.store.get_value(tree_id, 0))
        if watchdir_id:
            if col and col.get_title() == _('Active'):
                if self.watchdirs[watchdir_id]['enabled']:
                    client.autoadd.disable_watchdir(watchdir_id)
                else:
                    client.autoadd.enable_watchdir(watchdir_id)
            else:
                self.opts_dialog.show(self.watchdirs[watchdir_id], watchdir_id)

    def on_listitem_activated(self, treeview):
        tree, tree_id = self.treeView.get_selection().get_selected()
        if tree_id:
            self.builder.get_object('edit_button').set_sensitive(True)
            self.builder.get_object('remove_button').set_sensitive(True)
        else:
            self.builder.get_object('edit_button').set_sensitive(False)
            self.builder.get_object('remove_button').set_sensitive(False)

    def on_apply_prefs(self):
        log.debug('applying prefs for AutoAdd')
        for watchdir_id, watchdir in self.watchdirs.items():
            client.autoadd.set_options(watchdir_id, watchdir)

    def on_show_prefs(self):
        client.autoadd.get_watchdirs().addCallback(self.cb_get_config)

    def on_options_changed_event(self):
        client.autoadd.get_watchdirs().addCallback(self.cb_get_config)

    def cb_get_config(self, watchdirs):
        """callback for on show_prefs"""
        log.trace('Got whatchdirs from core: %s', watchdirs)
        self.watchdirs = watchdirs or {}
        self.store.clear()
        for watchdir_id, watchdir in self.watchdirs.items():
            self.store.append(
                [
                    watchdir_id,
                    watchdir['enabled'],
                    watchdir.get('owner', 'localclient'),
                    watchdir['path'],
                ]
            )
        # Workaround for cached glade signal appearing when re-enabling plugin in same session
        if self.builder.get_object('edit_button'):
            # Disable the remove and edit buttons, because nothing in the store is selected
            self.builder.get_object('remove_button').set_sensitive(False)
            self.builder.get_object('edit_button').set_sensitive(False)
