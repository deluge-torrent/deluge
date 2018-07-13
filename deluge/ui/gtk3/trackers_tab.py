# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.common import ftime

from .tab_data_funcs import fcount, ftranslate, fyes_no
from .torrentdetails import Tab

log = logging.getLogger(__name__)


class TrackersTab(Tab):
    def __init__(self):
        super(TrackersTab, self).__init__(
            'Trackers', 'trackers_tab', 'trackers_tab_label'
        )

        self.add_tab_widget('summary_next_announce', ftime, ('next_announce',))
        self.add_tab_widget('summary_tracker', None, ('tracker_host',))
        self.add_tab_widget('summary_tracker_status', ftranslate, ('tracker_status',))
        self.add_tab_widget('summary_tracker_total', fcount, ('trackers',))
        self.add_tab_widget('summary_private', fyes_no, ('private',))

        component.get('MainWindow').connect_signals(self)

    def update(self):
        # Get the first selected torrent
        selected = component.get('TorrentView').get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if selected:
            selected = selected[0]
        else:
            self.clear()
            return

        session = component.get('SessionProxy')
        session.get_torrent_status(selected, self.status_keys).addCallback(
            self._on_get_torrent_status
        )

    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if not status:
            return

        # Update all the tab label widgets
        for widget in self.tab_widgets.values():
            txt = self.widget_status_as_fstr(widget, status)
            if widget.obj.get_text() != txt:
                widget.obj.set_text(txt)

    def clear(self):
        for widget in self.tab_widgets.values():
            widget.obj.set_text('')

    def on_button_edit_trackers_clicked(self, button):
        torrent_id = component.get('TorrentView').get_selected_torrent()
        if torrent_id:
            from .edittrackersdialog import EditTrackersDialog

            dialog = EditTrackersDialog(torrent_id, component.get('MainWindow').window)
            dialog.run()
