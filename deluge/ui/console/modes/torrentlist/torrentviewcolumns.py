# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from deluge.decorators import overrides
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.utils.column import torrent_data_fields
from deluge.ui.console.widgets.fields import CheckedPlusInput, IntSpinInput
from deluge.ui.console.widgets.popup import InputPopup, MessagePopup

COLUMN_VIEW_HELP_STR = """
Control column visibilty with the following actions:

{!info!}'+'{!normal!} - {|indent_pos:|}Increase column width
{!info!}'-'{!normal!} - {|indent_pos:|}Decrease column width

{!info!}'CTRL+up'{!normal!} - {|indent_pos:|} Move column left
{!info!}'CTRL+down'{!normal!} - {|indent_pos:|} Move column right
"""

column_pref_names = [
    'queue',
    'name',
    'size',
    'downloaded',
    'uploaded',
    'remaining',
    'state',
    'progress',
    'seeds',
    'peers',
    'seeds_peers_ratio',
    'download_speed',
    'upload_speed',
    'max_download_speed',
    'max_upload_speed',
    'eta',
    'ratio',
    'avail',
    'time_added',
    'completed_time',
    'last_seen_complete',
    'tracker',
    'download_location',
    'active_time',
    'seeding_time',
    'finished_time',
    'time_since_transfer',
    'shared',
    'owner',
]


class ColumnAndWidth(CheckedPlusInput):
    def __init__(self, parent, name, message, child, on_width_func, **kwargs):
        CheckedPlusInput.__init__(self, parent, name, message, child, **kwargs)
        self.on_width_func = on_width_func

    @overrides(CheckedPlusInput)
    def handle_read(self, c):
        if c in [ord('+'), ord('-')]:
            val = self.child.get_value()
            change = 1 if chr(c) == '+' else -1
            self.child.set_value(val + change, validate=True)
            self.on_width_func(self.name, self.child.get_value())
            return util.ReadState.CHANGED
        return CheckedPlusInput.handle_read(self, c)


class TorrentViewColumns(InputPopup):
    def __init__(self, torrentlist):
        self.torrentlist = torrentlist
        self.torrentview = torrentlist.torrentview

        title = 'Visible columns (Esc to exit)'
        InputPopup.__init__(
            self,
            torrentlist,
            title,
            close_cb=self._do_set_column_visibility,
            immediate_action=True,
            height_req=len(column_pref_names) - 5,
            width_req=max(len(col) for col in column_pref_names + [title]) + 14,
            border_off_west=1,
            allow_rearrange=True,
        )

        msg_fmt = '%-25s'
        self.add_header((msg_fmt % _('Columns')) + ' ' + _('Width'), space_below=True)

        for colpref_name in column_pref_names:
            col = self.torrentview.config['torrentview']['columns'][colpref_name]
            width_spin = IntSpinInput(
                self,
                colpref_name + '_ width',
                '',
                self.move,
                col['width'],
                min_val=-1,
                max_val=99,
                fmt='%2d',
            )

            def on_width_func(name, width):
                self.torrentview.config['torrentview']['columns'][name]['width'] = width

            self._add_input(
                ColumnAndWidth(
                    self,
                    colpref_name,
                    torrent_data_fields[colpref_name]['name'],
                    width_spin,
                    on_width_func,
                    checked=col['visible'],
                    checked_char='*',
                    msg_fmt=msg_fmt,
                    show_usage_hints=False,
                    child_always_visible=True,
                )
            )

    def _do_set_column_visibility(
        self, data=None, state_changed=True, close=True, **kwargs
    ):
        if close:
            self.torrentlist.pop_popup()
            return
        elif not state_changed:
            return

        for key, value in data.items():
            self.torrentview.config['torrentview']['columns'][key]['visible'] = value[
                'value'
            ]
            self.torrentview.config['torrentview']['columns'][key]['order'] = value[
                'order'
            ]

        self.torrentview.config.save()
        self.torrentview.on_config_changed()
        self.torrentlist.refresh([])

    @overrides(InputPopup)
    def handle_read(self, c):
        if c == ord('h'):
            popup = MessagePopup(
                self.torrentlist,
                'Help',
                COLUMN_VIEW_HELP_STR,
                width_req=70,
                border_off_west=1,
            )
            self.torrentlist.push_popup(popup)
            return util.ReadState.READ
        return InputPopup.handle_read(self, c)
