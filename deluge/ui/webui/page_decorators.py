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
decorators for html-pages.
"""
#relative imports
from render import render
from utils import *
import utils
from deluge.ui.client import sclient as proxy
from deluge.log import LOG as log
#/relative

from web import cookies, setcookie as w_setcookie
from web import url, changequery
from utils import self_url
from render import error_page

#deco's:
def deluge_page_noauth(func):
    """
    add http headers;print result of func
    """
    def deco(self, name = None):
        render.set_global("is_auto_refreshed", False);
        web.header("Content-Type", "text/html; charset=utf-8")
        web.header("Cache-Control", "no-cache, must-revalidate")
        res = func(self, name) #deluge_page_noauth
        print res
    deco.__name__ = func.__name__
    return deco

def check_session(func):
    """
    1:check session
    2:block urls in config.disallow
    return func if session is valid, else redirect to login page.
    mostly used for POST-pages.
    """
    def deco(self, name = None):
        log.debug('%s.%s(name=%s)'  % (self.__class__.__name__, func.__name__,
            name))
        #check disallow config
        current_url = changequery()
        for blocked in utils.config["disallow"]:
            if current_url.startswith(blocked):
                return error_page("Not allowed to : '%s' , Reason: '%s'" %
                    (blocked , utils.config["disallow"][blocked]))
        #/check disallow

        #check session:
        vars = web.input(redir_after_login = None)
        ck = cookies()
        if ck.has_key("session_id") and ck["session_id"] in utils.config["sessions"]:
            return func(self, name) #check_session:ok
        elif vars.redir_after_login:
            utils.seeother(url("/login",redir=self_url()))
        else:
            utils.seeother("/login") #do not continue, and redirect to login page
        #/check session
    deco.__name__ = func.__name__
    return deco

def check_connected(func):
    def deco(self, name = None):
        connected = False
        try:
            proxy.ping()
            connected = True
        except Exception, e:
            log.debug("not_connected: %s" % e)
        if connected:
            return func(self, name) #check_connected:ok
        else:
            utils.seeother("/connect")
    deco.__name__ = func.__name__
    return deco

def deluge_page(func):
    "deluge_page_noauth+check_session+check connected"
    return check_session(check_connected(deluge_page_noauth(func)))

#combi-deco's:
#decorators to use in combination with the ones above.
def torrent_ids(func):
    """
    change page(self, name) to page(self, torrent_ids)
    for pages that allow a list of torrents.
    """
    def deco(self, name):
        return func (self, name.split(',')) #torrent_ids
    deco.__name__ = func.__name__
    return deco

def torrent_list(func):
    """
    change page(self, name) to page(self, torrent_ids)
    for pages that allow a list of torrents.
    """
    def deco(self, name):
        torrent_list = [get_torrent_status(id) for id in name.split(',')]
        return func (self, torrent_list) #torrent_list
    deco.__name__ = func.__name__
    return deco

def torrent(func):
    """
    change page(self, name) to page(self, get_torrent_status(torrent_id))
    """
    def deco(self, name):
        torrent_id = name.split(',')[0]
        torrent =get_torrent_status(torrent_id)
        return func (self, torrent) #torrent
    deco.__name__ = func.__name__
    return deco

def auto_refreshed(func):
    """"
    sets 'is_auto_refreshed' global for templates
    note : decorate AFTER deluge_page_*
    """
    def deco(self, name = None):
        render.set_global("is_auto_refreshed", True);
        return func(self, name) #auto_refreshed
    deco.__name__ = func.__name__
    return deco

def remote(func):
    "decorator for remote (string) api's"
    def deco(self, name = None):
        try:
            log.debug('%s.%s(%s)' ,self.__class__.__name__, func.__name__,name )
            print func(self, name) #remote
        except Exception, e:
            print 'error:%s' % e.message
            print '-'*20
            print  traceback.format_exc()
    deco.__name__ = func.__name__
    return deco
