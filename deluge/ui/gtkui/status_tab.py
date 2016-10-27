# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division

import logging

import deluge.component as component
from deluge.common import fdate, fpeer, fsize, fspeed, ftime
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.piecesbar import PiecesBar
from deluge.ui.gtkui.torrentdetails import Tab

log = logging.getLogger(__name__)


def ftotal_sized(first, second):
    return "%s (%s)" % (fsize(first, shortform=True), fsize(second, shortform=True))


def fratio(value):
    return ("%.3f" % value).rstrip('0').rstrip('.') if value > 0 else "∞"


def fpcnt(value, state):
    textstr = _(state)
    if state not in ("Error", "Seeding") and value < 100:
        textstr = ('%s %.2f' % (textstr, value)).rstrip('0').rstrip('.') + '%'
    return textstr


def fspeed_max(value, max_value=-1):
    value = fspeed(value, shortform=True)
    return "%s (%s %s)" % (value, max_value, _("K/s")) if max_value > -1 else value


def fdate_or_never(value):
    """Display value as date, eg 05/05/08 or Never"""
    return fdate(value, date_only=True) if value > 0 else _("Never")


def ftime_or_dash(value):
    """Display value as time, eg 2h 30m or dash"""
    return ftime(value) if value > 0 else "-"


def fseed_rank_or_dash(seed_rank, seeding_time):
    """Display value if seeding otherwise dash"""

    if seeding_time > 0:
        if seed_rank >= 1000:
            return "%ik" % (seed_rank // 1000)
        else:
            return str(seed_rank)
    else:
        return "-"


def flast_active(time_since_download, time_since_upload):
    """The last time the torrent was active as time e.g. 2h 30m or dash"""

    try:
        last_time_since = min((x for x in (time_since_download, time_since_upload) if x != -1))
    except ValueError:
        return "-"
    else:
        return ftime(last_time_since)


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

        self.label_widgets = [
            (builder.get_object("summary_availability"), fratio, ("distributed_copies",)),
            (builder.get_object("summary_total_downloaded"), ftotal_sized, ("all_time_download",
                                                                            "total_payload_download")),
            (builder.get_object("summary_total_uploaded"), ftotal_sized, ("total_uploaded", "total_payload_upload")),
            (builder.get_object("summary_download_speed"), fspeed_max, ("download_payload_rate", "max_download_speed")),
            (builder.get_object("summary_upload_speed"), fspeed_max, ("upload_payload_rate", "max_upload_speed")),
            (builder.get_object("summary_seeds"), fpeer, ("num_seeds", "total_seeds")),
            (builder.get_object("summary_peers"), fpeer, ("num_peers", "total_peers")),
            (builder.get_object("summary_eta"), ftime_or_dash, ("eta",)),
            (builder.get_object("summary_share_ratio"), fratio, ("ratio",)),
            (builder.get_object("summary_active_time"), ftime_or_dash, ("active_time",)),
            (builder.get_object("summary_seed_time"), ftime_or_dash, ("seeding_time",)),
            (builder.get_object("summary_seed_rank"), fseed_rank_or_dash, ("seed_rank", "seeding_time")),
            (builder.get_object("progressbar"), fpcnt, ("progress", "state")),
            (builder.get_object("summary_last_seen_complete"), fdate_or_never, ("last_seen_complete",)),
            (builder.get_object("summary_last_active"), flast_active, ("time_since_download",
                                                                       "time_since_upload")),
            (builder.get_object("summary_torrent_status"), str, ("message",)),
        ]

        self.status_keys = [status for widget in self.label_widgets for status in widget[2]]

        self.piecesbar = None
        self.config.register_set_function("show_piecesbar", self.on_show_piecesbar_config_changed, apply_now=True)

    def update(self):
        # Get the first selected torrent
        selected = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if selected:
            selected = selected[0]
        else:
            # No torrent is selected in the torrentview
            self.clear()
            return

        # Get the torrent status
        status_keys = self.status_keys
        if self.config['show_piecesbar']:
            status_keys = self.status_keys + ["pieces", "num_pieces"]

        component.get("SessionProxy").get_torrent_status(
            selected, status_keys).addCallback(self._on_get_torrent_status)

    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if status is None:
            return

        # Update all the label widgets
        for widget in self.label_widgets:
            txt = self.get_status_for_widget(widget, status)
            if widget[0].get_text() != txt:
                widget[0].set_text(txt)

        # Do the progress bar because it's a special case (not a label)
        if self.config['show_piecesbar']:
            self.piecesbar.update_from_status(status)
        else:
            fraction = status["progress"] / 100
            if self.progressbar.get_fraction() != fraction:
                self.progressbar.set_fraction(fraction)

    def on_show_piecesbar_config_changed(self, key, show):
        if show:
            self.show_piecesbar()
        else:
            self.hide_piecesbar()

    def show_piecesbar(self):
        if self.piecesbar is None:
            self.piecesbar = PiecesBar()
            self.builder.get_object("status_progress_vbox").pack_start(self.piecesbar, False, False, 0)
        self.piecesbar.show()
        self.progressbar.hide()

    def hide_piecesbar(self):
        self.progressbar.show()
        if self.piecesbar:
            self.piecesbar.hide()
            self.piecesbar = None

    def clear(self):
        for widget in self.label_widgets:
            widget[0].set_text("")

        if self.config['show_piecesbar']:
            self.piecesbar.clear()
        else:
            self.progressbar.set_fraction(0.0)
