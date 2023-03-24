#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import deluge.component as component
from deluge.conftest import BaseTestCase
from deluge.core.core import Core


class TestAlertManager(BaseTestCase):
    def set_up(self):
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.am = component.get('AlertManager')
        return component.start(['AlertManager'])

    def tear_down(self):
        return component.shutdown()

    def test_register_handler(self):
        def handler(alert):
            ...

        self.am.register_handler('dummy1', handler)
        self.am.register_handler('dummy2_alert', handler)
        assert self.am.handlers['dummy1'] == [handler]
        assert self.am.handlers['dummy2'] == [handler]

    def test_deregister_handler(self):
        def handler(alert):
            ...

        self.am.register_handler('dummy1', handler)
        self.am.register_handler('dummy2_alert', handler)
        self.am.deregister_handler(handler)
        assert self.am.handlers['dummy1'] == []
        assert self.am.handlers['dummy2'] == []
