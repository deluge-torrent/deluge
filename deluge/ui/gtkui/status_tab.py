# -*- coding: utf-8 -*-
#
# status_tab.py
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

import logging

import deluge.component as component
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.torrentdetails import Tab
from deluge.ui.gtkui.piecesbar import PiecesBar

log = logging.getLogger(__name__)

def fpeer_sized(first, second):
    return "%s (%s)" % (deluge.common.fsize(first), deluge.common.fsize(second))

def fpeer_size_second(first, second):
    return "%s (%s)" % (first, deluge.common.fsize(second))

def fratio(value):
    if value < 0:
        return "∞"
    return "%.3f" % value

def fpcnt(value):
    return "%.2f%%" % value

def fspeed(value, max_value=-1):
    if max_value > -1:
        return "%s (%s %s)" % (deluge.common.fspeed(value), max_value, _("KiB/s"))
    else:
        return deluge.common.fspeed(value)

def fdate_or_never(value):
    """Display value as date, eg 05/05/08 or Never"""
    if value > 0.0:
        return deluge.common.fdate(value)
    else:
        return "Never"

class StatusTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        # Get the labels we need to update.
        # widget name, modifier function, status keys
        self.builder = builder = component.get("MainWindow").get_builder()
        self.progressbar = builder.get_object("progressbar")

        self._name = "Status"
        self._child_widget = builder.get_object("status_tab")
        self._tab_label = builder.get_object("status_tab_label")
        self.config = ConfigManager("gtkui.conf")
        self.config.register_set_function(
            "show_piecesbar",
            self.on_show_pieces_bar_config_changed,
            apply_now=True
        )
        self.label_widgets = [
            (builder.get_object("summary_pieces"), fpeer_size_second, ("num_pieces", "piece_length")),
            (builder.get_object("summary_availability"), fratio, ("distributed_copies",)),
            (builder.get_object("summary_total_downloaded"), fpeer_sized, ("all_time_download", "total_payload_download")),
            (builder.get_object("summary_total_uploaded"), fpeer_sized, ("total_uploaded", "total_payload_upload")),
            (builder.get_object("summary_download_speed"), fspeed, ("download_payload_rate", "max_download_speed")),
            (builder.get_object("summary_upload_speed"), fspeed, ("upload_payload_rate", "max_upload_speed")),
            (builder.get_object("summary_seeders"), deluge.common.fpeer, ("num_seeds", "total_seeds")),
            (builder.get_object("summary_peers"), deluge.common.fpeer, ("num_peers", "total_peers")),
            (builder.get_object("summary_eta"), deluge.common.ftime, ("eta",)),
            (builder.get_object("summary_share_ratio"), fratio, ("ratio",)),
            (builder.get_object("summary_tracker_status"), None, ("tracker_status",)),
            (builder.get_object("summary_next_announce"), deluge.common.ftime, ("next_announce",)),
            (builder.get_object("summary_active_time"), deluge.common.ftime, ("active_time",)),
            (builder.get_object("summary_seed_time"), deluge.common.ftime, ("seeding_time",)),
            (builder.get_object("summary_seed_rank"), str, ("seed_rank",)),
            (builder.get_object("summary_auto_managed"), str, ("is_auto_managed",)),
            (builder.get_object("progressbar"), fpcnt, ("progress",)),
            (builder.get_object("summary_date_added"), deluge.common.fdate, ("time_added",)),
            (builder.get_object("summary_last_seen_complete"), fdate_or_never, ("last_seen_complete",)),
        ]

    def update(self):
        # Get the first selected torrent
        selected = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(selected) != 0:
            selected = selected[0]
        else:
            # No torrent is selected in the torrentview
            return

        # Get the torrent status
        status_keys = ["progress", "num_pieces", "piece_length",
            "distributed_copies", "all_time_download", "total_payload_download",
            "total_uploaded", "total_payload_upload", "download_payload_rate",
            "upload_payload_rate", "num_peers", "num_seeds", "total_peers",
            "total_seeds", "eta", "ratio", "next_announce",
            "tracker_status", "max_connections", "max_upload_slots",
            "max_upload_speed", "max_download_speed", "active_time",
            "seeding_time", "seed_rank", "is_auto_managed", "time_added", "last_seen_complete"]
        if self.config['show_piecesbar']:
            status_keys.extend(["pieces", "state"])


        component.get("SessionProxy").get_torrent_status(
            selected, status_keys).addCallback(self._on_get_torrent_status)

    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if status is None:
            return

        if status["is_auto_managed"]:
            status["is_auto_managed"]=_("On")
        else:
            status["is_auto_managed"]=_("Off")

        translate_tracker_status = {
            "Error" : _("Error"),
            "Warning" : _("Warning"),
            "Announce OK" : _("Announce OK"),
            "Announce Sent" : _("Announce Sent")
        }
        for key, value in translate_tracker_status.iteritems():
            if key in status["tracker_status"]:
                status["tracker_status"] = status["tracker_status"].replace(key, value, 1)
                break

        # Update all the label widgets
        for widget in self.label_widgets:
            if widget[1] != None:
                args = []
                try:
                    for key in widget[2]:
                        args.append(status[key])
                except Exception, e:
                    log.debug("Unable to get status value: %s", e)
                    continue

                txt = widget[1](*args)
            else:
                txt = status[widget[2][0]]

            if widget[0].get_text() != txt:
                widget[0].set_text(txt)

        # Do the progress bar because it's a special case (not a label)
        if self.config['show_piecesbar']:
            self.piecesbar.update_from_status(status)
        else:
            fraction = status["progress"] / 100
            if self.progressbar.get_fraction() != fraction:
                self.progressbar.set_fraction(fraction)

    def on_show_pieces_bar_config_changed(self, key, show):
        self.show_pieces_bar(show)

    def show_pieces_bar(self, show):
        if hasattr(self, 'piecesbar'):
            if show:
                self.piecesbar.show()
                self.progressbar.hide()
            else:
                self.piecesbar.hide()
                self.progressbar.show()
        else:
            if show:
                self.piecesbar = PiecesBar()
                self.builder.get_object("status_progress_vbox").pack_start(
                    self.piecesbar, False, False, 5
                )
                self.progressbar.hide()

    def clear(self):
        for widget in self.label_widgets:
            widget[0].set_text("")

        if self.config['show_piecesbar']:
            self.piecesbar.clear()
        else:
            self.progressbar.set_fraction(0.0)
