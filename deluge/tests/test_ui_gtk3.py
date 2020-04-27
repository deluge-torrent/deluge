# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import sys

import mock
import pytest
from twisted.trial import unittest


@pytest.mark.gtkui
class GTK3CommonTestCase(unittest.TestCase):
    def setUp(self):
        sys.modules['gi.repository'] = mock.MagicMock()

    def tearDown(self):
        pass

    def test_cmp(self):
        from deluge.ui.gtk3.common import cmp

        self.assertEqual(cmp(None, None), 0)
        self.assertEqual(cmp(1, None), 1)
        self.assertEqual(cmp(0, None), 1)
        self.assertEqual(cmp(None, 7), -1)
        self.assertEqual(cmp(None, 'bar'), -1)
        self.assertEqual(cmp('foo', None), 1)
        self.assertEqual(cmp('', None), 1)
