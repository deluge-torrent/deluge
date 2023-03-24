#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import os.path

import pytest

import deluge.component as component
import deluge.ui.tracker_icons
from deluge.conftest import BaseTestCase
from deluge.ui.tracker_icons import TrackerIcon, TrackerIcons

from . import common

common.disable_new_release_check()


@pytest.mark.internet
class TestTrackerIcons(BaseTestCase):
    def set_up(self):
        # Disable resizing with Pillow for consistency.
        self.patch(deluge.ui.tracker_icons, 'Image', None)
        self.icons = TrackerIcons()

    def tear_down(self):
        return component.shutdown()

    async def test_get_deluge_png(self, mock_mkstemp):
        # Deluge has a png favicon link
        icon = TrackerIcon(common.get_test_data_file('deluge.png'))
        result = await self.icons.fetch('deluge-torrent.org')
        assert result == icon
        assert not os.path.isfile(mock_mkstemp[1])

    async def test_get_google_ico(self):
        # Google doesn't have any icon links
        # So instead we'll grab its favicon.ico
        icon = TrackerIcon(common.get_test_data_file('google.ico'))
        result = await self.icons.fetch('www.google.com')
        assert result == icon

    async def test_get_google_ico_hebrew(self):
        """Test that Google.co.il page is read as UTF-8"""
        icon = TrackerIcon(common.get_test_data_file('google.ico'))
        result = await self.icons.fetch('www.google.co.il')
        assert result == icon

    async def test_get_google_ico_with_redirect(self):
        # google.com redirects to www.google.com
        icon = TrackerIcon(common.get_test_data_file('google.ico'))
        result = await self.icons.fetch('google.com')
        assert result == icon

    @pytest.mark.skip(reason='Site removed favicon, new SNI test will be needed')
    async def test_get_seo_svg_with_sni(self):
        # seo using certificates with SNI support only
        icon = TrackerIcon(common.get_test_data_file('seo.svg'))
        result = await self.icons.fetch('www.seo.com')
        assert result == icon

    async def test_get_empty_string_tracker(self):
        result = await self.icons.fetch('')
        assert result is None

    async def test_invalid_host(self, mock_mkstemp):
        """Test that TrackerIcon can handle invalid hostname"""
        result = await self.icons.fetch('deluge.example.com')
        assert not result
        assert not os.path.isfile(mock_mkstemp[1])
