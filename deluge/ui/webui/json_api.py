#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# webserver_framework.py
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
from deluge.ui.client import sclient
from deluge.log import LOG as log
from deluge import component

from page_decorators import check_session
try:
    import json #it's early enough to force people to install this
except:
    raise Exception("please install python-json")

class json_rpc:
    """
    == Full client api ==
    * url : /json/rpc
    * rpc-api : http://en.wikipedia.org/wiki/JSON-RPC#Version_1.0
    * methods : http://dev.deluge-torrent.org/wiki/Development/UiClient#Remoteapi
    """
    def GET(self):
        print '{"error":"only POST is supported"}'

    #security bug: does not check session!!
    def POST(self):
        web.header("Content-Type", "application/x-json")
        id = 0
        try:
            log.debug("json-data:")
            log.debug(webapi.data())
            json_data = json.read(webapi.data())
            id = json_data["id"]
            method = json_data["method"]
            params = json_data["params"]

            if method.startswith('_'):
                raise Exception('_ methods are illegal.')

            if method.startswith("system."):
                result = self.exec_system_method(method, params,id)
            elif method == ("list_torrents"):
                result = self.list_torrents(method, params,id)
            else:
                result = self.exec_client_method(method, params,id)

            log.debug("JSON-result:%s(%s)[%s] = %s" % (method, params, id, result))
            print json.write(result)

        except Exception,e:
            #verbose because you don't want exeptions in the error-handler.
            message = ""
            if hasattr(e,"message"):
                message = e.message
            log.debug(format_exc())
            log.error("JSON-error:%s:%s %s" % (e, message, id))
            print json.write({
                "version":"1.1",
                "id":id,
                "error":{
                    "number":123,
                    "message":"%s:%s %s" % (e, message, id),
                    "error":format_exc()
                    }
            })

    def exec_client_method(self, method, params, id):
        if not hasattr(sclient,method):
            raise Exception('Unknown method:%s', method)

        #Call:
        func = getattr(sclient, method)
        result = func(*params)

        return {
            "version":"1.1",
            "result":result,
            "id":id
        }

    def exec_system_method(self, method, params, id):
        if method == "system.listMethods":
            return self.exec_client_method("list_methods", params, id)
        raise Exception('Unknown method:%s', method)


    def list_torrents(self,params,id):
        """
        == torrent_list ==
        Composite call.
        Goal : limit the number of ajax calls

        filter is only effective if the organize plugin is enabled.
        label is redirected to the tracker column, there will be a label feature in the future.
        cache_id = future feature, not effective yet.

        === input ===
        {{{
        {
            keys: [<like get_torrent_status>],
            filter: {
                /*ommitted keys are ignored*/
                "keyword":string
                "label":string,
                "state":string
            } ,
            cache_id: int
        }
        }}}

        === output ===
        {{{
        {
        torrents:
            [ {"id":string,"name":string, ..}, ..]
        states:
            [('string',int), ..]
        trackers:
            [('string',int), ..]
        stats:
            [upload_rate, download_rate, nu_connections, num_dht_nodes]
        }
        cache_id:int
        }
        }}}
        """
        """filter = params["filter"]
        keys = params["keys"]
        cache_id = params["cache_id"]
        organize_filters = {}

        if 'Organize' in proxy.get_enabled_plugins():
            filter_dict = {}

            for filter_name in ["state","tracker","keyword"]:
                value = get(filter,filter_name)
                if value and value <> "All":
                    filter_dict[filter_name] = value

            torrent_ids =  proxy.organize_get_session_state(filter_dict)
            organize_filters = Storage(proxy.organize_all_filter_items())
        else:
             torrent_ids =  proxy.get_session_state()
            organize_filters = {"state":[["All",-1]],"tracker":[]}

        result = {
            "torrents":sclient.get_torrents_status(torrent_ids, keys),
            "state":organize_filters["state"],
            "tracker":organize_filters["tracker"],
            "stats":[0, 1, 2, 3], #todo
            "cache_id":cache_id
        }
        """



def register():
    component.get("PageManager").register_page("/json/rpc",json_rpc)

if __name__ == '__main__':
    print "todo: tests"
