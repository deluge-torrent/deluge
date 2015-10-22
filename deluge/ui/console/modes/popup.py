# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

try:
    import curses
except ImportError:
    pass

import logging

from deluge.ui.console.modes import format_utils

log = logging.getLogger(__name__)


class ALIGN:
    TOP_LEFT = 1
    TOP_CENTER = 2
    TOP_RIGHT = 3
    MIDDLE_LEFT = 4
    MIDDLE_CENTER = 5
    MIDDLE_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_CENTER = 8
    BOTTOM_RIGHT = 9
    DEFAULT = MIDDLE_CENTER


class Popup:
    def __init__(self, parent_mode, title, width_req=0, height_req=0, align=ALIGN.DEFAULT,
                 close_cb=None, init_lines=None):
        """
        Init a new popup.  The default constructor will handle sizing and borders and the like.

        NB: The parent mode is responsible for calling refresh on any popups it wants to show.
            This should be called as the last thing in the parents refresh method.

            The parent *must* also call read_input on the popup instead of/in addition to
            running its own read_input code if it wants to have the popup handle user input.

        :param parent_mode: must be a basemode (or subclass) which the popup will be drawn over
        :parem title: string, the title of the popup window

        Popups have two methods that must be implemented:

        refresh(self) - draw the popup window to screen.  this default mode simply draws a bordered window
                        with the supplied title to the screen

        add_string(self, row, string) - add string at row. handles triming/ignoring if the string won't fit in the popup

        read_input(self) - handle user input to the popup.
        """
        self.parent = parent_mode

        self.height_req = height_req
        self.width_req = width_req
        self.align = align

        self.handle_resize()

        self.title = title
        self.close_cb = close_cb

        self.divider = None
        self.lineoff = 0
        if init_lines:
            self._lines = init_lines
        else:
            self._lines = []

    def _refresh_lines(self):
        crow = 1
        for line in self._lines[self.lineoff:]:
            if crow >= self.height - 1:
                break
            self.parent.add_string(crow, line, self.screen, 1, False, True)
            crow += 1

    def handle_resize(self):
        if isinstance(self.height_req, float) and 0.0 < self.height_req <= 1.0:
            hr = int((self.parent.rows - 2) * self.height_req)
        else:
            hr = self.height_req

        if isinstance(self.width_req, float) and 0.0 < self.width_req <= 1.0:
            wr = int((self.parent.cols - 2) * self.width_req)
        else:
            wr = self.width_req

        log.debug("Resizing(or creating) popup window")

        # Height
        if hr == 0:
            hr = int(self.parent.rows / 2)
        elif hr == -1:
            hr = self.parent.rows - 2
        elif hr > self.parent.rows - 2:
            hr = self.parent.rows - 2

        # Width
        if wr == 0:
            wr = int(self.parent.cols / 2)
        elif wr == -1:
            wr = self.parent.cols
        elif wr >= self.parent.cols:
            wr = self.parent.cols

        if self.align in [ALIGN.TOP_CENTER, ALIGN.TOP_LEFT, ALIGN.TOP_RIGHT]:
            by = 1
        elif self.align in [ALIGN.MIDDLE_CENTER, ALIGN.MIDDLE_LEFT, ALIGN.MIDDLE_RIGHT]:
            by = (self.parent.rows / 2) - (hr / 2)
        elif self.align in [ALIGN.BOTTOM_CENTER, ALIGN.BOTTOM_LEFT, ALIGN.BOTTOM_RIGHT]:
            by = self.parent.rows - hr - 1

        if self.align in [ALIGN.TOP_LEFT, ALIGN.MIDDLE_LEFT, ALIGN.BOTTOM_LEFT]:
            bx = 0
        elif self.align in [ALIGN.TOP_CENTER, ALIGN.MIDDLE_CENTER, ALIGN.BOTTOM_CENTER]:
            bx = (self.parent.cols / 2) - (wr / 2)
        elif self.align in [ALIGN.TOP_RIGHT, ALIGN.MIDDLE_RIGHT, ALIGN.BOTTOM_RIGHT]:
            bx = self.parent.cols - wr - 1

        self.screen = curses.newwin(hr, wr, by, bx)

        self.x, self.y = bx, by
        self.height, self.width = self.screen.getmaxyx()

    def refresh(self):
        self.screen.erase()
        self.screen.border(0, 0, 0, 0)
        toff = max(1, (self.width // 2) - (len(self.title) // 2))
        self.parent.add_string(0, "{!white,black,bold!}%s" % self.title, self.screen, toff, False, True)

        self._refresh_lines()
        if len(self._lines) > (self.height - 2):
            lts = len(self._lines) - (self.height - 3)
            perc_sc = float(self.lineoff) / lts
            sb_pos = int((self.height - 2) * perc_sc) + 1
            if (sb_pos == 1) and (self.lineoff != 0):
                sb_pos += 1
            self.parent.add_string(sb_pos, "{!red,black,bold!}#", self.screen, col=(self.width - 1),
                                   pad=False, trim=False)

        self.screen.redrawwin()
        self.screen.noutrefresh()

    def clear(self):
        self._lines = []

    def handle_read(self, c):
        p_off = self.height - 3
        if c == curses.KEY_UP:
            self.lineoff = max(0, self.lineoff - 1)
        elif c == curses.KEY_PPAGE:
            self.lineoff = max(0, self.lineoff - p_off)
        elif c == curses.KEY_HOME:
            self.lineoff = 0
        elif c == curses.KEY_DOWN:
            if len(self._lines) - self.lineoff > (self.height - 2):
                self.lineoff += 1
        elif c == curses.KEY_NPAGE:
            self.lineoff = min(len(self._lines) - self.height + 2, self.lineoff + p_off)
        elif c == curses.KEY_END:
            self.lineoff = len(self._lines) - self.height + 2

        elif c == curses.KEY_ENTER or c == 10 or c == 27:  # close on enter/esc
            if self.close_cb:
                self.close_cb()
            return True  # close the popup

        if c > 31 and c < 256 and chr(c) == "q":
            if self.close_cb:
                self.close_cb()
            return True  # close the popup

        self.refresh()

        return False

    def set_title(self, title):
        self.title = title

    def add_line(self, string):
        self._lines.append(string)

    def add_divider(self):
        if not self.divider:
            self.divider = "-" * (self.width - 2)
        self._lines.append(self.divider)


class SelectablePopup(Popup):
    """
    A popup which will let the user select from some of the lines that
    are added.
    """
    def __init__(self, parent_mode, title, selection_callback, args=(), align=ALIGN.DEFAULT, immediate_action=False):
        Popup.__init__(self, parent_mode, title, align=align)
        self._selection_callback = selection_callback
        self._selection_args = args
        self._selectable_lines = []

        self._immediate_action = immediate_action

        self._select_data = []
        self._line_foregrounds = []
        self._udxs = {}
        self._hotkeys = {}
        self._selected = -1

    def add_line(self, string, selectable=True, use_underline=True, data=None, foreground=None):
        if use_underline:
            udx = string.find("_")
            if udx >= 0:
                string = string[:udx] + string[udx + 1:]
                self._udxs[len(self._lines) + 1] = udx
                c = string[udx].lower()
                self._hotkeys[c] = len(self._lines)
        Popup.add_line(self, string)
        self._line_foregrounds.append(foreground)
        if selectable:
            self._selectable_lines.append(len(self._lines) - 1)
            self._select_data.append(data)
            if self._selected < 0:
                self._selected = (len(self._lines) - 1)

    def _refresh_lines(self):
        crow = 1
        for row, line in enumerate(self._lines):
            if crow >= self.height - 1:
                break
            if row < self.lineoff:
                continue
            fg = self._line_foregrounds[row]
            udx = self._udxs.get(crow)
            if row == self._selected:
                if fg is None:
                    fg = "black"
                colorstr = "{!%s,white,bold!}" % fg
                if udx >= 0:
                    ustr = "{!%s,white,bold,underline!}" % fg
            else:
                if fg is None:
                    fg = "white"
                colorstr = "{!%s,black!}" % fg
                if udx >= 0:
                    ustr = "{!%s,black,underline!}" % fg
            if udx == 0:
                self.parent.add_string(crow, "- %s%c%s%s" % (
                    ustr, line[0], colorstr, line[1:]), self.screen, 1, False, True)
            elif udx > 0:
                # well, this is a litte gross
                self.parent.add_string(crow, "- %s%s%s%c%s%s" % (
                    colorstr, line[:udx], ustr, line[udx], colorstr, line[udx + 1:]), self.screen, 1, False, True)
            else:
                self.parent.add_string(crow, "- %s%s" % (colorstr, line), self.screen, 1, False, True)
            crow += 1

    def current_selection(self):
        "Returns a tuple of (selected index, selected data)"
        idx = self._selectable_lines.index(self._selected)
        return (idx, self._select_data[idx])

    def add_divider(self, color="white"):
        if not self.divider:
            self.divider = "-" * (self.width - 6) + " -"
        self._lines.append(self.divider)
        self._line_foregrounds.append(color)

    def _move_cursor_up(self, amount):
        if self._selectable_lines.index(self._selected) > amount:
            idx = self._selectable_lines.index(self._selected)
            self._selected = self._selectable_lines[idx - amount]
        else:
            self._selected = self._selectable_lines[0]

        if self._immediate_action:
            self._selection_callback(idx, self._select_data[idx], *self._selection_args)

    def _move_cursor_down(self, amount):
        idx = self._selectable_lines.index(self._selected)
        if idx < len(self._selectable_lines) - amount:
            self._selected = self._selectable_lines[idx + amount]
        else:
            self._selected = self._selectable_lines[-1]

        if self._immediate_action:
            self._selection_callback(idx, self._select_data[idx], *self._selection_args)

    def handle_read(self, c):
        if c == curses.KEY_UP:
            self._move_cursor_up(1)
        elif c == curses.KEY_DOWN:
            self._move_cursor_down(1)

        elif c == curses.KEY_PPAGE:
            self._move_cursor_up(4)
        elif c == curses.KEY_NPAGE:
            self._move_cursor_down(4)

        elif c == curses.KEY_HOME:
            self._move_cursor_up(len(self._selectable_lines))
        elif c == curses.KEY_END:
            self._move_cursor_down(len(self._selectable_lines))

        elif c == 27:  # close on esc, no action
            return True

        elif c == curses.KEY_ENTER or c == 10:
            idx = self._selectable_lines.index(self._selected)
            return self._selection_callback(idx, self._select_data[idx], *self._selection_args)

        if c > 31 and c < 256:
            if chr(c) == "q":
                return True  # close the popup
            uc = chr(c).lower()
            if uc in self._hotkeys:
                # exec hotkey action
                idx = self._selectable_lines.index(self._hotkeys[uc])
                return self._selection_callback(idx, self._select_data[idx], *self._selection_args)
        self.refresh()

        return False


class MessagePopup(Popup):
    """
    Popup that just displays a message
    """
    def __init__(self, parent_mode, title, message, align=ALIGN.DEFAULT, width_req=0.5):
        self.message = message
        # self.width= int(parent_mode.cols/2)
        Popup.__init__(self, parent_mode, title, align=align, width_req=width_req)
        lns = format_utils.wrap_string(self.message, self.width - 2, 3, True)
        self.height_req = min(len(lns) + 2, int(parent_mode.rows * 2 / 3))
        self.handle_resize()
        self._lines = lns

    def handle_resize(self):
        Popup.handle_resize(self)
        self.clear()
        self._lines = format_utils.wrap_string(self.message, self.width - 2, 3, True)
