# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.common
from deluge.ui.console.modes import format_utils

log = logging.getLogger(__name__)


def format_queue(qnum):
    if qnum >= 0:
        return "%d" % (qnum + 1)
    else:
        return ""

columns = {
    "#": (("queue",), format_queue),
    "Name": (("name",), None),
    "Size": (("total_wanted",), deluge.common.fsize),
    "State": (("state",), None),
    "Progress": (("progress",), format_utils.format_progress),
    "Seeds": (("num_seeds", "total_seeds"), format_utils.format_seeds_peers),
    "Peers": (("num_peers", "total_peers"), format_utils.format_seeds_peers),
    "Down Speed": (("download_payload_rate",), format_utils.format_speed),
    "Up Speed": (("upload_payload_rate",), format_utils.format_speed),
    "ETA": (("eta",), format_utils.format_time),
    "Ratio": (("ratio",), format_utils.format_float),
    "Avail": (("distributed_copies",), format_utils.format_float),
    "Added": (("time_added",), deluge.common.fdate),
    "Tracker": (("tracker_host",), None),
    "Download Folder": (("download_location",), None),
    "Downloaded": (("all_time_download",), deluge.common.fsize),
    "Uploaded": (("total_uploaded",), deluge.common.fsize),
    "Remaining": (("total_remaining",), deluge.common.fsize),
    "Owner": (("owner",), None),
    "Shared": (("shared",), str),
    "Active Time": (("active_time",), deluge.common.ftime),
    "Seeding Time": (("seeding_time",), deluge.common.ftime),
    "Complete Seen": (("last_seen_complete",), format_utils.format_date_never),
    "Completed": (("completed_time",), format_utils.format_date),
    "Seeds:Peers": (("seeds_peers_ratio",), format_utils.format_float),
    "Down Limit": (("max_download_speed",), format_utils.format_speed),
    "Up Limit": (("max_upload_speed",), format_utils.format_speed),
}


def get_column_value(name, state):
    try:
        col = columns[name]
    except KeyError:
        return "Please Wait"

    if col[1]:
        try:
            args = [state[key] for key in col[0]]
        except KeyError:
            return "Please Wait"
        return col[1](*args)
    else:
        try:
            return state[col[0][0]]
        except KeyError:
            return "Please Wait"


def get_required_fields(cols):
    fields = []
    for col in cols:
        fields.extend(columns.get(col)[0])
    return fields
