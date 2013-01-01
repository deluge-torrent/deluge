# -*- coding: utf-8 -*-
from twisted.trial import unittest
import os
from deluge.ui.common import TorrentInfo

class UICommonTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_utf8_encoded_paths(self):
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        ti = TorrentInfo(filename)
        self.assertTrue(ti.files_tree.has_key("azcvsupdater_2.6.2.jar"))

    def test_utf8_encoded_paths2(self):
        filename = os.path.join(os.path.dirname(__file__), "unicode_filenames.torrent")
        ti = TorrentInfo(filename)

        files = ti.files_tree["unicode_filenames"]
        self.assertTrue(files.has_key("\xe3\x83\x86\xe3\x82\xaf\xe3\x82\xb9\xe3\x83\xbb\xe3\x83"
                                      "\x86\xe3\x82\xaf\xe3\x82\xb5\xe3\x83\xb3.mkv"))
        self.assertTrue(files.has_key("\xd0\x9c\xd0\xb8\xd1\x85\xd0\xb0\xd0\xb8\xd0\xbb \xd0\x93"
                                      "\xd0\xbe\xd1\x80\xd0\xb1\xd0\xb0\xd1\x87\xd1\x91\xd0\xb2.mkv"))
        self.assertTrue(files.has_key("Alisher ibn G'iyosiddin Navoiy.mkv"))
        self.assertTrue(files.has_key("Ascii title.mkv"))
        self.assertTrue(files.has_key("\xe0\xa6\xb8\xe0\xa7\x81\xe0\xa6\x95\xe0\xa7\x81\xe0\xa6"
                                      "\xae\xe0\xa6\xbe\xe0\xa6\xb0 \xe0\xa6\xb0\xe0\xa6\xbe\xe0\xa7\x9f.mkv"))
