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

try:
    import curses
except ImportError:
    pass

import logging
import os
import os.path

from deluge.ui.console import colors
from deluge.ui.console.modes.popup import ALIGN, Popup

log = logging.getLogger(__name__)


class InputField:
    depend = None
    # render the input.  return number of rows taken up

    def get_height(self):
        return 0

    def render(self, screen, row, width, selected, col=1):
        return 0

    def handle_read(self, c):
        if c in [curses.KEY_ENTER, 10, 127, 113]:
            return True
        return False

    def get_value(self):
        return None

    def set_value(self, value):
        pass

    def set_depend(self, i, inverse=False):
        if not isinstance(i, CheckedInput):
            raise Exception("Can only depend on CheckedInputs")
        self.depend = i
        self.inverse = inverse

    def depend_skip(self):
        if not self.depend:
            return False
        if self.inverse:
            return self.depend.checked
        else:
            return not self.depend.checked


class CheckedInput(InputField):
    def __init__(self, parent, message, name, checked=False, additional_formatting=False):
        self.parent = parent
        self.additional_formatting = additional_formatting
        self.chkd_inact = "[X] %s" % message
        self.unchkd_inact = "[ ] %s" % message
        self.chkd_act = "[{!black,white,bold!}X{!white,black!}] %s" % message
        self.unchkd_act = "[{!black,white,bold!} {!white,black!}] %s" % message
        self.name = name
        self.checked = checked

    def get_height(self):
        return 1

    def render(self, screen, row, width, active, col=1):
        if self.checked and active:
            self.parent.add_string(row, self.chkd_act, screen, col, False, True)
        elif self.checked:
            self.parent.add_string(row, self.chkd_inact, screen, col, False, True)
        elif active:
            self.parent.add_string(row, self.unchkd_act, screen, col, False, True)
        else:
            self.parent.add_string(row, self.unchkd_inact, screen, col, False, True)
        return 1

    def handle_read(self, c):
        if c == 32:
            self.checked = not self.checked

    def get_value(self):
        return self.checked

    def set_value(self, c):
        self.checked = c


class CheckedPlusInput(InputField):
    def __init__(self, parent, message, name, child, checked=False, additional_formatting=False):
        self.parent = parent
        self.additional_formatting = additional_formatting
        self.chkd_inact = "[X] %s" % message
        self.unchkd_inact = "[ ] %s" % message
        self.chkd_act = "[{!black,white,bold!}X{!white,black!}] %s" % message
        self.unchkd_act = "[{!black,white,bold!} {!white,black!}] %s" % message
        self.name = name
        self.checked = checked
        self.msglen = len(self.chkd_inact) + 1
        # child = self.get_child() TOFIX
        self.child_active = False

    def get_height(self):
        return max(2, self.get_child().height)

    def render(self, screen, row, width, active, col=1):
        isact = active and not self.child_active
        if self.checked and isact:
            self.parent.add_string(row, self.chkd_act, screen, col, False, True)
        elif self.checked:
            self.parent.add_string(row, self.chkd_inact, screen, col, False, True)
        elif isact:
            self.parent.add_string(row, self.unchkd_act, screen, col, False, True)
        else:
            self.parent.add_string(row, self.unchkd_inact, screen, col, False, True)

        if active and self.checked and self.child_active:
            self.parent.add_string(row + 1, "(esc to leave)", screen, col, False, True)
        elif active and self.checked:
            self.parent.add_string(row + 1, "(right arrow to edit)", screen, col, False, True)
        rows = 2
        # show child
        if self.checked:
            if isinstance(self.get_child(), (TextInput, IntSpinInput, FloatSpinInput)):
                crows = self.get_child().render(screen, row, width - self.msglen,
                                                self.child_active and active, col + self.msglen, self.msglen)
            else:
                crows = self.get_child().render(screen, row, width - self.msglen,
                                                self.child_active and active, col + self.msglen)
            rows = max(rows, crows)
        else:
            self.parent.add_string(row, "(enable to view/edit value)", screen, col + self.msglen, False, True)
        return rows

    def handle_read(self, c):
        if self.child_active:
            if c == 27:  # leave child on esc
                self.child_active = False
                return
            # pass keys through to child
            self.get_child().handle_read(c)
        else:
            if c == 32:
                self.checked = not self.checked
            if c == curses.KEY_RIGHT:
                self.child_active = True

    def get_value(self):
        return self.checked

    def set_value(self, c):
        self.checked = c

    def get_child(self):
        return self.get_child()


class IntSpinInput(InputField):
    def __init__(self, parent, message, name, move_func, value, min_val=None, max_val=None,
                 additional_formatting=False):
        self.parent = parent
        self.message = message
        self.name = name

        self.additional_formatting = additional_formatting

        self.default_str = str(value)
        self.set_value(value)
        self.default_value = self.value

        self.cursor = len(self.valstr)
        self.cursoff = colors.get_line_width(self.message) + 4  # + 4 for the " [ " in the rendered string
        self.move_func = move_func
        self.min_val = min_val
        self.max_val = max_val
        self.need_update = False

    def get_height(self):
        return 1

    def __limit_value(self):
        if (self.min_val is not None) and self.value < self.min_val:
            self.value = self.min_val
        if (self.max_val is not None) and self.value > self.max_val:
            self.value = self.max_val

    def render(self, screen, row, width, active, col=1, cursor_offset=0):
        if not active and self.need_update:
            if not self.valstr or self.valstr == "-":
                self.value = self.default_value
                self.valstr = self.default_str
                try:
                    int(self.value)
                except:
                    self.real_value = False
            else:
                self.value = int(self.valstr)
                self.__limit_value()
                self.valstr = "%d" % self.value
                self.cursor = len(self.valstr)
            self.cursor = colors.get_line_width(self.valstr)
            self.need_update = False
        elif self.need_update and self.valstr != "-":
            self.real_value = True
            try:
                self.value = int(self.valstr)
            except:
                self.value = self.default_value
                try:
                    int(self.value)
                except:
                    self.real_value = False
        if not self.valstr:
            self.parent.add_string(row, "%s {!input!}[  ]" % self.message, screen, col, False, True)
        elif active:
            self.parent.add_string(row, "%s {!input!}[ {!black,white,bold!}%s{!input!} ]" % (
                self.message, self.valstr), screen, col, False, True)
        elif self.additional_formatting and self.valstr == self.default_str:
            self.parent.add_string(row, "%s {!input!}[ {!magenta,black!}%s{!input!} ]" % (
                self.message, self.valstr), screen, col, False, True)
        else:
            self.parent.add_string(row, "%s {!input!}[ %s ]" % (self.message, self.valstr), screen, col, False, True)

        if active:
            self.move_func(row, self.cursor + self.cursoff + cursor_offset)

        return 1

    def handle_read(self, c):
        if c == curses.KEY_PPAGE and self.value < self.max_val:
            if not self.real_value:
                self.value = self.min_val
                self.valstr = "%d" % self.value
                self.real_value = True
            else:
                self.value += 1
                self.valstr = "%d" % self.value
                self.cursor = len(self.valstr)
        elif c == curses.KEY_NPAGE and self.value > self.min_val:
            if not self.real_value:
                self.value = self.min_val
                self.valstr = "%d" % self.value
                self.real_value = True
            else:
                self.value -= 1
                self.valstr = "%d" % self.value
                self.cursor = len(self.valstr)
        elif c == curses.KEY_LEFT:
            if not self.real_value:
                return None
            self.cursor = max(0, self.cursor - 1)
        elif c == curses.KEY_RIGHT:
            if not self.real_value:
                return None
            self.cursor = min(len(self.valstr), self.cursor + 1)
        elif c == curses.KEY_HOME:
            if not self.real_value:
                return None
            self.cursor = 0
        elif c == curses.KEY_END:
            if not self.real_value:
                return None
            self.cursor = len(self.valstr)
        elif c == curses.KEY_BACKSPACE or c == 127:
            if not self.real_value:
                self.valstr = ""
                self.cursor = 0
                self.real_value = True
                self.need_update = True
            elif self.valstr and self.cursor > 0:
                self.valstr = self.valstr[:self.cursor - 1] + self.valstr[self.cursor:]
                self.cursor -= 1
                self.need_update = True
        elif c == curses.KEY_DC:
            if not self.real_value:
                return None
            if self.valstr and self.cursor < len(self.valstr):
                self.valstr = self.valstr[:self.cursor] + self.valstr[self.cursor + 1:]
                self.need_update = True
        elif c == 45 and self.min_val < 0:
            if not self.real_value:
                self.valstr = "-"
                self.cursor = 1
                self.real_value = True
                self.need_update = True
            if self.cursor != 0:
                return
            minus_place = self.valstr.find("-")
            if minus_place >= 0:
                return
            self.valstr = chr(c) + self.valstr
            self.cursor += 1
            self.need_update = True
        elif c > 47 and c < 58:
            if (not self.real_value) and self.valstr:
                self.valstr = ""
                self.cursor = 0
                self.real_value = True
                self.need_update = True
            if c == 48 and self.cursor == 0:
                return
            minus_place = self.valstr.find("-")
            if self.cursor <= minus_place:
                return
            if self.cursor == len(self.valstr):
                self.valstr += chr(c)
            else:
                # Insert into string
                self.valstr = self.valstr[:self.cursor] + chr(c) + self.valstr[self.cursor:]
            self.need_update = True
            # Move the cursor forward
            self.cursor += 1

    def get_value(self):
        if self.real_value:
            self.__limit_value()
            return self.value
        else:
            return None

    def set_value(self, val):
        try:
            self.value = int(val)
            self.valstr = "%d" % self.value
            self.real_value = True
        except ValueError:
            self.value = None
            self.real_value = False
            self.valstr = val
        self.cursor = len(self.valstr)


class FloatSpinInput(InputField):
    def __init__(self, parent, message, name, move_func, value, inc_amt, precision, min_val=None,
                 max_val=None, additional_formatting=False):
        self.parent = parent
        self.message = message
        self.name = name
        self.precision = precision
        self.inc_amt = inc_amt

        self.additional_formatting = additional_formatting

        self.fmt = "%%.%df" % precision

        self.default_str = str(value)
        self.set_value(value)
        self.default_value = self.value

        self.cursor = len(self.valstr)
        self.cursoff = colors.get_line_width(self.message) + 4  # + 4 for the " [ " in the rendered string
        self.move_func = move_func
        self.min_val = min_val
        self.max_val = max_val
        self.need_update = False

    def get_height(self):
        return 1

    def __limit_value(self):
        if (self.min_val is not None) and self.value < self.min_val:
            self.value = self.min_val
        if (self.max_val is not None) and self.value > self.max_val:
            self.value = self.max_val
        self.valstr = self.fmt % self.value

    def render(self, screen, row, width, active, col=1, cursor_offset=0):
        if not active and self.need_update:
            if not self.valstr or self.valstr == "-":
                self.value = self.default_value
                self.valstr = self.default_str
                try:
                    float(self.value)
                except:
                    self.real_value = False
            else:
                self.set_value(self.valstr)
                self.__limit_value()
                self.valstr = self.fmt % self.value
                self.cursor = len(self.valstr)
            self.cursor = colors.get_line_width(self.valstr)
            self.need_update = False
        elif self.need_update and self.valstr != "-":
            self.real_value = True
            try:
                self.value = round(float(self.valstr), self.precision)
            except:
                self.value = self.default_value
                try:
                    float(self.value)
                except:
                    self.real_value = False

        if not self.valstr:
            self.parent.add_string(row, "%s {!input!}[  ]" % self.message, screen, col, False, True)
        elif active:
            self.parent.add_string(row, "%s {!input!}[ {!black,white,bold!}%s{!white,black!} ]" % (
                self.message, self.valstr), screen, col, False, True)
        elif self.additional_formatting and self.valstr == self.default_str:
            self.parent.add_string(row, "%s {!input!}[ {!magenta,black!}%s{!input!} ]" % (
                self.message, self.valstr), screen, col, False, True)
        else:
            self.parent.add_string(row, "%s {!input!}[ %s ]" % (self.message, self.valstr), screen, col, False, True)
        if active:
            self.move_func(row, self.cursor + self.cursoff + cursor_offset)

        return 1

    def handle_read(self, c):
        if c == curses.KEY_PPAGE:
            if not self.real_value:
                self.value = self.min_val
                self.valstr = "%d" % self.value
                self.real_value = True
            else:
                self.value += self.inc_amt
                self.__limit_value()
                self.valstr = self.fmt % self.value
                self.cursor = len(self.valstr)
        elif c == curses.KEY_NPAGE:
            if not self.real_value:
                self.value = self.min_val
                self.valstr = "%d" % self.value
                self.real_value = True
            else:
                self.value -= self.inc_amt
                self.__limit_value()
                self.valstr = self.fmt % self.value
                self.cursor = len(self.valstr)
        elif c == curses.KEY_LEFT:
            if not self.real_value:
                return None
            self.cursor = max(0, self.cursor - 1)
        elif c == curses.KEY_RIGHT:
            if not self.real_value:
                return None
            self.cursor = min(len(self.valstr), self.cursor + 1)
        elif c == curses.KEY_HOME:
            if not self.real_value:
                return None
            self.cursor = 0
        elif c == curses.KEY_END:
            if not self.real_value:
                return None
            self.cursor = len(self.valstr)
        elif c == curses.KEY_BACKSPACE or c == 127:
            if not self.real_value:
                self.valstr = ""
                self.cursor = 0
                self.real_value = True
                self.need_update = True
            elif self.valstr and self.cursor > 0:
                self.valstr = self.valstr[:self.cursor - 1] + self.valstr[self.cursor:]
                self.cursor -= 1
                self.need_update = True
        elif c == curses.KEY_DC:
            if not self.real_value:
                return None
            if self.valstr and self.cursor < len(self.valstr):
                self.valstr = self.valstr[:self.cursor] + self.valstr[self.cursor + 1:]
                self.need_update = True
        elif c == 45 and self.min_val < 0:
            if not self.real_value:
                self.valstr = "-"
                self.cursor = 1
                self.need_update = True
                self.real_value = True
            if self.cursor != 0:
                return
            minus_place = self.valstr.find("-")
            if minus_place >= 0:
                return
            self.valstr = chr(c) + self.valstr
            self.cursor += 1
            self.need_update = True
        elif c == 46:
            if (not self.real_value) and self.valstr:
                self.valstr = "0."
                self.cursor = 2
                self.real_value = True
                self.need_update = True
            minus_place = self.valstr.find("-")
            if self.cursor <= minus_place:
                return
            point_place = self.valstr.find(".")
            if point_place >= 0:
                return
            if self.cursor == len(self.valstr):
                self.valstr += chr(c)
            else:
                # Insert into string
                self.valstr = self.valstr[:self.cursor] + chr(c) + self.valstr[self.cursor:]
            self.need_update = True
            # Move the cursor forward
            self.cursor += 1
        elif (c > 47 and c < 58):
            if (not self.real_value) and self.valstr:
                self.valstr = ""
                self.cursor = 0
                self.real_value = True
                self.need_update = True
            if self.value == "mixed":
                self.value = ""
            minus_place = self.valstr.find("-")
            if self.cursor <= minus_place:
                return
            if self.cursor == len(self.valstr):
                self.valstr += chr(c)
            else:
                # Insert into string
                self.valstr = self.valstr[:self.cursor] + chr(c) + self.valstr[self.cursor:]
            self.need_update = True
            # Move the cursor forward
            self.cursor += 1

    def get_value(self):
        if self.real_value:
            self.__limit_value()
            return self.value
        else:
            return None

    def set_value(self, val):
        try:
            self.value = round(float(val), self.precision)
            self.valstr = self.fmt % self.value
            self.real_value = True
        except ValueError:
            self.value = None
            self.real_value = False
            self.valstr = val
        self.cursor = len(self.valstr)


class SelectInput(InputField):
    def __init__(self, parent, message, name, opts, vals, selidx, additional_formatting=False):
        self.parent = parent
        self.message = message
        self.additional_formatting = additional_formatting
        self.name = name
        self.opts = opts
        self.vals = vals
        self.selidx = selidx
        self.default_option = selidx

    def get_height(self):
        return 1 + bool(self.message)

    def render(self, screen, row, width, selected, col=1):
        if self.message:
            self.parent.add_string(row, self.message, screen, col, False, True)
            row += 1
        off = col + 1
        for i, opt in enumerate(self.opts):
            if selected and i == self.selidx:
                self.parent.add_string(row, "{!black,white,bold!}[%s]" % opt, screen, off, False, True)
            elif i == self.selidx:
                if self.additional_formatting and i == self.default_option:
                    self.parent.add_string(row, "[{!magenta,black!}%s{!white,black!}]" % opt, screen, off, False, True)
                elif self.additional_formatting:
                    self.parent.add_string(row, "[{!white,blue!}%s{!white,black!}]" % opt, screen, off, False, True)
                else:
                    self.parent.add_string(row, "[{!white,black,underline!}%s{!white,black!}]" %
                                           opt, screen, off, False, True)
            else:
                self.parent.add_string(row, "[%s]" % opt, screen, off, False, True)
            off += len(opt) + 3
        if self.message:
            return 2
        else:
            return 1

    def handle_read(self, c):
        if c == curses.KEY_LEFT:
            self.selidx = max(0, self.selidx - 1)
        if c == curses.KEY_RIGHT:
            self.selidx = min(len(self.opts) - 1, self.selidx + 1)

    def get_value(self):
        return self.vals[self.selidx]

    def set_value(self, nv):
        for i, val in enumerate(self.vals):
            if nv == val:
                self.selidx = i
                return
        raise Exception("Invalid value for SelectInput")


class TextInput(InputField):
    def __init__(self, parent, move_func, width, message, name, value, docmp, additional_formatting=False):
        self.parent = parent
        self.move_func = move_func
        self.width = width

        self.additional_formatting = additional_formatting

        self.message = message
        self.name = name
        self.value = value
        self.default_value = value
        self.docmp = docmp

        self.tab_count = 0
        self.cursor = len(self.value)
        self.opts = None
        self.opt_off = 0

    def get_height(self):
        return 2 + bool(self.message)

    def render(self, screen, row, width, selected, col=1, cursor_offset=0):
        if not self.value and not selected and len(self.default_value) != 0:
            self.value = self.default_value
            self.cursor = len(self.value)

        if self.message:
            self.parent.add_string(row, self.message, screen, col, False, True)
            row += 1
        if selected:
            if self.opts:
                self.parent.add_string(row + 1, self.opts[self.opt_off:], screen, col, False, True)
            if self.cursor > (width - 3):
                self.move_func(row, width - 2)
            else:
                self.move_func(row, self.cursor + 1 + cursor_offset)
        slen = len(self.value) + 3
        if slen > width:
            vstr = self.value[(slen - width):]
        else:
            vstr = self.value.ljust(width - 2)

        if self.additional_formatting and len(self.value) != 0 and self.value == self.default_value:
            self.parent.add_string(row, "{!magenta,white!}%s" % vstr, screen, col, False, False)
        else:
            self.parent.add_string(row, "{!black,white,bold!}%s" % vstr, screen, col, False, False)

        if self.message:
            return 3
        else:
            return 2

    def get_value(self):
        return self.value

    def set_value(self, val):
        self.value = val
        self.cursor = len(self.value)

    # most of the cursor,input stuff here taken from ui/console/screen.py
    def handle_read(self, c):
        if c == 9 and self.docmp:
            # Keep track of tab hit count to know when it's double-hit
            self.tab_count += 1
            if self.tab_count > 1:
                second_hit = True
                self.tab_count = 0
            else:
                second_hit = False

            # We only call the tab completer function if we're at the end of
            # the input string on the cursor is on a space
            if self.cursor == len(self.value) or self.value[self.cursor] == " ":
                if self.opts:
                    prev = self.opt_off
                    self.opt_off += self.width - 3
                    # now find previous double space, best guess at a split point
                    # in future could keep opts unjoined to get this really right
                    self.opt_off = self.opts.rfind("  ", 0, self.opt_off) + 2
                    if second_hit and self.opt_off == prev:  # double tap and we're at the end
                        self.opt_off = 0
                else:
                    opts = self.complete(self.value)
                    if len(opts) == 1:  # only one option, just complete it
                        self.value = opts[0]
                        self.cursor = len(opts[0])
                        self.tab_count = 0
                    elif len(opts) > 1:
                        prefix = os.path.commonprefix(opts)
                        if prefix:
                            self.value = prefix
                            self.cursor = len(prefix)

                    if len(opts) > 1 and second_hit:  # display multiple options on second tab hit
                        sp = self.value.rfind(os.sep) + 1
                        self.opts = "  ".join([o[sp:] for o in opts])

        # Cursor movement
        elif c == curses.KEY_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif c == curses.KEY_RIGHT:
            self.cursor = min(len(self.value), self.cursor + 1)
        elif c == curses.KEY_HOME:
            self.cursor = 0
        elif c == curses.KEY_END:
            self.cursor = len(self.value)

        if c != 9:
            self.opts = None
            self.opt_off = 0
            self.tab_count = 0

        # Delete a character in the input string based on cursor position
        if c == curses.KEY_BACKSPACE or c == 127:
            if self.value and self.cursor > 0:
                self.value = self.value[:self.cursor - 1] + self.value[self.cursor:]
                self.cursor -= 1
        elif c == curses.KEY_DC:
            if self.value and self.cursor < len(self.value):
                self.value = self.value[:self.cursor] + self.value[self.cursor + 1:]
        elif c > 31 and c < 256:
            # Emulate getwch
            stroke = chr(c)
            uchar = ""
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
                    self.value = self.value[:self.cursor] + uchar + self.value[self.cursor:]
                # Move the cursor forward
                self.cursor += 1

    def complete(self, line):
        line = os.path.abspath(os.path.expanduser(line))
        ret = []
        if os.path.exists(line):
            # This is a correct path, check to see if it's a directory
            if os.path.isdir(line):
                # Directory, so we need to show contents of directory
                # ret.extend(os.listdir(line))
                for f in os.listdir(line):
                    # Skip hidden
                    if f.startswith("."):
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


class InputPopup(Popup):
    def __init__(self, parent_mode, title, width_req=0, height_req=0, align=ALIGN.DEFAULT, close_cb=None,
                 additional_formatting=True, immediate_action=False):
        Popup.__init__(self, parent_mode, title, width_req=width_req, height_req=height_req,
                       align=align, close_cb=close_cb)
        self.inputs = []
        self.lines = []
        self.current_input = 0

        self.additional_formatting = additional_formatting
        self.immediate_action = immediate_action

        # We need to replicate some things in order to wrap our inputs
        self.encoding = parent_mode.encoding

    def move(self, r, c):
        self._cursor_row = r
        self._cursor_col = c

    def add_text_input(self, message, name, value="", complete=True):
        """
        Add a text input field to the popup.

        :param message: string to display above the input field
        :param name: name of the field, for the return callback
        :param value: initial value of the field
        :param complete: should completion be run when tab is hit and this field is active
        """
        self.inputs.append(TextInput(self, self.move, self.width, message, name, value, complete,
                                     additional_formatting=self.additional_formatting))

    def getmaxyx(self):
        return self.screen.getmaxyx()

    def add_string(self, row, string, scr=None, col=0, pad=True, trim=True):
        if row <= 0:
            return False
        elif row >= self.height - 1:
            return False
        self.parent.add_string(row, string, scr, col, pad, trim)
        return True

    def add_spaces(self, num):
        for i in range(num):
            self.lines.append((len(self.inputs), ""))

    def add_text(self, string):
        lines = string.split("\n")
        for line in lines:
            self.lines.append((len(self.inputs), line))

    def add_select_input(self, message, name, opts, vals, default_index=0):
        self.inputs.append(SelectInput(self, message, name, opts, vals, default_index,
                           additional_formatting=self.additional_formatting))

    def add_checked_input(self, message, name, checked=False):
        self.inputs.append(CheckedInput(self, message, name, checked,
                           additional_formatting=self.additional_formatting))

    # def add_checked_plus_input(self, message, name, child)

    def add_float_spin_input(self, message, name, value=0.0, inc_amt=1.0, precision=1, min_val=None, max_val=None):
        i = FloatSpinInput(self, message, name, self.move, value, inc_amt, precision, min_val, max_val,
                           additional_formatting=self.additional_formatting)
        self.inputs.append(i)

    def add_int_spin_input(self, message, name, value=0, min_val=None, max_val=None):
        i = IntSpinInput(self, message, name, self.move, value, min_val, max_val,
                         additional_formatting=self.additional_formatting)
        self.inputs.append(i)

    def _refresh_lines(self):
        self._cursor_row = -1
        self._cursor_col = -1
        curses.curs_set(0)

        start_row = 0
        end_row = 0
        for i, ipt in enumerate(self.inputs):
            for line in self.lines:
                if line[0] == i:
                    end_row += 1
            start_row = end_row
            end_row += ipt.get_height()
            active = (i == self.current_input)

            if active:
                if end_row + 1 >= self.height + self.lineoff:
                    self.lineoff += ipt.get_height()
                elif start_row < self.lineoff:
                    self.lineoff -= ipt.get_height()
            self.content_height = end_row

        crow = 1 - self.lineoff
        for i, ipt in enumerate(self.inputs):
            for line in self.lines:
                if line[0] == i:
                    self.add_string(crow, line[1], self.screen, 1, pad=False)
                    crow += 1
            crow += ipt.render(self.screen, crow, self.width, i == self.current_input)

        if (self.content_height > (self.height - 2)):
            lts = self.content_height - (self.height - 3)
            perc_sc = float(self.lineoff) / lts
            sb_pos = int((self.height - 2) * perc_sc) + 1
            if (sb_pos == 1) and (self.lineoff != 0):
                sb_pos += 1
            self.add_string(sb_pos, "{!red,black,bold!}#", self.screen, col=(self.width - 1), pad=False, trim=False)
        if self._cursor_row >= 0:
            curses.curs_set(2)
            self.screen.move(self._cursor_row, self._cursor_col)

    def handle_read(self, c):
        if c == curses.KEY_UP:
            self.current_input = max(0, self.current_input - 1)
        elif c == curses.KEY_DOWN:
            self.current_input = min(len(self.inputs) - 1, self.current_input + 1)
        elif c == curses.KEY_ENTER or c == 10:
            if self.close_cb:
                vals = {}
                for ipt in self.inputs:
                    vals[ipt.name] = ipt.get_value()
                curses.curs_set(0)
                self.close_cb(vals)
            return True  # close the popup
        elif c == 27:  # close on esc, no action
            return True
        elif self.inputs:
            self.inputs[self.current_input].handle_read(c)
            if self.immediate_action:
                vals = {}
                for ipt in self.inputs:
                    vals[ipt.name] = ipt.get_value()
                self.close_cb(vals)

        self.refresh()
        return False
