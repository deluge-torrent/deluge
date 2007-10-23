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

import traceback
import random
from operator import attrgetter

from deluge import common
from webserver_common import  REVNO, VERSION
import webserver_common as ws

from debugerror import deluge_debugerror

#init:
web.webapi.internalerror = deluge_debugerror
#/init

#methods:
def setcookie(key, val):
    """add 30 days expires header for persistent cookies"""
    return w_setcookie(key, val , expires=2592000)

SESSIONS = [] #dumb sessions.
def start_session():
    session_id = str(random.random())
    SESSIONS.append(session_id)
    setcookie("session_id", session_id)

    if getcookie('auto_refresh_secs') == None:
        setcookie('auto_refresh_secs','10')

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
    COOKIE_DEFAULTS = {'auto_refresh_secs':'10'}
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
        if ck.has_key("session_id") and ck["session_id"] in SESSIONS:
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


def get_config(var):
    return ws.config.get(var)

template.Template.globals.update({
    'sort_head': template_sort_head,
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



#------------------------------------------------------------------------------
#Some copy and paste from web.py
#mostly caused by /static
#TODO : FIX THIS.
#static-files serving should be moved to the normal webserver!
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler
from gtk_cherrypy_wsgiserver import CherryPyWSGIServer
from BaseHTTPServer import BaseHTTPRequestHandler

from webpy022.request import webpyfunc
from webpy022 import webapi
import os

import posixpath
import urllib
import urlparse

class RelativeHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = urlparse.urlparse(path)[2]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.path.dirname(__file__)
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

class StaticApp(RelativeHandler):
    """WSGI application for serving static files."""
    def __init__(self, environ, start_response):
        self.headers = []
        self.environ = environ
        self.start_response = start_response

    def send_response(self, status, msg=""):
        self.status = str(status) + " " + msg

    def send_header(self, name, value):
        self.headers.append((name, value))

    def end_headers(self):
        pass

    def log_message(*a): pass

    def __iter__(self):
        environ = self.environ

        self.path = environ.get('PATH_INFO', '')
        self.client_address = environ.get('REMOTE_ADDR','-'), \
                              environ.get('REMOTE_PORT','-')
        self.command = environ.get('REQUEST_METHOD', '-')

        from cStringIO import StringIO
        self.wfile = StringIO() # for capturing error

        f = self.send_head()
        self.start_response(self.status, self.headers)

        if f:
            block_size = 16 * 1024
            while True:
                buf = f.read(block_size)
                if not buf:
                    break
                yield buf
            f.close()
        else:
            value = self.wfile.getvalue()
            yield value

class WSGIWrapper(BaseHTTPRequestHandler):
    """WSGI wrapper for logging the status and serving static files."""
    def __init__(self, app):
        self.app = app
        self.format = '%s - - [%s] "%s %s %s" - %s'

    def __call__(self, environ, start_response):
        def xstart_response(status, response_headers, *args):
            write = start_response(status, response_headers, *args)
            self.log(status, environ)
            return write

        path = environ.get('PATH_INFO', '')
        if path.startswith('/static/'):
            return StaticApp(environ, xstart_response)
        else:
            return self.app(environ, xstart_response)

    def log(self, status, environ):
        #mvoncken,no logging..
        return

        outfile = environ.get('wsgi.errors', web.debug)
        req = environ.get('PATH_INFO', '_')
        protocol = environ.get('ACTUAL_SERVER_PROTOCOL', '-')
        method = environ.get('REQUEST_METHOD', '-')
        host = "%s:%s" % (environ.get('REMOTE_ADDR','-'),
                          environ.get('REMOTE_PORT','-'))

        #@@ It is really bad to extend from
        #@@ BaseHTTPRequestHandler just for this method
        time = self.log_date_time_string()

        print >> outfile, self.format % (host, time, protocol,
                                         method, req, status)

def create_webserver(urls,methods):
    func = webapi.wsgifunc(webpyfunc(urls,methods, False))
    server_address=("0.0.0.0",ws.config.get('port'))

    func = WSGIWrapper(func)
    server = CherryPyWSGIServer(server_address, func, server_name="localhost")


    print "(created) http://%s:%d/" % server_address

    return server

#------
__all__ = ['deluge_page_noauth', 'deluge_page', 'remote',
    'auto_refreshed', 'check_session',
    'do_redirect', 'error_page','start_session','getcookie'
    ,'create_webserver','setcookie']



