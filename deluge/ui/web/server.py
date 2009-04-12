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
import signal
import urllib
import gettext
import hashlib
import logging
import tempfile
import pkg_resources

from twisted.application import service, internet
from twisted.internet import reactor
from twisted.web import http, resource, server, static

from deluge import common, component
from deluge.configmanager import ConfigManager
from deluge.log import setupLogger, LOG as _log
from deluge.ui import common as uicommon
from deluge.ui.tracker_icons import TrackerIcons
from deluge.ui.web.common import Template
from deluge.ui.web.json_api import JSON, WebApi
log = logging.getLogger(__name__)

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
    "template": "slate",
    "pwd_salt": "16f65d5c79b7e93278a28b60fed2431e",
    "pwd_md5": "2c9baa929ca38fb5c9eb5b054474d1ce",
    "base": "",
    "sessions": [],
    "sidebar_show_zero": False,
    "sidebar_show_trackers": False,
    "show_keyword_search": False,
    "show_sidebar": True,
    "https": False
}

def rpath(path):
    """Convert a relative path into an absolute path relative to the location
    of this script.
    """
    return os.path.join(current_dir, path)

class GetText(resource.Resource):
    def render(self, request):
        request.setHeader("content-type", "text/javascript; encoding=utf-8")
        template = Template(filename=rpath("gettext.js"))
        return template.render()

class Upload(resource.Resource):
    """
    Twisted Web resource to handle file uploads
    """
    
    def render(self, request):
        """
        Saves all uploaded files to the disk and returns a list of filenames,
        each on a new line.
        """
        
        # Block all other HTTP methods.
        if request.method != "POST":
            request.setResponseCode(http.NOT_ALLOWED)
            return ""
        
        if "file" not in request.args:
            request.setResponseCode(http.OK)
            return ""
        
        tempdir = os.path.join(tempfile.gettempdir(), "delugeweb")
        if not os.path.isdir(tempdir):
            os.mkdir(tempdir)

        filenames = []
        for upload in request.args.get("file"):
            fd, fn = tempfile.mkstemp('.torrent', dir=tempdir)
            os.write(fd, upload)
            os.close(fd)
            filenames.append(fn)
        request.setHeader("content-type", "text/plain")
        request.setResponseCode(http.OK)
        return "\n".join(filenames)

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
            request.setHeader("cache-control",
                              "public, must-revalidate, max-age=86400")
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
            request.setHeader("cache-control",
                              "public, must-revalidate, max-age=86400")
            request.setHeader("content-type", "image/png")
            data = open(filename, "rb")
            request.setResponseCode(http.OK)
            return data.read()
        else:
            request.setResponseCode(http.NOT_FOUND)
            return ""

class Icons(resource.Resource):
    def getChild(self, path, request):
        request.icon = path
        return self
    
    def render(self, request):
        headers = {}
        print request.icon
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
        self.putChild("themes", static.File(rpath("themes")))
        self.putChild("tracker", Tracker())
    
    def getChild(self, path, request):
        if path == "":
            return self
        else:
            return resource.Resource.getChild(self, path, request)

    def render(self, request):
        debug = request.args.get('debug', ['false'])[-1] == 'true'
        template = Template(filename=rpath("index.html"))
        request.setHeader("content-type", "text/html; charset=utf-8")
        return template.render(debug=debug)

class DelugeWeb(component.Component):
    def __init__(self):
        super(DelugeWeb, self).__init__("DelugeWeb")
        self.site = server.Site(TopLevel())
        self.config = ConfigManager("web.conf", CONFIG_DEFAULTS)
        self.port = self.config["port"]
        self.web_api = WebApi()
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        if not common.windows_check():
            signal.signal(signal.SIGHUP, self.shutdown)
        else:
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT
            from win32con import CTRL_SHUTDOWN_EVENT
            def win_handler(ctrl_type):
                log.debug("ctrl_type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or \
                   ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self.__shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)
    
    def start(self):
        log.info("%s %s.", _("Starting server in PID"), os.getpid())
        reactor.listenTCP(self.port, self.site)
        log.info("serving on %s:%s view at http://127.0.0.1:%s", "0.0.0.0",
            self.port, self.port)
        reactor.run()

    def shutdown(self, *args):
        log.info("Shutting down webserver")
        self.config.save()
        reactor.stop()

if __name__ == "__builtin__":
    deluge_web = DelugeWeb()
    application = service.Application("DelugeWeb")
    sc = service.IServiceCollection(application)
    i = internet.TCPServer(deluge_web.port, deluge_web.site)
    i.setServiceParent(sc)
elif __name__ == "__main__":
    deluge_web = DelugeWeb()
    deluge_web.start()
