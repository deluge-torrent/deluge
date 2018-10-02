# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from deluge.ui.client import client
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.widgets.popup import MessagePopup, SelectablePopup

from . import ACTION

try:
    import curses
except ImportError:
    pass

key_to_action = {
    curses.KEY_HOME: ACTION.QUEUE_TOP,
    curses.KEY_UP: ACTION.QUEUE_UP,
    curses.KEY_DOWN: ACTION.QUEUE_DOWN,
    curses.KEY_END: ACTION.QUEUE_BOTTOM,
}
QUEUE_MODE_HELP_STR = """
Change queue position of selected torrents

{!info!}'+'{!normal!} - {|indent_pos:|}Move up
{!info!}'-'{!normal!} - {|indent_pos:|}Move down

{!info!}'Home'{!normal!} - {|indent_pos:|}Move to top
{!info!}'End'{!normal!} - {|indent_pos:|}Move to bottom

"""


class QueueMode(object):
    def __init__(self, torrentslist, torrent_ids):
        self.torrentslist = torrentslist
        self.torrentview = torrentslist.torrentview
        self.torrent_ids = torrent_ids

    def set_statusbar_args(self, statusbar_args):
        statusbar_args[
            'bottombar'
        ] = '{!black,white!}Queue mode: change queue position of selected torrents.'
        statusbar_args['bottombar_help'] = ' Press [h] for help'

    def update_cursor(self):
        pass

    def update_colors(self, tidx, colors):
        pass

    def handle_read(self, c):
        if c in [util.KEY_ESC, util.KEY_BELL]:  # If Escape key or CTRL-g, we abort
            self.torrentslist.set_minor_mode(None)
        elif c == ord('h'):
            popup = MessagePopup(
                self.torrentslist,
                'Help',
                QUEUE_MODE_HELP_STR,
                width_req=0.65,
                border_off_west=1,
            )
            self.torrentslist.push_popup(popup, clear=True)
        elif c in [
            curses.KEY_UP,
            curses.KEY_DOWN,
            curses.KEY_HOME,
            curses.KEY_END,
            curses.KEY_NPAGE,
            curses.KEY_PPAGE,
        ]:
            action = key_to_action[c]
            self.do_queue(action)

    def move_selection(self, cb_arg, qact):
        if self.torrentslist.config['torrentview']['move_selection'] is False:
            return
        queue_length = 0
        selected_num = 0
        for tid in self.torrentview.curstate:
            tq = self.torrentview.curstate[tid]['queue']
            if tq != -1:
                queue_length += 1
                if tq in self.torrentview.marked:
                    selected_num += 1
        if qact == ACTION.QUEUE_TOP:
            if self.torrentview.marked:
                self.torrentview.cursel = 1 + sorted(self.torrentview.marked).index(
                    self.torrentview.cursel
                )
            else:
                self.torrentview.cursel = 1
            self.torrentview.marked = list(range(1, selected_num + 1))
        elif qact == ACTION.QUEUE_UP:
            self.torrentview.cursel = max(1, self.torrentview.cursel - 1)
            self.torrentview.marked = [marked - 1 for marked in self.torrentview.marked]
            self.torrentview.marked = [
                marked for marked in self.torrentview.marked if marked > 0
            ]
        elif qact == ACTION.QUEUE_DOWN:
            self.torrentview.cursel = min(queue_length, self.torrentview.cursel + 1)
            self.torrentview.marked = [marked + 1 for marked in self.torrentview.marked]
            self.torrentview.marked = [
                marked for marked in self.torrentview.marked if marked <= queue_length
            ]
        elif qact == ACTION.QUEUE_BOTTOM:
            if self.torrentview.marked:
                self.torrentview.cursel = (
                    queue_length
                    - selected_num
                    + 1
                    + sorted(self.torrentview.marked).index(self.torrentview.cursel)
                )
            else:
                self.torrentview.cursel = queue_length
            self.torrentview.marked = list(
                range(queue_length - selected_num + 1, queue_length + 1)
            )

    def do_queue(self, qact, *args, **kwargs):
        if qact == ACTION.QUEUE_TOP:
            client.core.queue_top(self.torrent_ids).addCallback(
                self.move_selection, qact
            )
        elif qact == ACTION.QUEUE_BOTTOM:
            client.core.queue_bottom(self.torrent_ids).addCallback(
                self.move_selection, qact
            )
        elif qact == ACTION.QUEUE_UP:
            client.core.queue_up(self.torrent_ids).addCallback(
                self.move_selection, qact
            )
        elif qact == ACTION.QUEUE_DOWN:
            client.core.queue_down(self.torrent_ids).addCallback(
                self.move_selection, qact
            )

    def popup(self, **kwargs):
        popup = SelectablePopup(
            self.torrentslist,
            'Queue Action',
            self.do_queue,
            cb_args=kwargs,
            border_off_west=1,
        )
        popup.add_line(ACTION.QUEUE_TOP, '_Top')
        popup.add_line(ACTION.QUEUE_UP, '_Up')
        popup.add_line(ACTION.QUEUE_DOWN, '_Down')
        popup.add_line(ACTION.QUEUE_BOTTOM, '_Bottom')
        self.torrentslist.push_popup(popup)
