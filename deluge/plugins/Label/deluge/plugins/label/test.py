#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

from deluge.ui.client import sclient

sclient.set_core_uri()

print(sclient.get_enabled_plugins())

# enable plugin.
if 'label' not in sclient.get_enabled_plugins():
    sclient.enable_plugin('label')


# test labels.
print('#init labels')
try:
    sclient.label_remove('test')
except Exception:
    pass
sess_id = sclient.get_session_state()[0]

print('#add')
sclient.label_add('test')
print('#set')
sclient.label_set_torrent(id, 'test')

print(sclient.get_torrents_status({'label': 'test'}, 'name'))


print('#set options')
sclient.label_set_options('test', {'max_download_speed': 999}, True)
print(sclient.get_torrent_status(sess_id, ['max_download_speed']), '999')
sclient.label_set_options('test', {'max_download_speed': 9}, True)
print(sclient.get_torrent_status(sess_id, ['max_download_speed']), '9')
sclient.label_set_options('test', {'max_download_speed': 888}, False)
print(sclient.get_torrent_status(sess_id, ['max_download_speed']), '9 (888)')

print(sclient.get_torrent_status(sess_id, ['name', 'tracker_host', 'label']))
