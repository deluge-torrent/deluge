from twisted.trial import unittest
from deluge.common import *
import os

class CommonTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fsize(self):
        self.failUnless(fsize(112245) == "109.6 KiB")

    def test_fpcnt(self):
        self.failUnless(fpcnt(0.9311) == "93.11%")

    def test_fspeed(self):
        self.failUnless(fspeed(43134) == "42.1 KiB/s")

    def test_fpeer(self):
        self.failUnless(fpeer(10, 20) == "10 (20)")
        self.failUnless(fpeer(10, -1) == "10")

    def test_ftime(self):
        self.failUnless(ftime(23011) == "6h 23m")

    def test_fdate(self):
        self.failUnless(fdate(-1) == "")

    def test_is_url(self):
        self.failUnless(is_url("http://deluge-torrent.org"))
        self.failIf(is_url("file://test.torrent"))

    def test_is_magnet(self):
        self.failUnless(is_magnet("magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN"))

    def test_get_path_size(self):
        self.failUnless(get_path_size(os.devnull) == 0)
        self.failUnless(get_path_size("non-existant.file") == -1)

    def test_is_ip(self):
        self.failUnless(is_ip("127.0.0.1"))
        self.failIf(is_ip("127..0.0"))

    def test_VersionSplit(self):
        self.failUnless(VersionSplit("1.2.2") == VersionSplit("1.2.2"))
        self.failUnless(VersionSplit("1.2.1") < VersionSplit("1.2.2"))
        self.failUnless(VersionSplit("1.1.9") < VersionSplit("1.2.2"))
        self.failUnless(VersionSplit("1.2.2") > VersionSplit("1.2.1"))
        self.failIf(VersionSplit("1.2.2") == VersionSplit("1.2.2-dev"))
        self.failUnless(VersionSplit("0.14.9") == VersionSplit("0.14.9"))
        self.failUnless(VersionSplit("0.14.9") > VersionSplit("0.14.5"))
        self.failUnless(VersionSplit("0.14.10") >= VersionSplit("0.14.9"))
