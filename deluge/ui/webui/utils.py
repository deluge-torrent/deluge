# -*- coding: utf-8 -*-
#
# webserver_framework.py
#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
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


import os
import subprocess
import traceback
import random
from operator import attrgetter
import datetime
import pickle
from urlparse import urlparse
from md5 import md5

import web
from web import changequery , template , url , Storage
from web import cookies, setcookie as w_setcookie
from web import seeother as w_seeother

from deluge.common import fsize, fspeed, ftime
from deluge.ui.common import get_localhost_auth_uri
from deluge import component
from deluge.log import LOG as log
from deluge.configmanager import ConfigManager

from webserver_common import  TORRENT_KEYS, CONFIG_DEFAULTS
from deluge.ui.client import sclient, aclient

webui_plugin_manager = component.get("WebPluginManager")
config = ConfigManager("webui06.conf", CONFIG_DEFAULTS)

#async-proxy: map callback to a a dict-setter
def dict_cb(key,d):
    def callback(result):
        d[key] = result
    return callback

#methods:
def setcookie(key, val):
    """add 30 days expires header for persistent cookies"""
    return w_setcookie(key, val , expires=2592000)

#really simple sessions, to bad i had to implement them myself.
def start_session():
    session_id = str(random.random())
    config["sessions"] = config["sessions"] + [session_id]
    if len(config["sessions"]) > 30: #store a max of 20 sessions.
        config["sessions"] = config["sessions"][:-20]
    setcookie("session_id", session_id)
    config.save()

def end_session():
    session_id = getcookie("session_id")
    setcookie("session_id","")
    if session_id in config["sessions"]:
        config["sessions"].remove(session_id)
        config["sessions"] = config["sessions"]
#/sessions

def seeother(url, *args, **kwargs):
    url_with_base = config["base"] + url
    log.debug("seeother:%s" % url_with_base)
    return w_seeother(url_with_base, *args, **kwargs)

def self_url(**kwargs):
    return config["base"]  + changequery(**kwargs)

def do_redirect():
    """go to /index unless the redir var is set."""
    vars = web.input(redir=None)
    if vars.redir:
        w_seeother(vars.redir) #redir variable contains base
        return
    #default:
    seeother('/index')

def getcookie(key, default = None):
    "because i'm too lazy to type 3 lines for something this simple"
    key = str(key).strip()
    ck = cookies()
    return ck.get(key, default)

def enhance_torrent_status(torrent_id, status):
    """
    in: raw torrent_status
    out: enhanced torrent_staus
    """
    status = Storage(status)

    if status.tracker == 0:
        #0.6 does not raise a decent error on non-existing torrent.
        raise UnknownTorrentError(torrent_id)

    status.id = torrent_id

    #action for torrent_pause
    if status.state == "Paused":
        status.action = "start"
    else:
        status.action = "stop"

    return status

def get_torrent_status(torrent_id):
    """
    helper method.
    enhance sclient.get_torrent_status with some extra data
    """
    status = sclient.get_torrent_status(torrent_id,TORRENT_KEYS)
    return enhance_torrent_status(torrent_id, status)

def get_enhanced_torrent_list(torrents):
    """
    returns a list of storified-torrent-dicts.
    """
    return [enhance_torrent_status(id, status)
            for id, status in torrents.iteritems()]

def get_newforms_data(form_class):
    """
    glue for using web.py and newforms.
    returns a dict with name/value of the post-data.
    """
    import lib.newforms_plus as forms
    fields = form_class.base_fields.keys()
    form_data = {}
    vars = web.input()
    for field in fields:
        value = vars.get(field)

        if value != None or  isinstance(form_class.base_fields[field], forms.BooleanField):
            form_data[field]  = value
            #for multiple-select) :
            if isinstance(form_class.base_fields[field], forms.MultipleChoiceField):
                form_data[field] = web.input(**{field:[]})[field]

    return form_data

#/utils

#daemon:
def daemon_test_online_status(uri):
    """Tests the status of URI.. Returns True or False depending on status.
    """
    online = True
    host = None
    try:
        import urlparse
        u = urlparse.urlsplit(uri)
        if u.hostname == "localhost" or u.hostname == "127.0.0.1":
            host = xmlrpclib.ServerProxy(get_localhost_auth_uri(uri))
        else:
            host = xmlrpclib.ServerProxy(uri)
        host.ping()
    except socket.error:
        online = False

    del host
    self.online_status[uri] = online
    return online

def daemon_start_localhost(port):
    """Starts a localhost daemon"""
    port = str(port)
    log.info("Starting localhost:%s daemon..", port)
    # Spawn a local daemon
    subprocess.Popen(["deluged", "-p %s" % port])

def daemon_connect(uri):
    if config['daemon'] <> uri:
        config['daemon'] = uri
        config.save()

    import urlparse
    u = urlparse.urlsplit(uri)
    if u.hostname == "localhost" or u.hostname == "127.0.0.1":
        uri = get_localhost_auth_uri(uri)
    sclient.set_core_uri(uri)
    webui_plugin_manager.start()

#generic:
def logcall(func):
    "deco to log a function/method-call"
    def deco(*args, **kwargs):
        log.debug("call: %s<%s,%s>"  % (func.__name__, args, kwargs))
        return func(*args, **kwargs) #logdeco

    return deco

#c&p from ws:
def update_pwd(pwd):
    sm = md5()
    sm.update(str(random.getrandbits(5000)))
    salt = sm.digest()
    m = md5()
    m.update(salt)
    m.update(pwd)
    #
    config["pwd_salt"] = salt
    config["pwd_md5"] = m.digest()
    config.save()

def check_pwd(pwd):
    m = md5()
    m.update(config['pwd_salt'])
    m.update(pwd)
    return (m.digest() == config['pwd_md5'])

def validate_config(cfg_dict):
    """
    call this before setting webui-config!
    #security : if template contains "../.." or other vars the filesystem could get compromized.
    """
    if "template" in cfg_dict:
        from render import render
        #make shure it is a real template
        if not cfg_dict["template"] in render.get_templates():
            raise Exception("Invalid template")


def set_config_defaults():
    """
    OBSOLETE, TODO REMOVE THIS !!
    """
    changed = False
    for key, value in CONFIG_DEFAULTS.iteritems():
        if not key in config.config:
            config.config[key] = value
            changed = True

    from render import render
    if not config["template"] in render.get_templates():
        config["template"] = CONFIG_DEFAULTS["template"]
        changed = True

    if changed:
        config.save()

def apply_config():
    #etc, mostly for apache:
    from render import render
    try:
        daemon_connect(config['daemon'])
    except Exception,e:
        log.debug("error setting core uri:%s:%s:%s" % (config['daemon'], e, e.message))
    render.set_global('base', config['base'])
    render.apply_cfg()

#exceptions:
class WebUiError(Exception):
    """the message of these exceptions will be rendered in
    render.error(e.message) in debugerror.py"""
    pass

class UnknownTorrentError(WebUiError):
    pass

#mime-type guessing :
def guess_mime_type(path):
    import posixpath
    from mimetypes import types_map as extensions_map
    base, ext = posixpath.splitext(path)
    if ext in extensions_map:
        return extensions_map[ext]
    ext = ext.lower()
    if ext in extensions_map:
        return extensions_map[ext]
    else:
        return 'application/octet-stream'
