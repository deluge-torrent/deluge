from twisted.trial import unittest

from deluge.ui.tracker_icons import TrackerIcons, TrackerIcon
from deluge.log import setupLogger

# Must come before import common
setupLogger("debug", "debug.log")

import common

common.set_tmp_config_dir()
icons = TrackerIcons()

class TrackerIconsTestCase(unittest.TestCase):
    def test_get_png(self):
        # Deluge has a png favicon link
        icon = TrackerIcon("../deluge.png")
        d = icons.get("deluge-torrent.org")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_ico(self):
        # Google doesn't have any icon links
        # So instead we'll grab its favicon.ico
        icon = TrackerIcon("../google.ico")
        d = icons.get("www.google.com")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_ico_with_redirect(self):
        # google.com redirects to www.google.com
        icon = TrackerIcon("../google.ico")
        d = icons.get("google.com")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d
