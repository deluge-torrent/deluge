#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
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

#


"""
this is an ugly hack, and it will be changed.
for experimental use only!!
"""
import os

def get_wsgi_application(base_url, config_dir):

    #monkeypatch:
    from deluge import common
    def get_config_dir(filename = ""):
        return os.path.join(config_dir, filename)
    common.get_config_dir = get_config_dir
    #/monkeypatch

    from deluge.configmanager import ConfigManager
    from deluge.ui.webui import deluge_webserver
    from deluge.ui.webui import utils

    config = ConfigManager("webui06.conf")

    utils.set_config_defaults()

    config.set('base','/deluge')
    config.set('disallow',{
        '/daemon/control':'running as an apache user',
        '/config/server':'running as an apache-user'
        })

    utils.apply_config()

    return deluge_webserver.WsgiApplication()
