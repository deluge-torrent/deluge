#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
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


import web
import random
import gettext
import locale
import deluge.common
from deluge.configmanager import ConfigManager
import deluge.configmanager
import pkg_resources
from deluge.ui.client import sclient
import components
from deluge.log import LOG as log
from webserver_common import  CONFIG_DEFAULTS

config = ConfigManager("webui06.conf", CONFIG_DEFAULTS)

# Initialize gettext
try:
    locale.setlocale(locale.LC_ALL, '')
    if hasattr(locale, "bindtextdomain"):
        locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    if hasattr(locale, "textdomain"):
        locale.textdomain("deluge")
    gettext.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    gettext.textdomain("deluge")
    gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"))
except Exception, e:
    log.error("Unable to initialize gettext/locale: %s", e)

components.register() #after gettext!!

from debugerror import deluge_debugerror
from render import render
import utils


## Init ##
random.seed()
web.webapi.internalerror = deluge_debugerror

#self registering pages etc.
import pages
import config_tabs_webui #auto registers in ConfigUiManager
import config_tabs_deluge #auto registers in ConfigUiManager
import register_menu #auto registers.
#manual register:
import torrent_add
torrent_add.register()
import torrent_options
torrent_options.register()
import torrent_move
torrent_move.register()
import config_forms
config_forms.register()
import json_api
json_api.register()
#/self registering pages.


def WsgiApplication(middleware = None):
    from web import webpyfunc, wsgifunc
    from deluge import component

    pagemanager = component.get("PageManager")
    if not middleware:
        middleware = []

    return wsgifunc(webpyfunc(pagemanager.urls, pagemanager.page_classes, False), *middleware)

def create_webserver(debug = False, base_url =None):
    "starts builtin webserver"
    import web

    utils.set_config_defaults()
    if base_url:
        config['base'] = base_url
    else:
        config['base'] = ''
    config['disallow'] = {}
    utils.apply_config()


    from lib.webpy022.wsgiserver import CherryPyWSGIServer

    middleware = None
    if debug:
        middleware = [web.reloader]

    wsgi_app = WsgiApplication(middleware)

    server_address=("0.0.0.0", int(config['port']))
    server = CherryPyWSGIServer(server_address, wsgi_app, server_name="localhost")

    https = False
    if config["https"]:
        import os
        cert_path = deluge.configmanager.get_config_dir("ssl/deluge.cert.pem")
        key_path = deluge.configmanager.get_config_dir("ssl/deluge.key.pem")
        if os.path.exists (key_path) and os.path.exists (cert_path):
            server.ssl_certificate = cert_path
            server.ssl_private_key = key_path
            https = True

    if https:
        log.info("https://%s:%d/" %  server_address)
    else:
        log.info("http://%s:%d/" % server_address)
    return server

def run(debug = False, base_url = ""):
    server = create_webserver(debug, base_url)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
