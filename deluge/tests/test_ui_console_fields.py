# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.trial import unittest

from deluge.ui.console.widgets.fields import TextInput


class Parent(object):

    def __init__(self):
        self.border_off_x = 1
        self.pane_width = 20


class UICommonTestCase(unittest.TestCase):

    def setUp(self):  # NOQA: N803
        self.parent = Parent()

    def tearDown(self):  # NOQA: N803
        pass

    def test_text_input(self):
        def move_func(self, r, c):
            self._cursor_row = r
            self._cursor_col = c

        t = TextInput(self.parent, 'name', 'message', move_func, 20, '/text/field/file/path', complete=False)
        self.assertTrue(t)  # Shut flake8 up (unused variable)
