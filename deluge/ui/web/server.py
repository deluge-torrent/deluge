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

import os
import time
import locale
import shutil
import urllib
import gettext
import hashlib
import logging
import tempfile
import mimetypes
import pkg_resources

from twisted.application import service, internet
from twisted.internet import reactor, error
from twisted.internet.ssl import SSL
from twisted.web import http, resource, server, static

from deluge import common, component
from deluge.configmanager import ConfigManager
from deluge.log import setupLogger, LOG as _log
from deluge.ui import common as uicommon
from deluge.ui.tracker_icons import TrackerIcons
from deluge.ui.web.auth import Auth
from deluge.ui.web.common import Template
from deluge.ui.web.json_api import JSON, WebApi
from deluge.ui.web.pluginmanager import PluginManager
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
    "enabled_plugins": [],
    "theme": "slate",
    "pwd_salt": "c26ab3bbd8b137f99cd83c2c1c0963bcc1a35cad",
    "pwd_sha1": "2ce1a410bcdcc53064129b6d950f2e9fee4edc1e",
    "base": "",
    "sessions": {},
    "sidebar_show_zero": False,
    "sidebar_show_trackers": False,
    "show_keyword_search": False,
    "show_sidebar": True,
    "cache_templates": False,
    "https": False,
    "pkey": "ssl/daemon.pkey",
    "cert": "ssl/daemon.cert"
}

OLD_CONFIG_KEYS = (
    "port", "enabled_plugins", "base", "sidebar_show_zero",
    "sidebar_show_trackers", "show_keyword_search", "show_sidebar",
    "cache_templates", "https"
)

def rpath(path):
    """Convert a relative path into an absolute path relative to the location
    of this script.
    """
    return os.path.join(current_dir, path)

class Config(resource.Resource):
    """
    Writes out a javascript file that contains the WebUI configuration
    available as Deluge.Config.
    """

    def render(self, request):
        return """Deluge = {
    author: 'Damien Churchill <damoxc@gmail.com>',
    version: '1.2-dev',
    config: %s
}""" % common.json.dumps(component.get("DelugeWeb").config.config)

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

class LookupResource(resource.Resource, component.Component):

    def __init__(self, name, *directories):
        resource.Resource.__init__(self)
        component.Component.__init__(self, name)
        self.__directories = list(directories)

    @property
    def directories(self):
        return self.__directories

    def getChild(self, path, request):
        request.path = path
        return self

    def render(self, request):
        log.debug("Requested path: '%s'", request.path)
        for lookup in self.directories:
            if request.path in os.listdir(lookup):
                path = os.path.join(lookup, request.path)
                log.debug("Serving path: '%s'", path)
                mime_type = mimetypes.guess_type(path)
                request.setHeader("content-type", mime_type[0])
                return open(path, "rb").read()
        request.setResponseCode(http.NOT_FOUND)
        return "<h1>404 - Not Found</h1>"

class TopLevel(resource.Resource):
    addSlash = True

    __stylesheets = [
        "/css/ext-all.css",
        "/css/ext-extensions.css",
        "/css/deluge.css"
    ]

    __scripts = [
        "/js/ext-base.js",
        "/js/ext-all.js",
        "/js/ext-extensions.js",
        "/config.js",
        "/gettext.js",
        "/js/deluge-yc.js"
    ]

    __debug_scripts = [
        "/js/ext-base.js",
        "/js/ext-all-debug.js",
        "/js/ext-extensions-debug.js",
        "/config.js",
        "/gettext.js",
        "/js/Deluge.js",
        "/js/Deluge.Formatters.js",
        "/js/Deluge.Menus.js",
        "/js/Deluge.Events.js",
        "/js/Deluge.OptionsManager.js",
        "/js/Deluge.Add.js",
        "/js/Deluge.Add.File.js",
        "/js/Deluge.Add.Url.js",
        "/js/Deluge.Add.Infohash.js",
        "/js/Deluge.Client.js",
        "/js/Deluge.ConnectionManager.js",
        "/js/Deluge.Details.js",
        "/js/Deluge.Details.Status.js",
        "/js/Deluge.Details.Details.js",
        "/js/Deluge.Details.Files.js",
        "/js/Deluge.Details.Peers.js",
        "/js/Deluge.Details.Options.js",
        "/js/Deluge.EditTrackers.js",
        "/js/Deluge.Keys.js",
        "/js/Deluge.Login.js",
        "/js/Deluge.Preferences.js",
        "/js/Deluge.Preferences.Downloads.js",
        "/js/Deluge.Preferences.Network.js",
        "/js/Deluge.Preferences.Bandwidth.js",
        "/js/Deluge.Preferences.Interface.js",
        "/js/Deluge.Preferences.Other.js",
        "/js/Deluge.Preferences.Daemon.js",
        "/js/Deluge.Preferences.Queue.js",
        "/js/Deluge.Preferences.Proxy.js",
        "/js/Deluge.Preferences.Notification.js",
        "/js/Deluge.Preferences.Plugins.js",
        "/js/Deluge.Sidebar.js",
        "/js/Deluge.Statusbar.js",
        "/js/Deluge.Toolbar.js",
        "/js/Deluge.Torrents.js",
        "/js/Deluge.UI.js"
    ]

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild("config.js", Config())
        self.putChild("css", LookupResource("Css", rpath("css")))
        self.putChild("gettext.js", GetText())
        self.putChild("flag", Flag())
        self.putChild("icons", LookupResource("Icons", rpath("icons")))
        self.putChild("images", LookupResource("Images", rpath("images")))
        self.putChild("js", LookupResource("Javascript", rpath("js")))
        self.putChild("json", JSON())
        self.putChild("upload", Upload())
        self.putChild("render", Render())
        self.putChild("themes", static.File(rpath("themes")))
        self.putChild("tracker", Tracker())

        theme = component.get("DelugeWeb").config["theme"]
        self.__stylesheets.insert(1, "/css/xtheme-%s.css" % theme)

    @property
    def scripts(self):
        return self.__scripts

    @property
    def debug_scripts(self):
        return self.__debug_scripts

    @property
    def stylesheets(self):
        return self.__stylesheets
    
    def add_script(self, script):
        """
        Adds a script to the server so it is included in the <head> element
        of the index page.
        
        :param script: The path to the script
        :type script: string
        """
        
        self.__scripts.append(script)
        self.__debug_scripts.append(script)
    
    def remove_script(self, script):
        """
        Removes a script from the server.
        
        :param script: The path to the script
        :type script: string
        """
        self.__scripts.remove(script)
        self.__debug_scripts.remove(script)
        

    def getChild(self, path, request):
        if path == "":
            return self
        else:
            return resource.Resource.getChild(self, path, request)

    def render(self, request):
        if request.args.get('debug', ['false'])[-1] == 'true':
            scripts = self.debug_scripts[:]
        else:
            scripts = self.scripts[:]

        template = Template(filename=rpath("index.html"))
        request.setHeader("content-type", "text/html; charset=utf-8")
        return template.render(scripts=scripts, stylesheets=self.stylesheets)

class ServerContextFactory:
    
    def getContext(self):
        """Creates an SSL context."""
        ctx = SSL.Context(SSL.SSLv3_METHOD)
        deluge_web = component.get("DelugeWeb")
        log.debug("Enabling SSL using:")
        log.debug("Pkey: %s", deluge_web.pkey)
        log.debug("Cert: %s", deluge_web.cert)
        ctx.use_privatekey_file(common.get_default_config_dir(deluge_web.pkey))
        ctx.use_certificate_file(common.get_default_config_dir(deluge_web.cert))
        return ctx

class DelugeWeb(component.Component):

    def __init__(self):
        super(DelugeWeb, self).__init__("DelugeWeb")
        self.config = ConfigManager("web.conf", CONFIG_DEFAULTS)
        
        old_config = ConfigManager("webui06.conf")
        if old_config.config:
            # we have an old config file here to handle so we should move
            # all the values across to the new config file, and then remove
            # it.
            for key in OLD_CONFIG_KEYS:
                self.config[key] = old_config[key]
            
            # We need to base64 encode the passwords since utf-8 can't handle
            # them otherwise.
            from base64 import encodestring
            self.config["old_pwd_md5"] = encodestring(old_config["pwd_md5"])
            self.config["old_pwd_salt"] = encodestring(old_config["pwd_salt"])
            
            # Save our config and if it saved successfully then rename the
            # old configuration file.
            if self.config.save():
                config_dir = os.path.dirname(old_config.config_file)
                backup_path = os.path.join(config_dir, 'web.conf.old')
                os.rename(old_config.config_file, backup_path)
                del old_config

        self.top_level = TopLevel()
        self.site = server.Site(self.top_level)
        self.port = self.config["port"]
        self.https = self.config["https"]
        self.pkey = self.config["pkey"]
        self.cert = self.config["cert"]
        self.web_api = WebApi()
        self.auth = Auth()

        # Since twisted assigns itself all the signals may as well make
        # use of it.
        reactor.addSystemEventTrigger("after", "shutdown", self.shutdown)

        # Twisted doesn't handle windows specific signals so we still
        # need to attach to those to handle the close correctly.
        if common.windows_check():
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT, CTRL_SHUTDOWN_EVENT
            def win_handler(ctrl_type):
                log.debug("ctrl type: %s", ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or \
                   ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self.shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)

        # Initalize the plugins
        self.plugins = PluginManager()

    def start(self):
        log.info("%s %s.", _("Starting server in PID"), os.getpid())
        reactor.listenTCP(self.port, self.site)
        log.info("serving on %s:%s view at http://127.0.0.1:%s", "0.0.0.0",
            self.port, self.port)
        self.plugins.enable_plugins()
        reactor.run()
    
    def start_ssl(self):
        log.info("%s %s.", _("Starting server in PID"), os.getpid())
        reactor.listenSSL(self.port, self.site, ServerContextFactory())
        log.info("serving on %s:%s view at https://127.0.0.1:%s", "0.0.0.0",
            self.port, self.port)
        self.plugins.enable_plugins()
        reactor.run()

    def shutdown(self, *args):
        log.info("Shutting down webserver")
        self.plugins.disable_plugins()
        log.debug("Saving configuration file")
        self.config.save()
        try:
            reactor.stop()
        except error.ReactorNotRunning:
            log.debug("Reactor not running")

if __name__ == "__builtin__":
    deluge_web = DelugeWeb()
    application = service.Application("DelugeWeb")
    sc = service.IServiceCollection(application)
    i = internet.TCPServer(deluge_web.port, deluge_web.site)
    i.setServiceParent(sc)
elif __name__ == "__main__":
    deluge_web = DelugeWeb()
    deluge_web.start()
