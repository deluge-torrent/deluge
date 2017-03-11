#
# deluge/ui/web/server.py
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
import locale
import shutil
import urllib
import fnmatch
import gettext
import hashlib
import logging
import tempfile
import mimetypes
import pkg_resources

from OpenSSL.crypto import FILETYPE_PEM
from twisted.application import service, internet
from twisted.internet import reactor, defer, error
from twisted.internet.ssl import SSL, Certificate, CertificateOptions, KeyPair
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
    "sidebar_multiple_filters": True,
    "show_session_speed": False,
    "show_sidebar": True,
    "theme": "gray",
    "first_login": True,

    # Server Settings
    "base": "/",
    "interface": "0.0.0.0",
    "port": 8112,
    "https": False,
    "pkey": "ssl/daemon.pkey",
    "cert": "ssl/daemon.cert"
}

UI_CONFIG_KEYS = (
    "theme", "sidebar_show_zero", "sidebar_multiple_filters",
    "show_session_speed", "base", "first_login"
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
        log.debug("uploading files to %s", tempdir)

        filenames = []
        for upload in request.args.get("file"):
            fd, fn = tempfile.mkstemp('.torrent', dir=tempdir)
            os.write(fd, upload)
            os.close(fd)
            filenames.append(fn)
        log.debug("uploaded %d file(s)", len(filenames))

        request.setHeader("content-type", "text/html")
        request.setResponseCode(http.OK)
        return compress(common.json.dumps({
            'success': True,
            'files': filenames
        }), request)

class Render(resource.Resource):
    def __init__(self):
        resource.Resource.__init__(self)
        # Make a list of all the template files to check requests against.
        self.template_files = fnmatch.filter(os.listdir(rpath('render')), '*.html')

    def getChild(self, path, request):
        request.render_file = path
        return self

    def render(self, request):
        if not hasattr(request, "render_file"):
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            return ""

        if request.render_file not in self.template_files:
            request.setResponseCode(http.NOT_FOUND)
            return "<h1>404 - Not Found</h1>"

        filename = os.path.join("render", request.render_file)
        template = Template(filename=rpath(filename))
        request.setHeader("content-type", "text/html")
        request.setResponseCode(http.OK)
        return compress(template.render(), request)

class Tracker(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)
        try:
            self.tracker_icons = component.get("TrackerIcons")
        except KeyError:
            self.tracker_icons = TrackerIcons()

    def getChild(self, path, request):
        request.tracker_name = path
        return self

    def on_got_icon(self, icon, request):
        headers = {}
        if icon:
            request.setHeader("cache-control",
                              "public, must-revalidate, max-age=86400")
            request.setHeader("content-type", icon.get_mimetype())
            request.setResponseCode(http.OK)
            request.write(icon.get_data())
            request.finish()
        else:
            request.setResponseCode(http.NOT_FOUND)
            request.finish()

    def render(self, request):
        d = self.tracker_icons.get(request.tracker_name)
        d.addCallback(self.on_got_icon, request)
        return server.NOT_DONE_YET

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
            with open(filename, "rb") as _file:
                data = _file.read()
            request.setResponseCode(http.OK)
            return data
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
            if os.path.join(directory, filename):
                path = os.path.join(directory, filename)
                log.debug("Serving path: '%s'", path)
                mime_type = mimetypes.guess_type(path)
                request.setHeader("content-type", mime_type[0])
                with open(path, "rb") as _file:
                    data = _file.read()
                return compress(data, request)

        request.setResponseCode(http.NOT_FOUND)
        return "<h1>404 - Not Found</h1>"

class ScriptResource(resource.Resource, component.Component):

    def __init__(self):
        resource.Resource.__init__(self)
        component.Component.__init__(self, "Scripts")
        self.__scripts = {
            "normal": {
                "scripts": {},
                "order": []
            },
            "debug": {
                "scripts": {},
                "order": []
            },
            "dev": {
                "scripts": {},
                "order": []
            }
        }

    def add_script(self, path, filepath, type=None):
        """
        Adds a script or scripts to the script resource.

        :param path: The path of the script (this supports globbing)
        :type path: string
        :param filepath: The physical location of the script
        :type filepath: string
        :keyword type: The type of script to add (normal, debug, dev)
        :param type: string
        """
        if type not in ("dev", "debug", "normal"):
            type = "normal"

        self.__scripts[type]["scripts"][path] = filepath
        self.__scripts[type]["order"].append(path)

    def add_script_folder(self, path, filepath, type=None, recurse=True):
        """
        Adds a folder of scripts to the script resource.

        :param path: The path of the folder
        :type path: string
        :param filepath: The physical location of the script
        :type filepath: string
        :keyword type: The type of script to add (normal, debug, dev)
        :param type: string
        :keyword recurse: Whether or not to recurse into other folders
        :param recurse: bool
        """
        if type not in ("dev", "debug", "normal"):
            type = "normal"

        self.__scripts[type]["scripts"][path] = (filepath, recurse)
        self.__scripts[type]["order"].append(path)

    def remove_script(self, path, type=None):
    	"""
    	Removes a script or folder of scripts from the script resource.

		:param path: The path of the folder
        :type path: string
        :keyword type: The type of script to add (normal, debug, dev)
        :param type: string
        """
        if type not in ("dev", "debug", "normal"):
            type = "normal"

        del self.__scripts[type]["scripts"][path]
        self.__scripts[type]["order"].remove(path)

    def get_scripts(self, type=None):
        """
        Returns a list of the scripts that can be used for producing
        script tags.

        :keyword type: The type of scripts to get (normal, debug, dev)
        :param type: string
        """
        scripts = []
        if type not in ("dev", "debug", "normal"):
            type = 'normal'

        _scripts = self.__scripts[type]["scripts"]
        _order = self.__scripts[type]["order"]

        for path in _order:
            filepath = _scripts[path]

            # this is a folder
            if isinstance(filepath, tuple):
                filepath, recurse = filepath
                if recurse:
                    for dirpath, dirnames, filenames in os.walk(filepath, False):
                        files = fnmatch.filter(filenames, "*.js")
                        files.sort()

                        order_file = os.path.join(dirpath, '.order')
                        if os.path.isfile(order_file):
                            with open(order_file, 'rb') as _file:
                                for line in _file:
                                    line = line.strip()
                                    if not line or line[0] == '#':
                                        continue
                                    try:
                                        pos, filename = line.split()
                                        files.pop(files.index(filename))
                                        if pos == '+':
                                            files.insert(0, filename)
                                        else:
                                            files.append(filename)
                                    except:
                                        pass

                        dirpath = dirpath[len(filepath)+1:]
                        if dirpath:
                            scripts.extend(['js/' + path + '/' + dirpath + '/' + f for f in files])
                        else:
                            scripts.extend(['js/' + path + '/' + f for f in files])
                else:
                    files = fnmatch.filter(os.listdir('.'), "*.js")
            else:
                scripts.append("js/" + path)
        return scripts

    def getChild(self, path, request):
        if hasattr(request, "lookup_path"):
            request.lookup_path += '/' + path
        else:
            request.lookup_path = path
        return self

    def render(self, request):
        log.debug("Requested path: '%s'", request.lookup_path)

        for type in ("dev", "debug", "normal"):
            scripts = self.__scripts[type]["scripts"]
            for pattern in scripts:
                if not request.lookup_path.startswith(pattern):
                    continue

                filepath = scripts[pattern]
                if isinstance(filepath, tuple):
                    filepath = filepath[0]

                path = filepath + request.lookup_path[len(pattern):]

                if not os.path.isfile(path):
                    continue

                log.debug("Serving path: '%s'", path)
                mime_type = mimetypes.guess_type(path)
                request.setHeader("content-type", mime_type[0])
                with open(path, "rb") as _file:
                    data = _file.read()
                return compress(data, request)

        request.setResponseCode(http.NOT_FOUND)
        return "<h1>404 - Not Found</h1>"

class TopLevel(resource.Resource):
    addSlash = True

    __stylesheets = [
        "css/ext-all-notheme.css",
        "css/ext-extensions.css",
        "css/deluge.css"
    ]

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild("css", LookupResource("Css", rpath("css")))
        self.putChild("gettext.js", GetText())
        self.putChild("flag", Flag())
        self.putChild("icons", LookupResource("Icons", rpath("icons")))
        self.putChild("images", LookupResource("Images", rpath("images")))

        js = ScriptResource()

        # configure the dev scripts
        js.add_script("ext-base-debug.js", rpath("js", "ext-base-debug.js"), "dev")
        js.add_script("ext-all-debug.js", rpath("js", "ext-all-debug.js"), "dev")
        js.add_script_folder("ext-extensions", rpath("js", "ext-extensions"), "dev")
        js.add_script_folder("deluge-all", rpath("js", "deluge-all"), "dev")

        # configure the debug scripts
        js.add_script("ext-base-debug.js", rpath("js", "ext-base-debug.js"), "debug")
        js.add_script("ext-all-debug.js", rpath("js", "ext-all-debug.js"), "debug")
        js.add_script("ext-extensions-debug.js", rpath("js", "ext-extensions-debug.js"), "debug")
        js.add_script("deluge-all-debug.js", rpath("js", "deluge-all-debug.js"), "debug")

        # configure the normal scripts
        js.add_script("ext-base.js", rpath("js", "ext-base.js"))
        js.add_script("ext-all.js", rpath("js", "ext-all.js"))
        js.add_script("ext-extensions.js", rpath("js", "ext-extensions.js"))
        js.add_script("deluge-all.js", rpath("js", "deluge-all.js"))

        self.putChild("js", js)

        self.putChild("json", JSON())
        self.putChild("upload", Upload())
        self.putChild("render", Render())
        self.putChild("themes", static.File(rpath("themes")))
        self.putChild("tracker", Tracker())

        theme = component.get("DelugeWeb").config["theme"]
        if not os.path.isfile(rpath("themes", "css", "xtheme-%s.css" % theme)):
            theme = CONFIG_DEFAULTS.get("theme")
        self.__stylesheets.insert(1, "themes/css/xtheme-%s.css" % theme)

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

    def getChildWithDefault(self, path, request):
        # Calculate the request base
        header = request.getHeader('x-deluge-base')
        base = header if header else component.get("DelugeWeb").base

        # validate the base parameter
        if not base:
            base = '/'

        if base[0] != '/':
            base = '/' + base

        if base[-1] != '/':
            base += '/'

        request.base = base.encode('idna')

        return resource.Resource.getChildWithDefault(self, path, request)

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
            mode = 'dev'
        elif debug:
            mode = 'debug'
        else:
            mode = None

        scripts = component.get("Scripts").get_scripts(mode)
        scripts.insert(0, "gettext.js")

        template = Template(filename=rpath("index.html"))
        request.setHeader("content-type", "text/html; charset=utf-8")

        web_config = component.get("Web").get_config()
        web_config["base"] = request.base
        config = dict([(key, web_config[key]) for key in UI_CONFIG_KEYS])
        js_config = common.json.dumps(config)
        return template.render(scripts=scripts, stylesheets=self.stylesheets,
            debug=debug, base=request.base, js_config=js_config)

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
        self.interface = self.config["interface"]
        self.port = self.config["port"]
        self.https = self.config["https"]
        self.pkey = self.config["pkey"]
        self.cert = self.config["cert"]
        self.base = self.config["base"]
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
        self.socket = reactor.listenTCP(self.port, self.site, interface=self.interface)
        log.info("Serving on %s:%s view at http://%s:%s", self.interface, self.port, self.interface, self.port)

    def start_ssl(self):
        log.debug("Enabling SSL with PKey: %s, Cert: %s", self.pkey, self.cert)
        check_ssl_keys()

        with open(configmanager.get_config_dir(self.cert)) as cert:
            certificate = Certificate.loadPEM(cert.read()).original
        with open(configmanager.get_config_dir(self.pkey)) as pkey:
            private_key = KeyPair.load(pkey.read(), FILETYPE_PEM).original
        options = CertificateOptions(privateKey=private_key, certificate=certificate, method=SSL.SSLv23_METHOD)
        options.getContext().set_options(SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3)

        self.socket = reactor.listenSSL(self.port, self.site, options, interface=self.interface)
        log.info("Serving on %s:%s view at https://%s:%s", self.interface, self.port, self.interface, self.port)

    def stop(self):
        log.info("Shutting down webserver")
        component.get("JSON").disable()

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
