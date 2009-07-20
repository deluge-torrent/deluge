from twisted.trial import unittest

import common

from deluge.core.authmanager import AuthManager

class AuthManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.auth = AuthManager()
        self.auth.start()

    def test_authorize(self):
        from deluge.ui import common
        self.assertEquals(self.auth.authorize(*common.get_localhost_auth()), 10)
