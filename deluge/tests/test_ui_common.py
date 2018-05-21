# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import unicode_literals

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
        ti = TorrentInfo(filename)

        files = ti.files_tree['unicode_filenames']
        self.assertTrue(
            (
                b'\xe3\x83\x86\xe3\x82\xaf\xe3\x82\xb9\xe3\x83\xbb\xe3\x83'
                b'\x86\xe3\x82\xaf\xe3\x82\xb5\xe3\x83\xb3.mkv'
            ).decode('utf8') in files,
        )
        self.assertTrue(
            (
                b'\xd0\x9c\xd0\xb8\xd1\x85\xd0\xb0\xd0\xb8\xd0\xbb \xd0\x93'
                b'\xd0\xbe\xd1\x80\xd0\xb1\xd0\xb0\xd1\x87\xd1\x91\xd0\xb2.mkv'
            ).decode('utf8') in files,
        )
        self.assertTrue(b"Alisher ibn G'iyosiddin Navoiy.mkv".decode('utf8') in files)
        self.assertTrue(b'Ascii title.mkv'.decode('utf8') in files)
        self.assertTrue(
            (
                b'\xe0\xa6\xb8\xe0\xa7\x81\xe0\xa6\x95\xe0\xa7\x81\xe0\xa6\xae\xe0\xa6\xbe'
                b'\xe0\xa6\xb0 \xe0\xa6\xb0\xe0\xa6\xbe\xe0\xa7\x9f.mkv'
            ).decode('utf8') in files,
        )
