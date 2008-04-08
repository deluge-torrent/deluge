#
# options_tab.py
#
# Copyright (C) 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
# 	Boston, MA    02110-1301, USA.
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

import deluge.component as component
from deluge.ui.client import aclient as client

class OptionsTab:
    def __init__(self):
        glade = component.get("MainWindow").get_glade()
        self.spin_max_download = glade.get_widget("spin_max_download")
        self.spin_max_upload = glade.get_widget("spin_max_upload")
        self.spin_max_connections = glade.get_widget("spin_max_connections")
        self.spin_max_upload_slots = glade.get_widget("spin_max_upload_slots")
        self.chk_private = glade.get_widget("chk_private")
        self.chk_prioritize_first_last = glade.get_widget("chk_prioritize_first_last")
        
        self.prev_torrent_id = None
        self.prev_status = None
        
        glade.signal_autoconnect({
            "on_button_apply_clicked": self._on_button_apply_clicked,
            "on_button_edit_trackers_clicked": self._on_button_edit_trackers_clicked
        })
        
    def update(self):
        # Get the first selected torrent
        torrent_id = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(torrent_id) != 0:
            torrent_id = torrent_id[0]
        else:
            # No torrent is selected in the torrentview
            return
        
        if torrent_id != self.prev_torrent_id:
            self.prev_status = None

        client.get_torrent_status(self._on_get_torrent_status, torrent_id,
            ["max_download_speed",
            "max_upload_speed",
            "max_connections",
            "max_upload_slots",
            "private",
            "prioritize_first_last"])
        self.prev_torrent_id = torrent_id

    def clear(self):
        pass
            
    def _on_get_torrent_status(self, status):
        # We only want to update values that have been applied in the core.  This
        # is so we don't overwrite the user changes that haven't been applied yet.
        if self.prev_status == None:
            self.prev_status = {}.fromkeys(status.keys(), None)
            
        if status != self.prev_status and status.keys() == self.prev_status.keys():
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
            self.prev_status = status
        
    def _on_button_apply_clicked(self, button):
        if self.spin_max_download.get_value() != self.prev_status["max_download_speed"]:
            client.set_torrent_max_download_speed(self.prev_torrent_id, self.spin_max_download.get_value())
        if self.spin_max_upload.get_value() != self.prev_status["max_upload_speed"]:
            client.set_torrent_max_upload_speed(self.prev_torrent_id, self.spin_max_upload.get_value())
        if self.spin_max_connections.get_value_as_int() != self.prev_status["max_connections"]:
            client.set_torrent_max_connections(self.prev_torrent_id, self.spin_max_connections.get_value_as_int())
        if self.spin_max_upload_slots.get_value_as_int() != self.prev_status["max_upload_slots"]:
            client.set_torrent_max_upload_slots(self.prev_torrent_id, self.spin_max_upload_slots.get_value_as_int())
        if self.chk_private.get_active() != self.prev_status["private"]:
            client.set_torrent_private_flag(self.prev_torrent_id, self.chk_private.get_active())
        if self.chk_prioritize_first_last.get_active() != self.prev_status["prioritize_first_last"]:
            client.set_torrent_prioritize_first_last(self.prev_torrent_id, self.chk_prioritize_first_last.get_active())
            
    def _on_button_edit_trackers_clicked(self, button):
        from edittrackersdialog import EditTrackersDialog
        dialog = EditTrackersDialog(
            self.prev_torrent_id,
            component.get("MainWindow").window)
        dialog.run()
