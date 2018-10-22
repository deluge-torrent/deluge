#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.internet.defer import Deferred

import deluge.component as component
from deluge.conftest import BaseTestCase
from deluge.core.core import Core


class DummyAlert1:
    def __init__(self):
        self.message = '1'


class DummyAlert2:
    def __init__(self):
        self.message = '2'


class SessionMock:
    def __init__(self):
        self.alerts = []

    def set_alerts(self, value):
        self.alerts = [DummyAlert1(), DummyAlert2()]

    def wait_for_alert(self, timeout):
        return self.alerts[0] if len(self.alerts) > 0 else None

    def pop_alerts(self):
        alerts = self.alerts
        self.alerts = []
        return alerts


class TestAlertManager(BaseTestCase):
    def set_up(self):
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.am = component.get('AlertManager')
        self.am.session = SessionMock()
        return component.start(['AlertManager'])

    def tear_down(self):
        return component.shutdown()

    def test_register_handler(self):
        def handler(alert):
            return

        self.am.register_handler('dummy_alert', handler)
        assert self.am.handlers['dummy_alert'] == [handler]

    def test_pop_alert(self):
        def dummy_alert_1_handler(alert):
            d.addCallback(self.assertEqual, alert.message, '1')
            d.callback(None)

        self.am.register_handler('DummyAlert1', dummy_alert_1_handler)
        self.am.session.set_alerts()

        d = Deferred()
        return d

    def test_pause_not_pop_alert(self):
        def on_pause(value):
            self.am.register_handler('DummyAlert1', dummy_alert_1_handler)
            d.addCallback(check_alert)

        def check_alert(value):
            event = self.am._event.isSet()
            self.assertFalse(event)

        def dummy_alert_1_handler(alert):
            self.fail()

        d = component.pause(['AlertManager'])
        d.addCallback(self.am.session.set_alerts)
        d.addCallback(on_pause)
        return d

    def test_deregister_handler(self):
        def handler(alert):
            return

        self.am.register_handler('dummy_alert', handler)
        self.am.deregister_handler(handler)
        assert self.am.handlers['dummy_alert'] == []
