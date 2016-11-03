# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import copy
import logging

import deluge.common
from deluge.ui.common import TORRENT_DATA_FIELD
from deluge.ui.util import lang

from . import format_utils

lang.setup_translations()

log = logging.getLogger(__name__)

torrent_data_fields = copy.deepcopy(TORRENT_DATA_FIELD)


def format_queue(qnum):
    if qnum < 0:
        return ''
    return '%d' % (qnum + 1)


formatters = {
    'queue': format_queue,
    'name': lambda a, b: b,
    'state': None,
    'tracker': None,
    'download_location': None,
    'owner': None,

    'progress_state': format_utils.format_progress,
    'progress': format_utils.format_progress,

    'size': deluge.common.fsize,
    'downloaded': deluge.common.fsize,
    'uploaded': deluge.common.fsize,
    'remaining': deluge.common.fsize,

    'ratio': format_utils.format_float,
    'avail': format_utils.format_float,
    'seeds_peers_ratio': format_utils.format_float,

    'download_speed': format_utils.format_speed,
    'upload_speed': format_utils.format_speed,
    'max_download_speed': format_utils.format_speed,
    'max_upload_speed': format_utils.format_speed,

    'peers': format_utils.format_seeds_peers,
    'seeds': format_utils.format_seeds_peers,

    'time_added': deluge.common.fdate,
    'seeding_time': deluge.common.ftime,
    'active_time': deluge.common.ftime,
    'finished_time': deluge.common.ftime,

    'last_seen_complete': format_utils.format_date_never,
    'completed_time': format_utils.format_date,
    'eta': format_utils.format_time,
    'pieces': format_utils.format_pieces,
}

torrent_data_fields['pieces'] = {'name': _('Pieces'), 'status': ['num_pieces', 'piece_length']}
torrent_data_fields['seed_rank'] = {'name': _('Seed Rank'), 'status': ['seed_rank']}

for data_field in torrent_data_fields:
    torrent_data_fields[data_field]['formatter'] = formatters.get(data_field, str)


def get_column_value(name, state):
    col = torrent_data_fields[name]

    if col['formatter']:
        args = [state[key] for key in col['status']]
        return col['formatter'](*args)
    else:
        return state[col['status'][0]]


def get_required_fields(cols):
    fields = []
    for col in cols:
        fields.extend(torrent_data_fields[col]['status'])
    return fields
