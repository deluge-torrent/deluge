#
# deluge/ui/web/json_api.py
#
# Copyright (C) 2009-2010 Damien Churchill <damoxc@gmail.com>
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
#   Boston, MA  02110-1301, USA.
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

from __future__ import with_statement

import os
import time
import base64
import shutil
import logging
import hashlib
import tempfile
from socket import gaierror, gethostbyname
from urlparse import urljoin
from urllib import unquote_plus

from types import FunctionType
from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList
from twisted.web import http, resource, server
import twisted.web.client
import twisted.web.error

from deluge import common, component, httpdownloader
from deluge.configmanager import ConfigManager, get_config_dir
from deluge.ui import common as uicommon
from deluge.ui.client import client, Client
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.sessionproxy import SessionProxy

from deluge.ui.web.common import _, compress
json = common.json

log = logging.getLogger(__name__)

AUTH_LEVEL_DEFAULT = None
AuthError = None

class JSONComponent(component.Component):
    def __init__(self, name, interval=1, depend=None):
        super(JSONComponent, self).__init__(name, interval, depend)
        self._json = component.get("JSON")
        self._json.register_object(self, name)

def export(auth_level=AUTH_LEVEL_DEFAULT):
    """
    Decorator function to register an object's method as a RPC. The object
    will need to be registered with a `:class:JSON` to be effective.

    :param func: the function to export
    :type func: function
    :keyword auth_level: the auth level required to call this method
    :type auth_level: int

    """
    global AUTH_LEVEL_DEFAULT, AuthError
    if AUTH_LEVEL_DEFAULT is None:
        from deluge.ui.web.auth import AUTH_LEVEL_DEFAULT, AuthError

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
    A Twisted Web resource that exposes a JSON-RPC interface for web clients \
    to use.
    """

    def __init__(self):
        resource.Resource.__init__(self)
        component.Component.__init__(self, "JSON")
        self._remote_methods = []
        self._local_methods = {}
        if client.is_classicmode():
            self.get_remote_methods()
        else:
            client.disconnect_callback = self._on_client_disconnect

    def on_get_methods(self, methods):
        """
        Handles receiving the method names.
        """
        self._remote_methods = methods

    def get_remote_methods(self, result=None):
        """
        Updates remote methods from the daemon.
        """
        return client.daemon.get_method_list().addCallback(self.on_get_methods)

    def connect(self, host="localhost", port=58846, username="", password=""):
        """
        Connects the client to a daemon
        """
        d = client.connect(host, port, username, password)

        def on_client_connected(connection_id):
            """
            Handles the client successfully connecting to the daemon and
            invokes retrieving the method names.
            """
            d = self.get_remote_methods()
            component.get("Web.PluginManager").start()
            component.get("Web").start()
            return d

        return d.addCallback(on_client_connected)

    def disable(self):
        client.deregister_event_handler("PluginEnabledEvent", self.get_remote_methods)
        client.deregister_event_handler("PluginDisabledEvent", self.get_remote_methods)

        if client.is_classicmode():
            component.get("Web.PluginManager").stop()
        else:
            client.disconnect()

    def enable(self):
        client.register_event_handler("PluginEnabledEvent", self.get_remote_methods)
        client.register_event_handler("PluginDisabledEvent", self.get_remote_methods)

        if client.is_classicmode():
            component.get("Web.PluginManager").start()
        elif component.get("DelugeWeb").config["default_daemon"]:
            # Sort out getting the default daemon here
            default = component.get("DelugeWeb").config["default_daemon"]
            host = component.get("Web").get_host(default)
            if host:
                self.connect(*host[1:])
            else:
                self.connect()

    def _on_client_disconnect(self, *args):
        component.get("Web.PluginManager").stop()
        component.get("Web").stop()

    def _exec_local(self, method, params, request):
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
            meth = self._local_methods[method]
            meth.func_globals['__request__'] = request
            component.get("Auth").check_request(request, meth)
            return meth(*params)
        raise JSONException("Unknown system method")

    def _exec_remote(self, method, params, request):
        """
        Executes methods using the Deluge client.
        """
        component.get("Auth").check_request(request, level=AUTH_LEVEL_DEFAULT)
        core_component, method = method.split(".")
        return getattr(getattr(client, core_component), method)(*params)

    def _handle_request(self, request):
        """
        Takes some json data as a string and attempts to decode it, and process
        the rpc object that should be contained, returning a deferred for all
        procedure calls and the request id.
        """
        try:
            request.json = json.loads(request.json)
        except ValueError:
            raise JSONException("JSON not decodable")

        if "method" not in request.json or "id" not in request.json or \
           "params" not in request.json:
            raise JSONException("Invalid JSON request")

        method, params = request.json["method"], request.json["params"]
        request_id = request.json["id"]
        result = None
        error = None

        try:
            if method.startswith("system.") or method in self._local_methods:
                result = self._exec_local(method, params, request)
            elif method in self._remote_methods:
                result = self._exec_remote(method, params, request)
            else:
                error = {"message": "Unknown method", "code": 2}
        except AuthError, e:
            error = {"message": "Not authenticated", "code": 1}
        except Exception, e:
            log.error("Error calling method `%s`", method)
            log.exception(e)

            error = {"message": e.message, "code": 3}

        return request_id, result, error

    def _on_rpc_request_finished(self, result, response, request):
        """
        Sends the response of any rpc calls back to the json-rpc client.
        """
        response["result"] = result
        return self._send_response(request, response)

    def _on_rpc_request_failed(self, reason, response, request):
        """
        Handles any failures that occurred while making an rpc call.
        """
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        return ""

    def _on_json_request(self, request):
        """
        Handler to take the json data as a string and pass it on to the
        _handle_request method for further processing.
        """
        if request.getHeader('content-type') != 'application/json':
            message = 'Invalid JSON request content-type: %s' % request.getHeader('content-type')
            raise JSONException(message)

        log.debug("json-request: %s", request.json)
        response = {"result": None, "error": None, "id": None}
        response["id"], d, response["error"] = self._handle_request(request)

        if isinstance(d, Deferred):
            d.addCallback(self._on_rpc_request_finished, response, request)
            d.addErrback(self._on_rpc_request_failed, response, request)
            return d
        else:
            response["result"] = d
            return self._send_response(request, response)

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
        request.write(compress(response, request))
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

        :param obj: the object that we want to export
        :type obj: object
        :param name: the name to use, if None, it will be the class name of the object
        :type name: string
        """
        name = name or obj.__class__.__name__
        name = name.lower()

        for d in dir(obj):
            if d[0] == "_":
                continue
            if getattr(getattr(obj, d), '_json_export', False):
                log.debug("Registering method: %s", name + "." + d)
                self._local_methods[name + "." + d] = getattr(obj, d)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 58846

DEFAULT_HOSTS = {
    "hosts": [(hashlib.sha1(str(time.time())).hexdigest(),
               DEFAULT_HOST, DEFAULT_PORT, "", "")]
}
HOSTLIST_ID = 0
HOSTLIST_NAME = 1
HOSTLIST_PORT = 2
HOSTLIST_USER = 3
HOSTLIST_PASS = 4

HOSTS_ID = HOSTLIST_ID
HOSTS_NAME = HOSTLIST_NAME
HOSTS_PORT = HOSTLIST_PORT
HOSTS_STATUS = 3
HOSTS_INFO = 4

FILES_KEYS = ["files", "file_progress", "file_priorities"]

class EventQueue(object):
    """
    This class subscribes to events from the core and stores them until all
    the subscribed listeners have received the events.
    """

    def __init__(self):
        self.__events = {}
        self.__handlers = {}
        self.__queue = {}
        self.__requests = {}

    def add_listener(self, listener_id, event):
        """
        Add a listener to the event queue.

        :param listener_id: A unique id for the listener
        :type listener_id: string
        :param event: The event name
        :type event: string
        """
        if event not in self.__events:

            def on_event(*args):
                for listener in self.__events[event]:
                    if listener not in self.__queue:
                        self.__queue[listener] = []
                    self.__queue[listener].append((event, args))

            client.register_event_handler(event, on_event)
            self.__handlers[event] = on_event
            self.__events[event] = [listener_id]
        elif listener_id not in self.__events[event]:
            self.__events[event].append(listener_id)

    def get_events(self, listener_id):
        """
        Retrieve the pending events for the listener.

        :param listener_id: A unique id for the listener
        :type listener_id: string
        """

        # Check to see if we have anything to return immediately
        if listener_id in self.__queue:
            queue = self.__queue[listener_id]
            del self.__queue[listener_id]
            return queue

        # Create a deferred to and check again in 100ms
        d = Deferred()
        reactor.callLater(0.1, self._get_events, listener_id, 0, d)
        return d

    def _get_events(self, listener_id, count, d):
        if listener_id in self.__queue:
            queue = self.__queue[listener_id]
            del self.__queue[listener_id]
            d.callback(queue)
        else:
            # Prevent this loop going on indefinitely incase a client leaves
            # the page or disconnects uncleanly.
            if count >= 50:
                d.callback(None)
            else:
                reactor.callLater(0.1, self._get_events, listener_id, count + 1, d)

    def remove_listener(self, listener_id, event):
        """
        Remove a listener from the event queue.

        :param listener_id: The unique id for the listener
        :type listener_id: string
        :param event: The event name
        :type event: string
        """
        self.__events[event].remove(listener_id)
        if not self.__events[event]:
            client.deregister_event_handler(event, self.__handlers[event])
            del self.__events[event]
            del self.__handlers[event]

class WebApi(JSONComponent):
    """
    The component that implements all the methods required for managing
    the web interface. The complete web json interface also exposes all the
    methods available from the core RPC.
    """

    def __init__(self):
        super(WebApi, self).__init__("Web", depend=["SessionProxy"])
        self.host_list = ConfigManager("hostlist.conf.1.2", DEFAULT_HOSTS)
        if not os.path.isfile(self.host_list.config_file):
            self.host_list.save()
        self.core_config = CoreConfig()
        self.event_queue = EventQueue()
        try:
            self.sessionproxy = component.get("SessionProxy")
        except KeyError:
            self.sessionproxy = SessionProxy()

    def get_host(self, host_id):
        """
        Return the information about a host

        :param host_id: the id of the host
        :type host_id: string
        :returns: the host information
        :rtype: list
        """
        for host in self.host_list["hosts"]:
            if host[0] == host_id:
                return host

    def start(self):
        self.core_config.start()
        self.sessionproxy.start()

    def stop(self):
        self.core_config.stop()
        self.sessionproxy.stop()

    @export
    def connect(self, host_id):
        """
        Connect the client to a daemon

        :param host_id: the id of the daemon in the host list
        :type host_id: string
        :returns: the methods the daemon supports
        :rtype: list
        """
        d = Deferred()
        def on_connected(methods):
            d.callback(methods)
        host = self.get_host(host_id)
        if host:
            self._json.connect(*host[1:]).addCallback(on_connected)
        return d

    @export
    def connected(self):
        """
        The current connection state.

        :returns: True if the client is connected
        :rtype: booleon
        """
        return client.connected()

    @export
    def disconnect(self):
        """
        Disconnect the web interface from the connected daemon.
        """
        client.disconnect()
        return True

    @export
    def update_ui(self, keys, filter_dict):
        """
        Gather the information required for updating the web interface.

        :param keys: the information about the torrents to gather
        :type keys: list
        :param filter_dict: the filters to apply when selecting torrents.
        :type filter_dict: dictionary
        :returns: The torrent and ui information.
        :rtype: dictionary
        """
        d = Deferred()
        ui_info = {
            "connected": client.connected(),
            "torrents": None,
            "filters": None,
            "stats": {
                "max_download": self.core_config.get("max_download_speed"),
                "max_upload": self.core_config.get("max_upload_speed"),
                "max_num_connections": self.core_config.get("max_connections_global")
            }
        }

        if not client.connected():
            d.callback(ui_info)
            return d

        def got_connections(connections):
            ui_info["stats"]["num_connections"] = connections

        def got_stats(stats):
            ui_info["stats"]["upload_rate"] = stats["payload_upload_rate"]
            ui_info["stats"]["download_rate"] = stats["payload_download_rate"]
            ui_info["stats"]["download_protocol_rate"] = stats["download_rate"] - stats["payload_download_rate"]
            ui_info["stats"]["upload_protocol_rate"] = stats["upload_rate"] - stats["payload_upload_rate"]
            ui_info["stats"]["dht_nodes"] = stats["dht_nodes"]
            ui_info["stats"]["has_incoming_connections"] = stats["has_incoming_connections"]

        def got_filters(filters):
            ui_info["filters"] = filters

        def got_free_space(free_space):
            ui_info["stats"]["free_space"] = free_space

        def got_torrents(torrents):
            ui_info["torrents"] = torrents

        def on_complete(result):
            d.callback(ui_info)

        d1 = component.get("SessionProxy").get_torrents_status(filter_dict, keys)
        d1.addCallback(got_torrents)

        d2 = client.core.get_filter_tree()
        d2.addCallback(got_filters)

        d3 = client.core.get_session_status([
            "payload_download_rate",
            "payload_upload_rate",
            "download_rate",
            "upload_rate",
            "dht_nodes",
            "has_incoming_connections"
        ])
        d3.addCallback(got_stats)

        d4 = client.core.get_num_connections()
        d4.addCallback(got_connections)

        d5 = client.core.get_free_space(self.core_config.get("download_location"))
        d5.addCallback(got_free_space)

        dl = DeferredList([d1, d2, d3, d4, d5], consumeErrors=True)
        dl.addCallback(on_complete)
        return d

    def _on_got_files(self, torrent, d):
        files = torrent.get("files")
        file_progress = torrent.get("file_progress")
        file_priorities = torrent.get("file_priorities")

        paths = []
        info = {}
        for index, torrent_file in enumerate(files):
            path = torrent_file["path"]
            paths.append(path)
            torrent_file["progress"] = file_progress[index]
            torrent_file["priority"] = file_priorities[index]
            torrent_file["index"] = index
            torrent_file["path"] = path
            info[path] = torrent_file

            # update the directory info
            dirname = os.path.dirname(path)
            while dirname:
                dirinfo = info.setdefault(dirname, {})
                dirinfo["size"] = dirinfo.get("size", 0) + torrent_file["size"]
                if "priority" not in dirinfo:
                    dirinfo["priority"] = torrent_file["priority"]
                else:
                    if dirinfo["priority"] != torrent_file["priority"]:
                        dirinfo["priority"] = 9

                progresses = dirinfo.setdefault("progresses", [])
                progresses.append(torrent_file["size"] * (torrent_file["progress"] / 100.0))
                dirinfo["progress"] = float(sum(progresses)) / dirinfo["size"] * 100
                dirinfo["path"] = dirname
                dirname = os.path.dirname(dirname)

        def walk(path, item):
            if item["type"] == "dir":
                item.update(info[path])
                return item
            else:
                item.update(info[path])
                return item

        file_tree = uicommon.FileTree2(paths)
        file_tree.walk(walk)
        d.callback(file_tree.get_tree())

    @export
    def get_torrent_status(self, torrent_id, keys):
        return component.get("SessionProxy").get_torrent_status(torrent_id, keys)

    @export
    def get_torrent_files(self, torrent_id):
        """
        Gets the files for a torrent in tree format

        :param torrent_id: the id of the torrent to retrieve.
        :type torrent_id: string
        :returns: The torrents files in a tree
        :rtype: dictionary
        """
        main_deferred = Deferred()
        d = component.get("SessionProxy").get_torrent_status(torrent_id, FILES_KEYS)
        d.addCallback(self._on_got_files, main_deferred)
        return main_deferred

    @export
    def download_torrent_from_url(self, url, cookie=None):
        """
        Download a torrent file from a url to a temporary directory.

        :param url: the url of the torrent
        :type url: string
        :returns: the temporary file name of the torrent file
        :rtype: string
        """

        def on_download_success(result):
            log.debug("Successfully downloaded %s to %s", url, result)
            return result

        def on_download_fail(result):
            if result.check(twisted.web.error.PageRedirect):
                new_url = urljoin(url, result.getErrorMessage().split(" to ")[1])
                result = httpdownloader.download_file(new_url, tmp_file, headers=headers)
                result.addCallbacks(on_download_success, on_download_fail)
            elif result.check(twisted.web.client.PartialDownloadError):
                result = httpdownloader.download_file(url, tmp_file, headers=headers,
                                                      allow_compression=False)
                result.addCallbacks(on_download_success, on_download_fail)
            else:
                log.error("Error occurred downloading torrent from %s", url)
                log.error("Reason: %s", result.getErrorMessage())
            return result

        tempdir = tempfile.mkdtemp(prefix="delugeweb-")
        tmp_file = os.path.join(tempdir, url.split("/")[-1])
        log.debug("filename: %s", tmp_file)
        headers = {}
        if cookie:
            headers["Cookie"] = cookie
            log.debug("cookie: %s", cookie)
        d = httpdownloader.download_file(url, tmp_file, headers=headers)
        d.addCallbacks(on_download_success, on_download_fail)
        return d

    @export
    def get_torrent_info(self, filename):
        """
        Return information about a torrent on the filesystem.

        :param filename: the path to the torrent
        :type filename: string

        :returns: information about the torrent:

        ::

            {
                "name": the torrent name,
                "files_tree": the files the torrent contains,
                "info_hash" the torrents info_hash
            }

        :rtype: dictionary
        """
        try:
            torrent_info = uicommon.TorrentInfo(filename.strip(), 2)
            return torrent_info.as_dict("name", "info_hash", "files_tree")
        except Exception, e:
            log.exception(e)
            return False

    @export
    def get_magnet_info(self, uri):
        """
        Return information about a magnet link.

        :param uri: the magnet link
        :type uri: string

        :returns: information about the magnet link:

        ::

            {
                "name": the torrent name,
                "info_hash": the torrents info_hash,
                "files_tree": empty value for magnet links
            }

        :rtype: dictionary
        """
        magnet_scheme = 'magnet:?'
        xt_param = 'xt=urn:btih:'
        dn_param = 'dn='
        if uri.startswith(magnet_scheme):
            name = None
            info_hash = None
            for param in uri[len(magnet_scheme):].split('&'):
                if param.startswith(xt_param):
                    xt_hash = param[len(xt_param):]
                    if len(xt_hash) == 32:
                        try:
                            info_hash = base64.b32decode(xt_hash.upper()).encode("hex")
                        except TypeError, ex:
                            log.debug("Invalid base32 magnet hash: %s, %s", xt_hash, ex)
                            break
                    elif len(xt_hash) == 40:
                        info_hash = xt_hash
                    else:
                        break
                elif param.startswith(dn_param):
                    name = unquote_plus(param[len(dn_param):])

            if info_hash:
                if not name:
                    name = info_hash
                return {"name":name, "info_hash":info_hash, "files_tree":''}
        return False

    @export
    def add_torrents(self, torrents):
        """
        Add torrents by file

        :param torrents: A list of dictionaries containing the torrent \
        path and torrent options to add with.
        :type torrents: list

        **Usage**

        >>> json_api.web.add_torrents([{
                "path": "/tmp/deluge-web/some-torrent-file.torrent",
                "options": {"download_location": "/home/deluge/"}
            }])

        """
        for torrent in torrents:
            if common.is_magnet(torrent["path"]):
                log.info("Adding torrent from magnet uri `%s` with options `%r`",
                         torrent["path"], torrent["options"])
                client.core.add_torrent_magnet(torrent["path"], torrent["options"])
            else:
                filename = os.path.basename(torrent["path"])
                with open(torrent["path"], "rb") as _file:
                    fdump = base64.encodestring(_file.read())
                log.info("Adding torrent from file `%s` with options `%r`",
                         filename, torrent["options"])
                client.core.add_torrent_file(filename, fdump, torrent["options"])
        return True

    @export
    def get_hosts(self):
        """
        Return the hosts in the hostlist.
        """
        log.debug("get_hosts called")
        return [(tuple(host[HOSTS_ID:HOSTS_PORT+1]) + ("Offline",)) for host in self.host_list["hosts"]]

    @export
    def get_host_status(self, host_id):
        """
        Returns the current status for the specified host.

        :param host_id: the hash id of the host
        :type host_id: string
        """

        def response(status, info=None):
            return host_id, host, port, status, info

        try:
            host_id, host, port, user, password = self.get_host(host_id)
        except TypeError, e:
            host = None
            port = None
            return response("Offline")

        def on_connect(connected, c, host_id):
            def on_info(info, c):
                c.disconnect()
                return response("Online", info)

            def on_info_fail(reason, c):
                c.disconnect()
                return response("Offline")

            if not connected:
                return response("Offline")

            return c.daemon.info(
                ).addCallback(on_info, c
                ).addErrback(on_info_fail, c)

        def on_connect_failed(reason, host_id):
            return response("Offline")

        if client.connected() and (host, port, "localclient" if not
                                   user and host in ("127.0.0.1", "localhost") else
                                   user)  == client.connection_info():
            def on_info(info):
                return response("Connected", info)

            return client.daemon.info().addCallback(on_info)
        else:
            c = Client()
            return c.connect(host, port, user, password
                ).addCallback(on_connect, c, host_id
                ).addErrback(on_connect_failed, host_id)

    @export
    def start_daemon(self, port):
        """
    Starts a local daemon.
    """
        client.start_daemon(port, get_config_dir())

    @export
    def stop_daemon(self, host_id):
        """
        Stops a running daemon.

        :param host_id: the hash id of the host
        :type host_id: string
        """
        main_deferred = Deferred()
        host = self.get_host(host_id)
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
            main_deferred.callback((False, "An error occurred"))
        return main_deferred

    @export
    def add_host(self, host, port, username="", password=""):
        """
        Adds a host to the list.

        :param host: the hostname
        :type host: string
        :param port: the port
        :type port: int
        :keyword username: the username to login as
        :type username: string
        :keyword password: the password to login with
        :type password: string

        """
        # Check to see if there is already an entry for this host and return
        # if thats the case
        for entry in self.host_list["hosts"]:
            if (entry[0], entry[1], entry[2]) == (host, port, username):
                return (False, "Host already in the list")

        try:
            gethostbyname(host)
        except gaierror, ex:
            return (False, "Hostname error: %s" % ex.args[1])

        try:
            port = int(port)
        except:
            return (False, "Port is invalid")

        # Host isn't in the list, so lets add it
        connection_id = hashlib.sha1(str(time.time())).hexdigest()
        self.host_list["hosts"].append([connection_id, host, port, username,
                                        password])
        self.host_list.save()
        return (True,)

    @export
    def remove_host(self, connection_id):
        """
        Removes a host for the list

        :param host_id: the hash id of the host
        :type host_id: string
        """
        host = self.get_host(connection_id)
        if host is None:
            return False

        self.host_list["hosts"].remove(host)
        self.host_list.save()
        return True

    @export
    def get_config(self):
        """
        Get the configuration dictionary for the web interface.

        :rtype: dictionary
        :returns: the configuration
        """
        config = component.get("DelugeWeb").config.config.copy()
        del config["sessions"]
        del config["pwd_salt"]
        del config["pwd_sha1"]
        return config

    @export
    def set_config(self, config):
        """
        Sets the configuration dictionary for the web interface.

        :param config: The configuration options to update
        :type config: dictionary
        """
        web_config = component.get("DelugeWeb").config
        for key in config.keys():
            if isinstance(config[key], unicode) or isinstance(config[key], str):
                config[key] = config[key].encode("utf8")
            web_config[key] = config[key]

    @export
    def get_plugins(self):
        return {
            "enabled_plugins": component.get("Web.PluginManager").plugins.keys(),
            "available_plugins": component.get("Web.PluginManager").available_plugins
        }

    @export
    def get_plugin_info(self, name):
        return component.get("Web.PluginManager").get_plugin_info(name)

    @export
    def get_plugin_resources(self, name):
        return component.get("Web.PluginManager").get_plugin_resources(name)

    @export
    def upload_plugin(self, filename, path):
        main_deferred = Deferred()

        shutil.copyfile(path, os.path.join(get_config_dir(), "plugins", filename))
        component.get("Web.PluginManager").scan_for_plugins()

        if client.is_localhost():
            client.core.rescan_plugins()
            return True

        with open(path, "rb") as _file:
            plugin_data = base64.encodestring(_file.read())

        def on_upload_complete(*args):
            client.core.rescan_plugins()
            component.get("Web.PluginManager").scan_for_plugins()
            main_deferred.callback(True)

        def on_upload_error(*args):
            main_deferred.callback(False)

        d = client.core.upload_plugin(filename, plugin_data)
        d.addCallback(on_upload_complete)
        d.addErrback(on_upload_error)
        return main_deferred

    @export
    def register_event_listener(self, event):
        """
        Add a listener to the event queue.

        :param event: The event name
        :type event: string
        """
        self.event_queue.add_listener(__request__.session_id, event)

    @export
    def deregister_event_listener(self, event):
        """
        Remove an event listener from the event queue.

        :param event: The event name
        :type event: string
        """
        self.event_queue.remove_listener(__request__.session_id, event)

    @export
    def get_events(self):
        """
        Retrieve the pending events for the session.
        """
        return self.event_queue.get_events(__request__.session_id)
