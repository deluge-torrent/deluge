#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from types import SimpleNamespace

import pytest_twisted

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

    def set_alerts(self):
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
            ...

        self.am.register_handler('dummy1', handler)
        self.am.register_handler('dummy2_alert', handler)
        assert self.am.handlers['dummy1'] == [handler]
        assert self.am.handlers['dummy2'] == [handler]

    @pytest_twisted.ensureDeferred
    async def test_pop_alert(self, mock_callback):
        mock_callback.reset_mock()
        self.am.register_handler('DummyAlert1', mock_callback)
        self.am.session.set_alerts()
        await mock_callback.deferred
        mock_callback.assert_called_once_with(SimpleNamespace(message='1'))

    @pytest_twisted.ensureDeferred
    async def test_pause_not_pop_alert(self, mock_callback):
        await component.pause(['AlertManager'])
        self.am.register_handler('DummyAlert1', mock_callback)
        self.am.session.set_alerts()
        await mock_callback.deferred
        mock_callback.assert_not_called()
        assert not self.am._event.isSet()
        assert len(self.am.session.alerts) == 2

    def test_deregister_handler(self):
        def handler(alert):
            ...

        self.am.register_handler('dummy1', handler)
        self.am.register_handler('dummy2_alert', handler)
        self.am.deregister_handler(handler)
        assert self.am.handlers['dummy1'] == []
        assert self.am.handlers['dummy2'] == []
