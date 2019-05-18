# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import unicode_literals

from twisted.trial import unittest

from deluge import bencode

from . import common


class BencodeTestCase(unittest.TestCase):
    def test_bencode_unicode_metainfo(self):
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            metainfo = bencode.bdecode(_file.read())[b'info']
        bencode.bencode({b'info': metainfo})

    def test_bencode_unicode_value(self):
        self.assertEqual(bencode.bencode(b'abc'), b'3:abc')
        self.assertEqual(bencode.bencode('abc'), b'3:abc')

    def test_bdecode(self):
        self.assertEqual(bencode.bdecode(b'3:dEf'), b'dEf')
        with self.assertRaises(bencode.BTFailure):
            bencode.bdecode('dEf')
        with self.assertRaises(bencode.BTFailure):
            bencode.bdecode(b'dEf')
        with self.assertRaises(bencode.BTFailure):
            bencode.bdecode({'dEf': 123})
