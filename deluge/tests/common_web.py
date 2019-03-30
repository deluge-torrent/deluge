# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import deluge.common
import deluge.component as component
import deluge.ui.web.auth
import deluge.ui.web.server
from deluge import configmanager
from deluge.ui.web.server import DelugeWeb

from .basetest import BaseTestCase
from .common import ReactorOverride
from .daemon_base import DaemonBase


class WebServerTestBase(BaseTestCase, DaemonBase):
    """
    Base class for tests that need a running webapi

    """

    def set_up(self):
        self.host_id = None
        deluge.ui.web.server.reactor = ReactorOverride()
        d = self.common_set_up()
        d.addCallback(self.start_core)
        d.addCallback(self.start_webapi)
        return d

    def start_webapi(self, arg):
        self.webserver_listen_port = 8999

        config_defaults = deluge.ui.web.server.CONFIG_DEFAULTS.copy()
        config_defaults['port'] = self.webserver_listen_port
        self.config = configmanager.ConfigManager('web.conf', config_defaults)

        self.deluge_web = DelugeWeb(daemon=False)

        host = list(self.deluge_web.web_api.hostlist.config['hosts'][0])
        host[2] = self.listen_port
        self.deluge_web.web_api.hostlist.config['hosts'][0] = tuple(host)
        self.host_id = host[0]
        self.deluge_web.start()

    def tear_down(self):
        d = component.shutdown()
        d.addCallback(self.terminate_core)
        return d


class WebServerMockBase(object):
    """
    Class with utility functions for mocking with tests using the webserver

    """

    def mock_authentication_ignore(self, auth):
        def check_request(request, method=None, level=None):
            pass

        self.patch(auth, 'check_request', check_request)
