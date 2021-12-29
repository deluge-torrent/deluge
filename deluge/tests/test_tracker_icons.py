# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import pytest

import deluge.component as component
import deluge.ui.tracker_icons
from deluge.ui.tracker_icons import TrackerIcon, TrackerIcons

from . import common
from .basetest import BaseTestCase

common.set_tmp_config_dir()
deluge.ui.tracker_icons.PIL_INSTALLED = False
common.disable_new_release_check()


@pytest.mark.internet
class TrackerIconsTestCase(BaseTestCase):

    # if windows_check():
    #     skip = 'cannot use os.path.samefile to compair on windows(unix only)'

    def set_up(self):
        # Disable resizing with Pillow for consistency.
        self.patch(deluge.ui.tracker_icons, 'Image', None)
        self.icons = TrackerIcons()

    def tear_down(self):
        return component.shutdown()

    def test_get_deluge_png(self):
        # Deluge has a png favicon link
        icon = TrackerIcon(common.get_test_data_file('deluge.png'))
        d = self.icons.fetch('deluge-torrent.org')
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEqual, icon)
        return d

    def test_get_google_ico(self):
        # Google doesn't have any icon links
        # So instead we'll grab its favicon.ico
        icon = TrackerIcon(common.get_test_data_file('google.ico'))
        d = self.icons.fetch('www.google.com')
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEqual, icon)
        return d

    def test_get_google_ico_with_redirect(self):
        # google.com redirects to www.google.com
        icon = TrackerIcon(common.get_test_data_file('google.ico'))
        d = self.icons.fetch('google.com')
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEqual, icon)
        return d

    def test_get_seo_ico_with_sni(self):
        # seo using certificates with SNI support only
        icon = TrackerIcon(common.get_test_data_file('seo.svg'))
        d = self.icons.fetch('www.seo.com')
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEqual, icon)
        return d

    def test_get_empty_string_tracker(self):
        d = self.icons.fetch('')
        d.addCallback(self.assertIdentical, None)
        return d
