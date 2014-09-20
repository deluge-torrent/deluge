from twisted.trial import unittest

import deluge.component as component
from deluge.core.core import Core


class AlertManagerTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        self.core = Core()

        self.am = component.get("AlertManager")
        component.start(["AlertManager"])

    def tearDown(self):  # NOQA
        def on_shutdown(result):
            component._ComponentRegistry.components = {}
            del self.am
            del self.core

        return component.shutdown().addCallback(on_shutdown)

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
