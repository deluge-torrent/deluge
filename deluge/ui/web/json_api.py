#
# deluge/ui/web/json_api.py
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA    02110-1301, USA.
#

import os
import time
import urllib
import hashlib
import logging
import tempfile

from types import FunctionType
from twisted.internet.defer import Deferred
from twisted.web import http, resource, server

from deluge import common, component
from deluge.configmanager import ConfigManager
from deluge.ui import common as uicommon
from deluge.ui.client import client, Client
from deluge.ui.web.auth import *
from deluge.ui.web.common import _
json = common.json

log = logging.getLogger(__name__)

def export(auth_level=AUTH_LEVEL_DEFAULT):
    """
    Decorator function to register an object's method as an RPC.  The object
    will need to be registered with an `:class:RPCServer` to be effective.

    :param func: function, the function to export
    :param auth_level: int, the auth level required to call this method

    """
    def wrap(func, *args, **kwargs):
        func._json_export = True
        func._json_auth_level = auth_level
        return func

    if type(auth_level) is FunctionType:
        func = auth_level
        auth_level = AUTH_LEVEL_DEFAULT
        return wrap(func)
    else:
        return wrap

class JSONException(Exception):
    def __init__(self, inner_exception):
        self.inner_exception = inner_exception
        Exception.__init__(self, str(inner_exception))

class JSON(resource.Resource, component.Component):
    """
    A Twisted Web resource that exposes a JSON-RPC interface for web clients
    to use.
    """
    
    def __init__(self):
        resource.Resource.__init__(self)
        component.Component.__init__(self, "JSON")
        self._remote_methods = []
        self._local_methods = {}
    
    def connect(self, host="localhost", port=58846, username="", password=""):
        """
        Connects the client to a daemon
        """
        d = Deferred()
        _d = client.connect(host, port, username, password)
        
        def on_get_methods(methods):
            """
            Handles receiving the method names
            """
            self._remote_methods = methods
            methods = list(self._remote_methods)
            methods.extend(self._local_methods)
            d.callback(methods)
        
        def on_client_connected(connection_id):
            """
            Handles the client successfully connecting to the daemon and 
            invokes retrieving the method names.
            """
            d = client.daemon.get_method_list()
            d.addCallback(on_get_methods)
        _d.addCallback(on_client_connected)
        return d
    
    def _exec_local(self, method, params):
        """
        Handles executing all local methods.
        """
        if method == "system.listMethods":
            d = Deferred()
            methods = list(self._remote_methods)
            methods.extend(self._local_methods)
            d.callback(methods)
            return d
        elif method in self._local_methods:
            # This will eventually process methods that the server adds
            # and any plugins.
            return self._local_methods[method](*params)
        raise JSONException("Unknown system method")
    
    def _exec_remote(self, method, params):
        """
        Executes methods using the Deluge client.
        """
        component, method = method.split(".")
        return getattr(getattr(client, component), method)(*params)
    
    def _handle_request(self, request):
        """
        Takes some json data as a string and attempts to decode it, and process
        the rpc object that should be contained, returning a deferred for all
        procedure calls and the request id.
        """
        request_id = None
        try:
            request = json.loads(request)
        except ValueError:
            raise JSONException("JSON not decodable")
        
        if "method" not in request or "id" not in request or \
           "params" not in request:
            raise JSONException("Invalid JSON request")
        
        method, params = request["method"], request["params"]
        request_id = request["id"]
        
        try:
            if method.startswith("system."):
                return self._exec_local(method, params), request_id
            elif method in self._local_methods:
                return self._exec_local(method, params), request_id
            elif method in self._remote_methods:
                return self._exec_remote(method, params), request_id
        except Exception, e:
            log.exception(e)
            d = Deferred()
            d.callback(None)
            return d, request_id
    
    def _on_rpc_request_finished(self, result, response, request):
        """
        Sends the response of any rpc calls back to the json-rpc client.
        """
        response["result"] = result
        return self._send_response(request, response)

    def _on_rpc_request_failed(self, reason, response, request):
        """
        Handles any failures that occured while making an rpc call.
        """
        print type(reason)
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        return ""
    
    def _on_json_request(self, request):
        """
        Handler to take the json data as a string and pass it on to the
        _handle_request method for further processing.
        """
        log.debug("json-request: %s", request.json)
        response = {"result": None, "error": None, "id": None}
        d, response["id"] = self._handle_request(request.json)
        d.addCallback(self._on_rpc_request_finished, response, request)
        d.addErrback(self._on_rpc_request_failed, response, request)
        return d
    
    def _on_json_request_failed(self, reason, request):
        """
        Errback handler to return a HTTP code of 500.
        """
        log.exception(reason)
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        return ""
    
    def _send_response(self, request, response):
        response = json.dumps(response)
        request.setHeader("content-type", "application/x-json")
        request.write(response)
        request.finish()
    
    def render(self, request):
        """
        Handles all the POST requests made to the /json controller.
        """

        if request.method != "POST":
            request.setResponseCode(http.NOT_ALLOWED)
            return ""
        
        try:
            request.content.seek(0)
            request.json = request.content.read()
            d = self._on_json_request(request)
            return server.NOT_DONE_YET
        except Exception, e:
            return self._on_json_request_failed(e, request)
    
    def register_object(self, obj, name=None):
        """
        Registers an object to export it's rpc methods.  These methods should
        be exported with the export decorator prior to registering the object.

        :param obj: object, the object that we want to export
        :param name: str, the name to use, if None, it will be the class name of the object
        """
        name = name or obj.__class__.__name__
        name = name.lower()

        for d in dir(obj):
            if d[0] == "_":
                continue
            if getattr(getattr(obj, d), '_json_export', False):
                log.debug("Registering method: %s", name + "." + d)
                self._local_methods[name + "." + d] = getattr(obj, d)

class JSONComponent(component.Component):
    def __init__(self, name, interval=1, depend=None):
        super(JSONComponent, self).__init__(name, interval, depend)
        self._json = component.get("JSON")
        self._json.register_object(self, name)
        

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 58846

DEFAULT_HOSTS = {
    "hosts": [(hashlib.sha1(str(time.time())).hexdigest(),
        DEFAULT_HOST, DEFAULT_PORT, "", "")]
}

class WebApi(JSONComponent):
    def __init__(self):
        super(WebApi, self).__init__("Web")
        self.host_list = ConfigManager("hostlist.conf.1.2", DEFAULT_HOSTS)
    
    def get_host(self, connection_id):
        for host in self.host_list["hosts"]:
            if host[0] == connection_id:
                return host
    
    @export
    def connect(self, host_id):
        d = Deferred()
        def on_connected(methods):
            d.callback(methods)
        for host in self.host_list["hosts"]:
            if host_id != host[0]:
                continue
            self._json.connect(*host[1:]).addCallback(on_connected)
        return d
    
    @export
    def connected(self):
        d = Deferred()
        d.callback(client.connected())
        return d
    
    @export
    def update_ui(self, keys, filter_dict):

        ui_info = {
            "torrents": None,
            "filters": None,
            "stats": None
        }
        
        d = Deferred()
        
        log.info("Updating ui with keys '%r' and filters '%r'", keys,
            filter_dict)
        
        def got_stats(stats):
            ui_info["stats"] = stats
            d.callback(ui_info)
        
        def got_filters(filters):
            ui_info["filters"] = filters
            client.core.get_stats().addCallback(got_stats)
            
        def got_torrents(torrents):
            ui_info["torrents"] = torrents
            client.core.get_filter_tree().addCallback(got_filters)
        client.core.get_torrents_status(filter_dict, keys).addCallback(got_torrents)
        return d

    @export
    def download_torrent_from_url(self, url):
        """
        input:
            url: the url of the torrent to download

        returns:
            filename: the temporary file name of the torrent file
        """
        tmp_file = os.path.join(tempfile.gettempdir(), url.split("/")[-1])
        filename, headers = urllib.urlretrieve(url, tmp_file)
        log.debug("filename: %s", filename)
        d = Deferred()
        d.callback(filename)
        return d
    
    @export
    def get_torrent_info(self, filename):
        """
        Goal:
            allow the webui to retrieve data about the torrent

        input:
            filename: the filename of the torrent to gather info about

        returns:
        {
            "filename": the torrent file
            "name": the torrent name
            "size": the total size of the torrent
            "files": the files the torrent contains
            "info_hash" the torrents info_hash
        }
        """
        d = Deferred()
        d.callback(uicommon.get_torrent_info(filename.strip()))
        return d

    @export
    def add_torrents(self, torrents):
        """
        input:
            torrents [{
                path: the path of the torrent file,
                options: the torrent options
            }]
        """
        for torrent in torrents:
            filename = os.path.basename(torrent["path"])
            fdump = open(torrent["path"], "r").read()
            client.add_torrent_file(filename, fdump, torrent["options"])
        d = Deferred()
        d.callback(True)
        return d
    
    @export
    def login(self, password):
        """Method to allow the webui to authenticate
        """
        config = component.get("DelugeWeb").config
        m = hashlib.md5()
        m.update(config['pwd_salt'])
        m.update(password)
        d = Deferred()
        d.callback(m.hexdigest() == config['pwd_md5'])
        return d
    
    @export
    def get_hosts(self):
        """Return the hosts in the hostlist"""
        hosts = dict((host[0], host[:]) for host in self.host_list["hosts"])
        
        main_deferred = Deferred()
        def run_check():
            if all(map(lambda x: x[3] is not None, hosts.values())):
                main_deferred.callback(hosts.values())
        
        def on_connect(connected, c, host_id):
            def on_info(info, c):
                hosts[host_id][3] = _("Online")
                hosts[host_id][4] = info
                c.disconnect()
                run_check()
            
            def on_info_fail(reason):
                hosts[host_id][3] = _("Offline")
                run_check()
            
            if not connected:
                hosts[host_id][3] = _("Offline")
                run_check()
                return

            d = c.daemon.info()
            d.addCallback(on_info, c)
            d.addErrback(on_info_fail)
            
        def on_connect_failed(reason, host_id):
            log.exception(reason)
            hosts[host_id][3] = _("Offline")
            run_check()
        
        for host in hosts.values():
            host_id, host, port, user, password = host[0:5]
            hosts[host_id][3:4] = (None, None)
            
            if client.connected() and (host, port, "localclient" if not \
                user and host in ("127.0.0.1", "localhost") else \
                user)  == client.connection_info():
                def on_info(info):
                    hosts[host_id][4] = info
                    run_check()
                hosts[host_id][3] = _("Connected")
                client.daemon.info().addCallback(on_info)
                continue
            
            c = Client()
            d = c.connect(host, port, user, password)
            d.addCallback(on_connect, c, host_id)
            d.addErrback(on_connect_failed, host_id)
        return main_deferred
    
    @export
    def stop_daemon(self, connection_id):
        """
        Stops a running daemon.

        :param connection_Id: str, the hash id of the connection

        """
        main_deferred = Deferred()
        host = self.get_host(connection_id)
        if not host:
            main_deferred.callback((False, _("Daemon doesn't exist")))
            return main_deferred
        
        try:
            def on_connect(connected, c):
                if not connected:
                    main_deferred.callback((False, _("Daemon not running")))
                    return
                c.daemon.shutdown()
                main_deferred.callback((True, ))
            
            def on_connect_failed(reason):
                main_deferred.callback((False, reason))

            host, port, user, password = host[1:5]
            c = Client()
            d = c.connect(host, port, user, password)
            d.addCallback(on_connect, c)
            d.addErrback(on_connect_failed)
        except:
            main_deferred.callback((False, "An error occured"))
        return main_deferred
    
    @export
    def add_host(self, host, port, username="", password=""):
        """
        Adds a host to the list.

        :param host: str, the hostname
        :param port: int, the port
        :param username: str, the username to login as
        :param password: str, the password to login with

        """
        d = Deferred()
        # Check to see if there is already an entry for this host and return
        # if thats the case
        for entry in self.host_list["hosts"]:
            if (entry[0], entry[1], entry[2]) == (host, port, username):
                d.callback((False, "Host already in the list"))
        
        try:
            port = int(port)
        except:
            d.callback((False, "Port is invalid"))
            return d
        
        # Host isn't in the list, so lets add it
        connection_id = hashlib.sha1(str(time.time())).hexdigest()
        self.host_list["hosts"].append([connection_id, host, port, username,
            password])
        self.host_list.save()
        d.callback((True,))
        return d
    
    @export
    def remove_host(self, connection_id):
        """
        Removes a host for the list

        :param connection_Id: str, the hash id of the connection

        """
        d = Deferred()
        host = self.get_host(connection_id)
        if host is None:
            d.callback(False)
        
        self.host_list["hosts"].remove(host)
        self.host_list.save()
        d.callback(True)
        return d
