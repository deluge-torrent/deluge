# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.component as component
from deluge.common import ftime
from deluge.ui.gtkui.torrentdetails import Tab

log = logging.getLogger(__name__)


def fcount(value):
    return "%s" % len(value)


def ftranslate(text):
    if text:
        text = _(text)
    return text


class TrackersTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        # Get the labels we need to update.
        # widget name, modifier function, status keys
        builder = component.get("MainWindow").get_builder()

        self._name = "Trackers"
        self._child_widget = builder.get_object("trackers_tab")
        self._tab_label = builder.get_object("trackers_tab_label")

        self.label_widgets = [
            (builder.get_object("summary_next_announce"), ftime, ("next_announce",)),
            (builder.get_object("summary_tracker"), None, ("tracker_host",)),
            (builder.get_object("summary_tracker_status"), ftranslate, ("tracker_status",)),
            (builder.get_object("summary_tracker_total"), fcount, ("trackers",)),
        ]

        self.status_keys = [status for widget in self.label_widgets for status in widget[2]]

        component.get("MainWindow").connect_signals({
            "on_button_edit_trackers_clicked": self._on_button_edit_trackers_clicked,
        })

    def update(self):
        # Get the first selected torrent
        selected = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if selected:
            selected = selected[0]
        else:
            self.clear()
            return

        session = component.get("SessionProxy")
        session.get_torrent_status(selected, self.status_keys).addCallback(self._on_get_torrent_status)

    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if not status:
            return

        # Update all the label widgets
        for widget in self.label_widgets:
            txt = self.get_status_for_widget(widget, status)
            if widget[0].get_text() != txt:
                widget[0].set_text(txt)

    def clear(self):
        for widget in self.label_widgets:
            widget[0].set_text("")

    def _on_button_edit_trackers_clicked(self, button):
        torrent_id = component.get("TorrentView").get_selected_torrent()
        if torrent_id:
            from deluge.ui.gtkui.edittrackersdialog import EditTrackersDialog
            dialog = EditTrackersDialog(torrent_id, component.get("MainWindow").window)
            dialog.run()
