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

admin_pages = [] #[(title, url),..]
detail_tabs = [] #[(title, url),..]
toolbar_items = [] #((id,title ,flag ,method ,url ,image ),.. )

#a storage+sorteddict ==  evildict.

#toolbar:

class TB:
    generic = 0
    torrent = 1
    torrent_list = 2

@logcall
def register_toolbar_item(id, title, image, flag, method, url, important):
    toolbar_items.append((id, title, image, flag, method, url, important))
    #todo: remove lower hack.

@logcall
def unregister_toolbar_item(item_id):
    for (i, toolbar) in enumerate(admin_pages):
        if toolbar[0] == item_id:
            del toolbar_items[i]

#admin:
@logcall
def register_admin_page(id, title, url):
    admin_pages.append((id, title, url))

@logcall
def unregister_admin_page(page_id):
    for (i, (id, title, url)) in list(enumerate(admin_pages)):
        if id == page_id:
            del admin_pages[i]
            return

#detail:
@logcall
def register_detail_tab(id, title, page):
    detail_tabs.append((id, title, page))

@logcall
def unregister_detail_tab(tab_id):
    for (i, (id, title, tab)) in list(enumerate(detail_tabs)):
        if id == tab_id:
            del detail_tabs[i]
            return


#def register_page
def register_page(url, method):
    pass #TODO :(


#register vars in template.
template.Template.globals["admin_pages"] = admin_pages
template.Template.globals["detail_tabs"] = detail_tabs
template.Template.globals["toolbar_items"] = toolbar_items
