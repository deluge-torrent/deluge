#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
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


#todo: remove useless imports.

from utils import *
import utils #todo remove the line above.
from render import render, error_page
import time
import page_decorators as deco
from config_forms import config_page
from torrent_options import torrent_options
from torrent_move import torrent_move

from deluge.common import get_pixmap
from deluge.log import LOG as log

import web
from web import seeother, url
from lib.static_handler import static_handler
from torrent_add import torrent_add

from operator import attrgetter
import os
from deluge import component
from deluge.ui.client import sclient as proxy

page_manager = component.get("PageManager")

#from json_api import json_api #secuity leak, todo:fix

#routing:
urls = [
    "/login", "login",
    "/index", "index",
    "/torrent/info/(.*)", "torrent_info",
    "/torrent/info_inner/(.*)", "torrent_info_inner",
    "/torrent/stop/(.*)", "torrent_stop",
    "/torrent/start/(.*)", "torrent_start",
    "/torrent/reannounce/(.*)", "torrent_reannounce",
    "/torrent/recheck/(.*)", "torrent_recheck",
    "/torrent/add(.*)", "torrent_add",
    "/torrent/delete/(.*)", "torrent_delete",
    "/torrent/move/(.*)", "torrent_move",
    "/torrent/queue/up/(.*)", "torrent_queue_up",
    "/torrent/queue/down/(.*)", "torrent_queue_down",
    "/torrent/files/(.*)","torrent_files",
    "/torrent/options/(.*)","torrent_options",
    "/pause_all", "pause_all",
    "/resume_all", "resume_all",
    "/refresh/set", "refresh_set",
    "/refresh/(.*)", "refresh",
    "/config/(.*)", "config_page",
    "/home", "home",
    "/about", "about",
    "/logout", "logout",
    "/connect","connect",
    "/daemon/control/(.*)","daemon_control",
    #remote-api:
    "/remote/torrent/add(.*)", "remote_torrent_add",
    #"/json/(.*)","json_api",
    #static:
    "/static/(.*)", "static",
    "/template/static/(.*)", "template_static",
    #"/downloads/(.*)","downloads" disabled until it can handle large downloads
    #default-pages
    "/", "home",
    "", "home",
    "/robots.txt","robots",
    "/template_style.css","template_style",
    "/pixmaps/(.*)","pixmaps"
]
#/routing

#pages:
class login:
    @deco.deluge_page_noauth
    def GET(self, name):
        vars = web.input(error = None)
        return render.login(vars.error)

    def POST(self):
        vars = web.input(pwd = None, redir = None)

        if utils.check_pwd(vars.pwd):
            #start new session
            start_session()
            do_redirect()
        elif vars.redir:
            seeother(url('/login', error=1, redir=vars.redir))
        else:
            seeother('/login?error=1')

class index:
    "page containing the torrent list."
    @deco.deluge_page
    @deco.auto_refreshed
    def GET(self, name):
        vars = web.input(sort=None, order=None)

        organize_filters = {}
        if 'Organize' in proxy.get_enabled_plugins():
            filter_dict = {}

            #organize-filters
            for filter_name in ["state","tracker","keyword"]:
                value = getattr(web.input(**{filter_name:None}), filter_name)
                if value and value <> "All":
                    filter_dict[filter_name] = value
                    setcookie(filter_name, vars.state)
                else:
                    setcookie(filter_name, "")

            log.debug(filter_dict)
            torrent_ids =  proxy.organize_get_session_state(filter_dict)
            organize_filters = Storage(proxy.organize_all_filter_items())

        else:
            torrent_ids =  proxy.get_session_state()

        torrent_list = utils.get_enhanced_torrent_list(torrent_ids)

        #sorting:
        if vars.sort:
            try:
                torrent_list.sort(key=attrgetter(vars.sort))
            except:
                log.error('Sorting Failed')

            if vars.order == 'up':
                torrent_list = list(reversed(torrent_list))

            setcookie("order", vars.order)
            setcookie("sort", vars.sort)
        return render.index(torrent_list, organize_filters)


class torrent_info:
    @deco.deluge_page
    @deco.auto_refreshed
    @deco.torrent
    def GET(self, torrent):
        return render.torrent_info(torrent)

class torrent_info_inner:
    @deco.deluge_page
    @deco.torrent
    def GET(self, torrent):
        vars = web.input(tab = None)
        if vars.tab:
            active_tab = vars.tab
        else:
            active_tab =  getcookie("torrent_info_tab") or "details"
        setcookie("torrent_info_tab", active_tab)
        return render.torrent_info_inner(torrent, active_tab)

#next 6 classes: a pattern is emerging here.
#todo: DRY (in less lines of code)
#deco.deluge_command, or a subclass?
"""
def torrents_command(command):
    class torrents_command_inner:
        @deco.check_session
        @deco.torrent_ids
        def POST(self, torrent_ids):
            proxy.getattr(command).(torrent_ids)
            do_redirect()

torrent_start = torrents_command("resume_torrent")
torrent_stop = torrents_command("pause_torrent")
torrent_reannounce = torrents_command("force_reannounce")
torrent_recheck = torrents_command("force_recheck")
torrent_queue_down = torrents_command("queue_down")
torrent_queue_up = torrents_command("queue_up")
"""
class torrent_start:
    @deco.check_session
    @deco.torrent_ids
    def POST(self, torrent_ids):
        proxy.resume_torrent(torrent_ids)
        do_redirect()

class torrent_stop:
    @deco.check_session
    @deco.torrent_ids
    def POST(self, torrent_ids):
        proxy.pause_torrent(torrent_ids)
        do_redirect()

class torrent_reannounce:
    @deco.check_session
    @deco.torrent_ids
    def POST(self, torrent_ids):
        proxy.force_reannounce(torrent_ids)
        do_redirect()

class torrent_recheck:
    @deco.check_session
    @deco.torrent_ids
    def POST(self, torrent_ids):
        proxy.force_recheck(torrent_ids)
        do_redirect()

class torrent_queue_up:
    @deco.check_session
    @deco.torrent_ids
    def POST(self, torrent_ids):
        proxy.queue_up(torrent_ids)
        do_redirect()

class torrent_queue_down:
    @deco.check_session
    @deco.torrent_ids
    def POST(self, torrent_ids):
        proxy.queue_down(torrent_ids)
        do_redirect()

class torrent_delete:
    @deco.deluge_page
    @deco.torrent_list
    def GET(self, torrent_list):
            torrent_str = ",".join([t.id for t in torrent_list])
            #todo: remove the ",".join!
            return render.torrent_delete(torrent_str, torrent_list)

    @deco.check_session
    @deco.torrent_ids
    def POST(self, torrent_ids):
        vars = web.input(data_also = None, torrent_also = None)
        data_also = bool(vars.data_also)
        torrent_also = bool(vars.torrent_also)
        proxy.remove_torrent(torrent_ids, torrent_also, data_also)
        do_redirect()

class torrent_files:
    @deco.check_session
    def POST(self, torrent_id):
        torrent = get_torrent_status(torrent_id)
        file_priorities = web.input(file_priorities=[]).file_priorities
        #file_priorities contains something like ['0','2','3','4']
        #transform to: [1,0,0,1,1,1]
        proxy_prio = [0 for x in xrange(len(torrent.file_priorities))]
        for pos in file_priorities:
            proxy_prio[int(pos)] = 1

        proxy.set_torrent_file_priorities(torrent_id, proxy_prio)
        do_redirect()

class pause_all:
    @deco.check_session
    def POST(self, name):
        proxy.pause_torrent(proxy.get_session_state())
        do_redirect()

class resume_all:
    @deco.check_session
    def POST(self, name):
        proxy.resume_torrent(proxy.get_session_state())
        do_redirect()

class refresh:
    def GET(self, name):
        return self.POST(name)
        #WRONG, but makes it easyer to link with <a href> in the status-bar

    @deco.check_session
    def POST(self, name):
        auto_refresh = {'off': '0', 'on': '1'}[name]
        setcookie('auto_refresh', auto_refresh)
        if not getcookie('auto_refresh_secs'):
            setcookie('auto_refresh_secs', 10)
        do_redirect()

class refresh_set:
    @deco.deluge_page
    def GET(self, name):
        return render.refresh_form()

    @deco.check_session
    def POST(self, name):
        vars = web.input(refresh = 0)
        refresh = int(vars.refresh)
        if refresh > 0:
            setcookie('auto_refresh', '1')
            setcookie('auto_refresh_secs', str(refresh))
            do_redirect()
        else:
            error_page(_('refresh must be > 0'))

class home:
    @deco.check_session
    def GET(self, name):
        do_redirect()

class about:
    @deco.deluge_page_noauth
    def GET(self, name):
        return render.about()

class logout:
    def GET(self):
        return self.POST()
        #WRONG, but makes it easyer to link with <a href> in the status-bar
    @deco.check_session
    def POST(self, name):
        end_session()
        seeother('/login')

class connect:
    @deco.check_session
    @deco.deluge_page_noauth
    def GET(self, name):
        try:
            proxy.ping()
            connected = proxy.get_core_uri()
        except:
            connected = None

        connect_list = ["http://localhost:58846"]
        return render.connect(connect_list, connected)

    def POST(self):
        vars = web.input(uri = None, other_uri = None)
        uri = ''
        if vars.uri == 'other_uri':
            if not vars.other:
                return error_page(_("no uri"))
            uri = vars.other
        else:
            uri = vars.uri
        #TODO: more error-handling
        utils.daemon_connect(uri)
        do_redirect()

class daemon_control:
    @deco.check_session
    def POST(self, command):
        if command == 'stop':
            proxy.shutdown()
        elif command == 'start':
            self.start()
            return do_redirect()
        elif command == 'restart':
            proxy.shutdown()
            self.start()
            return do_redirect()
        else:
            raise Exception('Unknown command:"%s"' % command)

        seeother('/connect')

    def start(self):
        uri = web.input(uri = None).uri
        if not uri:
            uri = 'http://localhost:58846'

        port = int(uri.split(':')[2])
        utils.daemon_start_localhost(port)
        time.sleep(1)  #pause a while to let it start?

        utils.daemon_connect( uri )


#other stuff:
class remote_torrent_add:
    """
    For use in remote scripts etc.
    curl ->POST pwd and torrent as file
    greasemonkey: POST pwd torrent_name and data_b64
    """
    @deco.remote
    def POST(self, name):
        vars = web.input(pwd = None, torrent = {},
            data_b64 = None , torrent_name= None)

        if not utils.check_pwd(vars.pwd):
            return 'error:wrong password'

        if vars.data_b64: #b64 post (greasemonkey)
            data_b64 = unicode(vars.data_b64)
            torrent_name = vars.torrent_name
        else:  #file-post (curl)
            data_b64 = base64.b64encode(vars.torrent.file.read())
            torrent_name = vars.torrent.filename
        proxy.add_torrent_filecontent(torrent_name, data_b64)
        return 'ok'

class static(static_handler):
    base_dir = os.path.join(os.path.dirname(__file__), 'static')

class template_static(static_handler):
    def get_base_dir(self):
        return os.path.join(os.path.dirname(__file__),
                'templates/%s/static' % ws.config.get('template'))

class downloads(static_handler):
    def GET(self, name):
        self.base_dir = proxy.get_config_value('default_download_path')
        if not ws.config.get('share_downloads'):
            raise Exception('Access to downloads is forbidden.')
        return static_handler.GET(self, name)

class robots:
    def GET(self):
        "no robots/prevent searchengines from indexing"
        web.header("Content-Type", "text/plain")
        print "User-agent: *\nDisallow:/\n"

class template_style:
    def GET(self):
        web.header("Content-Type", "text/css")
        style = Storage()
        print render.template_style(style)

class pixmaps:
    "use the deluge-images. located in data/pixmaps"
    def GET(self, name):
        if not name.endswith('.png'):
            if name == 'paused':
                name = 'inactive'
            if name == 'error':
                name = 'alert'
            name =  name + '16.png'

        if not os.path.exists(get_pixmap(name)):
            name = 'dht16.png'

        f = open(get_pixmap(name) ,'rb')
        fs = os.fstat(f.fileno())
        content = f.read()
        f.close()
        web.header("Content-Type", "image/png")
        web.header("Content-Length", str(fs[6]))
        web.header("Cache-Control" , "public, must-revalidate, max-age=86400")
        print content


#/pages

page_manager.register_pages(urls,globals())
