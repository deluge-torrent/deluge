# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.internet.defer import Deferred

import deluge.component as component
from deluge.core.core import Core

from .basetest import BaseTestCase


class DummyAlert1(object):
    def __init__(self):
        self.message = '1'


class DummyAlert2(object):
    def __init__(self):
        self.message = '2'


class SessionMock(object):
    def __init__(self):
        self.alerts = [DummyAlert1(), DummyAlert2()]

    def wait_for_alert(self, timeout):
        return self.alerts[0] if len(self.alerts) > 0 else None

    def pop_alerts(self):
        alerts = self.alerts
        self.alerts = []
        return alerts


class AlertManagerTestCase(BaseTestCase):
    def set_up(self):
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.am = component.get('AlertManager')
        return component.start(['AlertManager'])

    def tear_down(self):
        return component.shutdown()

    def test_register_handler(self):
        def handler(alert):
            return

        self.am.register_handler('dummy_alert', handler)
        self.assertEqual(self.am.handlers['dummy_alert'], [handler])

    def test_pop_alert(self):
        def dummy_alert_1_handler(alert):
            d.addCallback(self.assertEqual, alert.message, '1')
            d.callback(None)

        self.am.session = SessionMock()
        self.am.register_handler('DummyAlert1', dummy_alert_1_handler)

        d = Deferred()
        return d

    def test_pause_not_pop_alert(self):
        def on_pause(value):
            self.am.session = SessionMock()
            self.am.register_handler('DummyAlert1', dummy_alert_1_handler)
            d.addCallback(check_alert)

        def check_alert(value):
            event = self.am._event.isSet()
            self.assertFalse(event)

        def dummy_alert_1_handler(alert):
            self.fail()

        d = component.pause(['AlertManager'])
        d.addCallback(on_pause)
        return d

    def test_deregister_handler(self):
        def handler(alert):
            return

        self.am.register_handler('dummy_alert', handler)
        self.am.deregister_handler(handler)
        self.assertEqual(self.am.handlers['dummy_alert'], [])
