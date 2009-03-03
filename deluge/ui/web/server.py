#
# deluge/ui/web/webui.py
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
import locale
import shutil
import urllib
import gettext
import hashlib
import logging
import tempfile
import pkg_resources

from twisted.application import service, internet
from twisted.internet.defer import Deferred
from twisted.web import http, resource, server, static

from mako.template import Template as MakoTemplate

from deluge import common
from deluge.configmanager import ConfigManager
from deluge.log import setupLogger, LOG as _log
from deluge.ui import common as uicommon
from deluge.ui.client import client, Client
from deluge.ui.tracker_icons import TrackerIcons
log = logging.getLogger(__name__)
json = common.json

# Initialize gettext
try:
    locale.setlocale(locale.LC_ALL, "")
    if hasattr(locale, "bindtextdomain"):
        locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    if hasattr(locale, "textdomain"):
        locale.textdomain("deluge")
    gettext.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    gettext.textdomain("deluge")
    gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"))
except Exception, e:
    log.error("Unable to initialize gettext/locale: %s", e)

_ = gettext.gettext

current_dir = os.path.dirname(__file__)

CONFIG_DEFAULTS = {
    "port": 8112,
    "button_style": 2,
    "auto_refresh": False,
    "auto_refresh_secs": 10,
    "template": "white",
    "pwd_salt": "2\xe8\xc7\xa6(n\x81_\x8f\xfc\xdf\x8b\xd1\x1e\xd5\x90",
    "pwd_md5": ".\xe8w\\+\xec\xdb\xf2id4F\xdb\rUc",
    "cache_templates": True,
    "connections": [],
    "daemon": "http://localhost:58846",
    "base": "",
    "disallow": {},
    "sessions": [],
    "sidebar_show_zero": False,
    "sidebar_show_trackers": False,
    "show_keyword_search": False,
    "show_sidebar": True,
    "https": False,
    "refresh_secs": 10
}

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 58846
DEFAULT_HOSTS = {
    "hosts": [(hashlib.sha1(str(time.time())).hexdigest(), DEFAULT_HOST, DEFAULT_PORT, "", "")]
}

HOSTLIST_COL_ID = 0
HOSTLIST_COL_HOST = 1
HOSTLIST_COL_PORT = 2
HOSTLIST_COL_STATUS = 3
HOSTLIST_COL_USER = 4
HOSTLIST_COL_PASS = 5
HOSTLIST_COL_VERSION = 6

config = ConfigManager("webui06.conf", CONFIG_DEFAULTS)
hostlist = ConfigManager("hostlist.conf.1.2", DEFAULT_HOSTS)

def rpath(path):
    """Convert a relative path into an absolute path relative to the location
    of this script.
    """
    return os.path.join(current_dir, path)

class Template(MakoTemplate):
    
    builtins = {
        "_": _,
        "version": common.get_version()
    }
    
    def render(self, *args, **data):
        data.update(self.builtins)
        return MakoTemplate.render(self, *args, **data)

class JSONException(Exception):
    def __init__(self, inner_exception):
        self.inner_exception = inner_exception
        Exception.__init__(self, str(inner_exception))

class JSON(resource.Resource):
    """
    A Twisted Web resource that exposes a JSON-RPC interface for web clients
    to use.
    """
    
    def __init__(self):
        resource.Resource.__init__(self)
        self._remote_methods = []
        self._local_methods = {
            "web.update_ui": self.update_ui,
            "web.download_torrent_from_url": self.download_torrent_from_url,
            "web.get_torrent_info": self.get_torrent_info,
            "web.add_torrents": self.add_torrents,
            "web.login": self.login,
            "web.get_hosts": self.get_hosts,
            "web.connect": self.connect,
            "web.connected": self.connected
        }
    
    def _connect(self, host="localhost", port=58846, username="", password=""):
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
    
    def connect(self, host_id):
        d = Deferred()
        def on_connected(methods):
            d.callback(methods)
        for host in hostlist["hosts"]:
            if host_id != host[0]:
                continue
            self._connect(*host[1:]).addCallback(on_connected)
        return d
    
    def connected(self):
        d = Deferred()
        d.callback(client.connected())
        return d
    
    def update_ui(self, keys, filter_dict):

        ui_info = {
            "torrents": None,
            "filters": None,
            "stats": None
        }
        
        d = Deferred()
        
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
    
    def login(self, password):
        """Method to allow the webui to authenticate
        """
        m = hashlib.md5()
        m.update(config['pwd_salt'])
        m.update(password)
        d = Deferred()
        d.callback(m.digest() == config['pwd_md5'])
        return d
    
    def get_hosts(self):
        """Return the hosts in the hostlist"""
        hosts = dict((host[0], host[:]) for host in hostlist["hosts"])
        
        main_deferred = Deferred()
        def run_check():
            if all(map(lambda x: x[3] is not None, hosts.values())):
                main_deferred.callback(hosts.values())
        
        def on_connect(result, c, host_id):
            def on_info(info, c):
                hosts[host_id][3] = _("Online")
                hosts[host_id][4] = info
                c.disconnect()
                run_check()
            
            def on_info_fail(reason):
                hosts[host_id][3] = _("Offline")
                run_check()
            
            d = c.daemon.info()
            d.addCallback(on_info, c)
            d.addErrback(on_info_fail, c)
            
        def on_connect_failed(reason, host_id):
            log.exception(reason)
            hosts[host_id][3] = _("Offline")
            run_check()
        
        for host in hosts.values():
            host_id, host, port, user, password = host[0:5]
            hosts[host_id][3:4] = (None, None)
            
            if client.connected() and (host, port, user) == client.connection_info():
                def on_info(info):
                    hosts[host_id][4] = info
                    run_check()
                host[5] = _("Connected")
                client.daemon.info().addCallback(on_info)
                hosts[host_id] = host
                continue
            
            c = Client()
            d = c.connect(host, port, user, password)
            d.addCallback(on_connect, c, host_id)
            d.addErrback(on_connect_failed, host_id)
        return main_deferred

class GetText(resource.Resource):
    def render(self, request):
        request.setHeader("content-type", "text/javascript")
        template = Template(filename=rpath("gettext.js"))
        return template.render()

class Upload(resource.Resource):
    """
    Twisted Web resource to handle file uploads
    """
    
    def http_POST(self, request):
        """
        Saves all uploaded files to the disk and returns a list of filenames,
        each on a new line.
        """
        tempdir = os.path.join(tempfile.gettempdir(), "delugeweb")
        if not os.path.isdir(tempdir):
            os.mkdir(tempdir)

        filenames = []
        for files in request.files.values():
            for upload in files:
                fn = os.path.join(tempdir, upload[0])
                f = open(fn, upload[2].mode)
                shutil.copyfileobj(upload[2], f)
                filenames.append(fn)
        return http.Response(http.OK, stream="\n".join(filenames))
    
    def render(self, request):
        """
        Block all other HTTP methods.
        """
        return http.Response(http.NOT_ALLOWED)

class Render(resource.Resource):

    def getChild(self, path, request):
        request.render_file = path
        return self
    
    def render(self, request):
        if not hasattr(request, "render_file"):
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            return ""

        filename = os.path.join("render", request.render_file)
        template = Template(filename=rpath(filename))
        request.setHeader("content-type", "text/html")
        request.setResponseCode(http.OK)
        return template.render()

class Tracker(resource.Resource):
    tracker_icons = TrackerIcons()
    
    def getChild(self, path, request):
        request.tracker_name = path
        return self
    
    def render(self, request):
        headers = {}
        filename = self.tracker_icons.get(request.tracker_name)
        if filename:
            request.setHeader("cache-control", "public, must-revalidate, max-age=86400")
            if filename.endswith(".ico"):
                request.setHeader("content-type", "image/x-icon")
            elif filename.endwith(".png"):
                request.setHeader("content-type", "image/png")
            data = open(filename, "rb")
            request.setResponseCode(http.OK)
            return data.read()
        else:
            request.setResponseCode(http.NOT_FOUND)
            return ""

class Flag(resource.Resource):
    def getChild(self, path, request):
        request.country = path
        return self
    
    def render(self, request):
        headers = {}
        path = ("data", "pixmaps", "flags", request.country.lower() + ".png")
        filename = pkg_resources.resource_filename("deluge",
                                                   os.path.join(*path))
        if os.path.exists(filename):
            request.setHeader("cache-control", "public, must-revalidate, max-age=86400")
            request.setHeader("content-type", "image/png")
            data = open(filename, "rb")
            request.setResponseCode(http.OK)
            return data.read()
        else:
            request.setResponseCode(http.NOT_FOUND)
            return ""

class TopLevel(resource.Resource):
    addSlash = True
    
    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild("css", static.File(rpath("css")))
        self.putChild("gettext.js", GetText())
        self.putChild("flag", Flag())
        self.putChild("icons", static.File(rpath("icons")))
        self.putChild("images", static.File(rpath("images")))
        self.putChild("js", static.File(rpath("js")))
        self.putChild("json", JSON())
        self.putChild("upload", Upload())
        self.putChild("render", Render())
        self.putChild("test", static.File(rpath("test.html")))
        self.putChild("themes", static.File(rpath("themes")))
        self.putChild("tracker", Tracker())
    
    def getChild(self, path, request):
        if path == "":
            return self
        else:
            return resource.Resource.getChild(self, path, request)

    def render(self, request):
        template = Template(filename=rpath("index.html"))
        request.setHeader("content-type", "text/html; charset=utf-8")
        return template.render()

class DelugeWeb:
    def __init__(self):
        self.site = server.Site(TopLevel())
        self.port = config["port"]

if __name__ == "__builtin__":
    deluge_web = DelugeWeb()
    application = service.Application("DelugeWeb")
    sc = service.IServiceCollection(application)
    i = internet.TCPServer(deluge_web.port, deluge_web.site)
    i.setServiceParent(sc)
elif __name__ == "__main__":
    from twisted.internet import reactor
    deluge_web = DelugeWeb()
    reactor.listenTCP(deluge_web.port, deluge_web.site)
    reactor.run()