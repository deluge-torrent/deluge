#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import sys
from dataclasses import dataclass

import pytest

from deluge.core.core import Core


class LtSessionMock:
    def __init__(self):
        self.alerts = []

    def push_alerts(self, alerts):
        self.alerts = alerts

    def wait_for_alert(self, timeout):
        return self.alerts[0] if len(self.alerts) > 0 else None

    def pop_alerts(self):
        alerts = self.alerts
        self.alerts = []
        return alerts


@dataclass
class LtAlertMock:
    type: int
    name: str
    message: str

    def message(self):
        return self.message

    def what(self):
        return self.name


@pytest.fixture
def mock_alert1():
    return LtAlertMock(type=1, name='mock_alert1', message='Alert 1')


@pytest.fixture
def mock_alert2():
    return LtAlertMock(type=2, name='mock_alert2', message='Alert 2')


class TestAlertManager:
    @pytest.fixture(autouse=True)
    def set_up(self, component):
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.am = component.get('AlertManager')
        self.am.session = LtSessionMock()

        component.start(['AlertManager'])

    def test_register_handler(self):
        def handler(alert): ...

        self.am.register_handler('dummy1', handler)
        self.am.register_handler('dummy2_alert', handler)
        assert self.am.handlers['dummy1'] == [handler]
        assert self.am.handlers['dummy2'] == [handler]

    async def test_pop_alert(self, mock_callback, mock_alert1, mock_alert2):
        self.am.register_handler('mock_alert1', mock_callback)

        self.am.session.push_alerts([mock_alert1, mock_alert2])

        await mock_callback.deferred

        mock_callback.assert_called_once_with(mock_alert1)

    @pytest.mark.xfail(
        sys.platform == 'win32',
        reason='Issue under Windows where mock is already called.',
    )
    async def test_pause_not_pop_alert(
        self, component, mock_alert1, mock_alert2, mock_callback
    ):
        await component.pause(['AlertManager'])

        self.am.register_handler('mock_alert1', mock_callback)
        self.am.session.push_alerts([mock_alert1, mock_alert2])

        await mock_callback.deferred

        mock_callback.assert_not_called()
        assert not self.am._event.is_set()
        assert len(self.am.session.alerts) == 2

    def test_deregister_handler(self):
        def handler(alert): ...

        self.am.register_handler('dummy1', handler)
        self.am.register_handler('dummy2_alert', handler)
        self.am.deregister_handler(handler)
        assert self.am.handlers['dummy1'] == []
        assert self.am.handlers['dummy2'] == []
