# -*- coding: utf-8 -*-
#
# format_utils.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

import deluge.common
try:
    import unicodedata
    haveud = True
except:
    haveud = False

def format_speed(speed):
    if (speed > 0):
        return deluge.common.fspeed(speed)
    else:
        return "-"

def format_time(time):
    if (time > 0):
        return deluge.common.ftime(time)
    else:
        return "-"

def format_float(x):
    if x < 0:
        return "∞"
    else:
        return "%.3f"%x

def format_seeds_peers(num, total):
    return "%d (%d)"%(num,total)

def format_progress(perc):
    if perc < 100:
        return "%.2f%%"%perc
    else:
        return "100%"

def format_pieces(num, size):
    return "%d (%s)"%(num,deluge.common.fsize(size))

def format_priority(prio):
    if prio == -2: return "[Mixed]"
    if prio < 0: return "-"
    pstring = deluge.common.FILE_PRIORITY[prio]
    if prio > 0:
        return pstring[:pstring.index("Priority")-1]
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
            if unicodedata.east_asian_width(string[idx]) in ['W','F']:
                width += 2
            else:
                width += 1
            idx += 1
        if width != w:
            chrs.pop()
            chrs.append('.')
        return u"%s "%("".join(chrs))
    else:
        return u"%s "%(string[0:w-1])

def format_column(col, lim):
    dbls = 0
    if haveud and isinstance(col,unicode):
        # might have some double width chars
        col = unicodedata.normalize("NFC",col)
        for c in col:
            if unicodedata.east_asian_width(c) in ['W','F']:
                # found a wide/full char
                dbls += 1
    size = len(col)+dbls
    if (size >= lim - 1):
        return trim_string(col,lim,dbls>0)
    else:
        return "%s%s"%(col," "*(lim-size))

def format_row(row, column_widths):
    return "".join([format_column(row[i],column_widths[i]) for i in range(0,len(row))])

import re
_strip_re = re.compile("\{!.*?!\}")

def remove_formatting(string):
    return re.sub(_strip_re, "", string)

from collections import deque
def wrap_string(string,width,min_lines=0,strip_colors=True):
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

    def insert_clr(s,offset,mtchs,clrs):
        end_pos = offset+len(s)
        while mtchs and (mtchs[0] <= end_pos) and (mtchs[0] >= offset):
            mtc = mtchs.popleft()-offset
            clr = clrs.popleft()
            end_pos += len(clr)
            s = "%s%s%s"%(s[:mtc],clr,s[mtc:])
        return s

    for s in s1:
        cur_pos = offset = 0
        if strip_colors:
            mtchs = deque()
            clrs = deque()
            for m in _strip_re.finditer(s):
                mtchs.append(m.start())
                clrs.append(m.group())
            cstr = _strip_re.sub('',s)
        else:
            cstr = s
        while len(cstr) > width:
            sidx = cstr.rfind(" ",0,width-1)
            sidx += 1
            if sidx > 0:
                if strip_colors:
                    to_app = cstr[0:sidx]
                    to_app = insert_clr(to_app,offset,mtchs,clrs)
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
                    to_app = insert_clr(to_app,offset,mtchs,clrs)
                    ret.append(to_app)
                    offset += len(to_app)
                else:
                    ret.append(cstr[0:width])
                cstr = cstr[width:]
                if not cstr:
                    cstr = None
                    break
        if cstr != None:
            if strip_colors:
                ret.append(insert_clr(cstr,offset,mtchs,clrs))
            else:
                ret.append(cstr)

    if min_lines>0:
        for i in range(len(ret),min_lines):
            ret.append(" ")

    return ret
