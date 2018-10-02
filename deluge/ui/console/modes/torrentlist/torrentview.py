# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.decorators import overrides
from deluge.ui.console.modes.basemode import InputKeyHandler
from deluge.ui.console.modes.torrentlist import torrentviewcolumns
from deluge.ui.console.modes.torrentlist.torrentactions import torrent_actions_popup
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.utils import format_utils
from deluge.ui.console.utils.column import (
    get_column_value,
    get_required_fields,
    torrent_data_fields,
)

from . import ACTION

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


state_fg_colors = {
    'Downloading': 'green',
    'Seeding': 'cyan',
    'Error': 'red',
    'Queued': 'yellow',
    'Checking': 'blue',
    'Moving': 'green',
}


reverse_sort_fields = [
    'size',
    'download_speed',
    'upload_speed',
    'num_seeds',
    'num_peers',
    'distributed_copies',
    'time_added',
    'total_uploaded',
    'all_time_download',
    'total_remaining',
    'progress',
    'ratio',
    'seeding_time',
    'active_time',
]


default_column_values = {
    'queue': {'width': 4, 'visible': True},
    'name': {'width': -1, 'visible': True},
    'size': {'width': 8, 'visible': True},
    'progress': {'width': 7, 'visible': True},
    'download_speed': {'width': 7, 'visible': True},
    'upload_speed': {'width': 7, 'visible': True},
    'state': {'width': 13},
    'eta': {'width': 8, 'visible': True},
    'time_added': {'width': 15},
    'tracker': {'width': 15},
    'download_location': {'width': 15},
    'downloaded': {'width': 13},
    'uploaded': {'width': 7},
    'remaining': {'width': 13},
    'completed_time': {'width': 15},
    'last_seen_complete': {'width': 15},
    'max_upload_speed': {'width': 7},
}


default_columns = {}
for col_i, col_name in enumerate(torrentviewcolumns.column_pref_names):
    default_columns[col_name] = {'width': 10, 'order': col_i, 'visible': False}
    if col_name in default_column_values:
        default_columns[col_name].update(default_column_values[col_name])


class TorrentView(InputKeyHandler):
    def __init__(self, torrentlist, config):
        super(TorrentView, self).__init__()
        self.torrentlist = torrentlist
        self.config = config
        self.filter_dict = {}
        self.curr_filter = None
        self.cached_rows = {}
        self.sorted_ids = None
        self.torrent_names = None
        self.numtorrents = -1
        self.column_string = ''
        self.curoff = 0
        self.marked = []
        self.cursel = 0

    @property
    def rows(self):
        return self.torrentlist.rows

    @property
    def torrent_rows(self):
        return self.torrentlist.rows - 3  # Account for header lines + columns line

    @property
    def torrentlist_offset(self):
        return 2

    def update_state(self, state, refresh=False):
        self.curstate = state  # cache in case we change sort order
        self.cached_rows.clear()
        self.numtorrents = len(state)
        self.sorted_ids = self._sort_torrents(state)
        self.torrent_names = []
        for torrent_id in self.sorted_ids:
            ts = self.curstate[torrent_id]
            self.torrent_names.append(ts['name'])

        if refresh:
            self.torrentlist.refresh()

    def set_torrent_filter(self, state):
        self.curr_filter = state
        filter_dict = {'state': [state]}
        if state == 'All':
            self.curr_filter = None
            filter_dict = {}
        self.filter_dict = filter_dict
        self.torrentlist.go_top = True
        self.torrentlist.update()
        return True

    def _scroll_up(self, by):
        cursel = self.cursel
        prevoff = self.curoff
        self.cursel = max(self.cursel - by, 0)
        if self.cursel < self.curoff:
            self.curoff = self.cursel
        affected = []
        if prevoff == self.curoff:
            affected.append(cursel)
            if cursel != self.cursel:
                affected.insert(0, self.cursel)
        return affected

    def _scroll_down(self, by):
        cursel = self.cursel
        prevoff = self.curoff
        self.cursel = min(self.cursel + by, self.numtorrents - 1)
        if (self.curoff + self.torrent_rows) <= self.cursel:
            self.curoff = self.cursel - self.torrent_rows + 1
        affected = []
        if prevoff == self.curoff:
            affected.append(cursel)
            if cursel != self.cursel:
                affected.append(self.cursel)
        return affected

    def current_torrent_id(self):
        if not self.sorted_ids:
            return None
        return self.sorted_ids[self.cursel]

    def _selected_torrent_ids(self):
        if not self.sorted_ids:
            return None
        ret = []
        for i in self.marked:
            ret.append(self.sorted_ids[i])
        return ret

    def clear_marked(self):
        self.marked = []
        self.last_mark = -1

    def mark_unmark(self, idx):
        if idx in self.marked:
            self.marked.remove(idx)
            self.last_mark = -1
        else:
            self.marked.append(idx)
            self.last_mark = idx

    def add_marked(self, indices, last_marked):
        for i in indices:
            if i not in self.marked:
                self.marked.append(i)
        self.last_mark = last_marked

    def update_marked(self, index, last_mark=True, clear=False):
        if index not in self.marked:
            if clear:
                self.marked = []
            self.marked.append(index)
            if last_mark:
                self.last_mark = index
            return True
        return False

    def _sort_torrents(self, state):
        """Sorts by primary and secondary sort fields."""

        if not state:
            return {}

        s_primary = self.config['torrentview']['sort_primary']
        s_secondary = self.config['torrentview']['sort_secondary']

        result = state

        # Sort first by secondary sort field and then primary sort field
        # so it all works out

        def sort_by_field(state, to_sort, field):
            field = torrent_data_fields[field]['status'][0]
            reverse = field in reverse_sort_fields

            # Get first element so we can check if it has given field
            # and if it's a string
            first_element = state[list(state)[0]]
            if field in first_element:

                def sort_key(s):
                    try:
                        # Sort case-insensitively but preserve A>a order.
                        return state.get(s)[field].lower()
                    except AttributeError:
                        # Not a string.
                        return state.get(s)[field]

                to_sort = sorted(to_sort, key=sort_key, reverse=reverse)

            if field == 'eta':
                to_sort = sorted(to_sort, key=lambda s: state.get(s)['eta'] == 0)

            return to_sort

        # Just in case primary and secondary fields are empty and/or
        # both are too ambiguous, also sort by queue position first
        if 'queue' not in [s_secondary, s_primary]:
            result = sort_by_field(state, result, 'queue')
        if s_secondary != s_primary:
            result = sort_by_field(state, result, s_secondary)
        result = sort_by_field(state, result, s_primary)

        if self.config['torrentview']['separate_complete']:
            result = sorted(
                result, key=lambda s: state.get(s).get('progress', 0) == 100.0
            )

        return result

    def _get_colors(self, row, tidx):
        # default style
        colors = {'fg': 'white', 'bg': 'black', 'attr': None}

        if tidx in self.marked:
            colors.update({'bg': 'blue', 'attr': 'bold'})

        if tidx == self.cursel:
            col_selected = {'bg': 'white', 'fg': 'black', 'attr': 'bold'}
            if tidx in self.marked:
                col_selected['fg'] = 'blue'
            colors.update(col_selected)

        colors['fg'] = state_fg_colors.get(row[1], colors['fg'])

        if self.torrentlist.minor_mode:
            self.torrentlist.minor_mode.update_colors(tidx, colors)
        return colors

    def update_torrents(self, lines):
        # add all the torrents
        if self.numtorrents == 0:
            cols = self.torrentlist.torrentview_columns()
            msg = 'No torrents match filter'.center(cols)
            self.torrentlist.add_string(
                3, '{!info!}%s' % msg, scr=self.torrentlist.torrentview_panel
            )
        elif self.numtorrents == 0:
            self.torrentlist.add_string(1, 'Waiting for torrents from core...')
            return

        def draw_row(index):
            if index not in self.cached_rows:
                ts = self.curstate[self.sorted_ids[index]]
                self.cached_rows[index] = (
                    format_utils.format_row(
                        [get_column_value(name, ts) for name in self.cols_to_show],
                        self.column_widths,
                    ),
                    ts['state'],
                )
            return self.cached_rows[index]

        tidx = self.curoff
        currow = 0
        todraw = []
        # Affected lines are given when changing selected torrent
        if lines:
            for line in lines:
                if line < tidx:
                    continue
                if line >= (tidx + self.torrent_rows) or line >= self.numtorrents:
                    break
                todraw.append((line, line - self.curoff, draw_row(line)))
        else:
            for i in range(tidx, tidx + self.torrent_rows):
                if i >= self.numtorrents:
                    break
                todraw.append((i, i - self.curoff, draw_row(i)))

        for tidx, currow, row in todraw:
            if (currow + self.torrentlist_offset - 1) > self.torrent_rows:
                continue
            colors = self._get_colors(row, tidx)
            if colors['attr']:
                colorstr = '{!%(fg)s,%(bg)s,%(attr)s!}' % colors
            else:
                colorstr = '{!%(fg)s,%(bg)s!}' % colors

            self.torrentlist.add_string(
                currow + self.torrentlist_offset,
                '%s%s' % (colorstr, row[0]),
                trim=False,
                scr=self.torrentlist.torrentview_panel,
            )

    def update(self, refresh=False):
        d = component.get('SessionProxy').get_torrents_status(
            self.filter_dict, self.status_fields
        )
        d.addCallback(self.update_state, refresh=refresh)

    def on_config_changed(self):
        s_primary = self.config['torrentview']['sort_primary']
        s_secondary = self.config['torrentview']['sort_secondary']
        changed = None
        for col in default_columns:
            if col not in self.config['torrentview']['columns']:
                changed = self.config['torrentview']['columns'][col] = default_columns[
                    col
                ]
        if changed:
            self.config.save()

        self.cols_to_show = [
            col
            for col in sorted(
                self.config['torrentview']['columns'],
                key=lambda k: self.config['torrentview']['columns'][k]['order'],
            )
            if self.config['torrentview']['columns'][col]['visible']
        ]
        self.status_fields = get_required_fields(self.cols_to_show)

        # we always need these, even if we're not displaying them
        for rf in ['state', 'name', 'queue', 'progress']:
            if rf not in self.status_fields:
                self.status_fields.append(rf)

        # same with sort keys
        if s_primary and s_primary not in self.status_fields:
            self.status_fields.append(s_primary)
        if s_secondary and s_secondary not in self.status_fields:
            self.status_fields.append(s_secondary)

        self.update_columns()

    def update_columns(self):
        self.column_widths = [
            self.config['torrentview']['columns'][col]['width']
            for col in self.cols_to_show
        ]
        requested_width = sum(width for width in self.column_widths if width >= 0)

        cols = self.torrentlist.torrentview_columns()
        if requested_width > cols:  # can't satisfy requests, just spread out evenly
            cw = int(cols / len(self.cols_to_show))
            for i in range(0, len(self.column_widths)):
                self.column_widths[i] = cw
        else:
            rem = cols - requested_width
            var_cols = len([width for width in self.column_widths if width < 0])
            if var_cols > 0:
                vw = int(rem / var_cols)
                for i in range(0, len(self.column_widths)):
                    if self.column_widths[i] < 0:
                        self.column_widths[i] = vw

        self.column_string = '{!header!}'

        primary_sort_col_name = self.config['torrentview']['sort_primary']

        for i, column in enumerate(self.cols_to_show):
            ccol = torrent_data_fields[column]['name']
            width = self.column_widths[i]

            # Trim the column if it's too long to fit
            if len(ccol) > width:
                ccol = ccol[: width - 1]

            # Padding
            ccol += ' ' * (width - len(ccol))

            # Highlight the primary sort column
            if column == primary_sort_col_name:
                if i != len(self.cols_to_show) - 1:
                    ccol = '{!black,green,bold!}%s{!header!}' % ccol
                else:
                    ccol = ('{!black,green,bold!}%s' % ccol)[:-1]

            self.column_string += ccol

    @overrides(InputKeyHandler)
    def handle_read(self, c):
        affected_lines = None
        if c == curses.KEY_UP:
            if self.cursel != 0:
                affected_lines = self._scroll_up(1)
        elif c == curses.KEY_PPAGE:
            affected_lines = self._scroll_up(int(self.torrent_rows / 2))
        elif c == curses.KEY_DOWN:
            if self.cursel < self.numtorrents:
                affected_lines = self._scroll_down(1)
        elif c == curses.KEY_NPAGE:
            affected_lines = self._scroll_down(int(self.torrent_rows / 2))
        elif c == curses.KEY_HOME:
            affected_lines = self._scroll_up(self.cursel)
        elif c == curses.KEY_END:
            affected_lines = self._scroll_down(self.numtorrents - self.cursel)
        elif c == curses.KEY_DC:  # DEL
            added = self.update_marked(self.cursel)

            def on_close(**kwargs):
                if added:
                    self.marked.pop()

            torrent_actions_popup(
                self.torrentlist,
                self._selected_torrent_ids(),
                action=ACTION.REMOVE,
                close_cb=on_close,
            )
        elif c in [curses.KEY_ENTER, util.KEY_ENTER2] and self.numtorrents:
            added = self.update_marked(self.cursel)

            def on_close(data, **kwargs):
                if added:
                    self.marked.remove(self.cursel)

            torrent_actions_popup(
                self.torrentlist,
                self._selected_torrent_ids(),
                details=True,
                close_cb=on_close,
            )
            self.torrentlist.refresh()
        elif c == ord('j'):
            affected_lines = self._scroll_up(1)
        elif c == ord('k'):
            affected_lines = self._scroll_down(1)
        elif c == ord('m'):
            self.mark_unmark(self.cursel)
            affected_lines = [self.cursel]
        elif c == ord('M'):
            if self.last_mark >= 0:
                if self.cursel > self.last_mark:
                    mrange = list(range(self.last_mark, self.cursel + 1))
                else:
                    mrange = list(range(self.cursel, self.last_mark))
                self.add_marked(mrange, self.cursel)
                affected_lines = mrange
            else:
                self.mark_unmark(self.cursel)
                affected_lines = [self.cursel]
        elif c == ord('c'):
            self.clear_marked()
        elif c == ord('o'):
            if not self.marked:
                added = self.update_marked(self.cursel, clear=True)
            else:
                self.last_mark = -1
            torrent_actions_popup(
                self.torrentlist,
                self._selected_torrent_ids(),
                action=ACTION.TORRENT_OPTIONS,
            )
        elif c in [ord('>'), ord('<')]:
            try:
                i = self.cols_to_show.index(self.config['torrentview']['sort_primary'])
            except ValueError:
                i = 0 if chr(c) == '<' else len(self.cols_to_show)
            else:
                i += 1 if chr(c) == '>' else -1

            i = max(0, min(len(self.cols_to_show) - 1, i))
            self.config['torrentview']['sort_primary'] = self.cols_to_show[i]
            self.config.save()
            self.on_config_changed()
            self.update_columns()
            self.torrentlist.refresh([])
        else:
            return util.ReadState.IGNORED

        self.set_input_result(affected_lines)
        return util.ReadState.CHANGED if affected_lines else util.ReadState.READ
