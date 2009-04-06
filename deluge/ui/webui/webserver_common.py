#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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


"""
webui constants
"""
import os


TORRENT_KEYS = ['name', 'total_size', 'num_files', 'num_pieces', 'piece_length',
    'eta', 'ratio', 'file_progress', 'distributed_copies', 'total_done',
    'total_uploaded', 'state', 'paused', 'progress', 'next_announce',
    'total_payload_download', 'total_payload_upload', 'download_payload_rate',
    'upload_payload_rate', 'num_peers', 'num_seeds', 'total_peers', 'total_seeds',
    'total_wanted', 'tracker', 'trackers', 'tracker_status', 'save_path',
    'files', 'file_priorities', 'compact', 'max_connections',
    'max_upload_slots', 'max_download_speed', 'prioritize_first_last',
    'private','max_upload_speed','queue','peers',
    "active_time", "seeding_time", "seed_rank", "is_auto_managed", #stats
    "stop_at_ratio","stop_ratio","remove_at_ratio", #ratio
    'tracker_host', 'label' #label-plugin
    ]

CONFIG_DEFAULTS = {
    "port":8112,
    "button_style":2,
    "auto_refresh":False,
    "auto_refresh_secs": 10,
    "template":"white",
    "pwd_salt":"2\xe8\xc7\xa6(n\x81_\x8f\xfc\xdf\x8b\xd1\x1e\xd5\x90",
    "pwd_md5":".\xe8w\\+\xec\xdb\xf2id4F\xdb\rUc",
    "cache_templates":True,
    "daemon":"http://localhost:58846",
    "base":"",
    "disallow":{},
    "sessions":[],
    "sidebar_show_zero":False,
    "sidebar_show_trackers":False,
    "show_keyword_search":False,
    "show_sidebar":True,
    "https":False,
    "refresh_secs":10
}
