#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import pytest

import deluge.common
import deluge.ui.web.auth
import deluge.ui.web.server
from deluge import configmanager
from deluge.conftest import BaseTestCase
from deluge.ui.web.server import DelugeWeb

from .common import ReactorOverride


@pytest.mark.usefixtures('daemon', 'component')
class WebServerTestBase(BaseTestCase):
    """
    Base class for tests that need a running webapi

    """

    def set_up(self):
        self.host_id = None
        deluge.ui.web.server.reactor = ReactorOverride()
        return self.start_webapi(None)

    def start_webapi(self, arg):
        config_defaults = deluge.ui.web.server.CONFIG_DEFAULTS.copy()
        config_defaults['port'] = 8999
        self.config = configmanager.ConfigManager('web.conf', config_defaults)

        self.deluge_web = DelugeWeb(daemon=False)

        host = list(self.deluge_web.web_api.hostlist.config['hosts'][0])
        host[2] = self.listen_port
        self.deluge_web.web_api.hostlist.config['hosts'][0] = tuple(host)
        self.host_id = host[0]
        self.deluge_web.start()


class WebServerMockBase:
    """
    Class with utility functions for mocking with tests using the webserver

    """

    def mock_authentication_ignore(self, auth):
        def check_request(request, method=None, level=None):
            pass

        self.patch(auth, 'check_request', check_request)
