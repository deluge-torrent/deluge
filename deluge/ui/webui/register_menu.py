#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

#

from deluge import component

menu = component.get("MenuManager")
TB = menu.TOOLBAR_FLAGS

menu.register_admin_page("config", _("Config"), "/config/")
menu.register_admin_page("connect", _("Connect"), "/connect")
menu.register_admin_page("about", _("About"), "/about")
menu.register_admin_page("logout", _("Logout"), "/logout")

menu.register_detail_tab("statistics", _("Statistics"), "tab_statistics")
menu.register_detail_tab("details", _("Details"), "tab_details")
menu.register_detail_tab("options", _("Options"), "tab_options")
menu.register_detail_tab("trackers", _("Trackers"), "tab_trackers")
menu.register_detail_tab("peers", _("Peers"), "tab_peers")
menu.register_detail_tab("files", _("Files"), "tab_files")

menu.register_toolbar_item("add", _("Add"), "list-add.png" , TB.generic, "GET","/torrent/add/", True)
menu.register_toolbar_item("delete",_("Delete"), "list-remove.png" ,TB.torrent_list, "GET","/torrent/delete/" , True)
menu.register_toolbar_item("stop",_("Stop"), "pause.png" ,TB.torrent_list, "POST","/torrent/stop/", True)
menu.register_toolbar_item("start",_("Start"), "start.png" ,TB.torrent_list, "POST","/torrent/start/", True)
menu.register_toolbar_item("queue_up",_("Queue Up"), "queue-up.png" ,TB.torrent_list, "POST","/torrent/queue/up/", True)
menu.register_toolbar_item("queue_down",_("Queue Down"), "queue-down.png" ,TB.torrent_list, "POST","/torrent/queue/down/", True)
menu.register_toolbar_item("queue_top",_("Queue Top"), "go-top.png" ,TB.torrent_list, "POST","/torrent/queue/top/", True)
menu.register_toolbar_item("queue_bottom",_("Queue Bottom"), "go-bottom.png" ,TB.torrent_list, "POST","/torrent/queue/bottom/", True)
menu.register_toolbar_item("details",_("Details"), "details.png" ,TB.torrent, "GET","/torrent/info/", True)
menu.register_toolbar_item("move",_("Move"), "move.png" ,TB.torrent_list,"POST","/torrent/move/", True)
menu.register_toolbar_item("reannounce",_("Reannounce"), "view-refresh.png" ,TB.torrent_list, "POST","/torrent/reannounce/", False)
menu.register_toolbar_item("recheck",_("Recheck"), "edit-redo.png" ,TB.torrent_list, "POST","/torrent/recheck/", False)
