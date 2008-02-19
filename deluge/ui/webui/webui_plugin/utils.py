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
    #if len(ws.SESSIONS) > 20:  #save max 20 sessions?
    #    ws.SESSIONS = ws.SESSIONS[-20:]
    #not thread safe! , but a verry rare bug.
    #f = open(ws.session_file,'wb')
    #pickle.dump(ws.SESSIONS, f)
    #f.close()
    setcookie("session_id", session_id)

def end_session():
    session_id = getcookie("session_id")
    #if session_id in ws.SESSIONS:
    #    ws.SESSIONS.remove(session_id)
        #not thread safe! , but a verry rare bug.
        #f = open(ws.session_file,'wb')
        #pickle.dump(ws.SESSIONS, f)
        #f.close()
    setcookie("session_id","")

def do_redirect():
    """for redirects after a POST"""
    vars = web.input(redir = None)
    ck = cookies()
    url_vars = {}

    if vars.redir:
        seeother(vars.redir)
        return
    #todo:cleanup
    if ("order" in ck and "sort" in ck):
        url_vars.update({'sort':ck['sort'] ,'order':ck['order'] })
    if ("filter" in ck) and ck['filter']:
        url_vars['filter'] = ck['filter']
    if ("category" in ck) and ck['category']:
        url_vars['category'] = ck['category']

    seeother(url("/index", **url_vars))

def getcookie(key, default = None):
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

    #log.debug(str(stats))

    stats.download_rate = fspeed(stats.download_rate)
    stats.upload_rate = fspeed(stats.upload_rate)
    #stats.max_upload = stats.max_upload
    #stats.max_download = stats.max_download


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

    url = urlparse(status.tracker)
    if hasattr(url,'hostname'):
        status.category = url.hostname or 'unknown'
    else:
        status.category = 'No-tracker'

    #0.5-->0.6
    status.download_rate = status.download_payload_rate
    status.upload_rate = status.upload_payload_rate

    #for naming the status-images
    status.calc_state_str = "downloading"
    if status.paused:
        status.calc_state_str= "inactive"
    elif status.is_seed:
        status.calc_state_str = "seeding"

    #action for torrent_pause
    if status.paused: #no user-paused in 0.6 !!!
        status.action = "start"
    else:
        status.action = "stop"

    if status.user_paused:
        status.message = _("Paused")
    elif status.paused:
        status.message = _("Queued")
    else:
        status.message = (STATE_MESSAGES[status.state])

    #add some pre-calculated values
    status.update({
        "calc_total_downloaded"  : (fsize(status.total_done)
            + " (" + fsize(status.total_download) + ")"),
        "calc_total_uploaded": (fsize(status.uploaded_memory
            + status.total_payload_upload) + " ("
            + fsize(status.total_upload) + ")"),
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



def get_torrent_list():
    """
    uses async.
    """
    torrent_ids  = proxy.get_session_state() #Syc-api.
    torrent_dict = {}
    for id in torrent_ids:
        async_proxy.get_torrent_status(dict_cb(id,torrent_dict), id,
            TORRENT_KEYS)
    async_proxy.force_call(block=True)
    return [enhance_torrent_status(id, status)
            for id, status in torrent_dict.iteritems()]

def get_categories(torrent_list):
    trackers = [(torrent['category'] or 'unknown') for torrent in torrent_list]
    categories = {}
    for tracker in trackers:
        categories[tracker] = categories.get(tracker,0) + 1
    return categories

def filter_torrent_state(torrent_list,filter_name):
    filters = {
        'downloading': lambda t: (not t.paused and not t.is_seed)
        ,'queued':lambda t: (t.paused and not t.user_paused)
        ,'paused':lambda t: (t.user_paused)
        ,'seeding':lambda t:(t.is_seed and not t.paused )
        ,'traffic':lambda t: (t.download_rate > 0 or t.upload_rate > 0)
    }
    filter_func = filters[filter_name]
    return [t for t in torrent_list if filter_func(t)]

def get_category_choosers(torrent_list):
    """
    todo: split into 2 parts...
    """
    categories = get_categories(torrent_list)

    filter_tabs = [Storage(title='All (%s)' % len(torrent_list),
            filter='', category=None)]

    #static filters
    for title, filter_name in [
        (_('Downloading'),'downloading') ,
        (_('Queued'),'queued') ,
        (_('Paused'),'paused') ,
        (_('Seeding'),'seeding'),
        (_('Traffic'),'traffic')
        ]:
        title += ' (%s)' % (
            len(filter_torrent_state(torrent_list, filter_name)), )
        filter_tabs.append(Storage(title=title, filter=filter_name))

    categories = [x for x in  get_categories(torrent_list).iteritems()]
    categories.sort()

    #trackers:
    category_tabs = []
    category_tabs.append(
        Storage(title=_('Trackers'),category=''))
    for title,count in categories:
        category = title
        title += ' (%s)' % (count, )
        category_tabs.append(Storage(title=title, category=category))

    return  filter_tabs, category_tabs

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

class WebUiError(Exception):
    """the message of these exceptions will be rendered in
    render.error(e.message) in debugerror.py"""
    pass

class UnknownTorrentError(WebUiError):
    pass
