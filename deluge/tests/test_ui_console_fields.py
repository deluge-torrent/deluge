# -*- coding: utf-8 -*-

from twisted.trial import unittest

from deluge.ui.console.widgets.fields import TextInput


class Parent(object):

    def __init__(self):
        self.border_off_x = 1
        self.pane_width = 20


class UICommonTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        self.parent = Parent()

    def tearDown(self):  # NOQA
        pass

    def test_text_input(self):
        def move_func(self, r, c):
            self._cursor_row = r
            self._cursor_col = c

        t = TextInput(self.parent, 'name', 'message', move_func, 20, '/text/field/file/path', complete=False)
        self.assertTrue(t)  # Shut flake8 up (unused variable)
