#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import sys
from unittest import mock

import pytest


@pytest.mark.gtkui
class TestGTK3Common:
    def setUp(self):
        sys.modules['gi.repository'] = mock.MagicMock()

    def tearDown(self):
        pass

    def test_cmp(self):
        from deluge.ui.gtk3.common import cmp

        assert cmp(None, None) == 0
        assert cmp(1, None) == 1
        assert cmp(0, None) == 1
        assert cmp(None, 7) == -1
        assert cmp(None, 'bar') == -1
        assert cmp('foo', None) == 1
        assert cmp('', None) == 1
