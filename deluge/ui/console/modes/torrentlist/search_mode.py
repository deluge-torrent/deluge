# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from deluge.common import PY2
from deluge.decorators import overrides
from deluge.ui.console.modes.basemode import InputKeyHandler, move_cursor
from deluge.ui.console.modes.torrentlist.torrentactions import torrent_actions_popup
from deluge.ui.console.utils import curses_util as util

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)
QUEUE_MODE_HELP_STR = """
Change queue position of selected torrents

{!info!}'+'{!normal!} - {|indent_pos:|}Move up
{!info!}'-'{!normal!} - {|indent_pos:|}Move down

{!info!}'Home'{!normal!} - {|indent_pos:|}Move to top
{!info!}'End'{!normal!} - {|indent_pos:|}Move to bottom

"""
SEARCH_EMPTY = 0
SEARCH_FAILING = 1
SEARCH_SUCCESS = 2
SEARCH_START_REACHED = 3
SEARCH_END_REACHED = 4
SEARCH_FORMAT = {
    SEARCH_EMPTY: '{!black,white!}Search torrents: %s{!black,white!}',
    SEARCH_SUCCESS: '{!black,white!}Search torrents: {!black,green!}%s{!black,white!}',
    SEARCH_FAILING: '{!black,white!}Search torrents: {!black,red!}%s{!black,white!}',
    SEARCH_START_REACHED: '{!black,white!}Search torrents: {!black,yellow!}%s{!black,white!} (start reached)',
    SEARCH_END_REACHED: '{!black,white!}Search torrents: {!black,yellow!}%s{!black,white!} (end reached)',
}


class SearchMode(InputKeyHandler):
    def __init__(self, torrentlist):
        super(SearchMode, self).__init__()
        self.torrentlist = torrentlist
        self.torrentview = torrentlist.torrentview
        self.search_state = SEARCH_EMPTY
        self.search_string = ''

    def update_cursor(self):
        util.safe_curs_set(util.Curser.VERY_VISIBLE)
        move_cursor(
            self.torrentlist.stdscr,
            self.torrentlist.rows - 1,
            len(self.search_string) + 17,
        )

    def set_statusbar_args(self, statusbar_args):
        statusbar_args['bottombar'] = (
            SEARCH_FORMAT[self.search_state] % self.search_string
        )
        statusbar_args['bottombar_help'] = False

    def update_colors(self, tidx, colors):
        if len(self.search_string) > 1:
            lcase_name = self.torrentview.torrent_names[tidx].lower()
            sstring_lower = self.search_string.lower()
            if lcase_name.find(sstring_lower) != -1:
                if tidx == self.torrentview.cursel:
                    pass
                elif tidx in self.torrentview.marked:
                    colors['bg'] = 'magenta'
                else:
                    colors['bg'] = 'green'
                    if colors['fg'] == 'green':
                        colors['fg'] = 'black'
                    colors['attr'] = 'bold'

    def do_search(self, direction='first'):
        """
        Performs a search on visible torrent and sets cursor to the match

        Args:
            direction (str): The direction to search. Must be one of 'first', 'last', 'next' or 'previous'

        """
        search_space = list(enumerate(self.torrentview.torrent_names))

        if direction == 'last':
            search_space = reversed(search_space)
        elif direction == 'next':
            search_space = search_space[self.torrentview.cursel + 1 :]
        elif direction == 'previous':
            search_space = reversed(search_space[: self.torrentview.cursel])

        search_string = self.search_string.lower()
        for i, n in search_space:
            n = n.lower()
            if n.find(search_string) != -1:
                self.torrentview.cursel = i
                if (
                    self.torrentview.curoff
                    + self.torrentview.torrent_rows
                    - self.torrentview.torrentlist_offset
                ) < self.torrentview.cursel:
                    self.torrentview.curoff = (
                        self.torrentview.cursel - self.torrentview.torrent_rows + 1
                    )
                elif (self.torrentview.curoff + 1) > self.torrentview.cursel:
                    self.torrentview.curoff = max(0, self.torrentview.cursel)
                self.search_state = SEARCH_SUCCESS
                return
        if direction in ['first', 'last']:
            self.search_state = SEARCH_FAILING
        elif direction == 'next':
            self.search_state = SEARCH_END_REACHED
        elif direction == 'previous':
            self.search_state = SEARCH_START_REACHED

    @overrides(InputKeyHandler)
    def handle_read(self, c):
        cname = self.torrentview.torrent_names[self.torrentview.cursel]
        refresh = True

        if c in [
            util.KEY_ESC,
            util.KEY_BELL,
        ]:  # If Escape key or CTRL-g, we abort search
            self.torrentlist.set_minor_mode(None)
            self.search_state = SEARCH_EMPTY
        elif c in [curses.KEY_BACKSPACE, util.KEY_BACKSPACE2]:
            if self.search_string:
                self.search_string = self.search_string[:-1]
                if cname.lower().find(self.search_string.lower()) != -1:
                    self.search_state = SEARCH_SUCCESS
            else:
                self.torrentlist.set_minor_mode(None)
                self.search_state = SEARCH_EMPTY
        elif c == curses.KEY_DC:
            self.search_string = ''
            self.search_state = SEARCH_SUCCESS
        elif c == curses.KEY_UP:
            self.do_search('previous')
        elif c == curses.KEY_DOWN:
            self.do_search('next')
        elif c == curses.KEY_LEFT:
            self.torrentlist.set_minor_mode(None)
            self.search_state = SEARCH_EMPTY
        elif c == ord('/'):
            self.torrentlist.set_minor_mode(None)
            self.search_state = SEARCH_EMPTY
        elif c == curses.KEY_RIGHT:
            tid = self.torrentview.current_torrent_id()
            self.torrentlist.show_torrent_details(tid)
            refresh = False
        elif c == curses.KEY_HOME:
            self.do_search('first')
        elif c == curses.KEY_END:
            self.do_search('last')
        elif c in [10, curses.KEY_ENTER]:
            self.last_mark = -1
            tid = self.torrentview.current_torrent_id()
            torrent_actions_popup(self.torrentlist, [tid], details=True)
            refresh = False
        elif c == util.KEY_ESC:
            self.search_string = ''
            self.search_state = SEARCH_EMPTY
        elif c > 31 and c < 256:
            old_search_string = self.search_string
            stroke = chr(c)
            uchar = '' if PY2 else stroke
            while not uchar:
                try:
                    uchar = stroke.decode(self.torrentlist.encoding)
                except UnicodeDecodeError:
                    c = self.torrentlist.stdscr.getch()
                    stroke += chr(c)

            if uchar:
                self.search_string += uchar

            still_matching = (
                cname.lower().find(self.search_string.lower())
                == cname.lower().find(old_search_string.lower())
                and cname.lower().find(self.search_string.lower()) != -1
            )

            if self.search_string and not still_matching:
                self.do_search()
            elif self.search_string:
                self.search_state = SEARCH_SUCCESS
        else:
            refresh = False

        if not self.search_string:
            self.search_state = SEARCH_EMPTY
            refresh = True

        if refresh:
            self.torrentlist.refresh([])

        return util.ReadState.READ
