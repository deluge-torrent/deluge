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

import logging
import os

import gtk
import gtk.glade

import deluge.common
import deluge.component as component
from deluge.plugins.pluginbase import GtkPluginBase
from deluge.ui.client import client
from deluge.ui.gtkui import dialogs

from .common import get_resource

log = logging.getLogger(__name__)


class IncompatibleOption(Exception):
    pass


class OptionsDialog():
    spin_ids = ["max_download_speed", "max_upload_speed", "stop_ratio"]
    spin_int_ids = ["max_upload_slots", "max_connections"]
    chk_ids = ["stop_at_ratio", "remove_at_ratio", "move_completed",
               "add_paused", "auto_managed", "queue_to_top"]

    def __init__(self):
        self.accounts = gtk.ListStore(str)
        self.labels = gtk.ListStore(str)
        self.core_config = {}

    def show(self, options={}, watchdir_id=None):
        self.glade = gtk.glade.XML(get_resource("autoadd_options.glade"))
        self.glade.signal_autoconnect({
            "on_opts_add": self.on_add,
            "on_opts_apply": self.on_apply,
            "on_opts_cancel": self.on_cancel,
            "on_options_dialog_close": self.on_cancel,
            "on_toggle_toggled": self.on_toggle_toggled
        })
        self.dialog = self.glade.get_widget("options_dialog")
        self.dialog.set_transient_for(component.get("Preferences").pref_dialog)

        if watchdir_id:
            # We have an existing watchdir_id, we are editing
            self.glade.get_widget('opts_add_button').hide()
            self.glade.get_widget('opts_apply_button').show()
            self.watchdir_id = watchdir_id
        else:
            # We don't have an id, adding
            self.glade.get_widget('opts_add_button').show()
            self.glade.get_widget('opts_apply_button').hide()
            self.watchdir_id = None

        self.load_options(options)
        self.dialog.run()

    def load_options(self, options):
        self.glade.get_widget('enabled').set_active(options.get('enabled', True))
        self.glade.get_widget('append_extension_toggle').set_active(
            options.get('append_extension_toggle', False)
        )
        self.glade.get_widget('append_extension').set_text(
            options.get('append_extension', '.added')
        )
        self.glade.get_widget('download_location_toggle').set_active(
            options.get('download_location_toggle', False)
        )
        self.glade.get_widget('copy_torrent_toggle').set_active(
            options.get('copy_torrent_toggle', False)
        )
        self.glade.get_widget('delete_copy_torrent_toggle').set_active(
            options.get('delete_copy_torrent_toggle', False)
        )
        self.glade.get_widget('seed_mode').set_active(
            options.get('seed_mode', False)
        )
        self.accounts.clear()
        self.labels.clear()
        combobox = self.glade.get_widget('OwnerCombobox')
        combobox_render = gtk.CellRendererText()
        combobox.pack_start(combobox_render, True)
        combobox.add_attribute(combobox_render, 'text', 0)
        combobox.set_model(self.accounts)

        label_widget = self.glade.get_widget('label')
        label_widget.child.set_text(options.get('label', ''))
        label_widget.set_model(self.labels)
        label_widget.set_text_column(0)
        self.glade.get_widget('label_toggle').set_active(options.get('label_toggle', False))

        for id in self.spin_ids + self.spin_int_ids:
            self.glade.get_widget(id).set_value(options.get(id, 0))
            self.glade.get_widget(id + "_toggle").set_active(options.get(id + "_toggle", False))
        for id in self.chk_ids:
            self.glade.get_widget(id).set_active(bool(options.get(id, True)))
            self.glade.get_widget(id + "_toggle").set_active(options.get(id + "_toggle", False))
        if not options.get('add_paused', True):
            self.glade.get_widget('isnt_add_paused').set_active(True)
        if not options.get('queue_to_top', True):
            self.glade.get_widget('isnt_queue_to_top').set_active(True)
        if not options.get('auto_managed', True):
            self.glade.get_widget('isnt_auto_managed').set_active(True)
        for field in ['move_completed_path', 'path', 'download_location',
                      'copy_torrent']:
            if client.is_localhost():
                self.glade.get_widget(field + "_chooser").set_current_folder(
                    options.get(field, os.path.expanduser("~"))
                )
                self.glade.get_widget(field + "_chooser").show()
                self.glade.get_widget(field + "_entry").hide()
            else:
                self.glade.get_widget(field + "_entry").set_text(
                    options.get(field, "")
                )
                self.glade.get_widget(field + "_entry").show()
                self.glade.get_widget(field + "_chooser").hide()
        self.set_sensitive()

        def on_core_config(config):
            if client.is_localhost():
                self.glade.get_widget('download_location_chooser').set_current_folder(
                    options.get('download_location', config["download_location"])
                )
                if options.get('move_completed_toggle', config["move_completed"]):
                    self.glade.get_widget('move_completed_toggle').set_active(True)
                    self.glade.get_widget('move_completed_path_chooser').set_current_folder(
                        options.get('move_completed_path', config["move_completed_path"])
                    )
                if options.get('copy_torrent_toggle', config["copy_torrent_file"]):
                    self.glade.get_widget('copy_torrent_toggle').set_active(True)
                    self.glade.get_widget('copy_torrent_chooser').set_current_folder(
                        options.get('copy_torrent', config["torrentfiles_location"])
                    )
            else:
                self.glade.get_widget('download_location_entry').set_text(
                    options.get('download_location', config["download_location"])
                )
                if options.get('move_completed_toggle', config["move_completed"]):
                    self.glade.get_widget('move_completed_toggle').set_active(
                        options.get('move_completed_toggle', False)
                    )
                    self.glade.get_widget('move_completed_path_entry').set_text(
                        options.get('move_completed_path', config["move_completed_path"])
                    )
                if options.get('copy_torrent_toggle', config["copy_torrent_file"]):
                    self.glade.get_widget('copy_torrent_toggle').set_active(True)
                    self.glade.get_widget('copy_torrent_entry').set_text(
                        options.get('copy_torrent', config["torrentfiles_location"])
                    )

            if options.get('delete_copy_torrent_toggle', config["del_copy_torrent_file"]):
                self.glade.get_widget('delete_copy_torrent_toggle').set_active(True)

        if not options:
            client.core.get_config().addCallback(on_core_config)

        def on_accounts(accounts, owner):
            log.debug("Got Accounts")
            selected_iter = None
            for account in accounts:
                iter = self.accounts.append()
                self.accounts.set_value(
                    iter, 0, account['username']
                )
                if account['username'] == owner:
                    selected_iter = iter
            self.glade.get_widget('OwnerCombobox').set_active_iter(selected_iter)

        def on_accounts_failure(failure):
            log.debug("Failed to get accounts!!! %s", failure)
            iter = self.accounts.append()
            self.accounts.set_value(iter, 0, client.get_auth_user())
            self.glade.get_widget('OwnerCombobox').set_active(0)
            self.glade.get_widget('OwnerCombobox').set_sensitive(False)

        def on_labels(labels):
            log.debug("Got Labels: %s", labels)
            for label in labels:
                self.labels.set_value(self.labels.append(), 0, label)
            label_widget = self.glade.get_widget('label')
            label_widget.set_model(self.labels)
            label_widget.set_text_column(0)

        def on_failure(failure):
            log.exception(failure)

        def on_get_enabled_plugins(result):
            if 'Label' in result:
                self.glade.get_widget('label_frame').show()
                client.label.get_labels().addCallback(on_labels).addErrback(on_failure)
            else:
                self.glade.get_widget('label_frame').hide()
                self.glade.get_widget('label_toggle').set_active(False)

        client.core.get_enabled_plugins().addCallback(on_get_enabled_plugins)
        if client.get_auth_level() == deluge.common.AUTH_LEVEL_ADMIN:
            client.core.get_known_accounts().addCallback(
                on_accounts, options.get('owner', client.get_auth_user())
            ).addErrback(on_accounts_failure)
        else:
            iter = self.accounts.append()
            self.accounts.set_value(iter, 0, client.get_auth_user())
            self.glade.get_widget('OwnerCombobox').set_active(0)
            self.glade.get_widget('OwnerCombobox').set_sensitive(False)

    def set_sensitive(self):
        maintoggles = ['download_location', 'append_extension',
                       'move_completed', 'label', 'max_download_speed',
                       'max_upload_speed', 'max_connections',
                       'max_upload_slots', 'add_paused', 'auto_managed',
                       'stop_at_ratio', 'queue_to_top', 'copy_torrent']
        [self.on_toggle_toggled(self.glade.get_widget(x + "_toggle")) for x in maintoggles]

    def on_toggle_toggled(self, tb):
        toggle = str(tb.name).replace("_toggle", "")
        isactive = tb.get_active()
        if toggle == 'download_location':
            self.glade.get_widget('download_location_chooser').set_sensitive(isactive)
            self.glade.get_widget('download_location_entry').set_sensitive(isactive)
        elif toggle == 'append_extension':
            self.glade.get_widget('append_extension').set_sensitive(isactive)
        elif toggle == 'copy_torrent':
            self.glade.get_widget('copy_torrent_entry').set_sensitive(isactive)
            self.glade.get_widget('copy_torrent_chooser').set_sensitive(isactive)
            self.glade.get_widget('delete_copy_torrent_toggle').set_sensitive(isactive)
        elif toggle == 'move_completed':
            self.glade.get_widget('move_completed_path_chooser').set_sensitive(isactive)
            self.glade.get_widget('move_completed_path_entry').set_sensitive(isactive)
            self.glade.get_widget('move_completed').set_active(isactive)
        elif toggle == 'label':
            self.glade.get_widget('label').set_sensitive(isactive)
        elif toggle == 'max_download_speed':
            self.glade.get_widget('max_download_speed').set_sensitive(isactive)
        elif toggle == 'max_upload_speed':
            self.glade.get_widget('max_upload_speed').set_sensitive(isactive)
        elif toggle == 'max_connections':
            self.glade.get_widget('max_connections').set_sensitive(isactive)
        elif toggle == 'max_upload_slots':
            self.glade.get_widget('max_upload_slots').set_sensitive(isactive)
        elif toggle == 'add_paused':
            self.glade.get_widget('add_paused').set_sensitive(isactive)
            self.glade.get_widget('isnt_add_paused').set_sensitive(isactive)
        elif toggle == 'queue_to_top':
            self.glade.get_widget('queue_to_top').set_sensitive(isactive)
            self.glade.get_widget('isnt_queue_to_top').set_sensitive(isactive)
        elif toggle == 'auto_managed':
            self.glade.get_widget('auto_managed').set_sensitive(isactive)
            self.glade.get_widget('isnt_auto_managed').set_sensitive(isactive)
        elif toggle == 'stop_at_ratio':
            self.glade.get_widget('remove_at_ratio_toggle').set_active(isactive)
            self.glade.get_widget('stop_ratio_toggle').set_active(isactive)
            self.glade.get_widget('stop_at_ratio').set_active(isactive)
            self.glade.get_widget('stop_ratio').set_sensitive(isactive)
            self.glade.get_widget('remove_at_ratio').set_sensitive(isactive)

    def on_apply(self, event=None):
        try:
            options = self.generate_opts()
            client.autoadd.set_options(
                str(self.watchdir_id), options
            ).addCallbacks(self.on_added, self.on_error_show)
        except IncompatibleOption as ex:
            dialogs.ErrorDialog(_("Incompatible Option"), str(ex), self.dialog).run()

    def on_error_show(self, result):
        d = dialogs.ErrorDialog(_("Error"), result.value.exception_msg, self.dialog)
        result.cleanFailure()
        d.run()

    def on_added(self, result):
        self.dialog.destroy()

    def on_add(self, event=None):
        try:
            options = self.generate_opts()
            client.autoadd.add(options).addCallbacks(self.on_added, self.on_error_show)
        except IncompatibleOption as ex:
            dialogs.ErrorDialog(_("Incompatible Option"), str(ex), self.dialog).run()

    def on_cancel(self, event=None):
        self.dialog.destroy()

    def generate_opts(self):
        # generate options dict based on gtk objects
        options = {}
        options['enabled'] = self.glade.get_widget('enabled').get_active()
        if client.is_localhost():
            options['path'] = self.glade.get_widget('path_chooser').get_filename()
            options['download_location'] = self.glade.get_widget(
                'download_location_chooser').get_filename()
            options['move_completed_path'] = self.glade.get_widget(
                'move_completed_path_chooser').get_filename()
            options['copy_torrent'] = self.glade.get_widget(
                'copy_torrent_chooser').get_filename()
        else:
            options['path'] = self.glade.get_widget('path_entry').get_text()
            options['download_location'] = self.glade.get_widget(
                'download_location_entry').get_text()
            options['move_completed_path'] = self.glade.get_widget(
                'move_completed_path_entry').get_text()
            options['copy_torrent'] = self.glade.get_widget(
                'copy_torrent_entry').get_text()

        options['label'] = self.glade.get_widget('label').child.get_text().lower()
        options['append_extension'] = self.glade.get_widget('append_extension').get_text()
        options['owner'] = self.accounts[
            self.glade.get_widget('OwnerCombobox').get_active()][0]

        for key in ['append_extension_toggle', 'download_location_toggle',
                    'label_toggle', 'copy_torrent_toggle',
                    'delete_copy_torrent_toggle', 'seed_mode']:
            options[key] = self.glade.get_widget(key).get_active()

        for id in self.spin_ids:
            options[id] = self.glade.get_widget(id).get_value()
            options[id + "_toggle"] = self.glade.get_widget(id + "_toggle").get_active()
        for id in self.spin_int_ids:
            options[id] = self.glade.get_widget(id).get_value_as_int()
            options[id + "_toggle"] = self.glade.get_widget(id + "_toggle").get_active()
        for id in self.chk_ids:
            options[id] = self.glade.get_widget(id).get_active()
            options[id + "_toggle"] = self.glade.get_widget(id + "_toggle").get_active()

        if options['copy_torrent_toggle'] and options['path'] == options['copy_torrent']:
            raise IncompatibleOption(_("\"Watch Folder\" directory and \"Copy of .torrent"
                                       " files to\" directory cannot be the same!"))
        return options


class GtkUI(GtkPluginBase):
    def enable(self):

        self.glade = gtk.glade.XML(get_resource("config.glade"))
        self.glade.signal_autoconnect({
            "on_add_button_clicked": self.on_add_button_clicked,
            "on_edit_button_clicked": self.on_edit_button_clicked,
            "on_remove_button_clicked": self.on_remove_button_clicked
        })
        self.opts_dialog = OptionsDialog()

        component.get("PluginManager").register_hook(
            "on_apply_prefs", self.on_apply_prefs
        )
        component.get("PluginManager").register_hook(
            "on_show_prefs", self.on_show_prefs
        )
        client.register_event_handler(
            "AutoaddOptionsChangedEvent", self.on_options_changed_event
        )

        self.watchdirs = {}

        vbox = self.glade.get_widget("watchdirs_vbox")
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        vbox.pack_start(sw, True, True, 0)

        self.store = self.create_model()

        self.treeView = gtk.TreeView(self.store)
        self.treeView.connect("cursor-changed", self.on_listitem_activated)
        self.treeView.connect("row-activated", self.on_edit_button_clicked)
        self.treeView.set_rules_hint(True)

        self.create_columns(self.treeView)
        sw.add(self.treeView)
        sw.show_all()
        component.get("Preferences").add_page(
            _("AutoAdd"), self.glade.get_widget("prefs_box")
        )

    def disable(self):
        component.get("Preferences").remove_page(_("AutoAdd"))
        component.get("PluginManager").deregister_hook(
            "on_apply_prefs", self.on_apply_prefs
        )
        component.get("PluginManager").deregister_hook(
            "on_show_prefs", self.on_show_prefs
        )

    def create_model(self):
        store = gtk.ListStore(str, bool, str, str)
        for watchdir_id, watchdir in self.watchdirs.iteritems():
            store.append([
                watchdir_id, watchdir['enabled'],
                watchdir.get('owner', 'localclient'), watchdir['path']
            ])
        return store

    def create_columns(self, treeview):
        renderer_toggle = gtk.CellRendererToggle()
        column = gtk.TreeViewColumn(
            _("Active"), renderer_toggle, activatable=1, active=1
        )
        column.set_sort_column_id(1)
        treeview.append_column(column)
        tt = gtk.Tooltip()
        tt.set_text(_('Double-click to toggle'))
        treeview.set_tooltip_cell(tt, None, None, renderer_toggle)

        renderertext = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Owner"), renderertext, text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)
        tt2 = gtk.Tooltip()
        tt2.set_text(_('Double-click to edit'))
        treeview.set_has_tooltip(True)

        renderertext = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Path"), renderertext, text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)
        tt2 = gtk.Tooltip()
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
            if col and col.get_title() == _("Active"):
                if self.watchdirs[watchdir_id]['enabled']:
                    client.autoadd.disable_watchdir(watchdir_id)
                else:
                    client.autoadd.enable_watchdir(watchdir_id)
            else:
                self.opts_dialog.show(self.watchdirs[watchdir_id], watchdir_id)

    def on_listitem_activated(self, treeview):
        tree, tree_id = self.treeView.get_selection().get_selected()
        if tree_id:
            self.glade.get_widget('edit_button').set_sensitive(True)
            self.glade.get_widget('remove_button').set_sensitive(True)
        else:
            self.glade.get_widget('edit_button').set_sensitive(False)
            self.glade.get_widget('remove_button').set_sensitive(False)

    def on_apply_prefs(self):
        log.debug("applying prefs for AutoAdd")
        for watchdir_id, watchdir in self.watchdirs.iteritems():
            client.autoadd.set_options(watchdir_id, watchdir)

    def on_show_prefs(self):
        client.autoadd.get_watchdirs().addCallback(self.cb_get_config)

    def on_options_changed_event(self):
        client.autoadd.get_watchdirs().addCallback(self.cb_get_config)

    def cb_get_config(self, watchdirs):
        """callback for on show_prefs"""
        log.trace("Got whatchdirs from core: %s", watchdirs)
        self.watchdirs = watchdirs or {}
        self.store.clear()
        for watchdir_id, watchdir in self.watchdirs.iteritems():
            self.store.append([
                watchdir_id, watchdir['enabled'],
                watchdir.get('owner', 'localclient'), watchdir['path']
            ])
        # Workaround for cached glade signal appearing when re-enabling plugin in same session
        if self.glade.get_widget('edit_button'):
            # Disable the remove and edit buttons, because nothing in the store is selected
            self.glade.get_widget('remove_button').set_sensitive(False)
            self.glade.get_widget('edit_button').set_sensitive(False)
