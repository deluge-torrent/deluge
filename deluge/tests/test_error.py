from twisted.trial import unittest

import deluge.error


class ErrorTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        pass

    def tearDown(self):  # NOQA
        pass

    def test_deluge_error(self):
        msg = "Some message"
        e = deluge.error.DelugeError(msg)
        self.assertEquals(str(e), msg)
        self.assertEquals(e._args, (msg,))
        self.assertEquals(e._kwargs, {})

    def test_incompatible_client(self):
        version = "1.3.6"
        e = deluge.error.IncompatibleClient(version)
        self.assertEquals(str(e), "Your deluge client is not compatible with the daemon. \
Please upgrade your client to %s" % version)

    def test_not_authorized_error(self):
        current_level = 5
        required_level = 10
        e = deluge.error.NotAuthorizedError(current_level, required_level)
        self.assertEquals(str(e), "Auth level too low: %d < %d" % (current_level, required_level))

    def test_bad_login_error(self):
        message = "Login failed"
        username = "deluge"
        e = deluge.error.BadLoginError(message, username)
        self.assertEquals(str(e), message)
