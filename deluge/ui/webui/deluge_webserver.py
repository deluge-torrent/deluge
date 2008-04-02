#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
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
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import web
import random
import gettext
import locale
from deluge.configmanager import ConfigManager
import pkg_resources
from deluge.ui.client import sclient
import components
from deluge.log import LOG as log

# Initialize gettext
locale.setlocale(locale.LC_MESSAGES, '')
locale.bindtextdomain("deluge",
            pkg_resources.resource_filename(
                                    "deluge", "i18n"))
locale.textdomain("deluge")
gettext.bindtextdomain("deluge",
            pkg_resources.resource_filename(
                                    "deluge", "i18n"))
gettext.textdomain("deluge")
gettext.install("deluge",
            pkg_resources.resource_filename(
                                    "deluge", "i18n"))

components.register() #after gettext!!

from debugerror import deluge_debugerror
from render import render
import utils


## Init ##
config = ConfigManager("webui.conf")
random.seed()
web.webapi.internalerror = deluge_debugerror

#self registering pages etc.
import pages
import config_tabs_webui #auto registers in ConfigUiManager
import config_tabs_deluge #auto registers in ConfigUiManager
import register_menu
#
import torrent_add
import torrent_options
import torrent_move
import config_forms
torrent_add.register()
torrent_options.register()
torrent_move.register()
config_forms.register()
#/self registering pages.


def WsgiApplication(middleware = None):
    from web import webpyfunc, wsgifunc
    from deluge import component

    pagemanager = component.get("PageManager")
    if not middleware:
        middleware = []

    return wsgifunc(webpyfunc(pagemanager.urls, pagemanager.page_classes, False), *middleware)

def create_webserver(debug = False):
    "starts builtin webserver"
    import web

    utils.set_config_defaults()
    config.set('base','')
    config.set('disallow',{})
    utils.apply_config()


    from lib.gtk_cherrypy_wsgiserver import CherryPyWSGIServer

    middleware = None
    if debug:
        middleware = [web.reloader]

    wsgi_app = WsgiApplication(middleware)

    server_address=("0.0.0.0", int(config.get('port')))
    server = CherryPyWSGIServer(server_address, wsgi_app, server_name="localhost")

    log.info("http://%s:%d/" % server_address)
    return server

def run(debug = False):
    server = create_webserver(debug)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
