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

from deluge.decorators import overrides
from deluge.ui.console.modes.basemode import InputKeyHandler
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.utils import format_utils
from deluge.ui.console.widgets import BaseInputPane, BaseWindow

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


class ALIGN(object):
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


class PopupsHandler(object):
    def __init__(self):
        self._popups = []

    @property
    def popup(self):
        if self._popups:
            return self._popups[-1]
        return None

    def push_popup(self, pu, clear=False):
        if clear:
            self._popups = []
        self._popups.append(pu)

    def pop_popup(self):
        if self.popup:
            return self._popups.pop()

    def report_message(self, title, message):
        self.push_popup(MessagePopup(self, title, message))


class Popup(BaseWindow, InputKeyHandler):
    def __init__(
        self,
        parent_mode,
        title,
        width_req=0,
        height_req=0,
        align=ALIGN.DEFAULT,
        close_cb=None,
        encoding=None,
        base_popup=None,
        **kwargs
    ):
        """
        Init a new popup.  The default constructor will handle sizing and borders and the like.

        Args:
            parent_mode (basemode subclass): The mode which the popup will be drawn over
            title (str): the title of the popup window
            width_req (int or float): An integer value will be used as the width of the popup in character.
                                      A float value will indicate the requested ratio in relation to the
                                      parents screen width.
            height_req (int or float): An integer value will be used as the height of the popup in character.
                                       A float value will indicate the requested ratio in relation to the
                                       parents screen height.
            align (ALIGN): The alignment controlling the position of the popup on the screen.
            close_cb (func): Function to be called when the popup is closed
            encoding (str): The terminal encoding
            base_popup (Popup): A popup used to inherit width_req and height_req if not explicitly specified.

        Note: The parent mode is responsible for calling refresh on any popups it wants to show.
            This should be called as the last thing in the parents refresh method.

            The parent *must* also call read_input on the popup instead of/in addition to
            running its own read_input code if it wants to have the popup handle user input.

        Popups have two methods that must be implemented:

        refresh(self) - draw the popup window to screen.  this default mode simply draws a bordered window
                        with the supplied title to the screen

        read_input(self) - handle user input to the popup.

        """
        InputKeyHandler.__init__(self)
        self.parent = parent_mode
        self.close_cb = close_cb
        self.height_req = height_req
        self.width_req = width_req
        self.align = align
        if base_popup:
            if not self.width_req:
                self.width_req = base_popup.width_req
            if not self.height_req:
                self.height_req = base_popup.height_req

        hr, wr, posy, posx = self.calculate_size()
        BaseWindow.__init__(self, title, wr, hr, encoding=None)
        self.move_window(posy, posx)
        self._closed = False

    @overrides(BaseWindow)
    def refresh(self):
        self.screen.erase()
        height = self.get_content_height()
        self.ensure_content_pane_height(
            height + self.border_off_north + self.border_off_south
        )
        BaseInputPane.render_inputs(self, focused=True)
        BaseWindow.refresh(self)

    def calculate_size(self):

        if isinstance(self.height_req, float) and 0.0 < self.height_req <= 1.0:
            height = int((self.parent.rows - 2) * self.height_req)
        else:
            height = self.height_req

        if isinstance(self.width_req, float) and 0.0 < self.width_req <= 1.0:
            width = int((self.parent.cols - 2) * self.width_req)
        else:
            width = self.width_req

        # Height
        if height == 0:
            height = int(self.parent.rows / 2)
        elif height == -1:
            height = self.parent.rows - 2
        elif height > self.parent.rows - 2:
            height = self.parent.rows - 2

        # Width
        if width == 0:
            width = int(self.parent.cols / 2)
        elif width == -1:
            width = self.parent.cols
        elif width >= self.parent.cols:
            width = self.parent.cols

        if self.align in [ALIGN.TOP_CENTER, ALIGN.TOP_LEFT, ALIGN.TOP_RIGHT]:
            begin_y = 1
        elif self.align in [ALIGN.MIDDLE_CENTER, ALIGN.MIDDLE_LEFT, ALIGN.MIDDLE_RIGHT]:
            begin_y = (self.parent.rows / 2) - (height / 2)
        elif self.align in [ALIGN.BOTTOM_CENTER, ALIGN.BOTTOM_LEFT, ALIGN.BOTTOM_RIGHT]:
            begin_y = self.parent.rows - height - 1

        if self.align in [ALIGN.TOP_LEFT, ALIGN.MIDDLE_LEFT, ALIGN.BOTTOM_LEFT]:
            begin_x = 0
        elif self.align in [ALIGN.TOP_CENTER, ALIGN.MIDDLE_CENTER, ALIGN.BOTTOM_CENTER]:
            begin_x = (self.parent.cols / 2) - (width / 2)
        elif self.align in [ALIGN.TOP_RIGHT, ALIGN.MIDDLE_RIGHT, ALIGN.BOTTOM_RIGHT]:
            begin_x = self.parent.cols - width

        return height, width, begin_y, begin_x

    def handle_resize(self):
        height, width, begin_y, begin_x = self.calculate_size()
        self.resize_window(height, width)
        self.move_window(begin_y, begin_x)

    def closed(self):
        return self._closed

    def close(self, *args, **kwargs):
        self._closed = True
        if kwargs.get('call_cb', True):
            self._call_close_cb(*args)
        self.panel.hide()

    def _call_close_cb(self, *args, **kwargs):
        if self.close_cb:
            self.close_cb(*args, base_popup=self, **kwargs)

    @overrides(InputKeyHandler)
    def handle_read(self, c):
        if c == util.KEY_ESC:  # close on esc, no action
            self.close(None)
            return util.ReadState.READ
        return util.ReadState.IGNORED


class SelectablePopup(BaseInputPane, Popup):
    """
    A popup which will let the user select from some of the lines that are added.
    """

    def __init__(
        self,
        parent_mode,
        title,
        selection_cb,
        close_cb=None,
        input_cb=None,
        allow_rearrange=False,
        immediate_action=False,
        **kwargs
    ):
        """
        Args:
            parent_mode (basemode subclass): The mode which the popup will be drawn over
            title (str): the title of the popup window
            selection_cb (func): Function to be called on selection
            close_cb (func, optional): Function to be called when the popup is closed
            input_cb (func, optional): Function to be called on every keyboard input
            allow_rearrange (bool): Allow rearranging the selectable value
            immediate_action (bool): If immediate_action_cb should be called for every action
            kwargs (dict): Arguments passed to Popup

        """
        Popup.__init__(self, parent_mode, title, close_cb=close_cb, **kwargs)
        kwargs.update(
            {'allow_rearrange': allow_rearrange, 'immediate_action': immediate_action}
        )
        BaseInputPane.__init__(self, self, **kwargs)
        self.selection_cb = selection_cb
        self.input_cb = input_cb
        self.hotkeys = {}
        self.cb_arg = {}
        self.cb_args = kwargs.get('cb_args', {})
        if 'base_popup' not in self.cb_args:
            self.cb_args['base_popup'] = self

    @property
    @overrides(BaseWindow)
    def visible_content_pane_height(self):
        """We want to use the Popup property"""
        return Popup.visible_content_pane_height.fget(self)

    def current_selection(self):
        """Returns a tuple of (selected index, selected data)."""
        return self.active_input

    def set_selection(self, index):
        """Set a selected index"""
        self.active_input = index

    def add_line(
        self,
        name,
        string,
        use_underline=True,
        cb_arg=None,
        foreground=None,
        selectable=True,
        selected=False,
        **kwargs
    ):
        hotkey = None
        self.cb_arg[name] = cb_arg
        if use_underline:
            udx = string.find('_')
            if udx >= 0:
                hotkey = string[udx].lower()
                string = (
                    string[:udx]
                    + '{!+underline!}'
                    + string[udx + 1]
                    + '{!-underline!}'
                    + string[udx + 2 :]
                )

        kwargs['selectable'] = selectable
        if foreground:
            kwargs['color_active'] = '%s,white' % foreground
            kwargs['color'] = '%s,black' % foreground

        field = self.add_text_field(name, string, **kwargs)
        if hotkey:
            self.hotkeys[hotkey] = field

        if selected:
            self.set_selection(len(self.inputs) - 1)

    @overrides(Popup, BaseInputPane)
    def handle_read(self, c):
        if c in [curses.KEY_ENTER, util.KEY_ENTER2]:
            for k, v in self.get_values().items():
                if v['active']:
                    if self.selection_cb(k, **dict(self.cb_args, data=self.cb_arg)):
                        self.close(None)
            return util.ReadState.READ
        else:
            ret = BaseInputPane.handle_read(self, c)
            if ret != util.ReadState.IGNORED:
                return ret
            ret = Popup.handle_read(self, c)
            if ret != util.ReadState.IGNORED:
                if self.selection_cb(None):
                    self.close(None)
                return ret

            if self.input_cb:
                self.input_cb(c)

        self.refresh()
        return util.ReadState.IGNORED

    def add_divider(self, message=None, char='-', fill_width=True, color='white'):
        if message is not None:
            fill_width = False
        else:
            message = char
        self.add_divider_field('', message, selectable=False, fill_width=fill_width)


class MessagePopup(Popup, BaseInputPane):
    """
    Popup that just displays a message
    """

    def __init__(
        self,
        parent_mode,
        title,
        message,
        align=ALIGN.DEFAULT,
        height_req=0.75,
        width_req=0.5,
        **kwargs
    ):
        self.message = message
        Popup.__init__(
            self,
            parent_mode,
            title,
            align=align,
            height_req=height_req,
            width_req=width_req,
        )
        BaseInputPane.__init__(self, self, immediate_action=True, **kwargs)
        lns = format_utils.wrap_string(self.message, self.width - 3, 3, True)

        if isinstance(self.height_req, float):
            self.height_req = min(len(lns) + 2, int(parent_mode.rows * self.height_req))

        self.handle_resize()
        self.no_refresh = False
        self.add_text_area('TextMessage', message)

    @overrides(Popup, BaseInputPane)
    def handle_read(self, c):
        ret = BaseInputPane.handle_read(self, c)
        if ret != util.ReadState.IGNORED:
            return ret
        return Popup.handle_read(self, c)


class InputPopup(Popup, BaseInputPane):
    def __init__(self, parent_mode, title, **kwargs):
        Popup.__init__(self, parent_mode, title, **kwargs)
        BaseInputPane.__init__(self, self, **kwargs)
        # We need to replicate some things in order to wrap our inputs
        self.encoding = parent_mode.encoding

    def _handle_callback(self, state_changed=True, close=True):
        self._call_close_cb(self.get_values(), state_changed=state_changed, close=close)

    @overrides(BaseInputPane)
    def immediate_action_cb(self, state_changed=True):
        self._handle_callback(state_changed=state_changed, close=False)

    @overrides(Popup, BaseInputPane)
    def handle_read(self, c):
        ret = BaseInputPane.handle_read(self, c)
        if ret != util.ReadState.IGNORED:
            return ret

        if c in [curses.KEY_ENTER, util.KEY_ENTER2]:
            if self.close_cb:
                self._handle_callback(state_changed=False, close=False)
                util.safe_curs_set(util.Curser.INVISIBLE)
            return util.ReadState.READ
        elif c == util.KEY_ESC:  # close on esc, no action
            self._handle_callback(state_changed=False, close=True)
            self.close(None)
            return util.ReadState.READ

        self.refresh()
        return util.ReadState.READ
