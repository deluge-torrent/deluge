# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.trial import unittest

import deluge.error


class ErrorTestCase(unittest.TestCase):
    def setUp(self):  # NOQA: N803
        pass

    def tearDown(self):  # NOQA: N803
        pass

    def test_deluge_error(self):
        msg = 'Some message'
        e = deluge.error.DelugeError(msg)
        self.assertEqual(str(e), msg)
        from twisted.internet.defer import DebugInfo

        del DebugInfo.__del__  # Hides all errors
        self.assertEqual(e._args, (msg,))
        self.assertEqual(e._kwargs, {})

    def test_incompatible_client(self):
        version = '1.3.6'
        e = deluge.error.IncompatibleClient(version)
        self.assertEqual(
            str(e),
            'Your deluge client is not compatible with the daemon. \
Please upgrade your client to %s'
            % version,
        )

    def test_not_authorized_error(self):
        current_level = 5
        required_level = 10
        e = deluge.error.NotAuthorizedError(current_level, required_level)
        self.assertEqual(
            str(e), 'Auth level too low: %d < %d' % (current_level, required_level)
        )

    def test_bad_login_error(self):
        message = 'Login failed'
        username = 'deluge'
        e = deluge.error.BadLoginError(message, username)
        self.assertEqual(str(e), message)
