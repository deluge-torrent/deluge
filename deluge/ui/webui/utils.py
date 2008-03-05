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

import lib.webpy022 as web
import os
from lib.webpy022.webapi import cookies, setcookie as w_setcookie
from lib.webpy022 import changequery as self_url, template
from lib.webpy022.utils import Storage
from lib.webpy022.http import seeother, url

from deluge.common import fsize,fspeed,ftime

import traceback
import random
from operator import attrgetter
import datetime
import pickle
from urlparse import urlparse

from webserver_common import  REVNO, VERSION, TORRENT_KEYS, STATE_MESSAGES
from webserver_common import ws, proxy, async_proxy, log

debug_unicode = False

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
    log.debug('start session')
    session_id = str(random.random())
    ws.SESSIONS.append(session_id)
    setcookie("session_id", session_id)

def end_session():
    session_id = getcookie("session_id")
    setcookie("session_id","")

def do_redirect():
    """for redirects after a POST"""
    vars = web.input(redir = None)
    ck = cookies()
    url_vars = {}

    #redirect to a non-default page.
    if vars.redir:
        seeother(vars.redir)
        return

    #for the filters:
    if ("order" in ck and "sort" in ck):
        url_vars.update({'sort':ck['sort'] ,'order':ck['order'] })

    organize = False
    try:
        organize = ('Organize' in proxy.get_enabled_plugins())
    except:
        pass

    if organize:
        #todo:DRY
        if ("state" in ck) and ck['state']:
            url_vars['state'] = ck['state']
        if ("tracker" in ck) and ck['tracker']:
            url_vars['tracker'] = ck['tracker']
        if ("keyword" in ck) and ck['keyword']:
            url_vars['keyword'] = ck['keyword']

    #redirect.
    seeother(url("/index", **url_vars))

def getcookie(key, default = None):
    "because i'm too lazy to type 3 lines for something this simple"
    key = str(key).strip()
    ck = cookies()
    return ck.get(key, default)

def get_stats():
    stats = Storage()

    async_proxy.get_download_rate(dict_cb('download_rate',stats))
    async_proxy.get_upload_rate(dict_cb('upload_rate',stats))
    async_proxy.get_config_value(dict_cb('max_download',stats)
        ,"max_download_speed")
    async_proxy.get_config_value(dict_cb('max_upload',stats)
        ,"max_upload_speed")
    async_proxy.get_num_connections(dict_cb("num_connections",stats))
    async_proxy.get_config_value(dict_cb('max_num_connections',stats)
        ,"max_connections_global")
    async_proxy.get_dht_nodes(dict_cb('dht_nodes',stats))

    async_proxy.force_call(block=True)

    stats.download_rate = fspeed(stats.download_rate)
    stats.upload_rate = fspeed(stats.upload_rate)

    if stats.max_upload < 0:
        stats.max_upload = _("∞")
    else:
        stats.max_upload = "%s KiB/s" % stats.max_upload

    if stats.max_download < 0:
        stats.max_download = _("∞")
    else:
        stats.max_download = "%s KiB/s" % stats.max_download

    return stats

def enhance_torrent_status(torrent_id,status):
    """
    in: raw torrent_status
    out: enhanced torrent_staus
    """
    status = Storage(status)
    #add missing values for deluge 0.6:
    #todo : Remove this!, and clean up the rest
    for key in TORRENT_KEYS:
        if not key in status:
            status[key] = 0
            #log.warning('torrent_status:empty key in status:%s' % key)
        elif status[key] == None:
            status[key] = 0
            #log.warning('torrent_status:None key in status:%s' % key)

    if status.tracker == 0:
        #0.6 does not raise a decent error on non-existing torrent.
        raise UnknownTorrentError(torrent_id)

    status["id"] = torrent_id

    #0.5-->0.6
    status.download_rate = status.download_payload_rate
    status.upload_rate = status.upload_payload_rate

    #for naming the status-images
    status.calc_state_str = "downloading"
    if status.paused:
        status.calc_state_str= "inactive"
    elif status.state <> 2:
        status.calc_state_str = "seeding"

    #action for torrent_pause
    if status.paused: #no user-paused in 0.6 !!!
        status.action = "start"
    else:
        status.action = "stop"

    status.message =  _(status.state)

    #add some pre-calculated values
    status.update({
        "calc_total_downloaded"  : (fsize(status.total_done)
            + " (" + "??" + ")"
            ),
        "calc_total_uploaded": (fsize(
            #status.uploaded_memory +
            status.total_payload_upload) + " ("
            + "??" + ")"),
    })

    #no non-unicode string may enter the templates.
    #FIXED, was a translation bug..
    if debug_unicode:
        for k, v in status.iteritems():
            if (not isinstance(v, unicode)) and isinstance(v, str):
                try:
                    status[k] = unicode(v)
                except:
                    raise Exception('Non Unicode for key:%s' % (k, ))
    return status

def get_torrent_status(torrent_id):
    """
    helper method.
    enhance proxy.get_torrent_status with some extra data
    """
    status = proxy.get_torrent_status(torrent_id,TORRENT_KEYS)
    return enhance_torrent_status(torrent_id, status)

def get_enhanced_torrent_list(torrent_ids):
    """
    returns a list of storified-torrent-dicts.
    """
    torrent_dict = proxy.get_torrents_status(torrent_ids, TORRENT_KEYS)
    return [enhance_torrent_status(id, status)
            for id, status in torrent_dict.iteritems()]

def get_newforms_data(form_class):
    """
    glue for using web.py and newforms.
    returns a storified dict with name/value of the post-data.
    """
    import lib.newforms_plus as forms
    fields = form_class.base_fields.keys()
    form_data = {}
    vars = web.input()
    for field in fields:
        form_data[field] = vars.get(field)
        #log.debug("form-field:%s=%s" %  (field, form_data[field]))
        #DIRTY HACK: (for multiple-select)
        if isinstance(form_class.base_fields[field],
                forms.MultipleChoiceField):
            form_data[field] = web.input(**{field:[]})[field]
        #/DIRTY HACK
    return form_data

#/utils

#generic/ non-webui utils todo: move to trunk/core.
def daemon_test_online_status(uri):
    """Tests the status of URI.. Returns True or False depending on status.
    """
    online = True
    host = None
    try:
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
    os.popen("deluged -p %s" % port)

def logcall(func):
    "log a function/method-call"
    def deco(*args, **kwargs):
        log.debug("call: %s<%s,%s>"  % (func.__name__, args, kwargs))
        return func(*args, **kwargs) #logdeco

    return deco


#exceptions:
class WebUiError(Exception):
    """the message of these exceptions will be rendered in
    render.error(e.message) in debugerror.py"""
    pass

class UnknownTorrentError(WebUiError):
    pass
