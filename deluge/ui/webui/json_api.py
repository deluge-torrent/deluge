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
    json_exposed = ["update_ui","system_listMethods", "download_torrent_from_url",
        "get_webui_config","set_webui_config","get_webui_templates", "get_torrent_info"]
    cache = {}

    def GET(self):
        return json_error("only POST is supported")

    def POST(self , name=None):
        web.header("Content-Type", "application/x-json")
        ck = cookies()
        id = 0
        if not(ck.has_key("session_id") and ck["session_id"] in utils.config.get("sessions")):
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


    def update_ui(self, keys ,filter_dict , cache_id = None ):
        """
        Composite call.
        Goal : limit the number of ajax calls

        input:
            keys: see get_torrents_status
            filter_dict: see get_torrents_status
            cache_id: # todo
        returns:
        {
            "torrents": see get_torrent_status
            "filters": see get_filter_tree
            "stats": see get_stats
            "cache_id":int # todo
        }
        """
        filters = sclient.get_filter_tree()
        return {
            "torrents":sclient.get_torrents_status(filter_dict , keys),
            "filters":filters,
            "stats":sclient.get_stats(),
            "cache_id":-1
        }

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

    def download_torrent_from_url(self, url):
        """        
        input:
            url: the url of the torrent to download
        
        returns:
            filename: the temporary file name of the torrent file
        """
        import os
        import urllib
        import tempfile
        tmp_file = os.path.join(tempfile.gettempdir(), url.split("/")[-1])
        filename, headers = urllib.urlretrieve(url, tmp_file)
        log.debug("filename: %s", filename)
        return filename
    
    def get_torrent_info(self, filename):
        """
        Goal:
            allow the webui to retrieve data about the torrent
        
        input:
            url: the url of the torrent to download
        
        returns:
        {
            "name": the torrent name
            "size": the total size of the torrent
            "files": the files the torrent contains
            "info_hash" the torrents info_hash
        }
        """
        import os
        import deluge.bencode

        # Get the torrent data from the torrent file
        try:
            log.debug("Attempting to open %s for add.", filename)
            metadata = deluge.bencode.bdecode(open(filename, "rb").read())
        except Exception, e:
            log.warning("Unable to open %s: %s", filename, e)

        from sha import sha
        info_hash = sha(deluge.bencode.bencode(metadata["info"])).hexdigest()

        # Get list of files from torrent info
        files = []
        if metadata["info"].has_key("files"):
            prefix = ""
            if len(metadata["info"]["files"]) > 1:
                prefix = metadata["info"]["name"]
                
            for f in metadata["info"]["files"]:
                files.append({
                    'path': os.path.join(prefix, *f["path"]),
                    'size': f["length"],
                    'download': True
                })
        else:
            files.append({
                "path": metadata["info"]["name"],
                "size": metadata["info"]["length"],
                "download": True
            })
        log.debug(metadata)
        return {
            "name": metadata["info"]["name"],
            "size": metadata["info"]["length"],
            "files": files,
            "info_hash": info_hash
        }

def register():
    component.get("PageManager").register_page("/json/rpc",json_rpc)

if __name__ == '__main__':
    print "todo: tests"
