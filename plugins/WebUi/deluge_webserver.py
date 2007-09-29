#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# deluge_webserver.py
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
Todo's before beta:
-alternating rows?
-__init__:unload plugin is broken!
-__init__:kill->restart is not waiting for kill to be finished.
-redir is broken.
--later/features:---
-set prio
-clear finished?
-torrent files.
"""
import webpy022 as web
from webpy022.webapi import cookies, setcookie
from webpy022.http import seeother, url
from webpy022.utils import Storage
from webpy022 import template

import dbus

import gettext, os, platform, locale, traceback
import random
import base64
from operator import attrgetter

from deluge import common
from deluge.common import INSTALL_PREFIX


#init:
APP = 'deluge'
DIR = os.path.join(INSTALL_PREFIX, 'share', 'locale')
if platform.system() != "Windows":
    locale.setlocale(locale.LC_MESSAGES, '')
    locale.bindtextdomain(APP, DIR)
    locale.textdomain(APP)
else:
    locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
gettext.install(APP, DIR)

random.seed()
bus = dbus.SessionBus()
proxy = bus.get_object("org.deluge_torrent.dbusplugin"
    , "/org/deluge_torrent/DelugeDbusPlugin")

web.webapi.internalerror = web.debugerror

#/init

#framework:
SESSIONS = {}

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

def deluge_page_noauth(func):
    """
    add http headers
    print result of func
    """
    def deco(self, name=None):
            web.header("Content-Type", "text/html; charset=utf-8")
            web.header("Cache-Control", "no-cache, must-revalidate")
            res = func(self, name)
            print unicode(res)
    return deco

def check_session(func):
    """
    a decorator
    return func if session is valid, else redirect to login page.
    """
    def deco(self, name):
        ck = cookies()
        if ck.has_key("session_id") and ck["session_id"] in SESSIONS:
            return func(self, name) #ok, continue..
        else:
            seeother("/login") #do not continue, and redirect to login page
    return deco

def deluge_page(func):
    return check_session(deluge_page_noauth(func))

def auto_refreshed(func):
    "decorator:adds a refresh header"
    def deco(self, name):
        if proxy.get_webui_config('auto_refresh'):
            web.header("Refresh", "%i ; url=%s" %
                (proxy.get_webui_config('auto_refresh_secs'),
                web.changequery()))
        return func(self, name)
    return deco

def error_page(error):
    web.header("Content-Type", "text/html; charset=utf-8")
    web.header("Cache-Control", "no-cache, must-revalidate")
    print render.error(error)

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

#/framework

#utils:
torrent_keys = ['distributed_copies', 'download_payload_rate',
    'download_rate', 'eta', 'is_seed', 'message', 'name', 'next_announce',
    'num_files', 'num_peers', 'num_pieces', 'num_seeds', 'paused',
    'piece_length','progress', 'ratio', 'total_done', 'total_download',
    'total_payload_download', 'total_payload_upload', 'total_peers',
    'total_seeds', 'total_size', 'total_upload', 'total_wanted',
    'tracker_status', 'upload_payload_rate', 'upload_rate',
    'uploaded_memory','tracker']

def get_torrent_status(torrent_id):
    """
    helper method.
    enhance proxy.get_torrent_status with some extra data
    """
    status = proxy.get_torrent_status(torrent_id,torrent_keys)
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

    #add some pre-calculated values
    status.update({
        "calc_total_downloaded"  : (common.fsize(status["total_done"])
            + " (" + common.fsize(status["total_download"]) + ")"),
        "calc_total_uploaded": (common.fsize(status['uploaded_memory']
            + status["total_payload_upload"]) + " ("
            + common.fsize(status["total_upload"]) + ")"),
    })

    return Storage(status) #Storage for easy templating.

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

    return render.sort_column_head(id, name, order, active_up, active_down)


render = template.render('templates/%s/' % proxy.get_webui_config('template'))

template.Template.globals.update({
    'sort_head': template_sort_head,
    'crop': template_crop,
    '_': _ , #gettext/translations
    'str': str, #because % in templetor is broken.
    'sorted': sorted,
    'get_config': proxy.get_webui_config,
    'self_url': web.changequery,
    'fspeed': common.fspeed,
    'fsize': common.fsize,
    'render': render, #for easy resuse of templates
    'button_style': (proxy.get_webui_config('button_style')),
    'rev': ('rev.' +
        open(os.path.join(os.path.dirname(__file__),'revno')).read()),
    'version': (
        open(os.path.join(os.path.dirname(__file__),'version')).read())
})
#/template-defs

#routing:
urls = (
    "/login(.*)", "login",
    "/index(.*)", "index",
    "/torrent/info/(.*)", "torrent_info",
    "/torrent/pause(.*)", "torrent_pause",
    "/torrent/add(.*)", "torrent_add",
    "/torrent/delete/(.*)", "torrent_delete",
    "/pause_all(.*)", "pause_all",
    "/resume_all(.*)", "resume_all",
    "/refresh/set(.*)", "refresh_set",
    "/refresh/(.*)", "refresh",
    "/home(.*)", "home",
    "/about(.*)", "about",
    #default-pages
    "/", "login",
    "", "login",
    #remote-api:
    "/remote/torrent/add(.*)", "remote_torrent_add"
)

#/routing

#pages:
class login:
    @deluge_page_noauth
    def GET(self, name):
        vars = web.input(error = None)
        return render.login(vars.error)

    def POST(self, name):
        vars = web.input(pwd = None)

        if proxy.check_pwd(vars.pwd):
            #start new session
            session_id = str(random.random())
            SESSIONS[session_id]  = {"not":"used"}
            setcookie("session_id", session_id)
            do_redirect()
        else:
            seeother('/login?error=1')

class home:
    @check_session
    def GET(self, name):
        do_redirect()

class index:
    "page containing the torrent list."
    @auto_refreshed
    @deluge_page
    def GET(self, name):
        vars = web.input(sort=None, order=None)

        status_rows = [get_torrent_status(torrent_id)
            for torrent_id in proxy.get_torrent_state()]

        #sorting:
        if vars.sort:
            status_rows.sort(key=attrgetter(vars.sort))
            if vars.order == 'up':
                status_rows = reversed(status_rows)

            setcookie("order", vars.order)
            setcookie("sort", vars.sort)

        return render.index(status_rows)

class torrent_info:
    "torrent details"
    @auto_refreshed
    @deluge_page
    def GET(self, torrent_id):
        return render.torrent_info(get_torrent_status(torrent_id))

class torrent_pause:
    "start/stop a torrent"
    @check_session
    def POST(self, name):
        vars = web.input(stop = None, start = None, redir = None)
        if vars.stop:
            proxy.pause_torrent(vars.stop)
        elif vars.start:
            proxy.resume_torrent(vars.start)

        do_redirect()

class torrent_add:
    @deluge_page
    def GET(self, name):
        return render.torrent_add()

    @check_session
    def POST(self, name):

        vars = web.input(url = None, torrent = {})

        if vars.url and vars.torrent.filename:
            error_page(_("Choose an url or a torrent, not both."))
        if vars.url:
            proxy.add_torrent_url(vars.url)
            do_redirect()
        elif vars.torrent.filename:
            data = vars.torrent.file.read()
            data_b64 = base64.b64encode(data)
            #b64 because of strange bug-reports related to binary data
            proxy.add_torrent_filecontent(vars.torrent.filename,data_b64)
            do_redirect()
        else:
            error_page(_("no data."))

class remote_torrent_add:
    """
    For use in remote scripts etc.
    POST user and file
    Example : curl -F torrent=@./test1.torrent -F pwd=deluge http://localhost:8112/remote/torrent/add"
    """
    @remote
    def POST(self, name):
        vars = web.input(pwd = None, torrent = {})

        if not proxy.check_pwd(vars.pwd):
            return 'error:wrong password'

        data_b64 = base64.b64encode(vars.torrent.file.read())
        proxy.add_torrent_filecontent(vars.torrent.filename,data_b64)
        return 'ok'

class torrent_delete:
    @deluge_page
    def GET(self, torrent_id):
        return render.torrent_delete(get_torrent_status(torrent_id))

    @check_session
    def POST(self, name):
        torrent_id = name
        vars = web.input(data_also = None, torrent_also = None)
        data_also = bool(vars.data_also)
        torrent_also = bool(vars.torrent_also)
        proxy.remove_torrent(torrent_id, data_also, torrent_also)
        do_redirect()

class pause_all:
    @check_session
    def POST(self, name):
        for torrent_id in proxy.get_torrent_state():
            proxy.pause_torrent(torrent_id)
        do_redirect()

class resume_all:
    @check_session
    def POST(self, name):
        for torrent_id in proxy.get_torrent_state():
            proxy.resume_torrent(torrent_id)
        do_redirect()

class refresh:
    @check_session
    def POST(self, name):
        auto_refresh = {'off':False, 'on':True}[name]
        proxy.set_webui_config('auto_refresh', auto_refresh)
        do_redirect()

class refresh_set:
    @deluge_page
    def GET(self, name):
        return render.refresh_form()

    @check_session
    def POST(self, name):
        vars = web.input(refresh = 0)
        refresh = int(vars.refresh)
        if refresh > 0:
            proxy.set_webui_config('refresh', refresh)
            proxy.set_webui_config('auto_refresh', True)
            do_redirect()
        else:
            error_page(_('refresh must be > 0'))

class about:
    @deluge_page_noauth
    def GET(self, name):
        return render.about()


#/pages

if __name__ == "__main__":
  web.run(urls, globals())


