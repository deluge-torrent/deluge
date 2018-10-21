# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

TORRENT_OPTIONS = {
    'max_download_speed': float,
    'max_upload_speed': float,
    'max_connections': int,
    'max_upload_slots': int,
    'prioritize_first_last': bool,
    'is_auto_managed': bool,
    'stop_at_ratio': bool,
    'stop_ratio': float,
    'remove_at_ratio': bool,
    'move_completed': bool,
    'move_completed_path': str,
    'super_seeding': bool,
}
