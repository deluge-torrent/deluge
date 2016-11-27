import os

from twisted.trial import unittest

from deluge.common import (VersionSplit, fdate, fpcnt, fpeer, fsize, fspeed, ftime, get_path_size, is_infohash, is_ip,
                           is_ipv4, is_ipv6, is_magnet, is_url)
from deluge.ui.translations_util import setup_translations


class CommonTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        setup_translations()

    def tearDown(self):  # NOQA
        pass

    def test_fsize(self):
        self.assertEquals(fsize(0), '0 B')
        self.assertEquals(fsize(100), '100 B')
        self.assertEquals(fsize(1023), '1023 B')
        self.assertEquals(fsize(1024), '1.0 KiB')
        self.assertEquals(fsize(1048575), '1024.0 KiB')
        self.assertEquals(fsize(1048576), '1.0 MiB')
        self.assertEquals(fsize(1073741823), '1024.0 MiB')
        self.assertEquals(fsize(1073741824), '1.0 GiB')
        self.assertEquals(fsize(112245), '109.6 KiB')
        self.assertEquals(fsize(110723441824), '103.1 GiB')
        self.assertEquals(fsize(1099511627775), '1024.0 GiB')
        self.assertEquals(fsize(1099511627777), '1.0 TiB')
        self.assertEquals(fsize(766148267453245), '696.8 TiB')

    def test_fpcnt(self):
        self.failUnless(fpcnt(0.9311) == '93.11%')

    def test_fspeed(self):
        self.failUnless(fspeed(43134) == '42.1 KiB/s')

    def test_fpeer(self):
        self.failUnless(fpeer(10, 20) == '10 (20)')
        self.failUnless(fpeer(10, -1) == '10')

    def test_ftime(self):
        self.failUnless(ftime(0) == '')
        self.failUnless(ftime(5) == '5s')
        self.failUnless(ftime(100) == '1m 40s')
        self.failUnless(ftime(3789) == '1h 3m')
        self.failUnless(ftime(23011) == '6h 23m')
        self.failUnless(ftime(391187) == '4d 12h')
        self.failUnless(ftime(604800) == '1w 0d')
        self.failUnless(ftime(13893086) == '22w 6d')
        self.failUnless(ftime(59740269) == '1y 46w')

    def test_fdate(self):
        self.failUnless(fdate(-1) == '')

    def test_is_url(self):
        self.failUnless(is_url('http://deluge-torrent.org'))
        self.failIf(is_url('file://test.torrent'))

    def test_is_magnet(self):
        self.failUnless(is_magnet('magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN'))

    def test_is_infohash(self):
        self.failUnless(is_infohash('2dc5d0e71a66fe69649a640d39cb00a259704973'))

    def test_get_path_size(self):
        self.failUnless(get_path_size(os.devnull) == 0)
        self.failUnless(get_path_size('non-existant.file') == -1)

    def test_is_ip(self):
        self.failUnless(is_ip('192.0.2.0'))
        self.failIf(is_ip('192..0.0'))
        self.failUnless(is_ip('2001:db8::'))
        self.failIf(is_ip('2001:db8:'))

    def test_is_ipv4(self):
        self.failUnless(is_ipv4('192.0.2.0'))
        self.failIf(is_ipv4('192..0.0'))

    def test_is_ipv6(self):
        self.failUnless(is_ipv6('2001:db8::'))
        self.failIf(is_ipv6('2001:db8:'))

    def test_version_split(self):
        self.failUnless(VersionSplit('1.2.2') == VersionSplit('1.2.2'))
        self.failUnless(VersionSplit('1.2.1') < VersionSplit('1.2.2'))
        self.failUnless(VersionSplit('1.1.9') < VersionSplit('1.2.2'))
        self.failUnless(VersionSplit('1.2.2') > VersionSplit('1.2.1'))
        self.failUnless(VersionSplit('1.2.2') < VersionSplit('1.2.2-dev'))
        self.failUnless(VersionSplit('1.2.2-dev') < VersionSplit('1.3.0-rc2'))
        self.failUnless(VersionSplit('1.2.2') > VersionSplit('1.2.2-rc2'))
        self.failUnless(VersionSplit('1.2.2-rc2-dev') > VersionSplit('1.2.2-rc2'))
        self.failUnless(VersionSplit('1.2.2-rc3') > VersionSplit('1.2.2-rc2'))
        self.failUnless(VersionSplit('0.14.9') == VersionSplit('0.14.9'))
        self.failUnless(VersionSplit('0.14.9') > VersionSplit('0.14.5'))
        self.failUnless(VersionSplit('0.14.10') >= VersionSplit('0.14.9'))
        self.failUnless(VersionSplit('1.4.0') > VersionSplit('1.3.900.dev123'))
        self.failUnless(VersionSplit('1.3.2rc2.dev1') < VersionSplit('1.3.2-rc2'))
        self.failUnless(VersionSplit('1.3.900.dev888') > VersionSplit('1.3.900.dev123'))
        self.failUnless(VersionSplit('1.4.0') > VersionSplit('1.4.0.dev123'))
        self.failUnless(VersionSplit('1.4.0.dev1') < VersionSplit('1.4.0'))
        self.failUnless(VersionSplit('1.4.0a1') < VersionSplit('1.4.0'))

    def test_parse_human_size(self):
        from deluge.common import parse_human_size
        sizes = [('1', 1),
                 ('10 bytes', 10),
                 ('2048 bytes', 2048),
                 ('1MiB', 2**(10 * 2)),
                 ('1 MiB', 2**(10 * 2)),
                 ('1 GiB', 2**(10 * 3)),
                 ('1 GiB', 2**(10 * 3)),
                 ('1M', 10**6),
                 ('1MB', 10**6),
                 ('1 GB', 10**9),
                 ('1 TB', 10**12)]

        for human_size, byte_size in sizes:
            parsed = parse_human_size(human_size)
            self.assertEquals(parsed, byte_size, 'Mismatch when converting: %s' % human_size)
