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

from deluge.decorators import overrides
from deluge.ui.console.modes.basemode import InputKeyHandler, move_cursor
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.widgets.fields import (
    CheckedInput,
    CheckedPlusInput,
    ComboInput,
    DividerField,
    FloatSpinInput,
    Header,
    InfoField,
    IntSpinInput,
    NoInputField,
    SelectInput,
    TextArea,
    TextField,
    TextInput,
)

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


class BaseInputPane(InputKeyHandler):
    def __init__(
        self,
        mode,
        allow_rearrange=False,
        immediate_action=False,
        set_first_input_active=True,
        border_off_west=0,
        border_off_north=0,
        border_off_east=0,
        border_off_south=0,
        active_wrap=False,
        **kwargs
    ):
        InputKeyHandler.__init__(self)
        self.inputs = []
        self.mode = mode
        self.active_input = 0
        self.set_first_input_active = set_first_input_active
        self.allow_rearrange = allow_rearrange
        self.immediate_action = immediate_action
        self.move_active_many = 4
        self.active_wrap = active_wrap
        self.lineoff = 0
        self.border_off_west = border_off_west
        self.border_off_north = border_off_north
        self.border_off_east = border_off_east
        self.border_off_south = border_off_south
        self.last_lineoff_move = 0

        if not hasattr(self, 'visible_content_pane_height'):
            log.error(
                'The class "%s" does not have the attribute "%s" required by super class "%s"',
                self.__class__.__name__,
                'visible_content_pane_height',
                BaseInputPane.__name__,
            )
            raise AttributeError('visible_content_pane_height')

    @property
    def visible_content_pane_width(self):
        return self.mode.width

    def add_spaces(self, num):
        string = ''
        for i in range(num):
            string += '\n'

        self.add_text_area('space %d' % len(self.inputs), string)

    def add_text(self, string):
        self.add_text_area('', string)

    def move(self, r, c):
        self._cursor_row = r
        self._cursor_col = c

    def get_input(self, name):
        for e in self.inputs:
            if e.name == name:
                return e

    def _add_input(self, input_element):
        for e in self.inputs:
            if isinstance(e, NoInputField):
                continue
            if e.name == input_element.name:
                import traceback

                log.warning(
                    'Input element with name "%s" already exists in input pane (%s):\n%s',
                    input_element.name,
                    e,
                    ''.join(traceback.format_stack(limit=5)),
                )
                return

        self.inputs.append(input_element)
        if self.set_first_input_active and input_element.selectable():
            self.active_input = len(self.inputs) - 1
            self.set_first_input_active = False
        return input_element

    def add_header(self, header, space_above=False, space_below=False, **kwargs):
        return self._add_input(Header(self, header, space_above, space_below, **kwargs))

    def add_info_field(self, name, label, value):
        return self._add_input(InfoField(self, name, label, value))

    def add_text_field(self, name, message, selectable=True, col='+1', **kwargs):
        return self._add_input(
            TextField(self, name, message, selectable=selectable, col=col, **kwargs)
        )

    def add_text_area(self, name, message, **kwargs):
        return self._add_input(TextArea(self, name, message, **kwargs))

    def add_divider_field(self, name, message, **kwargs):
        return self._add_input(DividerField(self, name, message, **kwargs))

    def add_text_input(self, name, message, value='', col='+1', **kwargs):
        """
        Add a text input field

        :param message: string to display above the input field
        :param name: name of the field, for the return callback
        :param value: initial value of the field
        :param complete: should completion be run when tab is hit and this field is active
        """
        return self._add_input(
            TextInput(
                self,
                name,
                message,
                self.move,
                self.visible_content_pane_width,
                value,
                col=col,
                **kwargs
            )
        )

    def add_select_input(self, name, message, opts, vals, default_index=0, **kwargs):
        return self._add_input(
            SelectInput(self, name, message, opts, vals, default_index, **kwargs)
        )

    def add_checked_input(self, name, message, checked=False, col='+1', **kwargs):
        return self._add_input(
            CheckedInput(self, name, message, checked=checked, col=col, **kwargs)
        )

    def add_checkedplus_input(
        self, name, message, child, checked=False, col='+1', **kwargs
    ):
        return self._add_input(
            CheckedPlusInput(
                self, name, message, child, checked=checked, col=col, **kwargs
            )
        )

    def add_float_spin_input(self, name, message, value=0.0, col='+1', **kwargs):
        return self._add_input(
            FloatSpinInput(self, name, message, self.move, value, col=col, **kwargs)
        )

    def add_int_spin_input(self, name, message, value=0, col='+1', **kwargs):
        return self._add_input(
            IntSpinInput(self, name, message, self.move, value, col=col, **kwargs)
        )

    def add_combo_input(self, name, message, choices, col='+1', **kwargs):
        return self._add_input(
            ComboInput(self, name, message, choices, col=col, **kwargs)
        )

    @overrides(InputKeyHandler)
    def handle_read(self, c):
        if not self.inputs:  # no inputs added yet
            return util.ReadState.IGNORED
        ret = self.inputs[self.active_input].handle_read(c)
        if ret != util.ReadState.IGNORED:
            if self.immediate_action:
                self.immediate_action_cb(
                    state_changed=False if ret == util.ReadState.READ else True
                )
            return ret

        ret = util.ReadState.READ

        if c == curses.KEY_UP:
            self.move_active_up(1)
        elif c == curses.KEY_DOWN:
            self.move_active_down(1)
        elif c == curses.KEY_HOME:
            self.move_active_up(len(self.inputs))
        elif c == curses.KEY_END:
            self.move_active_down(len(self.inputs))
        elif c == curses.KEY_PPAGE:
            self.move_active_up(self.move_active_many)
        elif c == curses.KEY_NPAGE:
            self.move_active_down(self.move_active_many)
        elif c == util.KEY_ALT_AND_ARROW_UP:
            self.lineoff = max(self.lineoff - 1, 0)
        elif c == util.KEY_ALT_AND_ARROW_DOWN:
            tot_height = self.get_content_height()
            self.lineoff = min(
                self.lineoff + 1, tot_height - self.visible_content_pane_height
            )
        elif c == util.KEY_CTRL_AND_ARROW_UP:
            if not self.allow_rearrange:
                return ret
            val = self.inputs.pop(self.active_input)
            self.active_input -= 1
            self.inputs.insert(self.active_input, val)
            if self.immediate_action:
                self.immediate_action_cb(state_changed=True)
        elif c == util.KEY_CTRL_AND_ARROW_DOWN:
            if not self.allow_rearrange:
                return ret
            val = self.inputs.pop(self.active_input)
            self.active_input += 1
            self.inputs.insert(self.active_input, val)
            if self.immediate_action:
                self.immediate_action_cb(state_changed=True)
        else:
            ret = util.ReadState.IGNORED
        return ret

    def get_values(self):
        vals = {}
        for i, ipt in enumerate(self.inputs):
            if not ipt.has_input():
                continue
            vals[ipt.name] = {
                'value': ipt.get_value(),
                'order': i,
                'active': self.active_input == i,
            }
        return vals

    def immediate_action_cb(self, state_changed=True):
        pass

    def move_active(self, direction, amount):
        """
        direction == -1: Up
        direction ==  1: Down

        """
        self.last_lineoff_move = direction * amount

        if direction > 0:
            if self.active_wrap:
                limit = self.active_input - 1
                if limit < 0:
                    limit = len(self.inputs) + limit
            else:
                limit = len(self.inputs) - 1
        else:
            limit = 0
            if self.active_wrap:
                limit = self.active_input + 1

        def next_move(nc, direction, limit):
            next_index = nc
            while next_index != limit:
                next_index += direction
                if direction > 0:
                    next_index %= len(self.inputs)
                elif next_index < 0:
                    next_index = len(self.inputs) + next_index

                if self.inputs[next_index].selectable():
                    return next_index
                if next_index == limit:
                    return nc
            return nc

        next_sel = self.active_input
        for a in range(amount):
            cur_sel = next_sel
            next_sel = next_move(next_sel, direction, limit)
            if cur_sel == next_sel:
                tot_height = (
                    self.get_content_height()
                    + self.border_off_north
                    + self.border_off_south
                )
                if direction > 0:
                    self.lineoff = min(
                        self.lineoff + 1, tot_height - self.visible_content_pane_height
                    )
                else:
                    self.lineoff = max(self.lineoff - 1, 0)

        if next_sel is not None:
            self.active_input = next_sel

    def move_active_up(self, amount):
        self.move_active(-1, amount)
        if self.immediate_action:
            self.immediate_action_cb(state_changed=False)

    def move_active_down(self, amount):
        self.move_active(1, amount)
        if self.immediate_action:
            self.immediate_action_cb(state_changed=False)

    def get_content_height(self):
        height = 0
        for i, ipt in enumerate(self.inputs):
            if ipt.depend_skip():
                continue
            height += ipt.height
        return height

    def ensure_active_visible(self):
        start_row = 0
        end_row = self.border_off_north
        for i, ipt in enumerate(self.inputs):
            if ipt.depend_skip():
                continue
            start_row = end_row
            end_row += ipt.height
            if i != self.active_input or not ipt.has_input():
                continue
            height = self.visible_content_pane_height
            if end_row > height + self.lineoff:
                self.lineoff += end_row - (
                    height + self.lineoff
                )  # Correct result depends on paranthesis
            elif start_row < self.lineoff:
                self.lineoff -= self.lineoff - start_row
            break

    def render_inputs(self, focused=False):
        self._cursor_row = -1
        self._cursor_col = -1
        util.safe_curs_set(util.Curser.INVISIBLE)

        self.ensure_active_visible()

        crow = self.border_off_north
        for i, ipt in enumerate(self.inputs):
            if ipt.depend_skip():
                continue
            col = self.border_off_west
            field_width = self.width - self.border_off_east - self.border_off_west
            cursor_offset = self.border_off_west

            if ipt.default_col != -1:
                default_col = int(ipt.default_col)
                if isinstance(ipt.default_col, ''.__class__) and ipt.default_col[0] in [
                    '+',
                    '-',
                ]:
                    col += default_col
                    cursor_offset += default_col
                    field_width -= default_col  # Increase to col must be reflected here
                else:
                    col = default_col
            crow += ipt.render(
                self.screen,
                crow,
                width=field_width,
                active=i == self.active_input,
                focused=focused,
                col=col,
                cursor_offset=cursor_offset,
            )

        if self._cursor_row >= 0:
            util.safe_curs_set(util.Curser.VERY_VISIBLE)
            move_cursor(self.screen, self._cursor_row, self._cursor_col)
