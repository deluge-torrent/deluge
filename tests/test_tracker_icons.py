from twisted.trial import unittest

from deluge.ui.tracker_icons import TrackerIcons, TrackerIcon
from deluge.log import setupLogger

# Must come before import common
setupLogger("debug", "debug.log")

import common

common.set_tmp_config_dir()
icons = TrackerIcons()

class TrackerIconsTestCase(unittest.TestCase):
    def test_get_deluge_png(self):
        # Deluge has a png favicon link
        icon = TrackerIcon("../deluge.png")
        d = icons.get("deluge-torrent.org")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_google_ico(self):
        # Google doesn't have any icon links
        # So instead we'll grab its favicon.ico
        icon = TrackerIcon("../google.ico")
        d = icons.get("www.google.com")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_google_ico_with_redirect(self):
        # google.com redirects to www.google.com
        icon = TrackerIcon("../google.ico")
        d = icons.get("google.com")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_ubuntu_ico(self):
        # ubuntu.com has inline css which causes HTMLParser issues
        icon = TrackerIcon("../ubuntu.ico")
        d = icons.get("www.ubuntu.com")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_openbt_png(self):
        # openbittorrent.com has an incorrect type (image/gif)
        icon = TrackerIcon("../openbt.png")
        d = icons.get("openbittorrent.com")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_publicbt_ico(self):
        icon = TrackerIcon("../publicbt.ico")
        d = icons.get("publicbt.org")
        d.addCallback(self.assertNotIdentical, None)
        d.addCallback(self.assertEquals, icon)
        return d

    def test_get_empty_string_tracker(self):
        d = icons.get("")
        d.addCallback(self.assertIdentical, None)
        return d
