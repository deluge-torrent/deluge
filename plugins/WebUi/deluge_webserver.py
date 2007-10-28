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

import webserver_common as ws
from webserver_framework import *

import webpy022 as web
from webpy022.http import seeother, url

import base64
from operator import attrgetter
import os

#routing:
urls = (
    "/login(.*)", "login",
    "/index(.*)", "index",
    "/torrent/info/(.*)", "torrent_info",
    "/torrent/pause(.*)", "torrent_pause",
    "/torrent/add(.*)", "torrent_add",
    "/torrent/delete/(.*)", "torrent_delete",
    "/torrent/queue/up/(.*)", "torrent_queue_up",
    "/torrent/queue/down/(.*)", "torrent_queue_down",
    "/pause_all(.*)", "pause_all",
    "/resume_all(.*)", "resume_all",
    "/refresh/set(.*)", "refresh_set",
    "/refresh/(.*)", "refresh",
    "/config(.*)","config",
    "/home(.*)", "home",
    "/about(.*)", "about",
    "/logout(.*)", "logout",
    #default-pages
    "/", "home",
    "", "home",
    #remote-api:
    "/remote/torrent/add(.*)", "remote_torrent_add",
    #static:
    "/static/(.*)","static",
    "/template/static/(.*)","template_static",
    #"/downloads/(.*)","downloads" disabled until it can handle large downloads.

)
#/routing

#pages:
class login:
    @deluge_page_noauth
    def GET(self, name):
        vars = web.input(error = None)
        return ws.render.login(vars.error)

    def POST(self, name):
        vars = web.input(pwd = None ,redir = None)

        if check_pwd(vars.pwd):
            #start new session
            start_session()
            do_redirect()
        elif vars.redir:
            seeother(url('/login',error=1, redir=vars.redir))
        else:
            seeother('/login?error=1')

class index:
    "page containing the torrent list."
    @auto_refreshed
    @deluge_page
    def GET(self, name):
        vars = web.input(sort=None, order=None)

        status_rows = [get_torrent_status(torrent_id)
            for torrent_id in ws.proxy.get_session_state()]

        #sorting:
        if vars.sort:
            status_rows.sort(key=attrgetter(vars.sort))
            if vars.order == 'up':
                status_rows = reversed(status_rows)

            setcookie("order", vars.order)
            setcookie("sort", vars.sort)

        return ws.render.index(status_rows)

class torrent_info:
    @auto_refreshed
    @deluge_page
    def GET(self, torrent_id):
        return ws.render.torrent_info(get_torrent_status(torrent_id))

class torrent_pause:
    @check_session
    def POST(self, name):
        vars = web.input(stop = None, start = None, redir = None)
        if vars.stop:
            ws.proxy.pause_torrent([vars.stop])
        elif vars.start:
            ws.proxy.resume_torrent([vars.start])

        do_redirect()

class torrent_add:
    @deluge_page
    def GET(self, name):
        return ws.render.torrent_add()

    @check_session
    def POST(self, name):
        vars = web.input(url = None, torrent = {})

        if vars.url and vars.torrent.filename:
            error_page(_("Choose an url or a torrent, not both."))
        if vars.url:
            ws.proxy.add_torrent_url(vars.url )
            do_redirect()
        elif vars.torrent.filename:
            data = vars.torrent.file.read()
            data_b64 = base64.b64encode(data)
            #b64 because of strange bug-reports related to binary data
            ws.proxy.add_torrent_filecontent(vars.torrent.filename,data_b64)
            do_redirect()
        else:
            error_page(_("no data."))

class remote_torrent_add:
    """
    For use in remote scripts etc.
    POST pwd and torrent
    """
    @remote
    def POST(self, name):
        vars = web.input(pwd = None, torrent = {})

        if not check_pwd(vars.pwd):
            return 'error:wrong password'

        data_b64 = base64.b64encode(vars.torrent.file.read())
        ws.proxy.add_torrent_filecontent(vars.torrent.filename,data_b64)
        return 'ok'

class torrent_delete:
    @deluge_page
    def GET(self, torrent_id):
        return ws.render.torrent_delete(get_torrent_status(torrent_id))

    @check_session
    def POST(self, torrent_id):
        vars = web.input(data_also = None, torrent_also = None)
        data_also = bool(vars.data_also)
        torrent_also = bool(vars.torrent_also)
        ws.proxy.remove_torrent(torrent_id, data_also, torrent_also)
        do_redirect()


class torrent_queue_up:
    @check_session
    def POST(self, torrent_id):
        ws.proxy.queue_up(torrent_id)
        do_redirect()

class torrent_queue_down:
    @check_session
    def POST(self, torrent_id):
        ws.proxy.queue_down(torrent_id)
        do_redirect()

class pause_all:
    @check_session
    def POST(self, name):
        ws.proxy.pause_torrent(ws.proxy.get_session_state())
        do_redirect()

class resume_all:
    @check_session
    def POST(self, name):
        ws.proxy.resume_torrent(ws.proxy.get_session_state())
        do_redirect()

class refresh:
    @check_session
    def POST(self, name):
        auto_refresh = {'off':'0', 'on':'1'}[name]
        setcookie('auto_refresh',auto_refresh)
        do_redirect()

class refresh_set:
    @deluge_page
    def GET(self, name):
        return ws.render.refresh_form()

    @check_session
    def POST(self, name):
        vars = web.input(refresh = 0)
        refresh = int(vars.refresh)
        if refresh > 0:
            setcookie('auto_refresh','1')
            setcookie('auto_refresh_secs', str(refresh))
            do_redirect()
        else:
            error_page(_('refresh must be > 0'))

class config:
    """core config
    TODO:good validation.
    """
    cfg_form = web.form.Form(
        web.form.Dropdown('max_download', ws.SPEED_VALUES,
            description=_('Download Speed Limit'),
            post='%s Kib/sec' % ws.proxy.get_config_value('max_download_speed')
        )
        ,web.form.Dropdown('max_upload', ws.SPEED_VALUES,
            description=_('Upload Speed Limit'),
            post='%s Kib/sec' %  ws.proxy.get_config_value('max_upload_speed')
        )
    )

    @deluge_page
    def GET(self, name):
        return ws.render.config(self.cfg_form())

    def POST(self, name):
        vars = web.input(max_download=None, max_upload=None)

        #self.config.set("max_download_speed", float(str_bwdown))
        raise NotImplementedError('todo')

class home:
    @check_session
    def GET(self, name):
        do_redirect()

class about:
    @deluge_page_noauth
    def GET(self, name):
        return ws.render.about()

class logout:
    def POST(self, name):
        end_session()
        seeother('/login')

class static(static_handler):
    base_dir = os.path.join(os.path.dirname(__file__),'static')

class template_static(static_handler):
    def get_base_dir(self):
        return os.path.join(os.path.dirname(__file__),
                'templates/%s/static' % ws.config.get('template'))

class downloads(static_handler):
    def GET(self, name):
        self.base_dir = ws.proxy.get_config_value('default_download_path')
        if not ws.config.get('share_downloads'):
            raise Exception('Access to downloads is forbidden.')
        return static_handler.GET(self, name)
#/pages

def WebServer():
    return create_webserver(urls, globals())

def run():
    server = WebServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    run()
