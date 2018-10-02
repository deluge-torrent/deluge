# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import curses
import logging

from deluge.decorators import overrides
from deluge.ui.console.modes.basemode import add_string
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.widgets import BaseInputPane, BaseWindow

log = logging.getLogger(__name__)


class Sidebar(BaseInputPane, BaseWindow):
    """Base sidebar widget that handles choosing a selected widget
    with Up/Down arrows.

    Shows the different states of the torrents and allows to filter the
    torrents based on state.

    """

    def __init__(
        self, torrentlist, width, height, title=None, allow_resize=False, **kwargs
    ):
        BaseWindow.__init__(self, title, width, height, posy=1)
        BaseInputPane.__init__(self, self, immediate_action=True, **kwargs)
        self.parent = torrentlist
        self.focused = False
        self.allow_resize = allow_resize

    def set_focused(self, focused):
        self.focused = focused

    def has_focus(self):
        return self.focused and not self.hidden()

    @overrides(BaseInputPane)
    def handle_read(self, c):
        if c == curses.KEY_UP:
            self.move_active_up(1)
        elif c == curses.KEY_DOWN:
            self.move_active_down(1)
        elif self.allow_resize and c in [ord('+'), ord('-')]:
            width = self.visible_content_pane_width + (1 if c == ord('+') else -1)
            self.on_resize(width)
        else:
            return BaseInputPane.handle_read(self, c)
        return util.ReadState.READ

    def on_resize(self, width):
        self.resize_window(self.height, width)

    @overrides(BaseWindow)
    def refresh(self):
        height = self.get_content_height()
        self.ensure_content_pane_height(
            height + self.border_off_north + self.border_off_south
        )
        BaseInputPane.render_inputs(self, focused=self.has_focus())
        BaseWindow.refresh(self)

    def _refresh(self):
        self.screen.erase()
        height = self.get_content_height()
        self.ensure_content_pane_height(
            height + self.border_off_north + self.border_off_south
        )
        BaseInputPane.render_inputs(self, focused=True)
        BaseWindow.refresh(self)

    def add_string(self, row, string, scr=None, **kwargs):
        add_string(row, string, self.screen, self.parent.encoding, **kwargs)
