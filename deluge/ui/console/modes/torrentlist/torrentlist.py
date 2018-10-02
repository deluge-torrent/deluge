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
from collections import deque

import deluge.component as component
from deluge.component import Component
from deluge.decorators import overrides
from deluge.ui.client import client
from deluge.ui.console.modes.basemode import BaseMode, mkwin
from deluge.ui.console.modes.torrentlist import torrentview, torrentviewcolumns
from deluge.ui.console.modes.torrentlist.add_torrents_popup import (
    show_torrent_add_popup,
)
from deluge.ui.console.modes.torrentlist.filtersidebar import FilterSidebar
from deluge.ui.console.modes.torrentlist.queue_mode import QueueMode
from deluge.ui.console.modes.torrentlist.search_mode import SearchMode
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.widgets.popup import MessagePopup, PopupsHandler

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


# Big help string that gets displayed when the user hits 'h'
HELP_STR = """
This screen shows an overview of the current torrents Deluge is managing. \
The currently selected torrent is indicated with a white background. \
You can change the selected torrent using the up/down arrows or the \
PgUp/PgDown keys. Home and End keys go to the first and last torrent \
respectively.

Operations can be performed on multiple torrents by marking them and \
then hitting Enter. See below for the keys used to mark torrents.

You can scroll a popup window that doesn't fit its content (like \
this one) using the up/down arrows, PgUp/PgDown and Home/End keys.

All popup windows can be closed/canceled by hitting the Esc key \
or the 'q' key (does not work for dialogs like the add torrent dialog)

The actions you can perform and the keys to perform them are as follows:

{!info!}'h'{!normal!} - {|indent_pos:|}Show this help
{!info!}'p'{!normal!} - {|indent_pos:|}Open preferences
{!info!}'l'{!normal!} - {|indent_pos:|}Enter Command Line mode
{!info!}'e'{!normal!} - {|indent_pos:|}Show the event log view ({!info!}'q'{!normal!} to go back to overview)

{!info!}'a'{!normal!} - {|indent_pos:|}Add a torrent
{!info!}Delete{!normal!} - {|indent_pos:|}Delete a torrent

{!info!}'/'{!normal!} - {|indent_pos:|}Search torrent names. \
Searching starts immediately - matching torrents are highlighted in \
green, you can cycle through them with Up/Down arrows and Home/End keys \
You can view torrent details with right arrow, open action popup with \
Enter key and exit search mode with '/' key, left arrow or \
backspace with empty search field

{!info!}'f'{!normal!} - {|indent_pos:|}Show only torrents in a certain state
      (Will open a popup where you can select the state you want to see)
{!info!}'q'{!normal!} - {|indent_pos:|}Enter queue mode

{!info!}'S'{!normal!} - {|indent_pos:|}Show or hide the sidebar

{!info!}Enter{!normal!} - {|indent_pos:|}Show torrent actions popup. Here you can do things like \
pause/resume, remove, recheck and so on. These actions \
apply to all currently marked torrents. The currently \
selected torrent is automatically marked when you press enter.

{!info!}'o'{!normal!} - {|indent_pos:|}Show and set torrent options - this will either apply \
to all selected torrents(but not the highlighted one) or currently \
selected torrent if nothing is selected

{!info!}'Q'{!normal!} - {|indent_pos:|}quit deluge-console
{!info!}'C'{!normal!} - {|indent_pos:|}show connection manager

{!info!}'m'{!normal!} - {|indent_pos:|}Mark a torrent
{!info!}'M'{!normal!} - {|indent_pos:|}Mark all torrents between currently selected torrent and last marked torrent
{!info!}'c'{!normal!} - {|indent_pos:|}Clear selection

{!info!}'v'{!normal!} - {|indent_pos:|}Show a dialog which allows you to choose columns to display
{!info!}'<' / '>'{!normal!} - {|indent_pos:|}Change column by which to sort torrents

{!info!}Right Arrow{!normal!} - {|indent_pos:|}Torrent Detail Mode. This includes more detailed information \
about the currently selected torrent, as well as a view of the \
files in the torrent and the ability to set file priorities.

{!info!}'q'/Esc{!normal!} - {|indent_pos:|}Close a popup (Note that 'q' does not work for dialogs \
where you input something
"""


class TorrentList(BaseMode, PopupsHandler):
    def __init__(self, stdscr, encoding=None):
        BaseMode.__init__(
            self, stdscr, encoding=encoding, do_refresh=False, depend=['SessionProxy']
        )
        PopupsHandler.__init__(self)
        self.messages = deque()
        self.last_mark = -1
        self.go_top = False
        self.minor_mode = None

        self.consoleui = component.get('ConsoleUI')
        self.coreconfig = self.consoleui.coreconfig
        self.config = self.consoleui.config
        self.sidebar = FilterSidebar(self, self.config)
        self.torrentview_panel = mkwin(
            curses.COLOR_GREEN,
            curses.LINES - 1,
            curses.COLS - self.sidebar.width,
            0,
            self.sidebar.width,
        )
        self.torrentview = torrentview.TorrentView(self, self.config)

        util.safe_curs_set(util.Curser.INVISIBLE)
        self.stdscr.notimeout(0)

    def torrentview_columns(self):
        return self.torrentview_panel.getmaxyx()[1]

    def on_config_changed(self):
        self.config.save()
        self.torrentview.on_config_changed()

    def toggle_sidebar(self):
        if self.config['torrentview']['show_sidebar']:
            self.sidebar.show()
            self.sidebar.resize_window(curses.LINES - 2, self.sidebar.width)
            self.torrentview_panel.resize(
                curses.LINES - 1, curses.COLS - self.sidebar.width
            )
            self.torrentview_panel.mvwin(0, self.sidebar.width)
        else:
            self.sidebar.hide()
            self.torrentview_panel.resize(curses.LINES - 1, curses.COLS)
            self.torrentview_panel.mvwin(0, 0)
        self.torrentview.update_columns()
        # After updating the columns widths, clear row cache to recreate them
        self.torrentview.cached_rows.clear()
        self.refresh()

    @overrides(Component)
    def start(self):
        self.torrentview.on_config_changed()
        self.toggle_sidebar()

        if self.config['first_run']:
            self.push_popup(
                MessagePopup(self, 'Welcome to Deluge', HELP_STR, width_req=0.65)
            )
            self.config['first_run'] = False
            self.config.save()

        if client.connected():
            self.torrentview.update(refresh=False)

    @overrides(Component)
    def update(self):
        if self.mode_paused():
            return

        if client.connected():
            self.torrentview.update(refresh=True)

    @overrides(BaseMode)
    def resume(self):
        super(TorrentList, self).resume()

    @overrides(BaseMode)
    def on_resize(self, rows, cols):
        BaseMode.on_resize(self, rows, cols)

        if self.popup:
            self.popup.handle_resize()

        if not self.consoleui.is_active_mode(self):
            return

        self.toggle_sidebar()

    def show_torrent_details(self, tid):
        mode = self.consoleui.set_mode('TorrentDetail')
        mode.update(tid)

    def set_minor_mode(self, mode):
        self.minor_mode = mode
        self.refresh()

    def _show_visible_columns_popup(self):
        self.push_popup(torrentviewcolumns.TorrentViewColumns(self))

    @overrides(BaseMode)
    def refresh(self, lines=None):
        # Something has requested we scroll to the top of the list
        if self.go_top:
            self.torrentview.cursel = 0
            self.torrentview.curoff = 0
            self.go_top = False

        if not lines:
            if not self.consoleui.is_active_mode(self):
                return
            self.stdscr.erase()

        self.add_string(1, self.torrentview.column_string, scr=self.torrentview_panel)

        # Update the status bars
        statusbar_args = {'scr': self.stdscr, 'bottombar_help': True}
        if self.torrentview.curr_filter is not None:
            statusbar_args['topbar'] = '%s    {!filterstatus!}Current filter: %s' % (
                self.statusbars.topbar,
                self.torrentview.curr_filter,
            )

        if self.minor_mode:
            self.minor_mode.set_statusbar_args(statusbar_args)

        self.draw_statusbars(**statusbar_args)

        self.torrentview.update_torrents(lines)

        if self.minor_mode:
            self.minor_mode.update_cursor()
        else:
            util.safe_curs_set(util.Curser.INVISIBLE)

        if not self.consoleui.is_active_mode(self):
            return

        self.stdscr.noutrefresh()
        self.torrentview_panel.noutrefresh()

        if not self.sidebar.hidden():
            self.sidebar.refresh()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()

    @overrides(BaseMode)
    def read_input(self):
        # Read the character
        affected_lines = None
        c = self.stdscr.getch()

        # Either ESC or ALT+<some key>
        if c == util.KEY_ESC:
            n = self.stdscr.getch()
            if n == -1:  # Means it was the escape key
                pass
            else:  # ALT+<some key>
                c = [c, n]

        if self.popup:
            ret = self.popup.handle_read(c)
            if self.popup and self.popup.closed():
                self.pop_popup()
            self.refresh()
            return ret
        if util.is_printable_chr(c):
            if chr(c) == 'Q':
                component.get('ConsoleUI').quit()
            elif chr(c) == 'C':
                self.consoleui.set_mode('ConnectionManager')
                return
            elif chr(c) == 'q':
                self.torrentview.update_marked(self.torrentview.cursel)
                self.set_minor_mode(
                    QueueMode(self, self.torrentview._selected_torrent_ids())
                )
                return
            elif chr(c) == '/':
                self.set_minor_mode(SearchMode(self))
                return

        if self.sidebar.has_focus() and c not in [curses.KEY_RIGHT]:
            self.sidebar.handle_read(c)
            self.refresh()
            return

        if self.torrentview.numtorrents < 0:
            return
        elif self.minor_mode:
            self.minor_mode.handle_read(c)
            return

        affected_lines = None
        # Hand off to torrentview
        if self.torrentview.handle_read(c) == util.ReadState.CHANGED:
            affected_lines = self.torrentview.get_input_result()

        if c == curses.KEY_LEFT:
            if not self.sidebar.has_focus():
                self.sidebar.set_focused(True)
            self.refresh()
            return
        elif c == curses.KEY_RIGHT:
            if self.sidebar.has_focus():
                self.sidebar.set_focused(False)
                self.refresh()
                return
            # We enter a new mode for the selected torrent here
            tid = self.torrentview.current_torrent_id()
            if tid:
                self.show_torrent_details(tid)
                return

        elif util.is_printable_chr(c):
            if chr(c) == 'a':
                show_torrent_add_popup(self)
            elif chr(c) == 'v':
                self._show_visible_columns_popup()
            elif chr(c) == 'h':
                self.push_popup(MessagePopup(self, 'Help', HELP_STR, width_req=0.65))
            elif chr(c) == 'p':
                mode = self.consoleui.set_mode('Preferences')
                mode.load_config()
                return
            elif chr(c) == 'e':
                self.consoleui.set_mode('EventView')
                return
            elif chr(c) == 'S':
                self.config['torrentview']['show_sidebar'] = (
                    self.config['torrentview']['show_sidebar'] is False
                )
                self.config.save()
                self.toggle_sidebar()
            elif chr(c) == 'l':
                self.consoleui.set_mode('CmdLine', refresh=True)
                return

        self.refresh(affected_lines)
