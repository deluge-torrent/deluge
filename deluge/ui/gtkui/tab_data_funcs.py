# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from deluge.common import fdate, fsize, fspeed, ftime


def ftotal_sized(first, second):
    return '%s (%s)' % (fsize(first, shortform=True), fsize(second, shortform=True))


def fratio(value):
    return ('%.3f' % value).rstrip('0').rstrip('.') if value > 0 else '∞'


def fpcnt(value, state, message):
    textstr = _(state)
    if state not in ('Error', 'Seeding') and value < 100:
        textstr = ('%s %.2f' % (textstr, value)).rstrip('0').rstrip('.') + '%'
    elif state == 'Error':
        textstr = _('%s: %s') % (textstr, message)
    return textstr


def fspeed_max(value, max_value=-1):
    value = fspeed(value, shortform=True)
    return '%s (%s %s)' % (value, max_value, _('K/s')) if max_value > -1 else value


def fdate_or_never(value):
    """Display value as date, eg 05/05/08 or Never"""
    return fdate(value, date_only=True) if value > 0 else _('Never')


def fdate_or_dash(value):
    """Display value as date, eg 05/05/08 or dash"""
    if value > 0.0:
        return fdate(value)
    else:
        return '-'


def ftime_or_dash(value):
    """Display value as time, eg 2h 30m or dash"""
    return ftime(value) if value > 0 else '-'


def fseed_rank_or_dash(seed_rank, seeding_time):
    """Display value if seeding otherwise dash"""

    if seeding_time > 0:
        if seed_rank >= 1000:
            return '%ik' % (seed_rank // 1000)
        else:
            return str(seed_rank)
    else:
        return '-'


def flast_active(time_since_download, time_since_upload):
    """The last time the torrent was active as time e.g. 2h 30m or dash"""

    try:
        last_time_since = min((x for x in (time_since_download, time_since_upload) if x != -1))
    except ValueError:
        return '-'
    else:
        return ftime(last_time_since)


def fpieces_num_size(num_pieces, piece_size):
    return '%s (%s)' % (num_pieces, fsize(piece_size, precision=0))


def fcount(value):
    return '%s' % len(value)


def ftranslate(text):
    if text:
        text = _(text)
    return text


def fyes_no(value):
    """Return Yes or No to bool value"""
    return _('Yes') if value else _('No')
