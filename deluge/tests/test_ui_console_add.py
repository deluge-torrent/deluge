# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import argparse

from deluge.tests.test_ui_entry import ConsoleUIBaseTestCase
from deluge.ui.console.cmdline.commands.add import Command


class UICommonTestCase(ConsoleUIBaseTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_add_args_short_option_name(self):
        completed_path = 'completed_path'
        parser = argparse.ArgumentParser()
        cmd = Command()
        cmd.add_arguments(parser)
        args = parser.parse_args(['torrent', '-c', completed_path])
        self.assertEqual(args.completed, completed_path)

    def test_add_args_long_option_name(self):
        completed_path = 'completed_path'
        parser = argparse.ArgumentParser()
        cmd = Command()
        cmd.add_arguments(parser)
        args = parser.parse_args(['torrent', '--completed', completed_path])
        self.assertEqual(args.completed, completed_path)
