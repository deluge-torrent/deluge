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
from deluge.common import fpeer
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.piecesbar import PiecesBar
from deluge.ui.gtkui.tab_data_funcs import (fdate_or_never, flast_active, fpcnt, fratio, fseed_rank_or_dash, fspeed_max,
                                            ftime_or_dash, ftotal_sized)
from deluge.ui.gtkui.torrentdetails import Tab

log = logging.getLogger(__name__)


class StatusTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        # Get the labels we need to update.
        # widget name, modifier function, status keys
        main_builder = component.get('MainWindow').get_builder()

        self._name = 'Status'
        self._child_widget = main_builder.get_object('status_tab')
        self._tab_label = main_builder.get_object('status_tab_label')
        self.config = ConfigManager('gtkui.conf')

        self.progressbar = main_builder.get_object('progressbar')
        self.piecesbar = None
        self.piecesbar_label_widget = None

        self.label_widgets = [
            (main_builder.get_object('summary_availability'), fratio, ('distributed_copies',)),
            (main_builder.get_object('summary_total_downloaded'), ftotal_sized, ('all_time_download',
                                                                                 'total_payload_download')),
            (main_builder.get_object('summary_total_uploaded'), ftotal_sized, ('total_uploaded',
                                                                               'total_payload_upload')),
            (main_builder.get_object('summary_download_speed'), fspeed_max, ('download_payload_rate',
                                                                             'max_download_speed')),
            (main_builder.get_object('summary_upload_speed'), fspeed_max, ('upload_payload_rate',
                                                                           'max_upload_speed')),
            (main_builder.get_object('summary_seeds'), fpeer, ('num_seeds', 'total_seeds')),
            (main_builder.get_object('summary_peers'), fpeer, ('num_peers', 'total_peers')),
            (main_builder.get_object('summary_eta'), ftime_or_dash, ('eta',)),
            (main_builder.get_object('summary_share_ratio'), fratio, ('ratio',)),
            (main_builder.get_object('summary_active_time'), ftime_or_dash, ('active_time',)),
            (main_builder.get_object('summary_seed_time'), ftime_or_dash, ('seeding_time',)),
            (main_builder.get_object('summary_seed_rank'), fseed_rank_or_dash, ('seed_rank', 'seeding_time')),
            (main_builder.get_object('progressbar'), fpcnt, ('progress', 'state', 'message')),
            (main_builder.get_object('summary_last_seen_complete'), fdate_or_never, ('last_seen_complete',)),
            (main_builder.get_object('summary_last_active'), flast_active, ('time_since_download',
                                                                            'time_since_upload')),
        ]

        self.status_keys = [status for widget in self.label_widgets for status in widget[2]]
        self.config.register_set_function('show_piecesbar', self.on_show_piecesbar_config_changed, apply_now=True)

    def update(self):
        # Get the first selected torrent
        selected = component.get('TorrentView').get_selected_torrent()

        if not selected:
            # No torrent is selected in the torrentview
            self.clear()
            return

        # Get the torrent status
        status_keys = self.status_keys
        if self.config['show_piecesbar']:
            status_keys.extend(['pieces', 'num_pieces'])

        component.get('SessionProxy').get_torrent_status(
            selected, status_keys).addCallback(self._on_get_torrent_status)

    def _on_get_torrent_status(self, status):
        # Check to see if we got valid data from the core
        if not status:
            return

        # Update all the label widgets
        for widget in self.label_widgets:
            txt = self.get_status_for_widget(widget, status)
            if widget[0].get_text() != txt:
                widget[0].set_text(txt)

        # Update progress bar seperately as it's a special case (not a label).
        fraction = status['progress'] / 100

        if self.config['show_piecesbar']:
            if self.piecesbar.get_fraction() != fraction:
                self.piecesbar.set_fraction(fraction)
            if status['state'] != 'Checking' and self.piecesbar.get_pieces() != status['pieces']:
                # Skip pieces assignment if checking torrent.
                self.piecesbar.set_pieces(status['pieces'], status['num_pieces'])
            self.piecesbar.update()
        else:
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
            main_builder = component.get('MainWindow').get_builder()
            main_builder.get_object('status_progress_vbox').pack_start(self.piecesbar, False, False, 0)
        self.piecesbar_label_widget = (self.piecesbar, fpcnt, ('progress', 'state', 'message'))
        self.label_widgets.append(self.piecesbar_label_widget)
        self.piecesbar.show()
        self.progressbar.hide()

    def hide_piecesbar(self):
        self.progressbar.show()
        if self.piecesbar:
            self.piecesbar.hide()
            self.label_widgets.remove(self.piecesbar_label_widget)
            self.piecesbar = self.piecesbar_label_widget = None

    def clear(self):
        for widget in self.label_widgets:
            widget[0].set_text('')

        if self.config['show_piecesbar']:
            self.piecesbar.clear()
        else:
            self.progressbar.set_fraction(0)
