# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import argparse

from deluge.common import windows_check
from deluge.ui.console.cmdline.commands.add import Command
from deluge.ui.console.cmdline.commands.config import json_eval
from deluge.ui.console.widgets.fields import TextInput

from .basetest import BaseTestCase


class MockParent(object):
    def __init__(self):
        self.border_off_x = 1
        self.pane_width = 20
        self.encoding = 'utf8'


class UIConsoleFieldTestCase(BaseTestCase):
    def setUp(self):  # NOQA: N803
        self.parent = MockParent()

    def tearDown(self):  # NOQA: N803
        pass

    def test_text_input(self):
        def move_func(self, r, c):
            self._cursor_row = r
            self._cursor_col = c

        t = TextInput(
            self.parent,
            'name',
            'message',
            move_func,
            20,
            '/text/field/file/path',
            complete=False,
        )
        self.assertTrue(t)
        if not windows_check():
            self.assertTrue(t.handle_read(33))


class UIConsoleCommandsTestCase(BaseTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_add_move_completed(self):
        completed_path = 'completed_path'
        parser = argparse.ArgumentParser()
        cmd = Command()
        cmd.add_arguments(parser)
        args = parser.parse_args(['torrent', '-m', completed_path])
        self.assertEqual(args.move_completed_path, completed_path)
        args = parser.parse_args(['torrent', '--move-path', completed_path])
        self.assertEqual(args.move_completed_path, completed_path)

    def test_config_json_eval(self):
        self.assertEqual(json_eval('/downloads'), '/downloads')
        self.assertEqual(json_eval('/dir/with space'), '/dir/with space')
        self.assertEqual(json_eval('c:\\\\downloads'), 'c:\\\\downloads')
        self.assertEqual(json_eval('c:/downloads'), 'c:/downloads')
        # Ensure newlines are split and only first setting is used.
        self.assertEqual(json_eval('setting\nwithneline'), 'setting')
        # Allow both parentheses and square brackets.
        self.assertEqual(json_eval('(8000, 8001)'), [8000, 8001])
        self.assertEqual(json_eval('[8000, 8001]'), [8000, 8001])
        self.assertEqual(json_eval('["abc", "def"]'), ['abc', 'def'])
        self.assertEqual(json_eval('{"foo": "bar"}'), {'foo': 'bar'})
        self.assertEqual(json_eval('{"number": 1234}'), {'number': 1234})
        # Hex string for peer_tos.
        self.assertEqual(json_eval('0x00'), '0x00')
        self.assertEqual(json_eval('1000'), 1000)
        self.assertEqual(json_eval('-6'), -6)
        self.assertEqual(json_eval('10.5'), 10.5)
        self.assertEqual(json_eval('True'), True)
        self.assertEqual(json_eval('false'), False)
        self.assertEqual(json_eval('none'), None)
        # Empty values to clear config key.
        self.assertEqual(json_eval('[]'), [])
        self.assertEqual(json_eval(''), '')
