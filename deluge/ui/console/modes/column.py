# -*- coding: utf-8 -*-
#
# column.py
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
import format_utils

import logging
log = logging.getLogger(__name__)


def format_queue(qnum):
    if (qnum >= 0):
        return "%d"%(qnum+1)
    else:
        return ""

columns = {
    "#":(("queue",),format_queue),
    "Name":(("name",),None),
    "Size":(("total_wanted",),deluge.common.fsize),
    "State":(("state",),None),
    "Progress":(("progress",),format_utils.format_progress),
    "Seeders":(("num_seeds","total_seeds"),format_utils.format_seeds_peers),
    "Peers":(("num_peers","total_peers"),format_utils.format_seeds_peers),
    "Down Speed":(("download_payload_rate",),format_utils.format_speed),
    "Up Speed":(("upload_payload_rate",),format_utils.format_speed),
    "ETA":(("eta",), format_utils.format_time),
    "Ratio":(("ratio",), format_utils.format_float),
    "Avail":(("distributed_copies",), format_utils.format_float),
    "Added":(("time_added",), deluge.common.fdate),
    "Tracker":(("tracker_host",), None),
    "Save Path":(("save_path",), None),
    "Downloaded":(("all_time_download",), deluge.common.fsize),
    "Uploaded":(("total_uploaded",), deluge.common.fsize),
    "Owner":(("owner",),None)
    }

def get_column_value(name,state):
    try:
        col = columns[name]
    except KeyError:
        log.error("No such column: %s",name)
        return None

    if col[1]:
        try:
            args = [ state[key] for key in col[0] ]
        except:
            log.error("Could not get column field: %s",col[0])
            return None
        return col[1](*args)
    else:
        return state[col[0][0]]


def get_required_fields(cols):
    fields = []
    for col in cols:
        fields.extend(columns.get(col)[0])
    return fields



