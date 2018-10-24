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
from xml.sax.saxutils import escape as xml_escape

import deluge.component as component
from deluge.common import decode_bytes, fdate, fsize, is_url

from .tab_data_funcs import fdate_or_dash, fpieces_num_size
from .torrentdetails import Tab

log = logging.getLogger(__name__)


class DetailsTab(Tab):
    def __init__(self):
        super(DetailsTab, self).__init__('Details', 'details_tab', 'details_tab_label')

        self.add_tab_widget('summary_name', None, ('name',))
        self.add_tab_widget('summary_total_size', fsize, ('total_size',))
        self.add_tab_widget('summary_num_files', str, ('num_files',))
        self.add_tab_widget('summary_completed', fdate_or_dash, ('completed_time',))
        self.add_tab_widget('summary_date_added', fdate, ('time_added',))
        self.add_tab_widget('summary_torrent_path', None, ('download_location',))
        self.add_tab_widget('summary_hash', str, ('hash',))
        self.add_tab_widget('summary_comments', str, ('comment',))
        self.add_tab_widget('summary_creator', str, ('creator',))
        self.add_tab_widget(
            'summary_pieces', fpieces_num_size, ('num_pieces', 'piece_length')
        )

    def update(self):
        # Get the first selected torrent
        selected = component.get('TorrentView').get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if selected:
            selected = selected[0]
        else:
            # No torrent is selected in the torrentview
            self.clear()
            return

        session = component.get('SessionProxy')
        session.get_torrent_status(selected, self.status_keys).addCallback(
            self._on_get_torrent_status
        )

    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if status is None:
            return

        # Update all the label widgets
        for widget in self.tab_widgets.values():
            txt = xml_escape(self.widget_status_as_fstr(widget, status))
            if decode_bytes(widget.obj.get_text()) != txt:
                if 'comment' in widget.status_keys and is_url(txt):
                    widget.obj.set_markup('<a href="%s">%s</a>' % (txt, txt))
                else:
                    widget.obj.set_markup(txt)

    def clear(self):
        for widget in self.tab_widgets.values():
            widget.obj.set_text('')
