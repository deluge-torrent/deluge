#
# options_tab.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
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


import deluge.component as component
from deluge.ui.client import client
from deluge.ui.gtkui.torrentdetails import Tab

class OptionsTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        glade = component.get("MainWindow").get_glade()

        self._name = "Options"
        self._child_widget = glade.get_widget("options_tab")
        self._tab_label = glade.get_widget("options_tab_label")

        self.spin_max_download = glade.get_widget("spin_max_download")
        self.spin_max_upload = glade.get_widget("spin_max_upload")
        self.spin_max_connections = glade.get_widget("spin_max_connections")
        self.spin_max_upload_slots = glade.get_widget("spin_max_upload_slots")
        self.chk_private = glade.get_widget("chk_private")
        self.chk_prioritize_first_last = glade.get_widget("chk_prioritize_first_last")
        self.chk_auto_managed = glade.get_widget("chk_auto_managed")
        self.chk_stop_at_ratio = glade.get_widget("chk_stop_at_ratio")
        self.chk_remove_at_ratio = glade.get_widget("chk_remove_at_ratio")
        self.spin_stop_ratio = glade.get_widget("spin_stop_ratio")
        self.chk_move_completed = glade.get_widget("chk_move_completed")
        self.filechooser_move_completed = glade.get_widget("filechooser_move_completed")
        self.entry_move_completed = glade.get_widget("entry_move_completed")

        self.prev_torrent_id = None
        self.prev_status = None

        glade.signal_autoconnect({
            "on_button_apply_clicked": self._on_button_apply_clicked,
            "on_button_edit_trackers_clicked": self._on_button_edit_trackers_clicked,
            "on_chk_move_completed_toggled": self._on_chk_move_completed_toggled,
            "on_chk_stop_at_ratio_toggled": self._on_chk_stop_at_ratio_toggled
        })

    def start(self):
        if client.is_localhost():
            self.filechooser_move_completed.show()
            self.entry_move_completed.hide()
        else:
            self.filechooser_move_completed.hide()
            self.entry_move_completed.show()

    def stop(self):
        pass

    def update(self):
        # Get the first selected torrent
        torrent_id = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(torrent_id) != 0:
            torrent_id = torrent_id[0]
            self._child_widget.set_sensitive(True)
        else:
            # No torrent is selected in the torrentview
            self._child_widget.set_sensitive(False)
            return

        if torrent_id != self.prev_torrent_id:
            self.prev_status = None

        component.get("SessionProxy").get_torrent_status(torrent_id,
            ["max_download_speed",
            "max_upload_speed",
            "max_connections",
            "max_upload_slots",
            "private",
            "prioritize_first_last",
            "is_auto_managed",
            "stop_at_ratio",
            "stop_ratio",
            "remove_at_ratio",
            "move_on_completed",
            "move_on_completed_path"]).addCallback(self._on_get_torrent_status)
        self.prev_torrent_id = torrent_id

    def clear(self):
        self.prev_torrent_id = None
        self.prev_status = None

    def _on_get_torrent_status(self, status):
        # We only want to update values that have been applied in the core.  This
        # is so we don't overwrite the user changes that haven't been applied yet.
        if self.prev_status == None:
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
            if status["private"] != self.prev_status["private"]:
                self.chk_private.set_active(status["private"])
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
                if client.is_localhost():
                    self.filechooser_move_completed.unselect_all()
                    self.filechooser_move_completed.set_current_folder(status["move_on_completed_path"])
                else:
                    self.entry_move_completed.set_text(status["move_on_completed_path"])

            self.prev_status = status

    def _on_button_apply_clicked(self, button):
        if self.spin_max_download.get_value() != self.prev_status["max_download_speed"]:
            client.core.set_torrent_max_download_speed(self.prev_torrent_id, self.spin_max_download.get_value())
        if self.spin_max_upload.get_value() != self.prev_status["max_upload_speed"]:
            client.core.set_torrent_max_upload_speed(self.prev_torrent_id, self.spin_max_upload.get_value())
        if self.spin_max_connections.get_value_as_int() != self.prev_status["max_connections"]:
            client.core.set_torrent_max_connections(self.prev_torrent_id, self.spin_max_connections.get_value_as_int())
        if self.spin_max_upload_slots.get_value_as_int() != self.prev_status["max_upload_slots"]:
            client.core.set_torrent_max_upload_slots(self.prev_torrent_id, self.spin_max_upload_slots.get_value_as_int())
        if self.chk_prioritize_first_last.get_active() != self.prev_status["prioritize_first_last"]:
            client.core.set_torrent_prioritize_first_last(self.prev_torrent_id, self.chk_prioritize_first_last.get_active())
        if self.chk_auto_managed.get_active() != self.prev_status["is_auto_managed"]:
            client.core.set_torrent_auto_managed(self.prev_torrent_id, self.chk_auto_managed.get_active())
        if self.chk_stop_at_ratio.get_active() != self.prev_status["stop_at_ratio"]:
            client.core.set_torrent_stop_at_ratio(self.prev_torrent_id, self.chk_stop_at_ratio.get_active())
        if self.spin_stop_ratio.get_value() != self.prev_status["stop_ratio"]:
            client.core.set_torrent_stop_ratio(self.prev_torrent_id, self.spin_stop_ratio.get_value())
        if self.chk_remove_at_ratio.get_active() != self.prev_status["remove_at_ratio"]:
            client.core.set_torrent_remove_at_ratio(self.prev_torrent_id, self.chk_remove_at_ratio.get_active())
        if self.chk_move_completed.get_active() != self.prev_status["move_on_completed"]:
            client.core.set_torrent_move_completed(self.prev_torrent_id, self.chk_move_completed.get_active())
        if self.chk_move_completed.get_active():
            if client.is_localhost():
                path = self.filechooser_move_completed.get_filename()
            else:
                path = self.entry_move_completed.get_text()
            client.core.set_torrent_move_completed_path(self.prev_torrent_id, path)


    def _on_button_edit_trackers_clicked(self, button):
        from edittrackersdialog import EditTrackersDialog
        dialog = EditTrackersDialog(
            self.prev_torrent_id,
            component.get("MainWindow").window)
        dialog.run()

    def _on_chk_move_completed_toggled(self, widget):
        value = self.chk_move_completed.get_active()
        if client.is_localhost():
            widget = self.filechooser_move_completed
        else:
            widget = self.entry_move_completed

        widget.set_sensitive(value)

    def _on_chk_stop_at_ratio_toggled(self, widget):
        value = widget.get_active()

        self.spin_stop_ratio.set_sensitive(value)
        self.chk_remove_at_ratio.set_sensitive(value)
