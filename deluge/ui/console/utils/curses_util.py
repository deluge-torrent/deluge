# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

try:
    import curses
except ImportError:
    pass

KEY_BELL = 7  # CTRL-/ ^G (curses.keyname(KEY_BELL) == "^G")
KEY_TAB = 9
KEY_ENTER2 = 10
KEY_ESC = 27
KEY_SPACE = 32
KEY_BACKSPACE2 = 127

KEY_ALT_AND_ARROW_UP = 564
KEY_ALT_AND_ARROW_DOWN = 523

KEY_ALT_AND_KEY_PPAGE = 553
KEY_ALT_AND_KEY_NPAGE = 548

KEY_CTRL_AND_ARROW_UP = 566
KEY_CTRL_AND_ARROW_DOWN = 525


def is_printable_chr(c):
    return c >= 32 and c <= 126


def is_int_chr(c):
    return c > 47 and c < 58


class Curser(object):
    INVISIBLE = 0
    NORMAL = 1
    VERY_VISIBLE = 2


def safe_curs_set(visibility):
    """
    Args:
        visibility(int): 0, 1, or 2, for invisible, normal, or very visible

    curses.curs_set fails on monochrome terminals so use this
    to ignore errors
    """
    try:
        curses.curs_set(visibility)
    except curses.error:
        pass


class ReadState(object):
    IGNORED = 0
    READ = 1
    CHANGED = 2
