from twisted.trial import unittest

from deluge.core.authmanager import AUTH_LEVEL_ADMIN, AuthManager


class AuthManagerTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        self.auth = AuthManager()
        self.auth.start()

    def test_authorize(self):
        from deluge.ui import common
        self.assertEquals(
            self.auth.authorize(*common.get_localhost_auth()),
            AUTH_LEVEL_ADMIN
        )
