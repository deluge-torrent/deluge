import os

from twisted.trial import unittest

from deluge.common import (VersionSplit, fdate, fpcnt, fpeer, fsize, fspeed, ftime, get_path_size, is_ip, is_magnet,
                           is_url, setup_translations)


class CommonTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        setup_translations()

    def tearDown(self):  # NOQA
        pass

    def test_fsize(self):
        self.assertEquals(fsize(100), "100 Bytes")
        self.assertEquals(fsize(1023), "1023 Bytes")
        self.assertEquals(fsize(1024), "1.0 KiB")
        self.assertEquals(fsize(1048575), "1024.0 KiB")
        self.assertEquals(fsize(1048576), "1.0 MiB")
        self.assertEquals(fsize(1073741823), "1024.0 MiB")
        self.assertEquals(fsize(1073741824), "1.0 GiB")
        self.assertEquals(fsize(112245), "109.6 KiB")
        self.assertEquals(fsize(110723441824), "103.1 GiB")

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

    def test_version_split(self):
        self.failUnless(VersionSplit("1.2.2") == VersionSplit("1.2.2"))
        self.failUnless(VersionSplit("1.2.1") < VersionSplit("1.2.2"))
        self.failUnless(VersionSplit("1.1.9") < VersionSplit("1.2.2"))
        self.failUnless(VersionSplit("1.2.2") > VersionSplit("1.2.1"))
        self.failUnless(VersionSplit("1.2.2") < VersionSplit("1.2.2-dev"))
        self.failUnless(VersionSplit("1.2.2-dev") < VersionSplit("1.3.0-rc2"))
        self.failUnless(VersionSplit("1.2.2") > VersionSplit("1.2.2-rc2"))
        self.failUnless(VersionSplit("1.2.2-rc2-dev") > VersionSplit("1.2.2-rc2"))
        self.failUnless(VersionSplit("1.2.2-rc3") > VersionSplit("1.2.2-rc2"))
        self.failUnless(VersionSplit("0.14.9") == VersionSplit("0.14.9"))
        self.failUnless(VersionSplit("0.14.9") > VersionSplit("0.14.5"))
        self.failUnless(VersionSplit("0.14.10") >= VersionSplit("0.14.9"))
        self.failUnless(VersionSplit("1.4.0") > VersionSplit("1.3.900.dev123"))
        self.failUnless(VersionSplit("1.3.2rc2.dev1") < VersionSplit("1.3.2-rc2"))
        self.failUnless(VersionSplit("1.3.900.dev888") > VersionSplit("1.3.900.dev123"))
        self.failUnless(VersionSplit("1.4.0") > VersionSplit("1.4.0.dev123"))
        self.failUnless(VersionSplit("1.4.0.dev1") < VersionSplit("1.4.0"))
        self.failUnless(VersionSplit("1.4.0a1") < VersionSplit("1.4.0"))
