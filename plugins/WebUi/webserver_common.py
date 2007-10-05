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
from webpy022 import template

random.seed()

config_file = deluge.common.CONFIG_DIR + "/webui.conf"

#a bit hacky way of detecting i'm in the deluge gui or in a process :(
if not hasattr(deluge,'pref'):
    import dbus
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.deluge_torrent.dbusplugin"
        , "/org/deluge_torrent/DelugeDbusPlugin")
    config = pickle.load(open(config_file))
    render = template.render('templates/%s/' % config.get('template'),
        cache=config.get('cache_templates'))

def init():
    #appy possibly changed config-vars, only called in when runing inside gtk.
    from dbus_interface import get_dbus_manager
    globals()['proxy'] =  get_dbus_manager()
    globals()['config']  = deluge.pref.Preferences(config_file, False)
    globals()['render'] = template.render('templates/%s/' % config.get('template'),
        cache=config.get('cache_templates'))


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
