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

from gtk.gdk import keyval_name

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.gtkui.path_chooser import PathChooser
from deluge.ui.gtkui.torrentdetails import Tab


class OptionsTab(Tab):
    def __init__(self):
        super(OptionsTab, self).__init__('Options', 'options_tab', 'options_tab_label')

        self.prev_torrent_id = None
        self.prev_status = None

        # Create TabWidget items with widget id, get/set func name, status key.
        self.add_tab_widget('spin_max_download', 'value', ['max_download_speed'])
        self.add_tab_widget('spin_max_upload', 'value', ['max_upload_speed'])
        self.add_tab_widget('spin_max_connections', 'value_as_int', ['max_connections'])
        self.add_tab_widget('spin_max_upload_slots', 'value_as_int', ['max_upload_slots'])
        self.add_tab_widget('chk_prioritize_first_last', 'active', ['prioritize_first_last_pieces'])
        self.add_tab_widget('chk_sequential_download', 'active', ['sequential_download'])
        self.add_tab_widget('chk_auto_managed', 'active', ['is_auto_managed'])
        self.add_tab_widget('chk_stop_at_ratio', 'active', ['stop_at_ratio'])
        self.add_tab_widget('chk_remove_at_ratio', 'active', ['remove_at_ratio'])
        self.add_tab_widget('spin_stop_ratio', 'value', ['stop_ratio'])
        self.add_tab_widget('chk_move_completed', 'active', ['move_completed'])
        self.add_tab_widget('chk_shared', 'active', ['shared'])
        self.add_tab_widget('summary_owner', 'text', ['owner'])

        # Connect key press event for spin widgets.
        for widget_id in self.tab_widgets:
            if widget_id.startswith('spin_'):
                self.tab_widgets[widget_id].obj.connect('key-press-event', self.on_key_press_event)

        self.button_apply = self.main_builder.get_object('button_apply')

        self.move_completed_path_chooser = PathChooser('move_completed_paths_list')
        self.move_completed_path_chooser.set_sensitive(
            self.tab_widgets['chk_move_completed'].obj.get_active())
        self.move_completed_path_chooser.connect(
            'text-changed', self.on_path_chooser_text_changed_event)
        self.status_keys.append('move_completed_path')

        self.move_completed_hbox = self.main_builder.get_object('hbox_move_completed_path_chooser')
        self.move_completed_hbox.add(self.move_completed_path_chooser)
        self.move_completed_hbox.show_all()

        component.get('MainWindow').connect_signals(self)

    def start(self):
        pass

    def stop(self):
        pass

    def update(self):
        # Get the first selected torrent
        torrent_ids = component.get('TorrentView').get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if torrent_ids:
            torrent_id = torrent_ids[0]
            self._child_widget.set_sensitive(True)
        else:
            # No torrent is selected in the torrentview
            self._child_widget.set_sensitive(False)
            return

        if torrent_id != self.prev_torrent_id:
            self.prev_status = None

        component.get('SessionProxy').get_torrent_status(
            torrent_id, self.status_keys
            ).addCallback(self.on_get_torrent_status)

        self.prev_torrent_id = torrent_id

    def clear(self):
        self.prev_torrent_id = None
        self.prev_status = None

    def on_get_torrent_status(self, status):
        # So we don't overwrite the user's unapplied changes we only
        # want to update values that have been applied in the core.
        if self.prev_status is None:
            self.prev_status = dict.fromkeys(status, None)

        if status != self.prev_status:
            for widget in self.tab_widgets.values():
                status_key = widget.status_keys[0]
                if status[status_key] != self.prev_status[status_key]:
                    set_func = 'set_' + widget.func.replace('_as_int', '')
                    getattr(widget.obj, set_func)(status[status_key])

            if status['move_completed_path'] != self.prev_status['move_completed_path']:
                self.move_completed_path_chooser.set_text(
                    status['move_completed_path'], cursor_end=False, default_text=True)

            # Update sensitivity of widgets.
            self.tab_widgets['spin_stop_ratio'].obj.set_sensitive(status['stop_at_ratio'])
            self.tab_widgets['chk_remove_at_ratio'].obj.set_sensitive(status['stop_at_ratio'])

            # Ensure apply button sensitivity is set False.
            self.button_apply.set_sensitive(False)
            self.prev_status = status

    def on_button_apply_clicked(self, button):
        options = {}
        for widget in self.tab_widgets.values():
            status_key = widget.status_keys[0]
            if status_key == 'owner':
                continue  # A label so read-only
            widget_value = getattr(widget.obj, 'get_' + widget.func)()
            if widget_value != self.prev_status[status_key]:
                options[status_key] = widget_value

        if options.get('move_completed', False):
            options['move_completed_path'] = self.move_completed_path_chooser.get_text()

        client.core.set_torrent_options([self.prev_torrent_id], options)
        self.button_apply.set_sensitive(False)

    def on_chk_move_completed_toggled(self, widget):
        self.move_completed_path_chooser.set_sensitive(widget.get_active())
        self.button_apply.set_sensitive(True)

    def on_chk_stop_at_ratio_toggled(self, widget):
        is_active = widget.get_active()
        self.tab_widgets['spin_stop_ratio'].obj.set_sensitive(is_active)
        self.tab_widgets['chk_remove_at_ratio'].obj.set_sensitive(is_active)
        self.button_apply.set_sensitive(True)

    def on_chk_toggled(self, widget):
        self.button_apply.set_sensitive(True)

    def on_spin_value_changed(self, widget):
        self.button_apply.set_sensitive(True)

    def on_key_press_event(self, widget, event):
        keyname = keyval_name(event.keyval).lstrip('KP_').lower()
        if keyname.isdigit() or keyname in ['period', 'minus', 'delete', 'backspace']:
            self.button_apply.set_sensitive(True)

    def on_path_chooser_text_changed_event(self, widget, path):
        self.button_apply.set_sensitive(True)
