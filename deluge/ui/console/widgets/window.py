# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from deluge.ui.console.modes.basemode import add_string, mkpad, mkpanel
from deluge.ui.console.utils.colors import get_color_pair

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


class BaseWindow(object):
    """
    BaseWindow creates a curses screen to be used for showing panels and popup dialogs
    """

    def __init__(self, title, width, height, posy=0, posx=0, encoding=None):
        """
        Args:
            title (str): The title of the panel
            width (int): Width of the panel
            height (int): Height of the panel
            posy (int): Position of the panel's first row relative to the terminal screen
            posx (int): Position of the panel's first column relative to the terminal screen
            encoding (str): Terminal encoding
        """
        self.title = title
        self.posy, self.posx = posy, posx
        if encoding is None:
            from deluge import component

            encoding = component.get('ConsoleUI').encoding
        self.encoding = encoding

        self.panel = mkpanel(curses.COLOR_GREEN, height, width, posy, posx)
        self.outer_screen = self.panel.window()
        self.outer_screen.bkgdset(0, curses.COLOR_RED)
        by, bx = self.outer_screen.getbegyx()
        self.screen = mkpad(get_color_pair('white', 'black'), height - 1, width - 2)
        self._height, self._width = self.outer_screen.getmaxyx()

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    def add_string(self, row, string, scr=None, **kwargs):
        scr = scr if scr else self.screen
        add_string(row, string, scr, self.encoding, **kwargs)

    def hide(self):
        self.panel.hide()

    def show(self):
        self.panel.show()

    def hidden(self):
        return self.panel.hidden()

    def set_title(self, title):
        self.title = title

    @property
    def visible_content_pane_size(self):
        y, x = self.outer_screen.getmaxyx()
        return (y - 2, x - 2)

    @property
    def visible_content_pane_height(self):
        y, x = self.visible_content_pane_size
        return y

    @property
    def visible_content_pane_width(self):
        y, x = self.visible_content_pane_size
        return x

    def getmaxyx(self):
        return self.screen.getmaxyx()

    def resize_window(self, rows, cols):
        self.outer_screen.resize(rows, cols)
        self.screen.resize(rows - 2, cols - 2)
        self._height, self._width = rows, cols

    def move_window(self, posy, posx):
        posy = int(posy)
        posx = int(posx)
        self.outer_screen.mvwin(posy, posx)
        self.posy = posy
        self.posx = posx
        self._height, self._width = self.screen.getmaxyx()

    def ensure_content_pane_height(self, height):
        max_y, max_x = self.screen.getmaxyx()
        if max_y < height:
            self.screen.resize(height, max_x)

    def draw_scroll_indicator(self, screen):
        content_height = self.get_content_height()
        if content_height <= self.visible_content_pane_height:
            return

        percent_scroll = float(self.lineoff) / (
            content_height - self.visible_content_pane_height
        )
        indicator_row = int(self.visible_content_pane_height * percent_scroll) + 1

        # Never greater than height
        indicator_row = min(indicator_row, self.visible_content_pane_height)
        indicator_col = self.width + 1

        add_string(
            indicator_row,
            '{!red,black,bold!}#',
            screen,
            self.encoding,
            col=indicator_col,
            pad=False,
            trim=False,
        )

    def refresh(self):
        height, width = self.visible_content_pane_size
        self.outer_screen.erase()
        self.outer_screen.border(0, 0, 0, 0)

        if self.title:
            toff = max(1, (self.width // 2) - (len(self.title) // 2))
            self.add_string(
                0,
                '{!white,black,bold!}%s' % self.title,
                scr=self.outer_screen,
                col=toff,
                pad=False,
            )

        self.draw_scroll_indicator(self.outer_screen)
        self.outer_screen.noutrefresh()

        try:
            # pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol
            # the p arguments refer to the upper left corner of the pad region to be displayed and
            # the s arguments define a clipping box on the screen within which the pad region is to be displayed.
            pminrow = self.lineoff
            pmincol = 0
            sminrow = self.posy + 1
            smincol = self.posx + 1
            smaxrow = height + self.posy
            smaxcol = width + self.posx
            self.screen.noutrefresh(
                pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol
            )
        except curses.error as ex:
            import traceback

            log.warning(
                'Error on screen.noutrefresh(%s, %s, %s, %s, %s, %s) Error: %s\nStack: %s',
                pminrow,
                pmincol,
                sminrow,
                smincol,
                smaxrow,
                smaxcol,
                ex,
                ''.join(traceback.format_stack()),
            )
