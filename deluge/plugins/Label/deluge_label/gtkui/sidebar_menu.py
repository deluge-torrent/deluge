# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import gi  # isort:skip (Required before Gtk import).

gi.require_version('Gtk', '3.0')  # NOQA: E402

# isort:imports-thirdparty
from gi.repository import Gtk

# isort:imports-firstparty
import deluge.component as component
from deluge.ui.client import client

# isort:imports-localfolder
from ..common import get_resource

log = logging.getLogger(__name__)

NO_LABEL = 'No Label'


# menu
class LabelSidebarMenu(object):
    def __init__(self):

        self.treeview = component.get('FilterTreeView')
        self.menu = self.treeview.menu
        self.items = []

        # add items, in reverse order, because they are prepended.
        sep = Gtk.SeparatorMenuItem()
        self.items.append(sep)
        self.menu.prepend(sep)
        self._add_item('options', _('Label _Options'))
        self._add_item('remove', _('_Remove Label'))
        self._add_item('add', _('_Add Label'))

        self.menu.show_all()
        # dialogs:
        self.add_dialog = AddDialog()
        self.options_dialog = OptionsDialog()
        # hooks:
        self.menu.connect('show', self.on_show, None)

    def _add_item(self, item_id, label):
        """
        id is automatically-added as self.item_<id>
        """
        item = Gtk.MenuItem.new_with_mnemonic(label)
        func = getattr(self, 'on_%s' % item_id)
        item.connect('activate', func)
        self.menu.prepend(item)
        setattr(self, 'item_%s' % item_id, item)
        self.items.append(item)
        return item

    def on_add(self, event=None):
        self.add_dialog.show()

    def on_remove(self, event=None):
        client.label.remove(self.treeview.value)

    def on_options(self, event=None):
        self.options_dialog.show(self.treeview.value)

    def on_show(self, widget=None, data=None):
        """No Label:disable options/del."""
        log.debug('label-sidebar-popup:on-show')

        cat = self.treeview.cat
        label = self.treeview.value
        if cat == 'label' or (cat == 'cat' and label == 'label'):
            # is a label : show  menu-items
            for item in self.items:
                item.show()
            # default items
            sensitive = (label not in (NO_LABEL, None, '', 'All')) and (cat != 'cat')
            for item in self.items:
                item.set_sensitive(sensitive)

            # add is always enabled.
            self.item_add.set_sensitive(True)
        else:
            # not a label -->hide everything.
            for item in self.items:
                item.hide()

    def unload(self):
        log.debug('disable01')
        for item in list(self.items):
            item.hide()
            item.destroy()
            log.debug('disable02')
        self.items = []


# dialogs:
class AddDialog(object):
    def __init__(self):
        pass

    def show(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('label_add.ui'))
        self.dialog = self.builder.get_object('dlg_label_add')
        self.dialog.set_transient_for(component.get('MainWindow').window)

        self.builder.connect_signals(self)
        self.dialog.run()

    def on_add_ok(self, event=None):
        value = self.builder.get_object('txt_add').get_text()
        client.label.add(value)
        self.dialog.destroy()

    def on_add_cancel(self, event=None):
        self.dialog.destroy()


class OptionsDialog(object):
    spin_ids = ['max_download_speed', 'max_upload_speed', 'stop_ratio']
    spin_int_ids = ['max_upload_slots', 'max_connections']
    chk_ids = [
        'apply_max',
        'apply_queue',
        'stop_at_ratio',
        'apply_queue',
        'remove_at_ratio',
        'apply_move_completed',
        'move_completed',
        'is_auto_managed',
        'auto_add',
    ]

    # list of tuples, because order matters when nesting.
    sensitive_groups = [
        (
            'apply_max',
            [
                'max_download_speed',
                'max_upload_speed',
                'max_upload_slots',
                'max_connections',
            ],
        ),
        ('apply_queue', ['is_auto_managed', 'stop_at_ratio']),
        ('stop_at_ratio', ['remove_at_ratio', 'stop_ratio']),  # nested
        ('apply_move_completed', ['move_completed']),
        ('move_completed', ['move_completed_path']),  # nested
        ('auto_add', ['auto_add_trackers']),
    ]

    def __init__(self):
        pass

    def show(self, label):
        self.label = label
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('label_options.ui'))
        self.dialog = self.builder.get_object('dlg_label_options')
        self.dialog.set_transient_for(component.get('MainWindow').window)
        self.builder.connect_signals(self)
        # Show the label name in the header label
        self.builder.get_object('label_header').set_markup(
            '<b>%s:</b> %s' % (_('Label Options'), self.label)
        )

        for chk_id, group in self.sensitive_groups:
            chk = self.builder.get_object(chk_id)
            chk.connect('toggled', self.apply_sensitivity)

        client.label.get_options(self.label).addCallback(self.load_options)

        self.dialog.run()

    def load_options(self, options):
        log.debug(list(options))

        for spin_id in self.spin_ids + self.spin_int_ids:
            self.builder.get_object(spin_id).set_value(options[spin_id])
        for chk_id in self.chk_ids:
            self.builder.get_object(chk_id).set_active(bool(options[chk_id]))

        if client.is_localhost():
            self.builder.get_object('move_completed_path').set_filename(
                options['move_completed_path']
            )
            self.builder.get_object('move_completed_path').show()
            self.builder.get_object('move_completed_path_entry').hide()
        else:
            self.builder.get_object('move_completed_path_entry').set_text(
                options['move_completed_path']
            )
            self.builder.get_object('move_completed_path_entry').show()
            self.builder.get_object('move_completed_path').hide()

        self.builder.get_object('auto_add_trackers').get_buffer().set_text(
            '\n'.join(options['auto_add_trackers'])
        )

        self.apply_sensitivity()

    def on_options_ok(self, event=None):
        """Save options."""
        options = {}

        for spin_id in self.spin_ids:
            options[spin_id] = self.builder.get_object(spin_id).get_value()
        for spin_int_id in self.spin_int_ids:
            options[spin_int_id] = self.builder.get_object(
                spin_int_id
            ).get_value_as_int()
        for chk_id in self.chk_ids:
            options[chk_id] = self.builder.get_object(chk_id).get_active()

        if client.is_localhost():
            options['move_completed_path'] = self.builder.get_object(
                'move_completed_path'
            ).get_filename()
        else:
            options['move_completed_path'] = self.builder.get_object(
                'move_completed_path_entry'
            ).get_text()

        buff = self.builder.get_object(
            'auto_add_trackers'
        ).get_buffer()  # sometimes I hate gtk...
        tracker_lst = (
            buff.get_text(
                buff.get_start_iter(), buff.get_end_iter(), include_hidden_chars=False
            )
            .strip()
            .split('\n')
        )
        options['auto_add_trackers'] = [
            x for x in tracker_lst if x
        ]  # filter out empty lines.

        log.debug(options)
        client.label.set_options(self.label, options)
        self.dialog.destroy()

    def apply_sensitivity(self, event=None):
        for chk_id, sensitive_list in self.sensitive_groups:
            chk = self.builder.get_object(chk_id)
            sens = chk.get_active() and chk.get_property('sensitive')
            for widget_id in sensitive_list:
                self.builder.get_object(widget_id).set_sensitive(sens)

    def on_options_cancel(self, event=None):
        self.dialog.destroy()
