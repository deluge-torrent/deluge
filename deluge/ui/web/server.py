# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import fnmatch
import json
import logging
import mimetypes
import os
import tempfile

from OpenSSL.crypto import FILETYPE_PEM
from twisted.application import internet, service
from twisted.internet import defer, reactor
from twisted.internet.ssl import SSL, Certificate, CertificateOptions, KeyPair
from twisted.web import http, resource, server, static

from deluge import common, component, configmanager
from deluge.core.rpcserver import check_ssl_keys
from deluge.ui.tracker_icons import TrackerIcons
from deluge.ui.util import lang
from deluge.ui.web.auth import Auth
from deluge.ui.web.common import Template, compress
from deluge.ui.web.json_api import JSON, WebApi, WebUtils
from deluge.ui.web.pluginmanager import PluginManager

log = logging.getLogger(__name__)

CONFIG_DEFAULTS = {
    # Misc Settings
    'enabled_plugins': [],
    'default_daemon': '',

    # Auth Settings
    'pwd_salt': 'c26ab3bbd8b137f99cd83c2c1c0963bcc1a35cad',
    'pwd_sha1': '2ce1a410bcdcc53064129b6d950f2e9fee4edc1e',
    'session_timeout': 3600,
    'sessions': {},

    # UI Settings
    'sidebar_show_zero': False,
    'sidebar_show_owners': True,
    'sidebar_multiple_filters': True,
    'show_session_speed': False,
    'show_sidebar': True,
    'theme': 'gray',
    'first_login': True,
    'language': '',

    # Server Settings
    'base': '/',
    'interface': '0.0.0.0',
    'port': 8112,
    'https': False,
    'pkey': 'ssl/daemon.pkey',
    'cert': 'ssl/daemon.cert'
}

UI_CONFIG_KEYS = (
    'theme', 'sidebar_show_zero', 'sidebar_multiple_filters',
    'show_session_speed', 'base', 'first_login'
)


def rpath(*paths):
    """Convert a relative path into an absolute path relative to the location
    of this script.
    """
    return common.resource_filename('deluge.ui.web', os.path.join(*paths))


class GetText(resource.Resource):
    def render(self, request):
        request.setHeader('content-type', 'text/javascript; encoding=utf-8')
        template = Template(filename=rpath('js', 'gettext.js'))
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
        if request.method != 'POST':
            request.setResponseCode(http.NOT_ALLOWED)
            return ''

        if 'file' not in request.args:
            request.setResponseCode(http.OK)
            return json.dumps({
                'success': True,
                'files': []
            })

        tempdir = tempfile.mkdtemp(prefix='delugeweb-')
        log.debug('uploading files to %s', tempdir)

        filenames = []
        for upload in request.args.get('file'):
            fd, fn = tempfile.mkstemp('.torrent', dir=tempdir)
            os.write(fd, upload)
            os.close(fd)
            filenames.append(fn)
        log.debug('uploaded %d file(s)', len(filenames))

        request.setHeader('content-type', 'text/html')
        request.setResponseCode(http.OK)
        return compress(json.dumps({
            'success': True,
            'files': filenames
        }), request)


class Render(resource.Resource):

    def getChild(self, path, request):  # NOQA: N802
        request.render_file = path
        return self

    def render(self, request):
        if not hasattr(request, 'render_file'):
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            return ''

        filename = os.path.join('render', request.render_file)
        template = Template(filename=rpath(filename))
        request.setHeader('content-type', 'text/html')
        request.setResponseCode(http.OK)
        return compress(template.render(), request)


class Tracker(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)
        try:
            self.tracker_icons = component.get('TrackerIcons')
        except KeyError:
            self.tracker_icons = TrackerIcons()

    def getChild(self, path, request):  # NOQA: N802
        request.tracker_name = path
        return self

    def on_got_icon(self, icon, request):
        if icon:
            request.setHeader('cache-control',
                              'public, must-revalidate, max-age=86400')
            request.setHeader('content-type', icon.get_mimetype())
            request.setResponseCode(http.OK)
            request.write(icon.get_data())
            request.finish()
        else:
            request.setResponseCode(http.NOT_FOUND)
            request.finish()

    def render(self, request):
        d = self.tracker_icons.fetch(request.tracker_name)
        d.addCallback(self.on_got_icon, request)
        return server.NOT_DONE_YET


class Flag(resource.Resource):
    def getChild(self, path, request):  # NOQA: N802
        request.country = path
        return self

    def render(self, request):
        path = ('ui', 'data', 'pixmaps', 'flags', request.country.lower() + '.png')
        filename = common.resource_filename('deluge', os.path.join(*path))
        if os.path.exists(filename):
            request.setHeader('cache-control',
                              'public, must-revalidate, max-age=86400')
            request.setHeader('content-type', 'image/png')
            with open(filename, 'rb') as _file:
                data = _file.read()
            request.setResponseCode(http.OK)
            return data
        else:
            request.setResponseCode(http.NOT_FOUND)
            return ''


class LookupResource(resource.Resource, component.Component):

    def __init__(self, name, *directories):
        resource.Resource.__init__(self)
        component.Component.__init__(self, name)

        self.__paths = {}
        for directory in directories:
            self.add_directory(directory)

    def add_directory(self, directory, path=''):
        log.debug('Adding directory `%s` with path `%s`', directory, path)
        paths = self.__paths.setdefault(path, [])
        paths.append(directory)

    def remove_directory(self, directory, path=''):
        log.debug('Removing directory `%s`', directory)
        self.__paths[path].remove(directory)

    def getChild(self, path, request):  # NOQA: N802
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
            return '<h1>404 - Not Found</h1>'

        filename = os.path.basename(request.path)
        for directory in self.__paths[path]:
            if os.path.join(directory, filename):
                path = os.path.join(directory, filename)
                log.debug("Serving path: '%s'", path)
                mime_type = mimetypes.guess_type(path)
                request.setHeader('content-type', mime_type[0])
                with open(path, 'rb') as _file:
                    data = _file.read()
                return compress(data, request)

        request.setResponseCode(http.NOT_FOUND)
        return '<h1>404 - Not Found</h1>'


class ScriptResource(resource.Resource, component.Component):

    def __init__(self):
        resource.Resource.__init__(self)
        component.Component.__init__(self, 'Scripts')
        self.__scripts = {}
        for script_type in ['normal', 'debug', 'dev']:
            self.__scripts[script_type] = {'scripts': {}, 'order': [], 'files_exist': True}

    def has_script_type_files(self, script_type):
        """Returns whether all the script files exist for this script type.

        Args:
            script_type (str): The script type to check (normal, debug, dev).

        Returns:
            bool: True if the files for this script type exist, otherwise False.

        """
        return self.__scripts[script_type]['files_exist']

    def add_script(self, path, filepath, script_type=None):
        """
        Adds a script or scripts to the script resource.

        :param path: The path of the script (this supports globbing)
        :type path: string
        :param filepath: The physical location of the script
        :type filepath: string
        :keyword script_type: The type of script to add (normal, debug, dev)
        :param script_type: string
        """
        if script_type not in ('dev', 'debug', 'normal'):
            script_type = 'normal'

        self.__scripts[script_type]['scripts'][path] = filepath
        self.__scripts[script_type]['order'].append(path)
        if not os.path.isfile(filepath):
            self.__scripts[script_type]['files_exist'] = False

    def add_script_folder(self, path, filepath, script_type=None, recurse=True):
        """
        Adds a folder of scripts to the script resource.

        :param path: The path of the folder
        :type path: string
        :param filepath: The physical location of the script
        :type filepath: string
        :keyword script_type: The type of script to add (normal, debug, dev)
        :param script_type: string
        :keyword recurse: Whether or not to recurse into other folders
        :param recurse: bool
        """
        if script_type not in ('dev', 'debug', 'normal'):
            script_type = 'normal'

        self.__scripts[script_type]['scripts'][path] = (filepath, recurse)
        self.__scripts[script_type]['order'].append(path)
        if not os.path.isdir(filepath):
            self.__scripts[script_type]['files_exist'] = False

    def remove_script(self, path, script_type=None):
        """
        Removes a script or folder of scripts from the script resource.

        :param path: The path of the folder
        :type path: string
        :keyword script_type: The type of script to add (normal, debug, dev)
        :param script_type: string
        """
        if script_type not in ('dev', 'debug', 'normal'):
            script_type = 'normal'

        del self.__scripts[script_type]['scripts'][path]
        self.__scripts[script_type]['order'].remove(path)

    def get_scripts(self, script_type=None):
        """
        Returns a list of the scripts that can be used for producing
        script tags.

        :keyword script_type: The type of scripts to get (normal, debug, dev)
        :param script_type: string
        """
        if script_type not in ('dev', 'debug', 'normal'):
            script_type = 'normal'

        _scripts = self.__scripts[script_type]['scripts']
        _order = self.__scripts[script_type]['order']

        scripts = []
        for path in _order:
            # Index for grouping the scripts when inserting.
            script_idx = len(scripts)
            # A folder resource is enclosed in a tuple.
            if isinstance(_scripts[path], tuple):
                filepath, recurse = _scripts[path]
                for root, dirnames, filenames in os.walk(filepath):
                    dirnames.sort(reverse=True)
                    files = sorted(fnmatch.filter(filenames, '*.js'))

                    order_file = os.path.join(root, '.order')
                    if os.path.isfile(order_file):
                        with open(order_file, 'r') as _file:
                            for line in _file:
                                if line.startswith('+ '):
                                    order_filename = line.split()[1]
                                    files.pop(files.index(order_filename))
                                    files.insert(0, order_filename)

                    # Ensure sub-directory scripts are top of list with root directory scripts bottom.
                    if dirnames:
                        scripts.extend(['js/' + os.path.basename(root) + '/' + f for f in files])
                    else:
                        dirpath = os.path.basename(os.path.dirname(root)) + '/' + os.path.basename(root)
                        for filename in reversed(files):
                            scripts.insert(script_idx, 'js/' + dirpath + '/' + filename)

                    if not recurse:
                        break
            else:
                scripts.append('js/' + path)
        return scripts

    def getChild(self, path, request):  # NOQA: N802
        if hasattr(request, 'lookup_path'):
            request.lookup_path += '/' + path
        else:
            request.lookup_path = path
        return self

    def render(self, request):
        log.debug("Requested path: '%s'", request.lookup_path)

        for script_type in ('dev', 'debug', 'normal'):
            scripts = self.__scripts[script_type]['scripts']
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
                request.setHeader('content-type', mime_type[0])
                with open(path, 'rb') as _file:
                    data = _file.read()
                return compress(data, request)

        request.setResponseCode(http.NOT_FOUND)
        return '<h1>404 - Not Found</h1>'


class TopLevel(resource.Resource):
    addSlash = True

    __stylesheets = [
        'css/ext-all-notheme.css',
        'css/ext-extensions.css',
        'css/deluge.css'
    ]

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild('css', LookupResource('Css', rpath('css')))
        self.putChild('gettext.js', GetText())
        self.putChild('flag', Flag())
        self.putChild('icons', LookupResource('Icons', rpath('icons')))
        self.putChild('images', LookupResource('Images', rpath('images')))

        js = ScriptResource()

        # configure the dev scripts
        js.add_script('ext-base-debug.js', rpath('js', 'extjs', 'ext-base-debug.js'), 'dev')
        js.add_script('ext-all-debug.js', rpath('js', 'extjs', 'ext-all-debug.js'), 'dev')
        js.add_script_folder('ext-extensions', rpath('js', 'extjs', 'ext-extensions'), 'dev')
        js.add_script_folder('deluge-all', rpath('js', 'deluge-all'), 'dev')

        # configure the debug scripts
        js.add_script('ext-base-debug.js', rpath('js', 'extjs', 'ext-base-debug.js'), 'debug')
        js.add_script('ext-all-debug.js', rpath('js', 'extjs', 'ext-all-debug.js'), 'debug')
        js.add_script('ext-extensions-debug.js', rpath('js', 'extjs', 'ext-extensions-debug.js'), 'debug')
        js.add_script('deluge-all-debug.js', rpath('js', 'deluge-all-debug.js'), 'debug')

        # configure the normal scripts
        js.add_script('ext-base.js', rpath('js', 'extjs', 'ext-base.js'))
        js.add_script('ext-all.js', rpath('js', 'extjs', 'ext-all.js'))
        js.add_script('ext-extensions.js', rpath('js', 'extjs', 'ext-extensions.js'))
        js.add_script('deluge-all.js', rpath('js', 'deluge-all.js'))

        self.js = js
        self.putChild('js', js)
        self.putChild('json', JSON())
        self.putChild('upload', Upload())
        self.putChild('render', Render())
        self.putChild('themes', static.File(rpath('themes')))
        self.putChild('tracker', Tracker())

        theme = component.get('DelugeWeb').config['theme']
        if not os.path.isfile(rpath('themes', 'css', 'xtheme-%s.css' % theme)):
            theme = CONFIG_DEFAULTS.get('theme')
        self.__stylesheets.insert(1, 'themes/css/xtheme-%s.css' % theme)

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

    def getChild(self, path, request):  # NOQA: N802
        if path == '':
            return self
        else:
            return resource.Resource.getChild(self, path, request)

    def getChildWithDefault(self, path, request):  # NOQA: N802
        # Calculate the request base
        header = request.getHeader('x-deluge-base')
        base = header if header else component.get('DelugeWeb').base

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
        uri_true = ('true', 'yes', '1')
        debug_arg = request.args.get('debug', [''])[-1] in uri_true
        dev_arg = request.args.get('dev', [''])[-1] in uri_true
        dev_ver = 'dev' in common.get_version()

        script_type = 'normal'
        if debug_arg:
            script_type = 'debug'
        # Override debug if dev arg or version.
        if dev_arg or dev_ver:
            script_type = 'dev'

        if not self.js.has_script_type_files(script_type):
            if not dev_ver:
                log.warning("Failed to enable WebUI '%s' mode, script files are missing!", script_type)
            # Fallback to checking other types in order and selecting first with files available.
            for alt_script_type in [x for x in ['normal', 'debug', 'dev'] if x != script_type]:
                if self.js.has_script_type_files(alt_script_type):
                    script_type = alt_script_type
                    if not dev_ver:
                        log.warning("WebUI falling back to '%s' mode.", script_type)
                    break

        scripts = component.get('Scripts').get_scripts(script_type)
        scripts.insert(0, 'gettext.js')

        template = Template(filename=rpath('index.html'))
        request.setHeader('content-type', 'text/html; charset=utf-8')

        web_config = component.get('Web').get_config()
        web_config['base'] = request.base
        config = dict([(key, web_config[key]) for key in UI_CONFIG_KEYS])
        js_config = json.dumps(config)
        # Insert the values into 'index.html' and return.
        return template.render(scripts=scripts, stylesheets=self.stylesheets,
                               debug=debug_arg, base=request.base, js_config=js_config)


class DelugeWeb(component.Component):

    def __init__(self, options=None, daemon=True):
        """
        Setup the DelugeWeb server.

        Args:
            options (argparse.Namespace): The web server options.
            daemon (bool): If True run web server as a seperate daemon process (starts a twisted
                reactor). If False shares the process and twisted reactor from WebUI plugin or tests.

        """
        component.Component.__init__(self, 'DelugeWeb', depend=['Web'])
        self.config = configmanager.ConfigManager('web.conf', defaults=CONFIG_DEFAULTS, file_version=2)
        self.config.run_converter((0, 1), 2, self._migrate_config_1_to_2)
        self.config.register_set_function('language', self._on_language_changed)
        self.socket = None
        self.top_level = TopLevel()

        self.interface = self.config['interface']
        self.port = self.config['port']
        self.https = self.config['https']
        self.pkey = self.config['pkey']
        self.cert = self.config['cert']
        self.base = self.config['base']

        if options:
            self.interface = options.interface if options.interface else self.interface
            self.port = options.port if options.port else self.port
            self.base = options.base if options.base else self.base
            if options.ssl:
                self.https = True
            elif options.no_ssl:
                self.https = False

        if self.base != '/':
            # Strip away slashes and serve on the base path as well as root path
            self.top_level.putChild(self.base.strip('/'), self.top_level)

        lang.setup_translations(setup_gettext=True, setup_pygtk=False)

        self.site = server.Site(self.top_level)
        self.web_api = WebApi()
        self.web_utils = WebUtils()

        self.auth = Auth(self.config)
        self.daemon = daemon
        # Initalize the plugins
        self.plugins = PluginManager()

    def _on_language_changed(self, key, value):
        log.debug("Setting UI language '%s'", value)
        lang.set_language(value)

    def install_signal_handlers(self):
        # Since twisted assigns itself all the signals may as well make
        # use of it.
        reactor.addSystemEventTrigger('after', 'shutdown', self.shutdown)

        # Twisted doesn't handle windows specific signals so we still
        # need to attach to those to handle the close correctly.
        if common.windows_check():
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT, CTRL_SHUTDOWN_EVENT

            def win_handler(ctrl_type):
                log.debug('ctrl type: %s', ctrl_type)
                if ctrl_type == CTRL_CLOSE_EVENT or \
                   ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self.shutdown()
                    return 1
            SetConsoleCtrlHandler(win_handler)

    def start(self):
        """
        Start the DelugeWeb server
        """
        if self.socket:
            log.warn('DelugeWeb is already running and cannot be started')
            return

        log.info('Starting webui server at PID %s', os.getpid())
        if self.https:
            self.start_ssl()
        else:
            self.start_normal()

        component.get('Web').enable()

        if self.daemon:
            reactor.run()

    def start_normal(self):
        self.socket = reactor.listenTCP(self.port, self.site, interface=self.interface)
        log.info('Serving at http://%s:%s%s', self.interface, self.port, self.base)

    def start_ssl(self):
        check_ssl_keys()
        log.debug('Enabling SSL with PKey: %s, Cert: %s', self.pkey, self.cert)

        with open(configmanager.get_config_dir(self.cert)) as cert:
            certificate = Certificate.loadPEM(cert.read()).original
        with open(configmanager.get_config_dir(self.pkey)) as pkey:
            private_key = KeyPair.load(pkey.read(), FILETYPE_PEM).original
        options = CertificateOptions(privateKey=private_key, certificate=certificate, method=SSL.SSLv23_METHOD)
        options.getContext().set_options(SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3)

        self.socket = reactor.listenSSL(self.port, self.site, options, interface=self.interface)
        log.info('Serving at https://%s:%s%s', self.interface, self.port, self.base)

    def stop(self):
        log.info('Shutting down webserver')
        try:
            component.get('Web').disable()
        except KeyError:
            pass

        self.plugins.disable_plugins()
        log.debug('Saving configuration file')
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
        if self.daemon and reactor.running:
            reactor.stop()

    def _migrate_config_1_to_2(self, config):
        config['language'] = CONFIG_DEFAULTS['language']
        return config


if __name__ == '__builtin__':
    deluge_web = DelugeWeb()
    application = service.Application('DelugeWeb')
    sc = service.IServiceCollection(application)
    i = internet.TCPServer(deluge_web.port, deluge_web.site)
    i.setServiceParent(sc)
elif __name__ == '__main__':
    deluge_web = DelugeWeb()
    deluge_web.start()
