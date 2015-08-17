# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.gtkui.path_chooser import PathChooser
from deluge.ui.gtkui.torrentdetails import Tab
from gi.repository import Gdk


class OptionsTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        builder = component.get("MainWindow").get_builder()

        self._name = "Options"
        self._child_widget = builder.get_object("options_tab")
        self._tab_label = builder.get_object("options_tab_label")

        self.spin_max_download = builder.get_object("spin_max_download")
        self.spin_max_upload = builder.get_object("spin_max_upload")
        self.spin_max_connections = builder.get_object("spin_max_connections")
        self.spin_max_upload_slots = builder.get_object("spin_max_upload_slots")
        self.chk_prioritize_first_last = builder.get_object("chk_prioritize_first_last")
        self.chk_sequential_download = builder.get_object("chk_sequential_download")
        self.chk_auto_managed = builder.get_object("chk_auto_managed")
        self.chk_stop_at_ratio = builder.get_object("chk_stop_at_ratio")
        self.chk_remove_at_ratio = builder.get_object("chk_remove_at_ratio")
        self.spin_stop_ratio = builder.get_object("spin_stop_ratio")
        self.chk_move_completed = builder.get_object("chk_move_completed")
        self.entry_move_completed = builder.get_object("entry_move_completed")
        self.chk_shared = builder.get_object("chk_shared")
        self.button_apply = builder.get_object("button_apply")

        self.move_completed_hbox = builder.get_object("hbox_move_completed_path_chooser")
        self.move_completed_path_chooser = PathChooser("move_completed_paths_list")
        self.move_completed_path_chooser.set_sensitive(self.chk_move_completed.get_active())
        self.move_completed_hbox.add(self.move_completed_path_chooser)
        self.move_completed_hbox.show_all()
        self.move_completed_path_chooser.connect("text-changed", self._on_path_chooser_text_changed_event)

        self.prev_torrent_id = None
        self.prev_status = None

        component.get("MainWindow").connect_signals({
            "on_button_apply_clicked": self._on_button_apply_clicked,
            "on_chk_move_completed_toggled": self._on_chk_move_completed_toggled,
            "on_chk_stop_at_ratio_toggled": self._on_chk_stop_at_ratio_toggled,
            "on_chk_toggled": self._on_chk_toggled,
            "on_spin_value_changed": self._on_spin_value_changed,
            "on_move_completed_file_set": self._on_move_completed_file_set
        })

        self.spin_max_download.connect("key-press-event", self._on_key_press_event)
        self.spin_max_upload.connect("key-press-event", self._on_key_press_event)
        self.spin_max_connections.connect("key-press-event", self._on_key_press_event)
        self.spin_max_upload_slots.connect("key-press-event", self._on_key_press_event)
        self.spin_stop_ratio.connect("key-press-event", self._on_key_press_event)

    def start(self):
        pass

    def stop(self):
        pass

    def update(self):
        # Get the first selected torrent
        torrent_id = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if torrent_id:
            torrent_id = torrent_id[0]
            self._child_widget.set_sensitive(True)
        else:
            # No torrent is selected in the torrentview
            self._child_widget.set_sensitive(False)
            return

        if torrent_id != self.prev_torrent_id:
            self.prev_status = None

        component.get("SessionProxy").get_torrent_status(torrent_id, [
            "max_download_speed",
            "max_upload_speed",
            "max_connections",
            "max_upload_slots",
            "prioritize_first_last",
            "is_auto_managed",
            "stop_at_ratio",
            "stop_ratio",
            "remove_at_ratio",
            "storage_mode",
            "sequential_download",
            "move_on_completed",
            "move_on_completed_path",
            "shared"
        ]).addCallback(self._on_get_torrent_status)
        self.prev_torrent_id = torrent_id

    def clear(self):
        self.prev_torrent_id = None
        self.prev_status = None

    def _on_get_torrent_status(self, status):
        # We only want to update values that have been applied in the core.  This
        # is so we don't overwrite the user changes that haven't been applied yet.
        if self.prev_status is None:
            self.prev_status = {}.fromkeys(status.keys(), None)

        if status != self.prev_status:
            if status["max_download_speed"] != self.prev_status["max_download_speed"]:
                self.spin_max_download.set_value(status["max_download_speed"])
            if status["max_upload_speed"] != self.prev_status["max_upload_speed"]:
                self.spin_max_upload.set_value(status["max_upload_speed"])
            if status["max_connections"] != self.prev_status["max_connections"]:
                self.spin_max_connections.set_value(status["max_connections"])
            if status["max_upload_slots"] != self.prev_status["max_upload_slots"]:
                self.spin_max_upload_slots.set_value(status["max_upload_slots"])
            if status["prioritize_first_last"] != self.prev_status["prioritize_first_last"]:
                self.chk_prioritize_first_last.set_active(status["prioritize_first_last"])
            if status["is_auto_managed"] != self.prev_status["is_auto_managed"]:
                self.chk_auto_managed.set_active(status["is_auto_managed"])
            if status["stop_at_ratio"] != self.prev_status["stop_at_ratio"]:
                self.chk_stop_at_ratio.set_active(status["stop_at_ratio"])
                self.spin_stop_ratio.set_sensitive(status["stop_at_ratio"])
                self.chk_remove_at_ratio.set_sensitive(status["stop_at_ratio"])
            if status["stop_ratio"] != self.prev_status["stop_ratio"]:
                self.spin_stop_ratio.set_value(status["stop_ratio"])
            if status["remove_at_ratio"] != self.prev_status["remove_at_ratio"]:
                self.chk_remove_at_ratio.set_active(status["remove_at_ratio"])
            if status["move_on_completed"] != self.prev_status["move_on_completed"]:
                self.chk_move_completed.set_active(status["move_on_completed"])
            if status["move_on_completed_path"] != self.prev_status["move_on_completed_path"]:
                self.move_completed_path_chooser.set_text(status["move_on_completed_path"],
                                                          cursor_end=False, default_text=True)
            if status["shared"] != self.prev_status["shared"]:
                self.chk_shared.set_active(status["shared"])

            if status["storage_mode"] == "compact":
                self.chk_prioritize_first_last.set_sensitive(False)
                if self.chk_sequential_download.get_property("visible"):
                    self.chk_prioritize_first_last.hide()
                self.chk_sequential_download.set_sensitive(False)
                if self.chk_sequential_download.get_property("visible"):
                    self.chk_sequential_download.hide()
            else:
                if status["prioritize_first_last"] != self.prev_status["prioritize_first_last"]:
                    self.chk_prioritize_first_last.set_active(status["prioritize_first_last"])
                    if not self.chk_prioritize_first_last.get_property("visible"):
                        self.chk_prioritize_first_last.show()
                if status["sequential_download"] != self.prev_status["sequential_download"]:
                    self.chk_sequential_download.set_active(status["sequential_download"])
                    if not self.chk_sequential_download.get_property("visible"):
                        self.chk_sequential_download.show()

            if self.button_apply.is_sensitive():
                self.button_apply.set_sensitive(False)

            self.prev_status = status

    def _on_button_apply_clicked(self, button):
        if self.spin_max_download.get_value() != self.prev_status["max_download_speed"]:
            client.core.set_torrent_max_download_speed(
                self.prev_torrent_id, self.spin_max_download.get_value()
            )
        if self.spin_max_upload.get_value() != self.prev_status["max_upload_speed"]:
            client.core.set_torrent_max_upload_speed(
                self.prev_torrent_id, self.spin_max_upload.get_value()
            )
        if self.spin_max_connections.get_value_as_int() != self.prev_status["max_connections"]:
            client.core.set_torrent_max_connections(
                self.prev_torrent_id, self.spin_max_connections.get_value_as_int()
            )
        if self.spin_max_upload_slots.get_value_as_int() != self.prev_status["max_upload_slots"]:
            client.core.set_torrent_max_upload_slots(
                self.prev_torrent_id, self.spin_max_upload_slots.get_value_as_int()
            )
        if self.chk_prioritize_first_last.get_active() != \
            self.prev_status["prioritize_first_last"] and \
                not self.prev_status["storage_mode"] == "compact":
            client.core.set_torrent_prioritize_first_last(
                self.prev_torrent_id, self.chk_prioritize_first_last.get_active()
            )
        if self.chk_sequential_download.get_active() != \
            self.prev_status["sequential_download"] and \
                not self.prev_status["storage_mode"] == "compact":
            client.core.set_torrent_sequential_download(
                self.prev_torrent_id, self.chk_prioritize_first_last.get_active()
            )
        if self.chk_auto_managed.get_active() != self.prev_status["is_auto_managed"]:
            client.core.set_torrent_auto_managed(
                self.prev_torrent_id, self.chk_auto_managed.get_active()
            )
        if self.chk_stop_at_ratio.get_active() != self.prev_status["stop_at_ratio"]:
            client.core.set_torrent_stop_at_ratio(
                self.prev_torrent_id, self.chk_stop_at_ratio.get_active()
            )
        if self.spin_stop_ratio.get_value() != self.prev_status["stop_ratio"]:
            client.core.set_torrent_stop_ratio(
                self.prev_torrent_id, self.spin_stop_ratio.get_value()
            )
        if self.chk_remove_at_ratio.get_active() != self.prev_status["remove_at_ratio"]:
            client.core.set_torrent_remove_at_ratio(
                self.prev_torrent_id, self.chk_remove_at_ratio.get_active()
            )
        if self.chk_move_completed.get_active() != self.prev_status["move_on_completed"]:
            client.core.set_torrent_move_completed(
                self.prev_torrent_id, self.chk_move_completed.get_active()
            )
        if self.chk_move_completed.get_active():
            path = self.move_completed_path_chooser.get_text()
            client.core.set_torrent_move_completed_path(self.prev_torrent_id, path)
        if self.chk_shared.get_active() != self.prev_status["shared"]:
            client.core.set_torrents_shared(
                self.prev_torrent_id, self.chk_shared.get_active()
            )
        self.button_apply.set_sensitive(False)

    def _on_chk_move_completed_toggled(self, widget):
        value = self.chk_move_completed.get_active()
        self.move_completed_path_chooser.set_sensitive(value)
        if not self.button_apply.is_sensitive():
            self.button_apply.set_sensitive(True)

    def _on_chk_stop_at_ratio_toggled(self, widget):
        value = widget.get_active()

        self.spin_stop_ratio.set_sensitive(value)
        self.chk_remove_at_ratio.set_sensitive(value)

        if not self.button_apply.is_sensitive():
            self.button_apply.set_sensitive(True)

    def _on_chk_toggled(self, widget):
        if not self.button_apply.is_sensitive():
            self.button_apply.set_sensitive(True)

    def _on_spin_value_changed(self, widget):
        if not self.button_apply.is_sensitive():
            self.button_apply.set_sensitive(True)

    def _on_key_press_event(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval).lstrip("KP_").lower()
        if keyname.isdigit() or keyname in ["period", "minus", "delete", "backspace"]:
            if not self.button_apply.is_sensitive():
                self.button_apply.set_sensitive(True)

    def _on_move_completed_file_set(self, widget):
        if not self.button_apply.is_sensitive():
            self.button_apply.set_sensitive(True)

    def _on_entry_move_completed_changed(self, widget):
        if not self.button_apply.is_sensitive():
            self.button_apply.set_sensitive(True)

    def _on_path_chooser_text_changed_event(self, widget, path):
        self.button_apply.set_sensitive(True)
