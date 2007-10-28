#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# webserver_framework.py
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

"""
Todo's before stable:
-__init__:kill->restart is not waiting for kill to be finished.
--later/features:---
-alternating rows?
-set prio
-clear finished?
-torrent files.
"""
import webpy022 as web

from webpy022.webapi import cookies, setcookie as w_setcookie
from webpy022.http import seeother, url
from webpy022 import template,changequery as self_url
from webpy022.utils import Storage
from static_handler import static_handler

from deluge.common import fsize,fspeed

import traceback
import random
from operator import attrgetter
import datetime
import pickle
from md5 import md5

from deluge import common
from webserver_common import  REVNO, VERSION, COOKIE_DEFAULTS
import webserver_common as ws
from debugerror import deluge_debugerror

#init:
web.webapi.internalerror = deluge_debugerror
#/init

#methods:
def setcookie(key, val):
    """add 30 days expires header for persistent cookies"""
    return w_setcookie(key, val , expires=2592000)

#really simple sessions, to bad i had to implement them myself.
def start_session():
    session_id = str(random.random())
    ws.SESSIONS.append(session_id)
    if len(ws.SESSIONS) > 20:  #save max 20 sessions?
        ws.SESSIONS = ws.SESSIONS[-20:]
    #not thread safe! , but a verry rare bug.
    pickle.dump(ws.SESSIONS, open(ws.session_file,'wb'))
    setcookie("session_id", session_id)

def end_session():
    session_id = getcookie("session_id")
    if session_id in ws.SESSIONS:
        ws.SESSIONS.remove(session_id)
        #not thread safe! , but a verry rare bug.
        pickle.dump(ws.SESSIONS, open(ws.session_file,'wb'))

def do_redirect():
    """for redirects after a POST"""
    vars = web.input(redir = None)
    ck = cookies()

    if vars.redir:
        seeother(vars.redir)
    elif ("order" in ck and "sort" in ck):
        seeother(url("/index", sort=ck['sort'], order=ck['order']))
    else:
        seeother(url("/index"))

def error_page(error):
    web.header("Content-Type", "text/html; charset=utf-8")
    web.header("Cache-Control", "no-cache, must-revalidate")
    print ws.render.error(error)

def getcookie(key, default=None):
    key = str(key).strip()
    ck = cookies()
    val = ck.get(key, default)
    if (not val) and key in COOKIE_DEFAULTS:
        return COOKIE_DEFAULTS[key]
    return val

#deco's:
def deluge_page_noauth(func):
    """
    add http headers
    print result of func
    """
    def deco(self, name=None):
            web.header("Content-Type", "text/html; charset=utf-8")
            web.header("Cache-Control", "no-cache, must-revalidate")
            res = func(self, name)
            print res
    return deco

def check_session(func):
    """
    a decorator
    return func if session is valid, else redirect to login page.
    """
    def deco(self, name):
        vars = web.input(redir_after_login=None)
        ck = cookies()
        if ck.has_key("session_id") and ck["session_id"] in ws.SESSIONS:
            return func(self, name) #ok, continue..
        elif vars.redir_after_login:
            seeother(url("/login",redir=self_url()))
        else:
            seeother("/login") #do not continue, and redirect to login page
    return deco

def deluge_page(func):
    return check_session(deluge_page_noauth(func))

#combi-deco's:
def auto_refreshed(func):
    "decorator:adds a refresh header"
    def deco(self, name):
        if getcookie('auto_refresh') == '1':
            web.header("Refresh", "%i ; url=%s" %
                (int(getcookie('auto_refresh_secs',10)),self_url()))
        return func(self, name)
    return deco

def remote(func):
    "decorator for remote api's"
    def deco(self, name):
        try:
            print func(self, name)
        except Exception, e:
            print 'error:' + e.message
            print '-'*20
            print  traceback.format_exc()
    return deco

#utils:
def check_pwd(pwd):
    m = md5()
    m.update(ws.config.get('pwd_salt'))
    m.update(pwd)
    return (m.digest() == ws.config.get('pwd_md5'))

def get_stats():
    stats = Storage({
    'download_rate':fspeed(ws.proxy.get_download_rate()),
    'upload_rate':fspeed(ws.proxy.get_upload_rate()),
    'max_download':ws.proxy.get_config_value('max_download_speed_bps'),
    'max_upload':ws.proxy.get_config_value('max_upload_speed_bps'),
    })
    if stats.max_upload < 0:
        stats.max_upload = _("Unlimited")
    else:
        stats.max_upload = fspeed(stats.max_upload)

    if stats.max_download < 0:
        stats.max_download = _("Unlimited")
    else:
        stats.max_download = fspeed(stats.max_download)

    return stats


def get_torrent_status(torrent_id):
    """
    helper method.
    enhance ws.proxy.get_torrent_status with some extra data
    """
    status = Storage(ws.proxy.get_torrent_status(torrent_id,ws.TORRENT_KEYS))

    #add missing values for deluge 0.6:
    for key in ws.TORRENT_KEYS:
        if not key in status:
            status[key] = 0

    status["id"] = torrent_id

    #for naming the status-images
    status["calc_state_str"] = "downloading"
    if status["paused"]:
        status["calc_state_str"] = "inactive"
    elif status["is_seed"]:
        status["calc_state_str"] = "seeding"

    #action for torrent_pause
    if status["calc_state_str"] == "inactive":
        status["action"] = "start"
    else:
        status["action"] = "stop"

    if status["paused"]:
        status["message"] = _("Paused %s%%") % status['progress']
    else:
        status["message"] = "%s %i%%" % (ws.STATE_MESSAGES[status["state"]]
        , status['progress'])

    #add some pre-calculated values
    status.update({
        "calc_total_downloaded"  : (fsize(status["total_done"])
            + " (" + fsize(status["total_download"]) + ")"),
        "calc_total_uploaded": (fsize(status['uploaded_memory']
            + status["total_payload_upload"]) + " ("
            + fsize(status["total_upload"]) + ")"),
    })
    return status
#/utils

#template-defs:
def template_crop(text, end):
    if len(text) > end:
        return text[0:end - 3] + '...'
    return text

def template_sort_head(id,name):
    #got tired of doing these complex things inside templetor..
    vars = web.input(sort=None, order=None)
    active_up = False
    active_down = False
    order = 'down'

    if vars.sort == id:
        if vars.order == 'down':
            order = 'up'
            active_down = True
        else:
            active_up = True

    return ws.render.sort_column_head(id, name, order, active_up, active_down)

def template_part_stats():
    return ws.render.part_stats(get_stats())

def get_config(var):
    return ws.config.get(var)

template.Template.globals.update({
    'sort_head': template_sort_head,
    'part_stats':template_part_stats,
    'crop': template_crop,
    '_': _ , #gettext/translations
    'str': str, #because % in templetor is broken.
    'sorted': sorted,
    'get_config': get_config,
    'self_url': self_url,
    'fspeed': common.fspeed,
    'fsize': common.fsize,
    'render': ws.render, #for easy resuse of templates
    'rev': 'rev.%s'  % (REVNO, ),
    'version': VERSION,
    'getcookie':getcookie,
    'get': lambda (var): getattr(web.input(**{var:None}),var) # unreadable :-(
})
#/template-defs

def create_webserver(urls, methods):
    from webpy022.request import webpyfunc
    from webpy022 import webapi
    from gtk_cherrypy_wsgiserver import CherryPyWSGIServer

    func = webapi.wsgifunc(webpyfunc(urls, methods, False))
    server_address=("0.0.0.0", int(ws.config.get('port')))
    server = CherryPyWSGIServer(server_address, func, server_name="localhost")
    print "http://%s:%d/" % server_address
    return server

#------
__all__ = ['deluge_page_noauth', 'deluge_page', 'remote',
    'auto_refreshed', 'check_session',
    'do_redirect', 'error_page','start_session','getcookie'
    ,'setcookie','create_webserver','end_session',
    'get_torrent_status', 'check_pwd','static_handler']
