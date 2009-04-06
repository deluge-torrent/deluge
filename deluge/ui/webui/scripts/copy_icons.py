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
copy  icons from kde icon set.
Edit ICON_SET and TARGET_DIR before running this file.
#perl -pi -w -e 's/tango/16/g;' *.html
"""
import os
from os import path
from shutil import copyfile

ICON_SET  = "/home/martijn/prj/oxygen/oxygen"
TARGET_DIR = "/home/martijn/src/deluge/deluge/ui/webui"

def copy_icons(source_dir , target_dir , mapping):
    for target, source in mapping.iteritems():
        source = path.join(source_dir, source) +  ".png"
        target = path.join(target_dir, target) +  ".png"
        print "%s -> %s" % (source, target)
        copyfile(source, target)

map_static16 = {
    "down":"actions/1downarrow",
    "up":"actions/1downarrow",
    "connections":"apps/preferences_system_network_sharing",
    "details":"actions/object_edit",
    "edit-clear":"actions/clear_left",
    "edit-redo":"actions/edit_redo",
    "go-bottom":"actions/2downarrow",
    "go-top":"actions/2uparrow",
    "label":"actions/rss_tag",
    "list-add":"actions/add",
    "list-remove":"actions/fileclose",
    "move":"actions/filesaveas",
    "pause":"actions/media_playback_pause",
    "preferences-system":"apps/preferences_system",
    "process-stop":"actions/process_stop",
    "queue-down":"actions/1downarrow",
    "queue-up":"actions/1uparrow",
    "start":"actions/media_playback_start",
    "stop":"actions/media_playback_stop",
    "system-log-out":"actions/system_log_out",
    "user-trash":"actions/edittrash",
    "view-refresh":"actions/view_refresh",
    "gtk-yes":"actions/flag_green",
    "drive-harddisk":"devices/drive_harddisk",
    "select-all":"actions/edit_select_all"
}

map_ajax16 = {
    "gtk-edit":"actions/object_edit",
    "gtk-yes":"actions/flag_green",
    "network-idle":"apps/preferences_system_network_sharing",
    "view-refresh":"actions/view_refresh",
    "view-sort-ascending":"actions/view_sort_ascending",
    "view-sort-descending":"actions/view_sort_descending"
}

map_ajax32 = {
    "add":"actions/add",
    "connections":"apps/preferences_system_network_sharing",
    "down":"actions/1downarrow",
    "up":"actions/1uparrow",
    "new":"actions/document_new",
    "options":"apps/preferences_system",
    "pause":"actions/media_playback_pause",
    "remove":"actions/fileclose",
    "resume":"actions/media_playback_start"
}


copy_icons( path.join(ICON_SET, "16x16"), path.join(TARGET_DIR, "static/images/16"), map_static16)
copy_icons( path.join(ICON_SET, "16x16"), path.join(TARGET_DIR, "templates/ajax/static/icons/16"), map_ajax16)
copy_icons( path.join(ICON_SET, "32x32"), path.join(TARGET_DIR, "templates/ajax/static/icons/32"), map_ajax32)


