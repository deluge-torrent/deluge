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
import os

from deluge.common import PY2
from deluge.decorators import overrides
from deluge.ui.console.modes.basemode import InputKeyHandler
from deluge.ui.console.utils import colors
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.utils.format_utils import (
    delete_alt_backspace,
    remove_formatting,
    wrap_string,
)

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


class BaseField(InputKeyHandler):
    def __init__(self, parent=None, name=None, selectable=True, **kwargs):
        super(BaseField, self).__init__()
        self.name = name
        self.parent = parent
        self.fmt_keys = {}
        self.set_fmt_key('font', 'ignore', kwargs)
        self.set_fmt_key('color', 'white,black', kwargs)
        self.set_fmt_key('color_end', 'white,black', kwargs)
        self.set_fmt_key('color_active', 'black,white', kwargs)
        self.set_fmt_key('color_unfocused', 'color', kwargs)
        self.set_fmt_key('color_unfocused_active', 'black,whitegrey', kwargs)
        self.set_fmt_key('font_active', 'font', kwargs)
        self.set_fmt_key('font_unfocused', 'font', kwargs)
        self.set_fmt_key('font_unfocused_active', 'font_active', kwargs)
        self.default_col = kwargs.get('col', -1)
        self._selectable = selectable
        self.value = None

    def selectable(self):
        return self.has_input() and not self.depend_skip() and self._selectable

    def set_fmt_key(self, key, default, kwargsdict=None):
        value = self.fmt_keys.get(default, default)
        if kwargsdict:
            value = kwargsdict.get(key, value)
        self.fmt_keys[key] = value

    def get_fmt_keys(self, focused, active, **kwargs):
        color_key = kwargs.get('color_key', 'color')
        font_key = 'font'
        if not focused:
            color_key += '_unfocused'
            font_key += '_unfocused'
        if active:
            color_key += '_active'
            font_key += '_active'
        return color_key, font_key

    def build_fmt_string(self, focused, active, value_key='msg', **kwargs):
        color_key, font_key = self.get_fmt_keys(focused, active, **kwargs)
        return '{!%%(%s)s,%%(%s)s!}%%(%s)s{!%%(%s)s!}' % (
            color_key,
            font_key,
            value_key,
            'color_end',
        )

    def depend_skip(self):
        return False

    def has_input(self):
        return True

    @overrides(InputKeyHandler)
    def handle_read(self, c):
        return util.ReadState.IGNORED

    def render(self, screen, row, **kwargs):
        return 0

    @property
    def height(self):
        return 1

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value


class NoInputField(BaseField):
    @overrides(BaseField)
    def has_input(self):
        return False


class InputField(BaseField):
    def __init__(self, parent, name, message, format_default=None, **kwargs):
        BaseField.__init__(self, parent=parent, name=name, **kwargs)
        self.format_default = format_default
        self.message = None
        self.set_message(message)

    depend = None

    @overrides(BaseField)
    def handle_read(self, c):
        if c in [curses.KEY_ENTER, util.KEY_ENTER2, util.KEY_BACKSPACE2, 113]:
            return util.ReadState.READ
        return util.ReadState.IGNORED

    def set_message(self, msg):
        changed = self.message != msg
        self.message = msg
        return changed

    def set_depend(self, i, inverse=False):
        if not isinstance(i, CheckedInput):
            raise Exception('Can only depend on CheckedInputs')
        self.depend = i
        self.inverse = inverse

    def depend_skip(self):
        if not self.depend:
            return False
        if self.inverse:
            return self.depend.checked
        else:
            return not self.depend.checked


class Header(NoInputField):
    def __init__(self, parent, header, space_above, space_below, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = header
        NoInputField.__init__(self, parent=parent, **kwargs)
        self.header = '{!white,black,bold!}%s' % header
        self.space_above = space_above
        self.space_below = space_below

    @overrides(BaseField)
    def render(self, screen, row, col=0, **kwargs):
        rows = 1
        if self.space_above:
            row += 1
            rows += 1
        self.parent.add_string(row, self.header, scr=screen, col=col, pad=False)
        if self.space_below:
            rows += 1
        return rows

    @property
    def height(self):
        return 1 + int(self.space_above) + int(self.space_below)


class InfoField(NoInputField):
    def __init__(self, parent, name, label, value, **kwargs):
        NoInputField.__init__(self, parent=parent, name=name, **kwargs)
        self.label = label
        self.value = value
        self.txt = '%s %s' % (label, value)

    @overrides(BaseField)
    def render(self, screen, row, col=0, **kwargs):
        self.parent.add_string(row, self.txt, scr=screen, col=col, pad=False)
        return 1

    @overrides(BaseField)
    def set_value(self, v):
        self.value = v
        if isinstance(v, float):
            self.txt = '%s %.2f' % (self.label, self.value)
        else:
            self.txt = '%s %s' % (self.label, self.value)


class CheckedInput(InputField):
    def __init__(
        self,
        parent,
        name,
        message,
        checked=False,
        checked_char='X',
        unchecked_char=' ',
        checkbox_format='[%s] ',
        **kwargs
    ):
        InputField.__init__(self, parent, name, message, **kwargs)
        self.set_value(checked)
        self.fmt_keys.update(
            {
                'msg': message,
                'checkbox_format': checkbox_format,
                'unchecked_char': unchecked_char,
                'checked_char': checked_char,
            }
        )
        self.set_fmt_key('font_checked', 'font', kwargs)
        self.set_fmt_key('font_unfocused_checked', 'font_checked', kwargs)
        self.set_fmt_key('font_active_checked', 'font_active', kwargs)
        self.set_fmt_key('font_unfocused_active_checked', 'font_active_checked', kwargs)
        self.set_fmt_key('color_checked', 'color', kwargs)
        self.set_fmt_key('color_active_checked', 'color_active', kwargs)
        self.set_fmt_key('color_unfocused_checked', 'color_checked', kwargs)
        self.set_fmt_key(
            'color_unfocused_active_checked', 'color_unfocused_active', kwargs
        )

    @property
    def checked(self):
        return self.value

    @overrides(BaseField)
    def get_fmt_keys(self, focused, active, **kwargs):
        color_key, font_key = super(CheckedInput, self).get_fmt_keys(
            focused, active, **kwargs
        )
        if self.checked:
            color_key += '_checked'
            font_key += '_checked'
        return color_key, font_key

    def build_msg_string(self, focused, active):
        fmt_str = self.build_fmt_string(focused, active)
        char = self.fmt_keys['checked_char' if self.checked else 'unchecked_char']
        chk_box = ''
        try:
            chk_box = self.fmt_keys['checkbox_format'] % char
        except KeyError:
            pass
        msg = fmt_str % self.fmt_keys
        return chk_box + msg

    @overrides(InputField)
    def render(self, screen, row, col=0, **kwargs):
        string = self.build_msg_string(kwargs.get('focused'), kwargs.get('active'))

        self.parent.add_string(row, string, scr=screen, col=col, pad=False)
        return 1

    @overrides(InputField)
    def handle_read(self, c):
        if c == util.KEY_SPACE:
            self.set_value(not self.checked)
            return util.ReadState.CHANGED
        return util.ReadState.IGNORED

    @overrides(InputField)
    def set_message(self, msg):
        changed = InputField.set_message(self, msg)
        if 'msg' in self.fmt_keys and self.fmt_keys['msg'] != msg:
            changed = True
        self.fmt_keys.update({'msg': msg})

        return changed


class CheckedPlusInput(CheckedInput):
    def __init__(
        self,
        parent,
        name,
        message,
        child,
        child_always_visible=False,
        show_usage_hints=True,
        msg_fmt='%s ',
        **kwargs
    ):
        CheckedInput.__init__(self, parent, name, message, **kwargs)
        self.child = child
        self.child_active = False
        self.show_usage_hints = show_usage_hints
        self.msg_fmt = msg_fmt
        self.child_always_visible = child_always_visible

    @property
    def height(self):
        return max(2 if self.show_usage_hints else 1, self.child.height)

    @overrides(CheckedInput)
    def render(
        self, screen, row, width=None, active=False, focused=False, col=0, **kwargs
    ):
        isact = active and not self.child_active
        CheckedInput.render(
            self, screen, row, width=width, active=isact, focused=focused, col=col
        )
        rows = 1
        if self.show_usage_hints and (
            self.child_always_visible or (active and self.checked)
        ):
            msg = '(esc to leave)' if self.child_active else '(right arrow to edit)'
            self.parent.add_string(row + 1, msg, scr=screen, col=col, pad=False)
            rows += 1

        msglen = len(
            self.msg_fmt % colors.strip_colors(self.build_msg_string(focused, active))
        )
        # show child
        if self.checked or self.child_always_visible:
            crows = self.child.render(
                screen,
                row,
                width=width - msglen,
                active=self.child_active and active,
                col=col + msglen,
                cursor_offset=msglen,
            )
            rows = max(rows, crows)
        else:
            self.parent.add_string(
                row,
                '(enable to view/edit value)',
                scr=screen,
                col=col + msglen,
                pad=False,
            )
        return rows

    @overrides(CheckedInput)
    def handle_read(self, c):
        if self.child_active:
            if c == util.KEY_ESC:  # leave child on esc
                self.child_active = False
                return util.ReadState.READ
            # pass keys through to child
            return self.child.handle_read(c)
        else:
            if c == util.KEY_SPACE:
                self.set_value(not self.checked)
                return util.ReadState.CHANGED
            if (self.checked or self.child_always_visible) and c == curses.KEY_RIGHT:
                self.child_active = True
                return util.ReadState.READ
        return util.ReadState.IGNORED

    def get_child(self):
        return self.child


class IntSpinInput(InputField):
    def __init__(
        self,
        parent,
        name,
        message,
        move_func,
        value,
        min_val=None,
        max_val=None,
        inc_amt=1,
        incr_large=10,
        strict_validation=False,
        fmt='%d',
        **kwargs
    ):
        InputField.__init__(self, parent, name, message, **kwargs)
        self.convert_func = int
        self.fmt = fmt
        self.valstr = str(value)
        self.default_str = self.valstr
        self.set_value(value)
        self.default_value = self.value
        self.last_valid_value = self.value
        self.last_active = False
        self.cursor = len(self.valstr)
        self.cursoff = (
            colors.get_line_width(self.message) + 3
        )  # + 4 for the " [ " in the rendered string
        self.move_func = move_func
        self.strict_validation = strict_validation
        self.min_val = min_val
        self.max_val = max_val
        self.inc_amt = inc_amt
        self.incr_large = incr_large

    def validate_value(self, value, on_invalid=None):
        if (self.min_val is not None) and value < self.min_val:
            value = on_invalid if on_invalid else self.min_val
        if (self.max_val is not None) and value > self.max_val:
            value = on_invalid if on_invalid else self.max_val
        return value

    @overrides(InputField)
    def render(
        self, screen, row, active=False, focused=True, col=0, cursor_offset=0, **kwargs
    ):
        if active:
            self.last_active = True
        elif self.last_active:
            self.set_value(
                self.valstr, validate=True, value_on_fail=self.last_valid_value
            )
            self.last_active = False

        fmt_str = self.build_fmt_string(focused, active, value_key='value')
        value_format = '%(msg)s {!input!}'
        if not self.valstr:
            value_format += '[  ]'
        elif self.format_default and self.valstr == self.default_str:
            value_format += '[ {!magenta,black!}%(value)s{!input!} ]'
        else:
            value_format += '[ ' + fmt_str + ' ]'

        self.parent.add_string(
            row,
            value_format
            % dict({'msg': self.message, 'value': '%s' % self.valstr}, **self.fmt_keys),
            scr=screen,
            col=col,
            pad=False,
        )
        if active:
            if focused:
                util.safe_curs_set(util.Curser.NORMAL)
                self.move_func(row, self.cursor + self.cursoff + cursor_offset)
            else:
                util.safe_curs_set(util.Curser.INVISIBLE)
        return 1

    @overrides(InputField)
    def handle_read(self, c):
        if c == util.KEY_SPACE:
            return util.ReadState.READ
        elif c == curses.KEY_PPAGE:
            self.set_value(self.value + self.inc_amt, validate=True)
        elif c == curses.KEY_NPAGE:
            self.set_value(self.value - self.inc_amt, validate=True)
        elif c == util.KEY_ALT_AND_KEY_PPAGE:
            self.set_value(self.value + self.incr_large, validate=True)
        elif c == util.KEY_ALT_AND_KEY_NPAGE:
            self.set_value(self.value - self.incr_large, validate=True)
        elif c == curses.KEY_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif c == curses.KEY_RIGHT:
            self.cursor = min(len(self.valstr), self.cursor + 1)
        elif c == curses.KEY_HOME:
            self.cursor = 0
        elif c == curses.KEY_END:
            self.cursor = len(self.valstr)
        elif c == curses.KEY_BACKSPACE or c == util.KEY_BACKSPACE2:
            if self.valstr and self.cursor > 0:
                new_val = self.valstr[: self.cursor - 1] + self.valstr[self.cursor :]
                self.set_value(
                    new_val,
                    validate=False,
                    cursor=self.cursor - 1,
                    cursor_on_fail=True,
                    value_on_fail=self.valstr if self.strict_validation else None,
                )
        elif c == curses.KEY_DC:  # Del
            if self.valstr and self.cursor <= len(self.valstr):
                if self.cursor == 0:
                    new_val = self.valstr[1:]
                else:
                    new_val = (
                        self.valstr[: self.cursor] + self.valstr[self.cursor + 1 :]
                    )
                self.set_value(
                    new_val,
                    validate=False,
                    cursor=False,
                    value_on_fail=self.valstr if self.strict_validation else None,
                    cursor_on_fail=True,
                )
        elif c == ord('-'):  # minus
            self.set_value(
                self.value - 1,
                validate=True,
                cursor=True,
                cursor_on_fail=True,
                value_on_fail=self.value,
                on_invalid=self.value,
            )
        elif c == ord('+'):  # plus
            self.set_value(
                self.value + 1,
                validate=True,
                cursor=True,
                cursor_on_fail=True,
                value_on_fail=self.value,
                on_invalid=self.value,
            )
        elif util.is_int_chr(c):
            if self.strict_validation:
                new_val = (
                    self.valstr[: self.cursor - 1]
                    + chr(c)
                    + self.valstr[self.cursor - 1 :]
                )
                self.set_value(
                    new_val,
                    validate=True,
                    cursor=self.cursor + 1,
                    value_on_fail=self.valstr,
                    on_invalid=self.value,
                )
            else:
                minus_place = self.valstr.find('-')
                if self.cursor > minus_place:
                    new_val = (
                        self.valstr[: self.cursor] + chr(c) + self.valstr[self.cursor :]
                    )
                    self.set_value(
                        new_val,
                        validate=True,
                        cursor=self.cursor + 1,
                        on_invalid=self.value,
                    )
        else:
            return util.ReadState.IGNORED
        return util.ReadState.READ

    @overrides(BaseField)
    def set_value(
        self,
        val,
        cursor=True,
        validate=False,
        cursor_on_fail=False,
        value_on_fail=None,
        on_invalid=None,
    ):
        value = None
        try:
            value = self.convert_func(val)
            if validate:
                validated = self.validate_value(value, on_invalid)
                if validated != value:
                    # Value was not valid, so use validated value instead.
                    # Also set cursor according to validated value
                    cursor = True
                    value = validated

            new_valstr = self.fmt % value
            if new_valstr == self.valstr:
                # If string has not change, keep cursor
                cursor = False
            self.valstr = new_valstr
            self.last_valid_value = self.value = value
        except ValueError:
            if value_on_fail is not None:
                self.set_value(
                    value_on_fail,
                    cursor=cursor,
                    cursor_on_fail=cursor_on_fail,
                    validate=validate,
                    on_invalid=on_invalid,
                )
                return
            self.value = None
            self.valstr = val
            if cursor_on_fail:
                self.cursor = cursor
        except TypeError:
            import traceback

            log.warning('TypeError: %s', ''.join(traceback.format_exc()))
        else:
            if cursor is True:
                self.cursor = len(self.valstr)
            elif cursor is not False:
                self.cursor = cursor


class FloatSpinInput(IntSpinInput):
    def __init__(self, parent, message, name, move_func, value, precision=1, **kwargs):
        self.precision = precision
        IntSpinInput.__init__(self, parent, message, name, move_func, value, **kwargs)
        self.fmt = '%%.%df' % precision
        self.convert_func = lambda valstr: round(float(valstr), self.precision)
        self.set_value(value)
        self.cursor = len(self.valstr)

    @overrides(IntSpinInput)
    def handle_read(self, c):
        if c == ord('.'):
            minus_place = self.valstr.find('-')
            if self.cursor <= minus_place:
                return util.ReadState.READ
            point_place = self.valstr.find('.')
            if point_place >= 0:
                return util.ReadState.READ
            new_val = self.valstr[: self.cursor] + chr(c) + self.valstr[self.cursor :]
            self.set_value(new_val, validate=True, cursor=self.cursor + 1)
        else:
            return IntSpinInput.handle_read(self, c)


class SelectInput(InputField):
    def __init__(
        self,
        parent,
        name,
        message,
        opts,
        vals,
        active_index,
        active_default=False,
        require_select_action=True,
        **kwargs
    ):
        InputField.__init__(self, parent, name, message, **kwargs)
        self.opts = opts
        self.vals = vals
        self.active_index = active_index
        self.selected_index = active_index
        self.default_option = active_index if active_default else None
        self.require_select_action = require_select_action
        self.fmt_keys.update({'font_active': 'bold'})
        font_selected = kwargs.get('font_selected', 'bold,underline')

        self.set_fmt_key('font_selected', font_selected, kwargs)
        self.set_fmt_key('font_active_selected', 'font_selected', kwargs)
        self.set_fmt_key('font_unfocused_selected', 'font_selected', kwargs)
        self.set_fmt_key(
            'font_unfocused_active_selected', 'font_active_selected', kwargs
        )

        self.set_fmt_key('color_selected', 'color', kwargs)
        self.set_fmt_key('color_active_selected', 'color_active', kwargs)
        self.set_fmt_key('color_unfocused_selected', 'color_selected', kwargs)
        self.set_fmt_key(
            'color_unfocused_active_selected', 'color_unfocused_active', kwargs
        )
        self.set_fmt_key('color_default_value', 'magenta,black', kwargs)

        self.set_fmt_key('color_default_value', 'magenta,black')
        self.set_fmt_key('color_default_value_active', 'magentadark,white')
        self.set_fmt_key('color_default_value_selected', 'color_default_value', kwargs)
        self.set_fmt_key('color_default_value_unfocused', 'color_default_value', kwargs)
        self.set_fmt_key(
            'color_default_value_unfocused_selected',
            'color_default_value_selected',
            kwargs,
        )
        self.set_fmt_key('color_default_value_active_selected', 'magentadark,white')
        self.set_fmt_key(
            'color_default_value_unfocused_active_selected',
            'color_unfocused_active',
            kwargs,
        )

    @property
    def height(self):
        return 1 + bool(self.message)

    @overrides(BaseField)
    def get_fmt_keys(self, focused, active, selected=False, **kwargs):
        color_key, font_key = super(SelectInput, self).get_fmt_keys(
            focused, active, **kwargs
        )
        if selected:
            color_key += '_selected'
            font_key += '_selected'
        return color_key, font_key

    @overrides(InputField)
    def render(self, screen, row, active=False, focused=True, col=0, **kwargs):
        if self.message:
            self.parent.add_string(row, self.message, scr=screen, col=col, pad=False)
            row += 1

        off = col + 1
        for i, opt in enumerate(self.opts):
            self.fmt_keys['msg'] = opt
            fmt_args = {'selected': i == self.selected_index}
            if i == self.default_option:
                fmt_args['color_key'] = 'color_default_value'
            fmt = self.build_fmt_string(
                focused, (i == self.active_index) and active, **fmt_args
            )
            string = '[%s]' % (fmt % self.fmt_keys)
            self.parent.add_string(row, string, scr=screen, col=off, pad=False)
            off += len(opt) + 3
        if self.message:
            return 2
        else:
            return 1

    @overrides(InputField)
    def handle_read(self, c):
        if c == curses.KEY_LEFT:
            self.active_index = max(0, self.active_index - 1)
            if not self.require_select_action:
                self.selected_index = self.active_index
        elif c == curses.KEY_RIGHT:
            self.active_index = min(len(self.opts) - 1, self.active_index + 1)
            if not self.require_select_action:
                self.selected_index = self.active_index
        elif c == ord(' '):
            if self.require_select_action:
                self.selected_index = self.active_index
        else:
            return util.ReadState.IGNORED
        return util.ReadState.READ

    @overrides(BaseField)
    def get_value(self):
        return self.vals[self.selected_index]

    @overrides(BaseField)
    def set_value(self, value):
        for i, val in enumerate(self.vals):
            if value == val:
                self.selected_index = i
                return
        raise Exception('Invalid value for SelectInput')


class TextInput(InputField):
    def __init__(
        self,
        parent,
        name,
        message,
        move_func,
        width,
        value,
        complete=False,
        activate_input=False,
        **kwargs
    ):
        InputField.__init__(self, parent, name, message, **kwargs)
        self.move_func = move_func
        self._width = width
        self.value = value if value else ''
        self.default_value = value
        self.complete = complete
        self.tab_count = 0
        self.cursor = len(self.value)
        self.opts = None
        self.opt_off = 0
        self.value_offset = 0
        self.activate_input = activate_input  # Wether input must be activated
        self.input_active = not self.activate_input

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return 1 + bool(self.message)

    def calculate_textfield_value(self, width, cursor_offset):
        cursor_width = width

        if self.cursor > (cursor_width - 1):
            c_pos_abs = self.cursor - cursor_width
            if cursor_width <= (self.cursor - self.value_offset):
                new_cur = c_pos_abs + 1
                self.value_offset = new_cur
            else:
                if self.cursor >= len(self.value):
                    c_pos_abs = len(self.value) - cursor_width
                    new_cur = c_pos_abs + 1
                    self.value_offset = new_cur
            vstr = self.value[self.value_offset :]

            if len(vstr) > cursor_width:
                vstr = vstr[:cursor_width]
            vstr = vstr.ljust(cursor_width)
        else:
            if len(self.value) <= cursor_width:
                self.value_offset = 0
                vstr = self.value.ljust(cursor_width)
            else:
                self.value_offset = min(self.value_offset, self.cursor)
                vstr = self.value[self.value_offset :]
                if len(vstr) > cursor_width:
                    vstr = vstr[:cursor_width]
            vstr = vstr.ljust(cursor_width)

        return vstr

    def calculate_cursor_pos(self, width, col):
        cursor_width = width
        x_pos = self.cursor + col

        if (self.cursor + col - self.value_offset) > cursor_width:
            x_pos += self.value_offset
        else:
            x_pos -= self.value_offset

        return min(width - 1 + col, x_pos)

    @overrides(InputField)
    def render(
        self,
        screen,
        row,
        width=None,
        active=False,
        focused=True,
        col=0,
        cursor_offset=0,
        **kwargs
    ):
        if not self.value and not active and len(self.default_value) != 0:
            self.value = self.default_value
            self.cursor = len(self.value)

        if self.message:
            self.parent.add_string(row, self.message, scr=screen, col=col, pad=False)
            row += 1

        vstr = self.calculate_textfield_value(width, cursor_offset)

        if active:
            if self.opts:
                self.parent.add_string(
                    row + 1, self.opts[self.opt_off :], scr=screen, col=col, pad=False
                )

            if focused and self.input_active:
                util.safe_curs_set(
                    util.Curser.NORMAL
                )  # Make cursor visible when text field is focused
                x_pos = self.calculate_cursor_pos(width, col)
                self.move_func(row, x_pos)

        fmt = '{!black,white,bold!}%s'
        if (
            self.format_default
            and len(self.value) != 0
            and self.value == self.default_value
        ):
            fmt = '{!magenta,white!}%s'
        if not active or not focused or self.input_active:
            fmt = '{!white,grey,bold!}%s'

        self.parent.add_string(
            row, fmt % vstr, scr=screen, col=col, pad=False, trim=False
        )
        return self.height

    @overrides(BaseField)
    def set_value(self, val):
        self.value = val
        self.cursor = len(self.value)

    @overrides(InputField)
    def handle_read(self, c):
        """
        Return False when key was swallowed, i.e. we recognised
        the key and no further action by other components should
        be performed.
        """
        if self.activate_input:
            if not self.input_active:
                if c in [
                    curses.KEY_LEFT,
                    curses.KEY_RIGHT,
                    curses.KEY_HOME,
                    curses.KEY_END,
                    curses.KEY_ENTER,
                    util.KEY_ENTER2,
                ]:
                    self.input_active = True
                    return util.ReadState.READ
                else:
                    return util.ReadState.IGNORED
            elif c == util.KEY_ESC:
                self.input_active = False
                return util.ReadState.READ

        if c == util.KEY_TAB and self.complete:
            # Keep track of tab hit count to know when it's double-hit
            self.tab_count += 1
            if self.tab_count > 1:
                second_hit = True
                self.tab_count = 0
            else:
                second_hit = False

            # We only call the tab completer function if we're at the end of
            # the input string on the cursor is on a space
            if self.cursor == len(self.value) or self.value[self.cursor] == ' ':
                if self.opts:
                    prev = self.opt_off
                    self.opt_off += self.width - 3
                    # now find previous double space, best guess at a split point
                    # in future could keep opts unjoined to get this really right
                    self.opt_off = self.opts.rfind('  ', 0, self.opt_off) + 2
                    if (
                        second_hit and self.opt_off == prev
                    ):  # double tap and we're at the end
                        self.opt_off = 0
                else:
                    opts = self.do_complete(self.value)
                    if len(opts) == 1:  # only one option, just complete it
                        self.value = opts[0]
                        self.cursor = len(opts[0])
                        self.tab_count = 0
                    elif len(opts) > 1:
                        prefix = os.path.commonprefix(opts)
                        if prefix:
                            self.value = prefix
                            self.cursor = len(prefix)

                    if (
                        len(opts) > 1 and second_hit
                    ):  # display multiple options on second tab hit
                        sp = self.value.rfind(os.sep) + 1
                        self.opts = '  '.join([o[sp:] for o in opts])

        # Cursor movement
        elif c == curses.KEY_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif c == curses.KEY_RIGHT:
            self.cursor = min(len(self.value), self.cursor + 1)
        elif c == curses.KEY_HOME:
            self.cursor = 0
        elif c == curses.KEY_END:
            self.cursor = len(self.value)

        # Delete a character in the input string based on cursor position
        elif c == curses.KEY_BACKSPACE or c == util.KEY_BACKSPACE2:
            if self.value and self.cursor > 0:
                self.value = self.value[: self.cursor - 1] + self.value[self.cursor :]
                self.cursor -= 1
        elif c == [util.KEY_ESC, util.KEY_BACKSPACE2] or c == [
            util.KEY_ESC,
            curses.KEY_BACKSPACE,
        ]:
            self.value, self.cursor = delete_alt_backspace(self.value, self.cursor)
        elif c == curses.KEY_DC:
            if self.value and self.cursor < len(self.value):
                self.value = self.value[: self.cursor] + self.value[self.cursor + 1 :]
        elif c > 31 and c < 256:
            # Emulate getwch
            stroke = chr(c)
            uchar = '' if PY2 else stroke
            while not uchar:
                try:
                    uchar = stroke.decode(self.parent.encoding)
                except UnicodeDecodeError:
                    c = self.parent.parent.stdscr.getch()
                    stroke += chr(c)
            if uchar:
                if self.cursor == len(self.value):
                    self.value += uchar
                else:
                    # Insert into string
                    self.value = (
                        self.value[: self.cursor] + uchar + self.value[self.cursor :]
                    )
                # Move the cursor forward
                self.cursor += 1

        else:
            self.opts = None
            self.opt_off = 0
            self.tab_count = 0
            return util.ReadState.IGNORED
        return util.ReadState.READ

    def do_complete(self, line):
        line = os.path.abspath(os.path.expanduser(line))
        ret = []
        if os.path.exists(line):
            # This is a correct path, check to see if it's a directory
            if os.path.isdir(line):
                # Directory, so we need to show contents of directory
                for f in os.listdir(line):
                    # Skip hidden
                    if f.startswith('.'):
                        continue
                    f = os.path.join(line, f)
                    if os.path.isdir(f):
                        f += os.sep
                    ret.append(f)
            else:
                # This is a file, but we could be looking for another file that
                # shares a common prefix.
                for f in os.listdir(os.path.dirname(line)):
                    if f.startswith(os.path.split(line)[1]):
                        ret.append(os.path.join(os.path.dirname(line), f))
        else:
            # This path does not exist, so lets do a listdir on it's parent
            # and find any matches.
            ret = []
            if os.path.isdir(os.path.dirname(line)):
                for f in os.listdir(os.path.dirname(line)):
                    if f.startswith(os.path.split(line)[1]):
                        p = os.path.join(os.path.dirname(line), f)

                        if os.path.isdir(p):
                            p += os.sep
                        ret.append(p)
        return ret


class ComboInput(InputField):
    def __init__(
        self, parent, name, message, choices, default=None, searchable=True, **kwargs
    ):
        InputField.__init__(self, parent, name, message, **kwargs)
        self.choices = choices
        self.default = default
        self.set_value(default)
        max_width = 0
        for c in choices:
            max_width = max(max_width, len(c[1]))
        self.choices_width = max_width
        self.searchable = searchable

    @overrides(BaseField)
    def render(self, screen, row, col=0, **kwargs):
        fmt_str = self.build_fmt_string(kwargs.get('focused'), kwargs.get('active'))
        string = '%s: [%10s]' % (self.message, fmt_str % self.fmt_keys)
        self.parent.add_string(row, string, scr=screen, col=col, pad=False)
        return 1

    def _lang_selected(self, selected, *args, **kwargs):
        if selected is not None:
            self.set_value(selected)
        self.parent.pop_popup()

    @overrides(InputField)
    def handle_read(self, c):
        if c in [util.KEY_SPACE, curses.KEY_ENTER, util.KEY_ENTER2]:

            def search_handler(key):
                """Handle keyboard input to seach the list"""
                if not util.is_printable_chr(key):
                    return
                selected = select_popup.current_selection()

                def select_in_range(begin, end):
                    for i in range(begin, end):
                        val = select_popup.inputs[i].get_value()
                        if val.lower().startswith(chr(key)):
                            select_popup.set_selection(i)
                            return True
                    return False

                # First search downwards
                if not select_in_range(selected + 1, len(select_popup.inputs)):
                    # No match, so start at beginning
                    select_in_range(0, selected)

            from deluge.ui.console.widgets.popup import (  # Must import here
                SelectablePopup,
            )

            select_popup = SelectablePopup(
                self.parent,
                ' %s ' % _('Select Language'),
                self._lang_selected,
                input_cb=search_handler if self.searchable else None,
                border_off_west=1,
                active_wrap=False,
                width_req=self.choices_width + 12,
            )
            for choice in self.choices:
                args = {'data': choice[0]}
                select_popup.add_line(
                    choice[0],
                    choice[1],
                    selectable=True,
                    selected=choice[0] == self.get_value(),
                    **args
                )
            self.parent.push_popup(select_popup)
            return util.ReadState.CHANGED
        return util.ReadState.IGNORED

    @overrides(BaseField)
    def set_value(self, val):
        self.value = val
        msg = None
        for c in self.choices:
            if c[0] == val:
                msg = c[1]
                break
        if msg is None:
            log.warning(
                'Setting value "%s" found nothing in choices: %s', val, self.choices
            )
        self.fmt_keys.update({'msg': msg})


class TextField(BaseField):
    def __init__(self, parent, name, value, selectable=True, value_fmt='%s', **kwargs):
        BaseField.__init__(
            self, parent=parent, name=name, selectable=selectable, **kwargs
        )
        self.value = value
        self.value_fmt = value_fmt
        self.set_value(value)

    @overrides(BaseField)
    def set_value(self, value):
        self.value = value
        self.txt = self.value_fmt % (value)

    @overrides(BaseField)
    def has_input(self):
        return True

    @overrides(BaseField)
    def render(self, screen, row, active=False, focused=False, col=0, **kwargs):
        util.safe_curs_set(
            util.Curser.INVISIBLE
        )  # Make cursor invisible when text field is active
        fmt = self.build_fmt_string(focused, active)
        self.fmt_keys['msg'] = self.txt
        string = fmt % self.fmt_keys
        self.parent.add_string(row, string, scr=screen, col=col, pad=False, trim=False)
        return 1


class TextArea(TextField):
    def __init__(self, parent, name, value, value_fmt='%s', **kwargs):
        TextField.__init__(
            self, parent, name, value, selectable=False, value_fmt=value_fmt, **kwargs
        )

    @overrides(TextField)
    def render(self, screen, row, col=0, **kwargs):
        util.safe_curs_set(
            util.Curser.INVISIBLE
        )  # Make cursor invisible when text field is active
        color = '{!white,black!}'
        lines = wrap_string(self.txt, self.parent.width - 3, 3, True)

        for i, line in enumerate(lines):
            self.parent.add_string(
                row + i,
                '%s%s' % (color, line),
                scr=screen,
                col=col,
                pad=False,
                trim=False,
            )
        return len(lines)

    @property
    def height(self):
        lines = wrap_string(self.txt, self.parent.width - 3, 3, True)
        return len(lines)

    @overrides(TextField)
    def has_input(self):
        return False


class DividerField(NoInputField):
    def __init__(
        self,
        parent,
        name,
        value,
        selectable=False,
        fill_width=True,
        value_fmt='%s',
        **kwargs
    ):
        NoInputField.__init__(
            self, parent=parent, name=name, selectable=selectable, **kwargs
        )
        self.value = value
        self.value_fmt = value_fmt
        self.set_value(value)
        self.fill_width = fill_width

    @overrides(BaseField)
    def set_value(self, value):
        self.value = value
        self.txt = self.value_fmt % (value)

    @overrides(BaseField)
    def render(
        self, screen, row, active=False, focused=False, col=0, width=None, **kwargs
    ):
        util.safe_curs_set(
            util.Curser.INVISIBLE
        )  # Make cursor invisible when text field is active
        fmt = self.build_fmt_string(focused, active)
        self.fmt_keys['msg'] = self.txt
        if self.fill_width:
            self.fmt_keys['msg'] = ''
            string_len = len(remove_formatting(fmt % self.fmt_keys))
            fill_len = width - string_len - (len(self.txt) - 1)
            self.fmt_keys['msg'] = self.txt * fill_len
        string = fmt % self.fmt_keys
        self.parent.add_string(row, string, scr=screen, col=col, pad=False, trim=False)
        return 1
