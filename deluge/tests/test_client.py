
import common

from twisted.trial import unittest

from deluge import error
from deluge.core.authmanager import AUTH_LEVEL_ADMIN, AUTH_LEVEL_DEFAULT
from deluge.ui.client import client

class ClientTestCase(unittest.TestCase):

    def setUp(self):
        self.core = common.start_core()

    def tearDown(self):
        self.core.terminate()

    def test_connect_no_credentials(self):

        d = client.connect("localhost", 58846)

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.AuthenticationRequired),
                error.AuthenticationRequired
            )
            self.addCleanup(client.disconnect)

        d.addErrback(on_failure)
        return d

    def test_connect_localclient(self):
        from deluge.ui import common
        username, password = common.get_localhost_auth()
        d = client.connect(
            "localhost", 58846, username=username, password=password
        )

        def on_connect(result):
            self.assertEqual(client.get_auth_level(), AUTH_LEVEL_ADMIN)
            self.addCleanup(client.disconnect)
            return result

        d.addCallback(on_connect)
        return d

    def test_connect_bad_password(self):
        from deluge.ui import common
        username, password = common.get_localhost_auth()
        d = client.connect(
            "localhost", 58846, username=username, password=password+'1'
        )

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.BadLoginError),
                error.BadLoginError
            )
            self.addCleanup(client.disconnect)

        d.addErrback(on_failure)
        return d

    def test_connect_without_password(self):
        from deluge.ui import common
        username, password = common.get_localhost_auth()
        d = client.connect(
            "localhost", 58846, username=username
        )

        def on_failure(failure):
            self.assertEqual(
                failure.trap(error.AuthenticationRequired),
                error.AuthenticationRequired
            )
            self.assertEqual(failure.value.username, username)
            self.addCleanup(client.disconnect)

        d.addErrback(on_failure)
        return d
