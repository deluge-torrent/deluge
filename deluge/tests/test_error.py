from twisted.trial import unittest

import deluge.error


class ErrorTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_DelugeError(self):
        msg = "Some message"
        e = deluge.error.DelugeError(msg)
        self.assertEquals(str(e), msg)
        self.assertEquals(e._args, (msg,))
        self.assertEquals(e._kwargs, {})

    def test_IncompatibleClient(self):
        version = "1.3.6"
        e = deluge.error.IncompatibleClient(version)
        self.assertEquals(str(e), "Your deluge client is not compatible with the daemon. \
Please upgrade your client to %s" % version)

    def test_NotAuthorizedError(self):
        current_level = 5
        required_level = 10
        e = deluge.error.NotAuthorizedError(current_level, required_level)
        self.assertEquals(str(e), "Auth level too low: %d < %d" % (current_level, required_level))

    def test_BadLoginError(self):
        message = "Login failed"
        username = "deluge"
        e = deluge.error.BadLoginError(message, username)
        self.assertEquals(str(e), message)
