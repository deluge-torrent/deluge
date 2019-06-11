# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import unicode_literals

from mock import patch
from twisted.trial import unittest

from deluge.ui.web import auth


class MockConfig(object):
    def __init__(self, config):
        self.config = config

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value


class WebAuthTestCase(unittest.TestCase):
    @patch('deluge.ui.web.auth.JSONComponent.__init__', return_value=None)
    def test_change_password(self, mock_json):
        config = MockConfig(
            {
                'pwd_sha1': '8d8ff487626141d2b91025901d3ab57211180b48',
                'pwd_salt': '7555d757710158655bd1646e207dee21a89e9226',
            }
        )
        webauth = auth.Auth(config)
        self.assertTrue(webauth.change_password('deluge', 'deluge_new'))
