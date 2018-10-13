# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import unicode_literals

from six import assertCountEqual
from twisted.trial import unittest

from deluge.common import windows_check
from deluge.ui.common import TorrentInfo

from . import common


class UICommonTestCase(unittest.TestCase):
    def setUp(self):  # NOQA: N803
        pass

    def tearDown(self):  # NOQA: N803
        pass

    def test_utf8_encoded_paths(self):
        filename = common.get_test_data_file('test.torrent')
        ti = TorrentInfo(filename)
        self.assertTrue('azcvsupdater_2.6.2.jar' in ti.files_tree)

    def test_utf8_encoded_paths2(self):
        if windows_check():
            raise unittest.SkipTest('on windows KeyError: unicode_filenames')
        filename = common.get_test_data_file('unicode_filenames.torrent')
        filepath1 = '\u30c6\u30af\u30b9\u30fb\u30c6\u30af\u30b5\u30f3.mkv'
        filepath2 = (
            '\u041c\u0438\u0445\u0430\u0438\u043b \u0413\u043e'
            '\u0440\u0431\u0430\u0447\u0451\u0432.mkv'
        )
        filepath3 = "Alisher ibn G'iyosiddin Navoiy.mkv"
        filepath4 = 'Ascii title.mkv'
        filepath5 = '\u09b8\u09c1\u0995\u09c1\u09ae\u09be\u09b0 \u09b0\u09be\u09df.mkv'

        ti = TorrentInfo(filename)
        files_tree = ti.files_tree['unicode_filenames']
        self.assertIn(filepath1, files_tree)
        self.assertIn(filepath2, files_tree)
        self.assertIn(filepath3, files_tree)
        self.assertIn(filepath4, files_tree)
        self.assertIn(filepath5, files_tree)

        result_files = [
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath3,
                'size': 126158658,
            },
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath4,
                'size': 189321363,
            },
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath2,
                'size': 106649699,
            },
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath5,
                'size': 21590269,
            },
            {'download': True, 'path': 'unicode_filenames/' + filepath1, 'size': 1771},
        ]

        assertCountEqual(self, ti.files, result_files)
