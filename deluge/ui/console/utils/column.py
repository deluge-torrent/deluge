# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import copy
import logging

import deluge.common
from deluge.i18n import setup_translation
from deluge.ui.common import TORRENT_DATA_FIELD
from deluge.ui.console.utils import format_utils

setup_translation()

log = logging.getLogger(__name__)

torrent_data_fields = copy.deepcopy(TORRENT_DATA_FIELD)

formatters = {
    'queue': format_utils.format_queue,
    'name': lambda a, b: b,
    'state': None,
    'tracker': None,
    'download_location': None,
    'owner': None,
    'progress_state': format_utils.format_progress,
    'progress': format_utils.format_progress,
    'size': format_utils.format_size,
    'downloaded': format_utils.format_size,
    'uploaded': format_utils.format_size,
    'remaining': format_utils.format_size,
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
    'seeding_time': format_utils.format_time,
    'active_time': format_utils.format_time,
    'time_since_transfer': format_utils.format_date_dash,
    'finished_time': deluge.common.ftime,
    'last_seen_complete': format_utils.format_date_never,
    'completed_time': format_utils.format_date_dash,
    'eta': format_utils.format_time,
    'pieces': format_utils.format_pieces,
}

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
