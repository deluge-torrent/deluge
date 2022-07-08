#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import sys
import tarfile
from urllib.parse import quote_plus

import pytest

from deluge.common import (
    VersionSplit,
    archive_files,
    fdate,
    fpcnt,
    fpeer,
    fsize,
    fspeed,
    ftime,
    get_magnet_info,
    get_path_size,
    is_infohash,
    is_interface,
    is_interface_name,
    is_ip,
    is_ipv4,
    is_ipv6,
    is_magnet,
    is_url,
    windows_check,
)

from .common import get_test_data_file


class TestCommon:
    def test_fsize(self):
        assert fsize(0) == '0 B'
        assert fsize(100) == '100 B'
        assert fsize(1023) == '1023 B'
        assert fsize(1024) == '1.0 KiB'
        assert fsize(1048575) == '1024.0 KiB'
        assert fsize(1048576) == '1.0 MiB'
        assert fsize(1073741823) == '1024.0 MiB'
        assert fsize(1073741824) == '1.0 GiB'
        assert fsize(112245) == '109.6 KiB'
        assert fsize(110723441824) == '103.1 GiB'
        assert fsize(1099511627775) == '1024.0 GiB'
        assert fsize(1099511627777) == '1.0 TiB'
        assert fsize(766148267453245) == '696.8 TiB'

    def test_fpcnt(self):
        assert fpcnt(0.9311) == '93.11%'

    def test_fspeed(self):
        assert fspeed(43134) == '42.1 KiB/s'

    def test_fpeer(self):
        assert fpeer(10, 20) == '10 (20)'
        assert fpeer(10, -1) == '10'

    def test_ftime(self):
        assert ftime(0) == ''
        assert ftime(5) == '5s'
        assert ftime(100) == '1m 40s'
        assert ftime(3789) == '1h 3m'
        assert ftime(23011) == '6h 23m'
        assert ftime(391187) == '4d 12h'
        assert ftime(604800) == '1w 0d'
        assert ftime(13893086) == '22w 6d'
        assert ftime(59740269) == '1y 46w'
        assert ftime(61.25) == '1m 1s'
        assert ftime(119.9) == '1m 59s'

    def test_fdate(self):
        assert fdate(-1) == ''

    def test_is_url(self):
        assert is_url('http://deluge-torrent.org')
        assert not is_url('file://test.torrent')

    def test_is_magnet(self):
        assert is_magnet('magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN')
        assert not is_magnet(None)

    def test_is_infohash(self):
        assert is_infohash('2dc5d0e71a66fe69649a640d39cb00a259704973')

    def test_get_path_size(self):
        if windows_check() and sys.version_info < (3, 8):
            # https://bugs.python.org/issue1311
            pytest.skip('os.devnull returns False on Windows')
        assert get_path_size(os.devnull) == 0
        assert get_path_size('non-existant.file') == -1

    def test_is_ip(self):
        assert is_ip('192.0.2.0')
        assert not is_ip('192..0.0')
        assert is_ip('2001:db8::')
        assert not is_ip('2001:db8:')

    def test_is_ipv4(self):
        assert is_ipv4('192.0.2.0')
        assert not is_ipv4('192..0.0')

    def test_is_ipv6(self):
        assert is_ipv6('2001:db8::')
        assert not is_ipv6('2001:db8:')

    def test_is_interface_name(self):
        if windows_check():
            assert not is_interface_name('2001:db8:')
            assert not is_interface_name('{THIS0000-IS00-ONLY-FOR0-TESTING00000}')
        else:
            assert is_interface_name('lo')
            assert not is_interface_name('127.0.0.1')
            assert not is_interface_name('eth01101')

    def test_is_interface(self):
        if windows_check():
            assert is_interface('127.0.0.1')
            assert not is_interface('127')
            assert not is_interface('{THIS0000-IS00-ONLY-FOR0-TESTING00000}')
        else:
            assert is_interface('lo')
            assert is_interface('127.0.0.1')
            assert not is_interface('127.')
            assert not is_interface('eth01101')

    def test_version_split(self):
        assert VersionSplit('1.2.2') == VersionSplit('1.2.2')
        assert VersionSplit('1.2.1') < VersionSplit('1.2.2')
        assert VersionSplit('1.1.9') < VersionSplit('1.2.2')
        assert VersionSplit('1.2.2') > VersionSplit('1.2.1')
        assert VersionSplit('1.2.2') > VersionSplit('1.2.2-dev0')
        assert VersionSplit('1.2.2-dev') < VersionSplit('1.3.0-rc2')
        assert VersionSplit('1.2.2') > VersionSplit('1.2.2-rc2')
        assert VersionSplit('1.2.2-rc2-dev') < VersionSplit('1.2.2-rc2')
        assert VersionSplit('1.2.2-rc3') > VersionSplit('1.2.2-rc2')
        assert VersionSplit('0.14.9') == VersionSplit('0.14.9')
        assert VersionSplit('0.14.9') > VersionSplit('0.14.5')
        assert VersionSplit('0.14.10') >= VersionSplit('0.14.9')
        assert VersionSplit('1.4.0') > VersionSplit('1.3.900.dev123')
        assert VersionSplit('1.3.2rc2.dev1') < VersionSplit('1.3.2-rc2')
        assert VersionSplit('1.3.900.dev888') > VersionSplit('1.3.900.dev123')
        assert VersionSplit('1.4.0') > VersionSplit('1.4.0.dev123')
        assert VersionSplit('1.4.0.dev1') < VersionSplit('1.4.0')
        assert VersionSplit('1.4.0a1') < VersionSplit('1.4.0')

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
            ('1M', 10**6),
            ('1MB', 10**6),
            ('1 GB', 10**9),
            ('1 TB', 10**12),
        ]

        for human_size, byte_size in sizes:
            parsed = parse_human_size(human_size)
            assert parsed == byte_size, 'Mismatch when converting: %s' % human_size

    def test_archive_files(self):
        arc_filelist = [
            get_test_data_file('test.torrent'),
            get_test_data_file('deluge.png'),
        ]
        arc_filepath = archive_files('test-arc', arc_filelist)

        with tarfile.open(arc_filepath, 'r') as tar:
            for tar_info in tar:
                assert tar_info.isfile()
                assert tar_info.name in [
                    os.path.basename(arcf) for arcf in arc_filelist
                ]

    def test_archive_files_missing(self):
        """Archive exists even with file not found."""
        filelist = ['test.torrent', 'deluge.png', 'missing.file']
        arc_filepath = archive_files(
            'test-arc', [get_test_data_file(f) for f in filelist]
        )
        filelist.remove('missing.file')

        with tarfile.open(arc_filepath, 'r') as tar:
            assert tar.getnames() == filelist
            assert all(tarinfo.isfile() for tarinfo in tar)

    def test_archive_files_message(self):
        filelist = ['test.torrent', 'deluge.png']
        arc_filepath = archive_files(
            'test-arc', [get_test_data_file(f) for f in filelist], message='test'
        )

        result_files = filelist + ['archive_message.txt']
        with tarfile.open(arc_filepath, 'r') as tar:
            assert tar.getnames() == result_files
            for tar_info in tar:
                assert tar_info.isfile()
                if tar_info.name == 'archive_message.txt':
                    result = tar.extractfile(tar_info).read().decode()
                    assert result == 'test'

    def test_get_magnet_info_tiers(self):
        tracker1 = 'udp://tracker1.example.com'
        tracker2 = 'udp://tracker2.example.com'
        magnet = (
            'magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN'
            f'&tr.1={quote_plus(tracker1)}'
            f'&tr.2={quote_plus(tracker2)}'
        )
        result = get_magnet_info(magnet)
        assert result['info_hash'] == '953bad769164e8482c7785a21d12166f94b9e14d'
        assert result['trackers'][tracker1] == 1
        assert result['trackers'][tracker2] == 2
