#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import pytest

from deluge import bencode

from . import common


class TestBencode:
    def test_bencode_unicode_metainfo(self):
        filename = common.get_test_data_file('test.torrent')
        with open(filename, 'rb') as _file:
            metainfo = bencode.bdecode(_file.read())[b'info']
        bencode.bencode({b'info': metainfo})

    def test_bencode_unicode_value(self):
        assert bencode.bencode(b'abc') == b'3:abc'
        assert bencode.bencode('abc') == b'3:abc'

    def test_bdecode(self):
        assert bencode.bdecode(b'3:dEf') == b'dEf'
        with pytest.raises(bencode.BTFailure):
            bencode.bdecode('dEf')
        with pytest.raises(bencode.BTFailure):
            bencode.bdecode(b'dEf')
        with pytest.raises(bencode.BTFailure):
            bencode.bdecode({'dEf': 123})
