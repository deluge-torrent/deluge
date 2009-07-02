from twisted.trial import unittest

import common

from deluge.core.alertmanager import AlertManager
from deluge.core.core import Core

class AlertManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.core = Core()

        self.am = AlertManager()
        self.am.start()

    def test_register_handler(self):
        def handler(alert):
            return

        self.am.register_handler("dummy_alert", handler)

        self.assertEquals(self.am.handlers["dummy_alert"], [handler])

    def test_deregister_handler(self):
        def handler(alert):
            return

        self.am.register_handler("dummy_alert", handler)
        self.am.deregister_handler(handler)
        self.assertEquals(self.am.handlers["dummy_alert"], [])
