#!/usr/bin/env python
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
# License: GPL v2(+OpenSSL exception), see LICENSE file in base directory.
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

    config['base'] = '/deluge'
    config['disallow'] = {
        '/daemon/control':'running as an apache user',
        '/config/server':'running as an apache-user'
        }

    utils.apply_config()

    return deluge_webserver.WsgiApplication()
