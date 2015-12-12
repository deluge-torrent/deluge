# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
from xml.sax.saxutils import escape as xml_escape

import deluge.component as component
from deluge.common import fdate, fsize, is_url
from deluge.ui.gtkui.torrentdetails import Tab

log = logging.getLogger(__name__)


def fpeer_size_second(first, second):
    return "%s (%s)" % (first, fsize(second))


def fdate_or_dash(value):
    """Display value as date, eg 05/05/08 or dash"""
    if value > 0.0:
        return fdate(value)
    else:
        return "-"


def str_yes_no(value):
    """Return Yes or No to bool value"""
    return _("Yes") if value else _("No")


class DetailsTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        # Get the labels we need to update.
        # widget name, modifier function, status keys
        builder = component.get("MainWindow").get_builder()

        self._name = "Details"
        self._child_widget = builder.get_object("details_tab")
        self._tab_label = builder.get_object("details_tab_label")

        self.label_widgets = [
            (builder.get_object("summary_name"), None, ("name",)),
            (builder.get_object("summary_total_size"), fsize, ("total_size",)),
            (builder.get_object("summary_num_files"), str, ("num_files",)),
            (builder.get_object("summary_completed"), fdate_or_dash, ("completed_time",)),
            (builder.get_object("summary_date_added"), fdate, ("time_added",)),
            (builder.get_object("summary_private"), str_yes_no, ("private",)),
            (builder.get_object("summary_torrent_path"), None, ("download_location",)),
            (builder.get_object("summary_hash"), str, ("hash",)),
            (builder.get_object("summary_comments"), str, ("comment",)),
            (builder.get_object("summary_owner"), str, ("owner",)),
            (builder.get_object("summary_shared"), str_yes_no, ("shared",)),
            (builder.get_object("summary_pieces"), fpeer_size_second, ("num_pieces", "piece_length")),
        ]

        self.status_keys = [status for widget in self.label_widgets for status in widget[2]]

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

        session = component.get("SessionProxy")
        session.get_torrent_status(selected, self.status_keys).addCallback(self._on_get_torrent_status)

    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if status is None:
            return

        # Update all the label widgets
        for widget in self.label_widgets:
            txt = xml_escape(self.get_status_for_widget(widget, status))
            if widget[0].get_text() != txt:
                if widget[2][0] == "comment" and is_url(txt):
                    widget[0].set_markup('<a href="%s">%s</a>' % (txt, txt))
                else:
                    widget[0].set_markup(txt)

    def clear(self):
        for widget in self.label_widgets:
            widget[0].set_text("")
