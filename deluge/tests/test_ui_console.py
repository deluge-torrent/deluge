#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import argparse

import pytest

from deluge.ui.console.cmdline.commands.add import Command
from deluge.ui.console.cmdline.commands.config import json_eval
from deluge.ui.console.widgets.fields import TextInput


class MockParent:
    def __init__(self):
        self.border_off_x = 1
        self.pane_width = 20
        self.encoding = 'utf8'


class TestUIConsoleField:
    @pytest.fixture(autouse=True)
    def set_up(self):
        self.parent = MockParent()

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
        assert t
        assert t.handle_read(33)


class TestUIConsoleCommands:
    def test_add_move_completed(self):
        completed_path = 'completed_path'
        parser = argparse.ArgumentParser()
        cmd = Command()
        cmd.add_arguments(parser)
        args = parser.parse_args(['torrent', '-m', completed_path])
        assert args.move_completed_path == completed_path
        args = parser.parse_args(['torrent', '--move-path', completed_path])
        assert args.move_completed_path == completed_path

    def test_config_json_eval(self):
        assert json_eval('/downloads') == '/downloads'
        assert json_eval('/dir/with space') == '/dir/with space'
        assert json_eval('c:\\\\downloads') == 'c:\\\\downloads'
        assert json_eval('c:/downloads') == 'c:/downloads'
        # Ensure newlines are split and only first setting is used.
        assert json_eval('setting\nwithneline') == 'setting'
        # Allow both parentheses and square brackets.
        assert json_eval('(8000, 8001)') == [8000, 8001]
        assert json_eval('[8000, 8001]') == [8000, 8001]
        assert json_eval('["abc", "def"]') == ['abc', 'def']
        assert json_eval('{"foo": "bar"}') == {'foo': 'bar'}
        assert json_eval('{"number": 1234}') == {'number': 1234}
        # Hex string for peer_tos.
        assert json_eval('0x00') == '0x00'
        assert json_eval('1000') == 1000
        assert json_eval('-6') == -6
        assert json_eval('10.5') == 10.5
        assert json_eval('True')
        assert not json_eval('false')
        assert json_eval('none') is None
        # Empty values to clear config key.
        assert json_eval('[]') == []
        assert json_eval('') == ''
