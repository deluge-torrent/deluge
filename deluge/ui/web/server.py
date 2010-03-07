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
from twisted.internet import reactor, defer, error
from twisted.internet.ssl import SSL
from twisted.web import http, resource, server, static

from deluge import common, component, configmanager
from deluge.core.rpcserver import check_ssl_keys
from deluge.log import setupLogger, LOG as _log
from deluge.ui import common as uicommon
from deluge.ui.tracker_icons import TrackerIcons
from deluge.ui.web.auth import Auth
from deluge.ui.web.common import Template, compress
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
    # Misc Settings
    "enabled_plugins": [],
    "default_daemon": "",

    # Auth Settings
    "pwd_salt": "c26ab3bbd8b137f99cd83c2c1c0963bcc1a35cad",
    "pwd_sha1": "2ce1a410bcdcc53064129b6d950f2e9fee4edc1e",
    "session_timeout": 3600,
    "sessions": {},

    # UI Settings
    "sidebar_show_zero": False,
    "sidebar_show_trackers": False,
    "show_session_speed": False,
    "show_sidebar": True,
    "theme": "gray",

    # Server Settings
    "port": 8112,
    "https": False,
    "pkey": "ssl/daemon.pkey",
    "cert": "ssl/daemon.cert"
}

UI_CONFIG_KEYS = (
    "theme", "sidebar_show_zero", "sidebar_show_trackers",
    "show_session_speed"
)

OLD_CONFIG_KEYS = (
    "port", "enabled_plugins", "base", "sidebar_show_zero",
    "sidebar_show_trackers", "show_keyword_search", "show_sidebar",
    "https"
)

def rpath(*paths):
    """Convert a relative path into an absolute path relative to the location
    of this script.
    """
    return os.path.join(current_dir, *paths)

class Config(resource.Resource):
    """
    Writes out a javascript file that contains the WebUI configuration
    available as Deluge.Config.
    """

    def render(self, request):
        web_config = component.get("Web").get_config()
        config = dict([(key, web_config[key]) for key in UI_CONFIG_KEYS])
        return compress("""Deluge = {
    author: 'Damien Churchill <damoxc@gmail.com>',
    version: '1.2-dev',
    config: %s
}""" % common.json.dumps(config), request)

class GetText(resource.Resource):
    def render(self, request):
        request.setHeader("content-type", "text/javascript; encoding=utf-8")
        template = Template(filename=rpath("gettext.js"))
        return compress(template.render(), request)

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
            return common.json.dumps({
                'success': True,
                'files': []
            })

        tempdir = tempfile.mkdtemp(prefix="delugeweb-")

        filenames = []
        for upload in request.args.get("file"):
            fd, fn = tempfile.mkstemp('.torrent', dir=tempdir)
            os.write(fd, upload)
            os.close(fd)
            filenames.append(fn)
        request.setHeader("content-type", "text/html")
        request.setResponseCode(http.OK)
        return common.json.dumps({
            'success': True,
            'files': filenames
        })

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
        return compress(template.render(), request)

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
            elif filename.endswith(".png"):
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

        self.__paths = {}
        for directory in directories:
            self.addDirectory(directory)

    def addDirectory(self, directory, path=""):
        log.debug("Adding directory `%s` with path `%s`", directory, path)
        paths = self.__paths.setdefault(path, [])
        paths.append(directory)

    def removeDirectory(self, directory, path=""):
        log.debug("Removing directory `%s`", directory)
        self.__paths[path].remove(directory)

    def getChild(self, path, request):
        if hasattr(request, 'lookup_path'):
            request.lookup_path = os.path.join(request.lookup_path, path)
        else:
            request.lookup_path = path
        return self

    def render(self, request):
        log.debug("Requested path: '%s'", request.lookup_path)
        path = os.path.dirname(request.lookup_path)

        if path not in self.__paths:
            request.setResponseCode(http.NOT_FOUND)
            return "<h1>404 - Not Found</h1>"

        filename = os.path.basename(request.path)
        for directory in self.__paths[path]:
            if filename in os.listdir(directory):
                path = os.path.join(directory, filename)
                log.debug("Serving path: '%s'", path)
                mime_type = mimetypes.guess_type(path)
                request.setHeader("content-type", mime_type[0])
                return compress(open(path, "rb").read(), request)

        request.setResponseCode(http.NOT_FOUND)
        return "<h1>404 - Not Found</h1>"

class TopLevel(resource.Resource):
    addSlash = True

    __stylesheets = [
        "/css/ext-all-notheme.css",
        "/css/ext-extensions.css",
        "/css/deluge.css"
    ]

    __scripts = [
        "/js/ext-base.js",
        "/js/ext-all.js",
        "/js/ext-extensions.js",
        "/config.js",
        "/gettext.js",
        "/js/deluge-all.js"
    ]

    __debug_scripts = [
        "/js/ext-base-debug.js",
        "/js/ext-all-debug.js",
        "/js/ext-extensions-debug.js",
        "/config.js",
        "/gettext.js",
        "/js/deluge-all-debug.js"
    ]

    __dev_scripts = [
        "/js/ext-base-debug.js",
        "/js/ext-all-debug.js",
        "/js/ext-extensions/BufferView.js",
        "/js/ext-extensions/FileUploadField.js",
        "/js/ext-extensions/JSLoader.js",
        "/js/ext-extensions/Spinner.js",
        "/js/ext-extensions/SpinnerField.js",
        "/js/ext-extensions/StatusBar.js",
        "/js/ext-extensions/ToggleField.js",
        "/js/ext-extensions/TreeGridSorter.js",
        "/js/ext-extensions/TreeGridColumnResizer.js",
        "/js/ext-extensions/TreeGridNodeUI.js",
        "/js/ext-extensions/TreeGridLoader.js",
        "/js/ext-extensions/TreeGridColumns.js",
        "/js/ext-extensions/TreeGridRenderColumn.js",
        "/js/ext-extensions/TreeGrid.js",
        "/config.js",
        "/gettext.js",
        "/js/deluge-all/Deluge.js",
        "/js/deluge-all/Deluge.Formatters.js",
        "/js/deluge-all/Deluge.Menus.js",
        "/js/deluge-all/Deluge.Events.js",
        "/js/deluge-all/Deluge.OptionsManager.js",
        "/js/deluge-all/Deluge.MultiOptionsManager.js",
        "/js/deluge-all/Deluge.Add.js",
        "/js/deluge-all/Deluge.Add.File.js",
        "/js/deluge-all/Deluge.Add.Url.js",
        "/js/deluge-all/Deluge.Add.Infohash.js",
        "/js/deluge-all/Deluge.Client.js",
        "/js/deluge-all/Deluge.ConnectionManager.js",
        "/js/deluge-all/Deluge.Details.js",
        "/js/deluge-all/Deluge.Details.Status.js",
        "/js/deluge-all/Deluge.Details.Details.js",
        "/js/deluge-all/Deluge.Details.Files.js",
        "/js/deluge-all/Deluge.Details.Peers.js",
        "/js/deluge-all/Deluge.Details.Options.js",
        "/js/deluge-all/Deluge.EditTrackers.js",
        "/js/deluge-all/Deluge.FileBrowser.js",
        "/js/deluge-all/Deluge.Keys.js",
        "/js/deluge-all/Deluge.Login.js",
        "/js/deluge-all/Deluge.MoveStorage.js",
        "/js/deluge-all/Deluge.Plugin.js",
        "/js/deluge-all/Deluge.Preferences.js",
        "/js/deluge-all/Deluge.Preferences.Downloads.js",
        #"/js/deluge-all/Deluge.Preferences.Network.js",
        "/js/deluge-all/Deluge.Preferences.Encryption.js",
        "/js/deluge-all/Deluge.Preferences.Bandwidth.js",
        "/js/deluge-all/Deluge.Preferences.Interface.js",
        "/js/deluge-all/Deluge.Preferences.Other.js",
        "/js/deluge-all/Deluge.Preferences.Daemon.js",
        "/js/deluge-all/Deluge.Preferences.Queue.js",
        "/js/deluge-all/Deluge.Preferences.Proxy.js",
        "/js/deluge-all/Deluge.Preferences.Cache.js",
        "/js/deluge-all/Deluge.Preferences.Plugins.js",
        "/js/deluge-all/Deluge.Remove.js",
        "/js/deluge-all/Deluge.Sidebar.js",
        "/js/deluge-all/Deluge.Statusbar.js",
        "/js/deluge-all/Deluge.Toolbar.js",
        "/js/deluge-all/Deluge.Torrent.js",
        "/js/deluge-all/Deluge.Torrents.js",
        "/js/deluge-all/Deluge.UI.js"
    ]

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild("config.js", Config())
        self.putChild("css", LookupResource("Css", rpath("css")))
        self.putChild("gettext.js", GetText())
        self.putChild("flag", Flag())
        self.putChild("icons", LookupResource("Icons", rpath("icons")))
        self.putChild("images", LookupResource("Images", rpath("images")))

        # Add the javascript resource with the development paths
        js = LookupResource("Javascript", rpath("js"))
        js.addDirectory(rpath("js", "ext-extensions"), "ext-extensions")
        js.addDirectory(rpath("js", "deluge-all"), "deluge-all")
        self.putChild("js", js)

        self.putChild("json", JSON())
        self.putChild("upload", Upload())
        self.putChild("render", Render())
        self.putChild("themes", static.File(rpath("themes")))
        self.putChild("tracker", Tracker())

        theme = component.get("DelugeWeb").config["theme"]
        if not os.path.isfile(rpath("css", "xtheme-%s.css" % theme)):
            theme = CONFIG_DEFAULTS.get("theme")
        self.__stylesheets.insert(1, "/css/xtheme-%s.css" % theme)


    @property
    def scripts(self):
        return self.__scripts

    @property
    def debug_scripts(self):
        return self.__debug_scripts

    @property
    def dev_scripts(self):
        return self.__dev_scripts

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
        debug = False
        if 'debug' in request.args:
            debug_arg = request.args.get('debug')[-1]
            if debug_arg in ('true', 'yes', '1'):
                debug = True
            else:
                debug = False

        dev = 'dev' in common.get_version()
        if 'dev' in request.args:
            dev_arg = request.args.get('dev')[-1]
            if dev_arg in ('true', 'yes' '1'):
                dev = True
            else:
                dev = False

        if dev:
            scripts = self.dev_scripts[:]
        elif debug:
            scripts = self.debug_scripts[:]
        else:
            scripts = self.scripts[:]

        base = request.args.get('base', [''])[-1]
        template = Template(filename=rpath("index.html"))
        request.setHeader("content-type", "text/html; charset=utf-8")
        return template.render(scripts=scripts, stylesheets=self.stylesheets, debug=debug, base=base)

class ServerContextFactory:

    def getContext(self):
        """Creates an SSL context."""
        ctx = SSL.Context(SSL.SSLv3_METHOD)
        deluge_web = component.get("DelugeWeb")
        log.debug("Enabling SSL using:")
        log.debug("Pkey: %s", deluge_web.pkey)
        log.debug("Cert: %s", deluge_web.cert)
        ctx.use_privatekey_file(configmanager.get_config_dir(deluge_web.pkey))
        ctx.use_certificate_file(configmanager.get_config_dir(deluge_web.cert))
        return ctx

class DelugeWeb(component.Component):

    def __init__(self):
        super(DelugeWeb, self).__init__("DelugeWeb")
        self.config = configmanager.ConfigManager("web.conf", CONFIG_DEFAULTS)

        # Check to see if a configuration from the web interface prior to 1.2
        # exists and convert it over.
        if os.path.exists(configmanager.get_config_dir("webui06.conf")):
            old_config = configmanager.ConfigManager("webui06.conf")
            if old_config.config:
                # we have an old config file here to handle so we should move
                # all the values across to the new config file, and then remove
                # it.
                for key in OLD_CONFIG_KEYS:
                    if key in old_config:
                        self.config[key] = old_config[key]

                # We need to base64 encode the passwords since json can't handle
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

        self.socket = None
        self.top_level = TopLevel()
        self.site = server.Site(self.top_level)
        self.port = self.config["port"]
        self.https = self.config["https"]
        self.pkey = self.config["pkey"]
        self.cert = self.config["cert"]
        self.web_api = WebApi()
        self.auth = Auth()

        # Initalize the plugins
        self.plugins = PluginManager()

    def install_signal_handlers(self):
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

    def start(self, start_reactor=True):
        log.info("%s %s.", _("Starting server in PID"), os.getpid())
        if self.https:
            self.start_ssl()
        else:
            self.start_normal()

        component.get("JSON").enable()

        if start_reactor:
            reactor.run()

    def start_normal(self):
        self.socket = reactor.listenTCP(self.port, self.site)
        log.info("serving on %s:%s view at http://127.0.0.1:%s", "0.0.0.0",
            self.port, self.port)

    def start_ssl(self):
        check_ssl_keys()
        self.socket = reactor.listenSSL(self.port, self.site, ServerContextFactory())
        log.info("serving on %s:%s view at https://127.0.0.1:%s", "0.0.0.0",
            self.port, self.port)

    def stop(self):
        log.info("Shutting down webserver")
        self.plugins.disable_plugins()
        log.debug("Saving configuration file")
        self.config.save()

        if self.socket:
            d = self.socket.stopListening()
            self.socket = None
        else:
            d = defer.Deferred()
            d.callback(False)
        return d

    def shutdown(self, *args):
        self.stop()
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
