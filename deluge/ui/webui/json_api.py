#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# webserver_framework.py
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
json api.

design:
== Full client api ==
 * url : /json/rpc/
 * rpc-api : http://en.wikipedia.org/wiki/JSON-RPC
 * methods : http://dev.deluge-torrent.org/wiki/Development/UiClient#Remoteapi

"""
from traceback import format_exc
import web
from web import webapi
import page_decorators as deco
from web import cookies, setcookie as w_setcookie
import utils
from render import render
from utils import dict_cb
from lib import json

from deluge.ui.client import sclient,aclient
from deluge.log import LOG as log
from deluge import component

def json_response(result, id):
    print json.write({
            "version":"1.1",
            "result":result,
            "id":id
    })

def json_error(message , id=-1, msg_number=123):
    log.error("JSON-error:%s" % message)
    print json.write({
        "version":"1.1",
        "id":id,
        "error":{
            "number":msg_number,
            "message":message,
            "error":message
            }
    })

class json_rpc:
    """
    == Full client api ==
    * url : /json/rpc
    * rpc-api : http://en.wikipedia.org/wiki/JSON-RPC#Version_1.0
    * methods : http://dev.deluge-torrent.org/wiki/Development/UiClient#Remoteapi
    """
    #extra exposed methods
    json_exposed = ["update_ui","get_stats","set_torrent_options","system_listMethods",
        "get_webui_config","set_webui_config","get_webui_templates"]
    cache = {}
    torrent_options = ["trackers","max_connections","max_upload_slots","max_upload_speed",
    "max_download_speed","file_priorities","prioritize_first_last","auto_managed","stop_at_ratio",
    "stop_ratio","remove_at_ratio"]

    def GET(self):
        return json_error("only POST is supported")

    def POST(self , name=None):
        web.header("Content-Type", "application/x-json")
        ck = cookies()
        id = 0
        if not(ck.has_key("session_id") and ck["session_id"] in utils.SESSIONS):
            return json_error("not authenticated", id)

        try:
            log.debug("json-data:")
            log.debug(webapi.data())
            json_data = json.read(webapi.data())
            id = json_data["id"]
            method = json_data["method"].replace(".", "_")
            params = json_data["params"]

            if method.startswith('_'):
                raise Exception('_ methods are illegal.')

            elif method in self.json_exposed:
                func = getattr(self, method)
                result = func(*params)
            else:
                result = self.exec_client_method(method, params)

            #log.debug("JSON-result:%s(%s)[%s] = %s" % (method, params, id, result))

            return json_response(result, id)

        except Exception,e:
            #verbose because you don't want exeptions in the error-handler.
            message = ""
            if hasattr(e,"message"):
                message = e.message
            log.debug(format_exc())
            return json_error("%s:%s" % (e, message), id)

    def exec_client_method(self, method, params):
        if not hasattr(sclient,method):
            raise Exception('Unknown method:%s', method)

        #Call:
        func = getattr(sclient, method)
        return func(*params)

    #
    #Extra exposed methods:
    #
    def system_listMethods(self):
        "system.listMethods() see json/xmlrpc docs"
        return sclient.list_methods() + self.json_exposed

    def get_stats(self):
        """
        returns:
        {{{
        {
        'download_rate':float(),
        'upload_rate':float(),
        'max_download':float(),
        'max_upload':float(),
        'num_connections':int(),
        'max_num_connections':int(),
        'dht_nodes',int()
        }
        }}}
        """
        stats = {}

        aclient.get_download_rate(dict_cb('download_rate',stats))
        aclient.get_upload_rate(dict_cb('upload_rate',stats))
        aclient.get_config_value(dict_cb('max_download',stats)
            ,"max_download_speed")
        aclient.get_config_value(dict_cb('max_upload',stats)
            ,"max_upload_speed")
        aclient.get_num_connections(dict_cb("num_connections",stats))
        aclient.get_config_value(dict_cb('max_num_connections',stats)
            ,"max_connections_global")
        aclient.get_dht_nodes(dict_cb('dht_nodes',stats))

        aclient.force_call(block=True)

        return stats

    def update_ui(self, keys ,filter_dict , cache_id = None ):
        """
        Composite call.
        Goal : limit the number of ajax calls

        input:
        {{{
            keys: see get_torrent_status
            filter_dict: see label_get_filtered_ids # only effective if the label plugin is enabled.
            cache_id: # todo
        }}}
        returns:
        {{{
        {
            "torrents": see get_torrent_status
            "filters": see label_get_filters
            "stats": see get_stats
            "cache_id":int # todo
        }
        }}}
        """
        if 'Label' in sclient.get_enabled_plugins():
            torrent_ids =  sclient.label_get_filtered_ids(filter_dict)
            filters = sclient.label_filter_items()
        else:
            torrent_ids =  sclient.get_session_state()
            filters = {"state":[["All",-1]],"tracker":[],"label":[]}

        return {
            "torrents":sclient.get_torrents_status({"id":torrent_ids}, keys),
            "filters":filters,
            "stats":self.get_stats(),
            "cache_id":-1
        }

    def set_torrent_options(self, torrent_id, options_dict):
        """
        Composite call.
        Goal: limit the number of ajax calls

        input:
        {{{
            torrent_id: the id of the torrent who's options are to be changed
            options_dict: a dictionary inwhich the options to be changed are contained
        }}}
        """

        for option in options_dict:
            if option in self.torrent_options:
                value = options_dict[option]
                if type(value) == str:
                    try:
                        value = float(value)
                    except:
                        pass
                func = getattr(sclient, 'set_torrent_' + option)
                func(torrent_id, value)

    def get_webui_config(self):
        return dict([x for x in utils.config.get_config().iteritems() if not x[0].startswith("pwd")])

    def set_webui_config(self, data):
        utils.validate_config(data)
        if "pwd" in data:
            utils.update_pwd(pwd)
            del data["pwd"]
        for key, value in data.iteritems():
            utils.config.set(key, value)
        utils.config.save()
        utils.apply_config()

    def get_webui_templates(self):
        return render.get_templates()



def register():
    component.get("PageManager").register_page("/json/rpc",json_rpc)

if __name__ == '__main__':
    print "todo: tests"
