#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
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
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import os
import deluge
from deluge.common import INSTALL_PREFIX
import random
import pickle
random.seed()

config_file = deluge.common.CONFIG_DIR + "/webui.conf"
#config = deluge.pref.Preferences(config_file, False)
config = pickle.load(open(config_file))

if config.get('run_in_thread'):
    #do not use dbus ipc for threads!
    from dbus_interface import get_dbus_manager
    proxy = get_dbus_manager()
else:
    import dbus
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.deluge_torrent.dbusplugin"
        , "/org/deluge_torrent/DelugeDbusPlugin")

REVNO = open(os.path.join(os.path.dirname(__file__),'revno')).read()
VERSION = open(os.path.join(os.path.dirname(__file__),'version')).read()

TORRENT_KEYS = ['distributed_copies', 'download_payload_rate',
    'download_rate', 'eta', 'is_seed', 'name', 'next_announce',
    'num_files', 'num_peers', 'num_pieces', 'num_seeds', 'paused',
    'piece_length','progress', 'ratio', 'total_done', 'total_download',
    'total_payload_download', 'total_payload_upload', 'total_peers',
    'total_seeds', 'total_size', 'total_upload', 'total_wanted',
    'tracker_status', 'upload_payload_rate', 'upload_rate',
    'uploaded_memory','tracker','state']

STATE_MESSAGES = (_("Queued"),
    _("Checking"),
    _("Connecting"),
    _("Downloading Metadata"),
    _("Downloading"),
    _("Finished"),
    _("Seeding"),
    _("Allocating"))
