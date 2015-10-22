# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import re
from collections import deque
from unicodedata import normalize as ud_normalize
from unicodedata import east_asian_width

import deluge.common


def format_speed(speed):
    if speed > 0:
        return deluge.common.fspeed(speed)
    else:
        return "-"


def format_time(time):
    if time > 0:
        return deluge.common.ftime(time)
    else:
        return "-"


def format_date(time):
    if time > 0:
        return deluge.common.fdate(time)
    else:
        return ""


def format_date_never(time):
    if time > 0:
        return deluge.common.fdate(time)
    else:
        return "Never"


def format_float(x):
    if x < 0:
        return "-"
    else:
        return "%.3f" % x


def format_seeds_peers(num, total):
    return "%d (%d)" % (num, total)


def format_progress(perc):
    if perc < 100:
        return "%.2f%%" % perc
    else:
        return "100%"


def format_pieces(num, size):
    return "%d (%s)" % (num, deluge.common.fsize(size))


def format_priority(prio):
    if prio == - 2:
        return "[Mixed]"
    if prio < 0:
        return "-"
    pstring = deluge.common.FILE_PRIORITY[prio]
    if prio > 0:
        return pstring[:pstring.index("Priority") - 1]
    else:
        return pstring


def trim_string(string, w, have_dbls):
    if w <= 0:
        return ""
    elif w == 1:
        return u" "
    elif have_dbls:
        # have to do this the slow way
        chrs = []
        width = 4
        idx = 0
        while width < w:
            chrs.append(string[idx])
            if east_asian_width(string[idx]) in ["W", "F"]:
                width += 2
            else:
                width += 1
            idx += 1
        if width != w:
            chrs.pop()
            chrs.append(".")
        return u"%s " % ("".join(chrs))
    else:
        return u"%s " % (string[0:w - 1])


def format_column(col, lim):
    dbls = 0
    # Chosen over isinstance(col, unicode) and col.__class__ == unicode
    # for speed - it's ~3 times faster for non-unicode strings and ~1.5
    # for unicode strings.
    if col.__class__ is unicode:
        # might have some double width chars
        col = ud_normalize("NFC", col)
        dbls = sum(east_asian_width(c) in "WF" for c in col)
    size = len(col) + dbls
    if size >= lim - 1:
        return trim_string(col, lim, dbls > 0)
    else:
        return "%s%s" % (col, " " * (lim - size))


def format_row(row, column_widths):
    return "".join([format_column(row[i], column_widths[i]) for i in range(0, len(row))])

_strip_re = re.compile("\\{!.*?!\\}")


def remove_formatting(string):
    return re.sub(_strip_re, "", string)


def wrap_string(string, width, min_lines=0, strip_colors=True):
    """
    Wrap a string to fit in a particular width.  Returns a list of output lines.

    :param string: str, the string to wrap
    :param width: int, the maximum width of a line of text
    :param min_lines: int, extra lines will be added so the output tuple contains at least min_lines lines
    :param strip_colors: boolean, if True, text in {!!} blocks will not be considered as adding to the
                              width of the line.  They will still be present in the output.
    """
    ret = []
    s1 = string.split("\n")

    def insert_clr(s, offset, mtchs, clrs):
        end_pos = offset + len(s)
        while mtchs and (mtchs[0] <= end_pos) and (mtchs[0] >= offset):
            mtc = mtchs.popleft() - offset
            clr = clrs.popleft()
            end_pos += len(clr)
            s = "%s%s%s" % (s[:mtc], clr, s[mtc:])
        return s

    for s in s1:
        offset = 0
        if strip_colors:
            mtchs = deque()
            clrs = deque()
            for m in _strip_re.finditer(s):
                mtchs.append(m.start())
                clrs.append(m.group())
            cstr = _strip_re.sub("", s)
        else:
            cstr = s
        while len(cstr) > width:
            sidx = cstr.rfind(" ", 0, width - 1)
            sidx += 1
            if sidx > 0:
                if strip_colors:
                    to_app = cstr[0:sidx]
                    to_app = insert_clr(to_app, offset, mtchs, clrs)
                    ret.append(to_app)
                    offset += len(to_app)
                else:
                    ret.append(cstr[0:sidx])
                cstr = cstr[sidx:]
                if not cstr:
                    cstr = None
                    break
            else:
                # can't find a reasonable split, just split at width
                if strip_colors:
                    to_app = cstr[0:width]
                    to_app = insert_clr(to_app, offset, mtchs, clrs)
                    ret.append(to_app)
                    offset += len(to_app)
                else:
                    ret.append(cstr[0:width])
                cstr = cstr[width:]
                if not cstr:
                    cstr = None
                    break
        if cstr is not None:
            if strip_colors:
                ret.append(insert_clr(cstr, offset, mtchs, clrs))
            else:
                ret.append(cstr)

    if min_lines > 0:
        for i in range(len(ret), min_lines):
            ret.append(" ")

    # Carry colors over to the next line
    last_color_string = ""
    for i, line in enumerate(ret):
        if i != 0:
            ret[i] = "%s%s" % (last_color_string, ret[i])

        colors = re.findall("\\{![^!]+!\\}", line)
        if colors:
            last_color_string = colors[-1]

    return ret


def strwidth(string):
    """
    Measure width of a string considering asian double width characters
    """
    if not isinstance(string, unicode):
        string = unicode(string, "utf-8")
    return sum([1 + (east_asian_width(char) in ["W", "F"]) for char in string])


def pad_string(string, length, character=" ", side="right"):
    """
    Pad string with specified character to desired length, considering double width characters.
    """
    w = strwidth(string)
    diff = length - w
    if side == "left":
        return "%s%s" % (character * diff, string)
    elif side == "right":
        return "%s%s" % (string, character * diff)
