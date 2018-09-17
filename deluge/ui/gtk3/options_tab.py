# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#               2017 Calum Lind <calumlind+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from gi.repository.Gdk import keyval_name

import deluge.component as component
from deluge.ui.client import client

from .path_chooser import PathChooser
from .torrentdetails import Tab


class OptionsTab(Tab):
    def __init__(self):
        super(OptionsTab, self).__init__('Options', 'options_tab', 'options_tab_label')

        self.prev_torrent_ids = None
        self.prev_status = None
        self.inconsistent_keys = []

        # Create TabWidget items with widget id, get/set func name, status key.
        self.add_tab_widget('spin_max_download', 'value', ['max_download_speed'])
        self.add_tab_widget('spin_max_upload', 'value', ['max_upload_speed'])
        self.add_tab_widget('spin_max_connections', 'value_as_int', ['max_connections'])
        self.add_tab_widget(
            'spin_max_upload_slots', 'value_as_int', ['max_upload_slots']
        )
        self.add_tab_widget(
            'chk_prioritize_first_last', 'active', ['prioritize_first_last_pieces']
        )
        self.add_tab_widget(
            'chk_sequential_download', 'active', ['sequential_download']
        )
        self.add_tab_widget('chk_auto_managed', 'active', ['auto_managed'])
        self.add_tab_widget('chk_stop_at_ratio', 'active', ['stop_at_ratio'])
        self.add_tab_widget('chk_remove_at_ratio', 'active', ['remove_at_ratio'])
        self.add_tab_widget('spin_stop_ratio', 'value', ['stop_ratio'])
        self.add_tab_widget('chk_move_completed', 'active', ['move_completed'])
        self.add_tab_widget('chk_shared', 'active', ['shared'])
        self.add_tab_widget('summary_owner', 'text', ['owner'])
        self.add_tab_widget('chk_super_seeding', 'active', ['super_seeding'])

        # Connect key press event for spin widgets.
        for widget_id in self.tab_widgets:
            if widget_id.startswith('spin_'):
                self.tab_widgets[widget_id].obj.connect(
                    'key-press-event', self.on_key_press_event
                )

        self.button_apply = self.main_builder.get_object('button_apply')

        self.move_completed_path_chooser = PathChooser(
            'move_completed_paths_list', parent=component.get('MainWindow').window
        )
        self.move_completed_path_chooser.set_sensitive(
            self.tab_widgets['chk_move_completed'].obj.get_active()
        )
        self.move_completed_path_chooser.connect(
            'text-changed', self.on_path_chooser_text_changed_event
        )
        self.status_keys.append('move_completed_path')

        self.move_completed_hbox = self.main_builder.get_object(
            'hbox_move_completed_path_chooser'
        )
        self.move_completed_hbox.add(self.move_completed_path_chooser)
        self.move_completed_hbox.show_all()

        component.get('MainWindow').connect_signals(self)

    def start(self):
        pass

    def stop(self):
        pass

    def clear(self):
        self.prev_torrent_ids = None
        self.prev_status = None
        self.inconsistent_keys = []

    def update(self):
        torrent_ids = component.get('TorrentView').get_selected_torrents()

        # Set True if torrent(s) selected in torrentview, else False.
        self._child_widget.set_sensitive(bool(torrent_ids))

        if torrent_ids:
            if torrent_ids != self.prev_torrent_ids:
                self.clear()

            component.get('SessionProxy').get_torrents_status(
                {'id': torrent_ids}, self.status_keys
            ).addCallback(self.parse_torrents_statuses)

            self.prev_torrent_ids = torrent_ids

    def parse_torrents_statuses(self, statuses):
        """Finds common status values to all torrrents in statuses.

        Values which differ are replaced with config values.


        Args:
            statuses (dict): A status dict of {torrent_id: {key: value}}.

        Returns:
            dict: A single status dict.

        """
        status = {}
        if len(statuses) == 1:
            # A single torrent so pop torrent status.
            status = statuses.popitem()[1]
            self.button_apply.set_label('_Apply')
        else:
            for status_key in self.status_keys:
                prev_value = None
                for idx, status in enumerate(statuses.values()):
                    if idx == 0:
                        prev_value = status[status_key]
                        continue
                    elif status[status_key] != prev_value:
                        self.inconsistent_keys.append(status_key)
                        break
                status[status_key] = prev_value
            self.button_apply.set_label(_('_Apply to selected'))

        self.on_get_torrent_status(status)

    def on_get_torrent_status(self, new_status):
        # So we don't overwrite the user's unapplied changes we only
        # want to update values that have been applied in the core.
        if self.prev_status is None:
            self.prev_status = dict.fromkeys(new_status, None)

        if new_status != self.prev_status:
            for widget in self.tab_widgets.values():
                status_key = widget.status_keys[0]
                status_value = new_status[status_key]
                if status_value != self.prev_status[status_key]:
                    set_func = 'set_' + widget.func.replace('_as_int', '')
                    getattr(widget.obj, set_func)(status_value)
                    if set_func == 'set_active':
                        widget.obj.set_inconsistent(
                            status_key in self.inconsistent_keys
                        )

            if (
                new_status['move_completed_path']
                != self.prev_status['move_completed_path']
            ):
                text = new_status['move_completed_path']
                self.move_completed_path_chooser.set_text(
                    text, cursor_end=False, default_text=True
                )

            # Update sensitivity of widgets.
            self.tab_widgets['spin_stop_ratio'].obj.set_sensitive(
                new_status['stop_at_ratio']
            )
            self.tab_widgets['chk_remove_at_ratio'].obj.set_sensitive(
                new_status['stop_at_ratio']
            )

            # Ensure apply button sensitivity is set False.
            self.button_apply.set_sensitive(False)
            self.prev_status = new_status

    # === Widget signal handlers === #

    def on_button_apply_clicked(self, button):
        options = {}
        for widget in self.tab_widgets.values():
            status_key = widget.status_keys[0]
            if status_key == 'owner':
                continue  # A label so read-only
            widget_value = getattr(widget.obj, 'get_' + widget.func)()
            if widget_value != self.prev_status[status_key] or (
                status_key in self.inconsistent_keys
                and not widget.obj.get_inconsistent()
            ):
                options[status_key] = widget_value

        if options.get('move_completed', False):
            options['move_completed_path'] = self.move_completed_path_chooser.get_text()

        client.core.set_torrent_options(self.prev_torrent_ids, options)
        self.button_apply.set_sensitive(False)

    def on_chk_move_completed_toggled(self, widget):
        self.move_completed_path_chooser.set_sensitive(widget.get_active())
        self.on_chk_toggled(widget)

    def on_chk_stop_at_ratio_toggled(self, widget):
        self.tab_widgets['spin_stop_ratio'].obj.set_sensitive(widget.get_active())
        self.tab_widgets['chk_remove_at_ratio'].obj.set_sensitive(widget.get_active())
        self.on_chk_toggled(widget)

    def on_chk_toggled(self, widget):
        widget.set_inconsistent(False)
        self.button_apply.set_sensitive(True)

    def on_spin_value_changed(self, widget):
        self.button_apply.set_sensitive(True)

    def on_key_press_event(self, widget, event):
        keyname = keyval_name(event.keyval).lstrip('KP_').lower()
        if keyname.isdigit() or keyname in ['period', 'minus', 'delete', 'backspace']:
            self.button_apply.set_sensitive(True)

    def on_path_chooser_text_changed_event(self, widget, path):
        self.button_apply.set_sensitive(True)
