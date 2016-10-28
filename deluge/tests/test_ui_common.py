# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from twisted.trial import unittest

from deluge.ui.common import TorrentInfo

from . import common


class UICommonTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        pass

    def tearDown(self):  # NOQA
        pass

    def test_utf8_encoded_paths(self):
        filename = common.rpath("test.torrent")
        ti = TorrentInfo(filename)
        self.assertTrue("azcvsupdater_2.6.2.jar" in ti.files_tree)

    def test_utf8_encoded_paths2(self):
        filename = common.rpath("unicode_filenames.torrent")
        ti = TorrentInfo(filename)

        files = ti.files_tree["unicode_filenames"]
        self.assertTrue("\xe3\x83\x86\xe3\x82\xaf\xe3\x82\xb9\xe3\x83\xbb\xe3\x83"
                        "\x86\xe3\x82\xaf\xe3\x82\xb5\xe3\x83\xb3.mkv" in files)
        self.assertTrue("\xd0\x9c\xd0\xb8\xd1\x85\xd0\xb0\xd0\xb8\xd0\xbb \xd0\x93"
                        "\xd0\xbe\xd1\x80\xd0\xb1\xd0\xb0\xd1\x87\xd1\x91\xd0\xb2.mkv" in files)
        self.assertTrue("Alisher ibn G'iyosiddin Navoiy.mkv" in files)
        self.assertTrue("Ascii title.mkv" in files)
        self.assertTrue("\xe0\xa6\xb8\xe0\xa7\x81\xe0\xa6\x95\xe0\xa7\x81\xe0\xa6"
                        "\xae\xe0\xa6\xbe\xe0\xa6\xb0 \xe0\xa6\xb0\xe0\xa6\xbe\xe0\xa7\x9f.mkv" in files)

    def test_torrent_info_json_dump(self):
        # This torrent file contains an uncommon field 'filehash' which must be hex
        # encoded to allow dumping the torrent info to json. Otherwise it will fail with:
        # UnicodeDecodeError: 'utf8' codec can't decode byte 0xe5 in position 0: invalid continuation byte
        filename = common.get_test_data_file("filehash_field.torrent")
        ti = TorrentInfo(filename, 2)
        files = ti.files_tree["contents"]["torrent_filehash"]["contents"]

        self.assertTrue("還在一個人無聊嗎~還不趕緊上來聊天美.txt" in files)
        json_lib.dumps(ti.as_dict("name", "info_hash", "files_tree"))
