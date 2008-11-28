#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
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

from deluge.ui.client import sclient

sclient.set_core_uri()

print sclient.get_enabled_plugins()

#enable plugin.
if not "label" in sclient.get_enabled_plugins():
    sclient.enable_plugin("label")


#test labels.
print "#init labels"
try:
    sclient.label_remove("test")
except:
    pass
id = sclient.get_session_state()[0]

print "#add"
sclient.label_add("test")
print "#set"
sclient.label_set_torrent(id,"test")

print sclient.get_torrents_status({"label":"test"},"name")


print "#set options"
sclient.label_set_options("test",{"max_download_speed":999}, True)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "999"
sclient.label_set_options("test",{"max_download_speed":9}, True)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "9"
sclient.label_set_options("test",{"max_download_speed":888}, False)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "9 (888)"

print sclient.get_torrent_status(id,['name', 'tracker_host', 'label'])
