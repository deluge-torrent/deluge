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

def format_seeds_peers(num, total):
    return "%d (%d)"%(num,total)

def format_progress(perc):
    return "%.2f%%"%perc

def format_pieces(num, size):
    return "%d (%s)"%(num,deluge.common.fsize(size))

def format_priority(prio):
    if prio < 0: return "-"
    pstring = deluge.common.FILE_PRIORITY[prio]
    if prio > 0:
        return pstring[:pstring.index("Priority")-1]
    else:
        return pstring

def trim_string(string, w):
        return "%s... "%(string[0:w-4])

def format_column(col, lim):
    dbls = 0
    if haveud and isinstance(col,unicode):
        # might have some double width chars
        for c in col:
            if unicodedata.east_asian_width(c) in ['W','F']:
                # found a wide/full char
                dbls += 1
    size = len(col)+dbls
    if (size >= lim - 1):
        return trim_string(col,lim)
    else:
        return "%s%s"%(col," "*(lim-size))

def format_row(row,column_widths):
    return "".join([format_column(row[i],column_widths[i]) for i in range(0,len(row))])
