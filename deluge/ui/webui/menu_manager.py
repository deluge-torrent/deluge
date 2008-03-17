#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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
#

"""
register toolbar and menu items.
future : required for plugin-api.
"""
from utils import logcall
from render import template
from deluge import component

class TOOLBAR_FLAGS:
    generic = 0
    torrent = 1
    torrent_list = 2

class MenuManager(component.Component):
    TOOLBAR_FLAGS = TOOLBAR_FLAGS
    def __init__(self):
        component.Component.__init__(self, "MenuManager")
        self.admin_pages = [] #[(title, url),..]
        self.detail_tabs = [] #[(title, url),..]
        self.toolbar_items = [] #((id,title ,flag ,method ,url ,image ),.. )


        #register vars in template.
        template.Template.globals["admin_pages"] = self.admin_pages
        template.Template.globals["detail_tabs"] = self.detail_tabs
        template.Template.globals["toolbar_items"] = self.toolbar_items


    def register_toolbar_item(self, id, title, image, flag, method, url, important):
        self.toolbar_items.append((id, title, image, flag, method, url, important))
        #todo: remove lower hack.

    def unregister_toolbar_item(self, item_id):
        for (i, toolbar) in enumerate(admin_pages):
            if toolbar[0] == item_id:
                del self.toolbar_items[i]

    #admin:
    def register_admin_page(self, id, title, url):
        self.admin_pages.append((id, title, url))

    def unregister_admin_page(page_id):
        for (i, (id, title, url)) in list(enumerate(admin_pages)):
            if id == page_id:
                del self.admin_pages[i]
                return

    #detail:
    def register_detail_tab(self, id, title, page):
        self.detail_tabs.append((id, title, page))

    def unregister_detail_tab(self, tab_id):
        for (i, (id, title, tab)) in list(enumerate(detail_tabs)):
            if id == tab_id:
                del self.detail_tabs[i]
                return

__menu_manager = MenuManager()

