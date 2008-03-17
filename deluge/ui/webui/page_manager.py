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

from deluge import component

class PageManager(component.Component):
    """
    web,py 0.2 mapping hack..
    see deluge_webserver.py
    """
    def __init__(self):
        component.Component.__init__(self, "PageManager")
        self.page_classes = {}
        self.urls = []

    def register_pages(self, url_list, class_list):
        self.urls += url_list
        self.page_classes.update(class_list)

    def register_page(self, url, klass):
        self.urls.append(url)
        self.urls.append(klass.__name__)
        self.page_classes[klass.__name__] = klass

    def unregister_page(self, url):
        raise NotImplemenetedError()
        #self.page_classes[klass.__name__] = None

__page_manager = PageManager()










