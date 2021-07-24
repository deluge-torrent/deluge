# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import os
import sys
import tarfile

from twisted.trial import unittest

from deluge.common import (
    VersionSplit,
    archive_files,
    fdate,
    fpcnt,
    fpeer,
    fsize,
    fspeed,
    ftime,
    get_path_size,
    is_infohash,
    is_ip,
    is_ipv4,
    is_ipv6,
    is_magnet,
    is_url,
    windows_check,
)
from deluge.i18n import setup_translation

from .common import get_test_data_file, set_tmp_config_dir


class CommonTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        self.config_dir = set_tmp_config_dir()
        setup_translation()

    def tearDown(self):  # NOQA
        pass

    def test_fsize(self):
        self.assertEqual(fsize(0), '0 B')
        self.assertEqual(fsize(100), '100 B')
        self.assertEqual(fsize(1023), '1023 B')
        self.assertEqual(fsize(1024), '1.0 KiB')
        self.assertEqual(fsize(1048575), '1024.0 KiB')
        self.assertEqual(fsize(1048576), '1.0 MiB')
        self.assertEqual(fsize(1073741823), '1024.0 MiB')
        self.assertEqual(fsize(1073741824), '1.0 GiB')
        self.assertEqual(fsize(112245), '109.6 KiB')
        self.assertEqual(fsize(110723441824), '103.1 GiB')
        self.assertEqual(fsize(1099511627775), '1024.0 GiB')
        self.assertEqual(fsize(1099511627777), '1.0 TiB')
        self.assertEqual(fsize(766148267453245), '696.8 TiB')

    def test_fpcnt(self):
        self.assertTrue(fpcnt(0.9311) == '93.11%')

    def test_fspeed(self):
        self.assertTrue(fspeed(43134) == '42.1 KiB/s')

    def test_fpeer(self):
        self.assertTrue(fpeer(10, 20) == '10 (20)')
        self.assertTrue(fpeer(10, -1) == '10')

    def test_ftime(self):
        self.assertEqual(ftime(0), '')
        self.assertEqual(ftime(5), '5s')
        self.assertEqual(ftime(100), '1m 40s')
        self.assertEqual(ftime(3789), '1h 3m')
        self.assertEqual(ftime(23011), '6h 23m')
        self.assertEqual(ftime(391187), '4d 12h')
        self.assertEqual(ftime(604800), '1w 0d')
        self.assertEqual(ftime(13893086), '22w 6d')
        self.assertEqual(ftime(59740269), '1y 46w')
        self.assertEqual(ftime(61.25), '1m 1s')
        self.assertEqual(ftime(119.9), '1m 59s')

    def test_fdate(self):
        self.assertTrue(fdate(-1) == '')

    def test_is_url(self):
        self.assertTrue(is_url('http://deluge-torrent.org'))
        self.assertFalse(is_url('file://test.torrent'))

    def test_is_magnet(self):
        self.assertTrue(
            is_magnet('magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN')
        )
        self.assertFalse(is_magnet(None))

    def test_is_infohash(self):
        self.assertTrue(is_infohash('2dc5d0e71a66fe69649a640d39cb00a259704973'))

    def test_get_path_size(self):
        if windows_check() and sys.version_info < (3, 8):
            # https://bugs.python.org/issue1311
            raise unittest.SkipTest('os.devnull returns False on Windows')
        self.assertTrue(get_path_size(os.devnull) == 0)
        self.assertTrue(get_path_size('non-existant.file') == -1)

    def test_is_ip(self):
        self.assertTrue(is_ip('192.0.2.0'))
        self.assertFalse(is_ip('192..0.0'))
        self.assertTrue(is_ip('2001:db8::'))
        self.assertFalse(is_ip('2001:db8:'))

    def test_is_ipv4(self):
        self.assertTrue(is_ipv4('192.0.2.0'))
        self.assertFalse(is_ipv4('192..0.0'))

    def test_is_ipv6(self):
        self.assertTrue(is_ipv6('2001:db8::'))
        self.assertFalse(is_ipv6('2001:db8:'))

    def test_version_split(self):
        self.assertTrue(VersionSplit('1.2.2') == VersionSplit('1.2.2'))
        self.assertTrue(VersionSplit('1.2.1') < VersionSplit('1.2.2'))
        self.assertTrue(VersionSplit('1.1.9') < VersionSplit('1.2.2'))
        self.assertTrue(VersionSplit('1.2.2') > VersionSplit('1.2.1'))
        self.assertTrue(VersionSplit('1.2.2') > VersionSplit('1.2.2-dev0'))
        self.assertTrue(VersionSplit('1.2.2-dev') < VersionSplit('1.3.0-rc2'))
        self.assertTrue(VersionSplit('1.2.2') > VersionSplit('1.2.2-rc2'))
        self.assertTrue(VersionSplit('1.2.2-rc2-dev') < VersionSplit('1.2.2-rc2'))
        self.assertTrue(VersionSplit('1.2.2-rc3') > VersionSplit('1.2.2-rc2'))
        self.assertTrue(VersionSplit('0.14.9') == VersionSplit('0.14.9'))
        self.assertTrue(VersionSplit('0.14.9') > VersionSplit('0.14.5'))
        self.assertTrue(VersionSplit('0.14.10') >= VersionSplit('0.14.9'))
        self.assertTrue(VersionSplit('1.4.0') > VersionSplit('1.3.900.dev123'))
        self.assertTrue(VersionSplit('1.3.2rc2.dev1') < VersionSplit('1.3.2-rc2'))
        self.assertTrue(VersionSplit('1.3.900.dev888') > VersionSplit('1.3.900.dev123'))
        self.assertTrue(VersionSplit('1.4.0') > VersionSplit('1.4.0.dev123'))
        self.assertTrue(VersionSplit('1.4.0.dev1') < VersionSplit('1.4.0'))
        self.assertTrue(VersionSplit('1.4.0a1') < VersionSplit('1.4.0'))

    def test_parse_human_size(self):
        from deluge.common import parse_human_size

        sizes = [
            ('1', 1),
            ('10 bytes', 10),
            ('2048 bytes', 2048),
            ('1MiB', 2 ** (10 * 2)),
            ('1 MiB', 2 ** (10 * 2)),
            ('1 GiB', 2 ** (10 * 3)),
            ('1 GiB', 2 ** (10 * 3)),
            ('1M', 10 ** 6),
            ('1MB', 10 ** 6),
            ('1 GB', 10 ** 9),
            ('1 TB', 10 ** 12),
        ]

        for human_size, byte_size in sizes:
            parsed = parse_human_size(human_size)
            self.assertEqual(
                parsed, byte_size, 'Mismatch when converting: %s' % human_size
            )

    def test_archive_files(self):
        arc_filelist = [
            get_test_data_file('test.torrent'),
            get_test_data_file('deluge.png'),
        ]
        arc_filepath = archive_files('test-arc', arc_filelist)

        with tarfile.open(arc_filepath, 'r') as tar:
            for tar_info in tar:
                self.assertTrue(tar_info.isfile())
                self.assertTrue(
                    tar_info.name in [os.path.basename(arcf) for arcf in arc_filelist]
                )

    def test_archive_files_missing(self):
        """Archive exists even with file not found."""
        filelist = ['test.torrent', 'deluge.png', 'missing.file']
        arc_filepath = archive_files(
            'test-arc', [get_test_data_file(f) for f in filelist]
        )
        filelist.remove('missing.file')

        with tarfile.open(arc_filepath, 'r') as tar:
            self.assertEqual(tar.getnames(), filelist)
            self.assertTrue(all(tarinfo.isfile() for tarinfo in tar))

    def test_archive_files_message(self):
        filelist = ['test.torrent', 'deluge.png']
        arc_filepath = archive_files(
            'test-arc', [get_test_data_file(f) for f in filelist], message='test'
        )

        result_files = filelist + ['archive_message.txt']
        with tarfile.open(arc_filepath, 'r') as tar:
            self.assertEqual(tar.getnames(), result_files)
            for tar_info in tar:
                self.assertTrue(tar_info.isfile())
                if tar_info.name == 'archive_message.txt':
                    result = tar.extractfile(tar_info).read().decode()
                    self.assertEqual(result, 'test')
