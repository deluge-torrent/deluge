# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import fnmatch
import json
import logging
import mimetypes
import os
import tempfile

from twisted.application import internet, service
from twisted.internet import defer, reactor
from twisted.web import http, resource, server, static
from twisted.web.resource import EncodingResourceWrapper

from deluge import common, component, configmanager
from deluge.common import is_ipv6
from deluge.core.rpcserver import check_ssl_keys
from deluge.crypto_utils import get_context_factory
from deluge.i18n import set_language, setup_translation
from deluge.ui.tracker_icons import TrackerIcons
from deluge.ui.web.auth import Auth
from deluge.ui.web.common import Template
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
    'cert': 'ssl/daemon.cert',
}

UI_CONFIG_KEYS = (
    'theme',
    'sidebar_show_zero',
    'sidebar_multiple_filters',
    'show_session_speed',
    'base',
    'first_login',
)


def rpath(*paths):
    """Convert a relative path into an absolute path relative to the location
    of this script.
    """
    return common.resource_filename('deluge.ui.web', os.path.join(*paths))


class GetText(resource.Resource):
    def render(self, request):
        request.setHeader(b'content-type', b'text/javascript; encoding=utf-8')
        template = Template(filename=rpath('js', 'gettext.js'))
        return template.render()


class MockGetText(resource.Resource):
    """GetText Mocking class

    This class will mock the file `gettext.js` in case it does not exists.
    It will be used to define the `_` (underscore) function for translations,
    and will return the string to translate, as is.
    """

    def render(self, request):
        request.setHeader(b'content-type', b'text/javascript; encoding=utf-8')
        return b'function _(string) { return string; }'


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
        if request.method != b'POST':
            request.setResponseCode(http.NOT_ALLOWED)
            request.finish()
            return server.NOT_DONE_YET

        files = request.args.get(b'file', [])
        filenames = []

        if files:
            tempdir = tempfile.mkdtemp(prefix='delugeweb-')
            log.debug('uploading files to %s', tempdir)

            for upload in files:
                fd, fn = tempfile.mkstemp('.torrent', dir=tempdir)
                os.write(fd, upload)
                os.close(fd)
                filenames.append(fn)

            log.debug('uploaded %d file(s)', len(filenames))

        request.setHeader(b'content-type', b'text/html')
        request.setResponseCode(http.OK)
        return json.dumps({'success': bool(filenames), 'files': filenames}).encode(
            'utf8'
        )


class Render(resource.Resource):
    def __init__(self):
        resource.Resource.__init__(self)
        # Make a list of all the template files to check requests against.
        self.template_files = fnmatch.filter(os.listdir(rpath('render')), '*.html')

    def getChild(self, path, request):  # NOQA: N802
        request.render_file = path
        return EncodingResourceWrapper(self, [server.GzipEncoderFactory()])

    def render(self, request):
        log.debug('Render template file: %s', request.render_file)
        if not hasattr(request, 'render_file'):
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            return ''

        request.setHeader(b'content-type', b'text/html')

        tpl_file = request.render_file.decode()
        if tpl_file in self.template_files:
            request.setResponseCode(http.OK)
        else:
            request.setResponseCode(http.NOT_FOUND)
            tpl_file = '404.html'

        template = Template(filename=rpath(os.path.join('render', tpl_file)))
        return template.render()


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
            request.setHeader(
                b'cache-control', b'public, must-revalidate, max-age=86400'
            )
            request.setHeader(b'content-type', icon.get_mimetype().encode('utf8'))
            request.setResponseCode(http.OK)
            request.write(icon.get_data())
            request.finish()
        else:
            request.setResponseCode(http.NOT_FOUND)
            request.finish()

    def render(self, request):
        d = self.tracker_icons.fetch(request.tracker_name.decode())
        d.addCallback(self.on_got_icon, request)
        return server.NOT_DONE_YET


class Flag(resource.Resource):
    def getChild(self, path, request):  # NOQA: N802
        request.country = path
        return self

    def render(self, request):
        flag = request.country.decode('utf-8').lower() + '.png'
        path = ('ui', 'data', 'pixmaps', 'flags', flag)
        filename = common.resource_filename('deluge', os.path.join(*path))
        if os.path.exists(filename):
            request.setHeader(
                b'cache-control', b'public, must-revalidate, max-age=86400'
            )
            request.setHeader(b'content-type', b'image/png')
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

        if request.uri.endswith(b'css'):
            return EncodingResourceWrapper(self, [server.GzipEncoderFactory()])
        else:
            return self

    def render(self, request):
        log.debug('Requested path: %s', request.lookup_path)
        path = os.path.dirname(request.lookup_path).decode()

        if path in self.__paths:
            filename = os.path.basename(request.path).decode()
            for directory in self.__paths[path]:
                path = os.path.join(directory, filename)
                if os.path.isfile(path):
                    log.debug('Serving path: %s', path)
                    mime_type = mimetypes.guess_type(path)
                    request.setHeader(b'content-type', mime_type[0].encode())
                    with open(path, 'rb') as _file:
                        data = _file.read()
                    return data

        request.setResponseCode(http.NOT_FOUND)
        request.setHeader(b'content-type', b'text/html')
        template = Template(filename=rpath(os.path.join('render', '404.html')))
        return template.render()


class ScriptResource(resource.Resource, component.Component):
    def __init__(self):
        resource.Resource.__init__(self)
        component.Component.__init__(self, 'Scripts')
        self.__scripts = {}
        for script_type in ['normal', 'debug', 'dev']:
            self.__scripts[script_type] = {
                'scripts': {},
                'order': [],
                'files_exist': True,
            }

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
        :param script_type: The type of script to add (normal, debug, dev)
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
        :param script_type: The type of script to add (normal, debug, dev)
        :param script_type: string
        :param recurse: Whether or not to recurse into other folders
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
        :param script_type: The type of script to add (normal, debug, dev)
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

        :param script_type: The type of scripts to get (normal, debug, dev)
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
                        scripts.extend(
                            ['js/' + os.path.basename(root) + '/' + f for f in files]
                        )
                    else:
                        dirpath = (
                            os.path.basename(os.path.dirname(root))
                            + '/'
                            + os.path.basename(root)
                        )
                        for filename in reversed(files):
                            scripts.insert(script_idx, 'js/' + dirpath + '/' + filename)

                    if not recurse:
                        break
            else:
                scripts.append('js/' + path)
        return scripts

    def getChild(self, path, request):  # NOQA: N802
        if hasattr(request, 'lookup_path'):
            request.lookup_path += b'/' + path
        else:
            request.lookup_path = path
        return EncodingResourceWrapper(self, [server.GzipEncoderFactory()])

    def render(self, request):
        log.debug('Requested path: %s', request.lookup_path)
        lookup_path = request.lookup_path.decode()
        for script_type in ('dev', 'debug', 'normal'):
            scripts = self.__scripts[script_type]['scripts']
            for pattern in scripts:
                if not lookup_path.startswith(pattern):
                    continue

                filepath = scripts[pattern]
                if isinstance(filepath, tuple):
                    filepath = filepath[0]

                path = filepath + lookup_path[len(pattern) :]

                if not os.path.isfile(path):
                    continue

                log.debug('Serving path: %s', path)
                mime_type = mimetypes.guess_type(path)
                request.setHeader(b'content-type', mime_type[0].encode())
                with open(path, 'rb') as _file:
                    data = _file.read()
                return data

        request.setResponseCode(http.NOT_FOUND)
        request.setHeader(b'content-type', b'text/html')
        template = Template(filename=rpath(os.path.join('render', '404.html')))
        return template.render()


class Themes(static.File):
    def getChild(self, path, request):  # NOQA: N802
        child = static.File.getChild(self, path, request)
        if request.uri.endswith(b'css'):
            return EncodingResourceWrapper(child, [server.GzipEncoderFactory()])
        else:
            return child


class TopLevel(resource.Resource):

    __stylesheets = [
        'css/ext-all-notheme.css',
        'css/ext-extensions.css',
        'css/deluge.css',
    ]

    def __init__(self):
        resource.Resource.__init__(self)

        self.putChild(b'css', LookupResource('Css', rpath('css')))
        if os.path.isfile(rpath('js', 'gettext.js')):
            self.putChild(
                b'gettext.js',
                EncodingResourceWrapper(GetText(), [server.GzipEncoderFactory()]),
            )
        else:
            log.warning(
                'Cannot find "gettext.js" translation file!'
                ' Text will only be available in English.'
            )
            self.putChild(b'gettext.js', MockGetText())
        self.putChild(b'flag', Flag())
        self.putChild(b'icons', LookupResource('Icons', rpath('icons')))
        self.putChild(b'images', LookupResource('Images', rpath('images')))
        self.putChild(
            b'ui_images',
            LookupResource(
                'UI_Images', common.resource_filename('deluge.ui.data', 'pixmaps')
            ),
        )

        js = ScriptResource()

        # configure the dev scripts
        js.add_script(
            'ext-base-debug.js', rpath('js', 'extjs', 'ext-base-debug.js'), 'dev'
        )
        js.add_script(
            'ext-all-debug.js', rpath('js', 'extjs', 'ext-all-debug.js'), 'dev'
        )
        js.add_script_folder(
            'ext-extensions', rpath('js', 'extjs', 'ext-extensions'), 'dev'
        )
        js.add_script_folder('deluge-all', rpath('js', 'deluge-all'), 'dev')

        # configure the debug scripts
        js.add_script(
            'ext-base-debug.js', rpath('js', 'extjs', 'ext-base-debug.js'), 'debug'
        )
        js.add_script(
            'ext-all-debug.js', rpath('js', 'extjs', 'ext-all-debug.js'), 'debug'
        )
        js.add_script(
            'ext-extensions-debug.js',
            rpath('js', 'extjs', 'ext-extensions-debug.js'),
            'debug',
        )
        js.add_script(
            'deluge-all-debug.js', rpath('js', 'deluge-all-debug.js'), 'debug'
        )

        # configure the normal scripts
        js.add_script('ext-base.js', rpath('js', 'extjs', 'ext-base.js'))
        js.add_script('ext-all.js', rpath('js', 'extjs', 'ext-all.js'))
        js.add_script('ext-extensions.js', rpath('js', 'extjs', 'ext-extensions.js'))
        js.add_script('deluge-all.js', rpath('js', 'deluge-all.js'))

        self.js = js
        self.putChild(b'js', js)
        self.putChild(
            b'json', EncodingResourceWrapper(JSON(), [server.GzipEncoderFactory()])
        )
        self.putChild(
            b'upload', EncodingResourceWrapper(Upload(), [server.GzipEncoderFactory()])
        )
        self.putChild(b'render', Render())
        self.putChild(b'themes', Themes(rpath('themes')))
        self.putChild(b'tracker', Tracker())

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
        if not path:
            return self
        else:
            return resource.Resource.getChild(self, path, request)

    def getChildWithDefault(self, path, request):  # NOQA: N802
        # Calculate the request base
        header = request.getHeader(b'x-deluge-base')
        base = header.decode('utf-8') if header else component.get('DelugeWeb').base

        # validate the base parameter
        if not base:
            base = '/'

        if base[0] != '/':
            base = '/' + base

        if base[-1] != '/':
            base += '/'

        request.base = base.encode('utf-8')

        return resource.Resource.getChildWithDefault(self, path, request)

    def render(self, request):
        uri_true = ('true', 'yes', 'on', '1')
        uri_false = ('false', 'no', 'off', '0')

        debug_arg = None
        req_dbg_arg = request.args.get('debug', [b''])[-1].decode().lower()
        if req_dbg_arg in uri_true:
            debug_arg = True
        elif req_dbg_arg in uri_false:
            debug_arg = False

        dev_arg = request.args.get('dev', [b''])[-1].decode().lower() in uri_true
        dev_ver = 'dev' in common.get_version()

        script_type = 'normal'
        if debug_arg is not None:
            # Use debug arg to force switching to normal script type.
            script_type = 'debug' if debug_arg else 'normal'
        elif dev_arg or dev_ver:
            # Also use dev files if development version.
            script_type = 'dev'

        if not self.js.has_script_type_files(script_type):
            if not dev_ver:
                log.warning(
                    'Failed to enable WebUI "%s" mode, script files are missing!',
                    script_type,
                )
            # Fallback to checking other types in order and selecting first with
            # files available. Ordered to start with dev files lookup.
            for alt_script_type in [
                x for x in ['dev', 'debug', 'normal'] if x != script_type
            ]:
                if self.js.has_script_type_files(alt_script_type):
                    script_type = alt_script_type
                    if not dev_ver:
                        log.warning('WebUI falling back to "%s" mode.', script_type)
                    break

        scripts = component.get('Scripts').get_scripts(script_type)
        scripts.insert(0, 'gettext.js')

        template = Template(filename=rpath('index.html'))
        request.setHeader(b'content-type', b'text/html; charset=utf-8')

        web_config = component.get('Web').get_config()
        web_config['base'] = request.base.decode()
        config = {key: web_config[key] for key in UI_CONFIG_KEYS}
        js_config = json.dumps(config)
        # Insert the values into 'index.html' and return.
        return template.render(
            scripts=scripts,
            stylesheets=self.stylesheets,
            debug=str(bool(debug_arg)).lower(),
            base=web_config['base'],
            js_config=js_config,
        )


class DelugeWeb(component.Component):
    def __init__(self, options=None, daemon=True):
        """
        Setup the DelugeWeb server.

        Args:
            options (argparse.Namespace): The web server options.
            daemon (bool): If True run web server as a separate daemon process (starts a twisted
                reactor). If False shares the process and twisted reactor from WebUI plugin or tests.

        """
        component.Component.__init__(self, 'DelugeWeb', depend=['Web'])
        self.config = configmanager.ConfigManager(
            'web.conf', defaults=CONFIG_DEFAULTS, file_version=2
        )
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
            self.interface = (
                options.interface if options.interface is not None else self.interface
            )
            self.port = options.port if options.port else self.port
            self.base = options.base if options.base else self.base
            if options.ssl:
                self.https = True
            elif options.no_ssl:
                self.https = False

        if self.base != '/':
            # Strip away slashes and serve on the base path as well as root path
            self.top_level.putChild(self.base.strip('/'), self.top_level)

        setup_translation()

        # Remove twisted version number from 'server' http-header for security reasons
        server.version = 'TwistedWeb'
        self.site = server.Site(self.top_level)
        self.web_api = WebApi()
        self.web_utils = WebUtils()

        self.auth = Auth(self.config)
        self.daemon = daemon
        # Initialize the plugins
        self.plugins = PluginManager()

    def _on_language_changed(self, key, value):
        log.debug('Setting UI language %s', value)
        set_language(value)

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
                if ctrl_type == CTRL_CLOSE_EVENT or ctrl_type == CTRL_SHUTDOWN_EVENT:
                    self.shutdown()
                    return 1

            SetConsoleCtrlHandler(win_handler)

    def start(self):
        """
        Start the DelugeWeb server
        """
        if self.socket:
            log.warning('DelugeWeb is already running and cannot be started')
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
        ip = self.socket.getHost().host
        ip = '[%s]' % ip if is_ipv6(ip) else ip
        log.info('Serving at http://%s:%s%s', ip, self.port, self.base)

    def start_ssl(self):
        check_ssl_keys()
        log.debug('Enabling SSL with PKey: %s, Cert: %s', self.pkey, self.cert)

        cert = configmanager.get_config_dir(self.cert)
        pkey = configmanager.get_config_dir(self.pkey)

        self.socket = reactor.listenSSL(
            self.port,
            self.site,
            get_context_factory(cert, pkey),
            interface=self.interface,
        )
        ip = self.socket.getHost().host
        ip = '[%s]' % ip if is_ipv6(ip) else ip
        log.info('Serving at https://%s:%s%s', ip, self.port, self.base)

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
