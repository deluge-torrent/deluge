#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from deluge.ui.common import TorrentInfo

from . import common


class TestUICommon:
    def test_hash_optional_single_file(self):
        """Ensure single file with `ed2k` and `sha1` keys are not in filetree output."""
        filename = common.get_test_data_file('test.torrent')
        files_tree = {'azcvsupdater_2.6.2.jar': (0, 307949, True)}
        ti = TorrentInfo(filename, filetree=1)
        assert ti.files_tree == files_tree

        files_tree2 = {
            'contents': {
                'azcvsupdater_2.6.2.jar': {
                    'type': 'file',
                    'index': 0,
                    'length': 307949,
                    'download': True,
                }
            }
        }
        ti = TorrentInfo(filename, filetree=2)
        assert ti.files_tree == files_tree2

    def test_hash_optional_multi_file(self):
        """Ensure multi-file with `filehash` and `ed2k` are keys not in filetree output."""
        filename = common.get_test_data_file('filehash_field.torrent')
        files_tree = {
            'torrent_filehash': {
                'tull.txt': (0, 54, True),
                '還在一個人無聊嗎~還不趕緊上來聊天美.txt': (1, 54, True),
            }
        }
        ti = TorrentInfo(filename, filetree=1)
        assert ti.files_tree == files_tree

        files_tree2 = {
            'contents': {
                'torrent_filehash': {
                    'type': 'dir',
                    'contents': {
                        'tull.txt': {
                            'type': 'file',
                            'path': 'torrent_filehash/tull.txt',
                            'length': 54,
                            'index': 0,
                            'download': True,
                        },
                        '還在一個人無聊嗎~還不趕緊上來聊天美.txt': {
                            'type': 'file',
                            'path': 'torrent_filehash/還在一個人無聊嗎~還不趕緊上來聊天美.txt',
                            'length': 54,
                            'index': 1,
                            'download': True,
                        },
                    },
                    'length': 108,
                    'download': True,
                }
            },
            'type': 'dir',
        }
        ti = TorrentInfo(filename, filetree=2)
        assert ti.files_tree == files_tree2

    def test_hash_optional_md5sum(self):
        # Ensure `md5sum` key is not included in filetree output
        filename = common.get_test_data_file('md5sum.torrent')
        files_tree = {'test': {'lol': (0, 4, True), 'rofl': (1, 5, True)}}
        ti = TorrentInfo(filename, filetree=1)
        assert ti.files_tree == files_tree
        ti = TorrentInfo(filename, filetree=2)
        files_tree2 = {
            'contents': {
                'test': {
                    'type': 'dir',
                    'contents': {
                        'lol': {
                            'type': 'file',
                            'path': 'test/lol',
                            'index': 0,
                            'length': 4,
                            'download': True,
                        },
                        'rofl': {
                            'type': 'file',
                            'path': 'test/rofl',
                            'index': 1,
                            'length': 5,
                            'download': True,
                        },
                    },
                    'length': 9,
                    'download': True,
                }
            },
            'type': 'dir',
        }
        assert ti.files_tree == files_tree2

    def test_utf8_encoded_paths(self):
        filename = common.get_test_data_file('test.torrent')
        ti = TorrentInfo(filename)
        assert 'azcvsupdater_2.6.2.jar' in ti.files_tree

    def test_utf8_encoded_paths2(self):
        filename = common.get_test_data_file('unicode_filenames.torrent')
        filepath1 = '\u30c6\u30af\u30b9\u30fb\u30c6\u30af\u30b5\u30f3.mkv'
        filepath2 = (
            '\u041c\u0438\u0445\u0430\u0438\u043b \u0413\u043e'
            '\u0440\u0431\u0430\u0447\u0451\u0432.mkv'
        )
        filepath3 = "Alisher ibn G'iyosiddin Navoiy.mkv"
        filepath4 = 'Ascii title.mkv'
        filepath5 = '\u09b8\u09c1\u0995\u09c1\u09ae\u09be\u09b0 \u09b0\u09be\u09df.mkv'

        ti = TorrentInfo(filename)
        files_tree = ti.files_tree['unicode_filenames']
        assert filepath1 in files_tree
        assert filepath2 in files_tree
        assert filepath3 in files_tree
        assert filepath4 in files_tree
        assert filepath5 in files_tree

        result_files = [
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath3,
                'size': 126158658,
            },
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath4,
                'size': 189321363,
            },
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath2,
                'size': 106649699,
            },
            {
                'download': True,
                'path': 'unicode_filenames/' + filepath5,
                'size': 21590269,
            },
            {'download': True, 'path': 'unicode_filenames/' + filepath1, 'size': 1771},
        ]

        assert len(ti.files) == len(result_files)

    def test_directory_with_single_file(self):
        filename = common.get_test_data_file('dir_with_single_file.torrent')

        ti = TorrentInfo(filename)
        expected_file_tree = {'dir_with_single_file': {'single_file.txt': (0, 9, True)}}
        assert ti.files_tree == expected_file_tree

        result_files = [
            {
                'path': 'dir_with_single_file/single_file.txt',
                'size': 9,
                'download': True,
            }
        ]
        assert ti.files == result_files

    def test_bittorrent_v2_path(self):
        filename = common.get_test_data_file('v2_test.torrent')
        files_tree = {
            'torrent_test': {
                'small.txt': (0, 22, True),
                '還在一個人無聊嗎~還不趕緊上來聊天美.txt': (1, 32, True),
            }
        }
        ti = TorrentInfo(filename, filetree=1)
        assert ti.files_tree == files_tree

        files_tree2 = {
            'contents': {
                'torrent_test': {
                    'type': 'dir',
                    'contents': {
                        'small.txt': {
                            'type': 'file',
                            'path': 'torrent_test/small.txt',
                            'length': 22,
                            'index': 0,
                            'download': True,
                        },
                        '還在一個人無聊嗎~還不趕緊上來聊天美.txt': {
                            'type': 'file',
                            'path': 'torrent_test/還在一個人無聊嗎~還不趕緊上來聊天美.txt',
                            'length': 32,
                            'index': 1,
                            'download': True,
                        },
                    },
                    'length': 54,
                    'download': True,
                }
            },
            'type': 'dir',
        }
        ti = TorrentInfo(filename, filetree=2)
        assert ti.files_tree == files_tree2

    def test_bittorrent_v2_hybrid_path(self):
        filename = common.get_test_data_file('v2_hybrid.torrent')
        files_tree = {
            'torrent_test': {
                'small.txt': (0, 22, True),
                '還在一個人無聊嗎~還不趕緊上來聊天美.txt': (2, 32, True),
                '.pad': {
                    '16362': (1, 16362, True),
                    '16352': (3, 16352, True),
                },
            }
        }
        ti = TorrentInfo(filename, filetree=1, force_bt_version=1)
        assert ti.files_tree == files_tree
        del files_tree['torrent_test']['.pad']
        files_tree['torrent_test']['還在一個人無聊嗎~還不趕緊上來聊天美.txt'] = (1, 32, True)
        ti = TorrentInfo(filename, filetree=1, force_bt_version=2)
        assert ti.files_tree == files_tree

        files_tree2 = {
            'contents': {
                'torrent_test': {
                    'type': 'dir',
                    'contents': {
                        'small.txt': {
                            'type': 'file',
                            'path': 'torrent_test/small.txt',
                            'length': 22,
                            'index': 0,
                            'download': True,
                        },
                        '還在一個人無聊嗎~還不趕緊上來聊天美.txt': {
                            'type': 'file',
                            'path': 'torrent_test/還在一個人無聊嗎~還不趕緊上來聊天美.txt',
                            'length': 32,
                            'index': 2,
                            'download': True,
                        },
                        '.pad': {
                            'type': 'dir',
                            'contents': {
                                '16362': {
                                    'type': 'file',
                                    'path': 'torrent_test/.pad/16362',
                                    'length': 16362,
                                    'index': 1,
                                    'download': True,
                                },
                                '16352': {
                                    'type': 'file',
                                    'path': 'torrent_test/.pad/16352',
                                    'length': 16352,
                                    'index': 3,
                                    'download': True,
                                },
                            },
                            'length': 32714,
                            'download': True,
                        },
                    },
                    'length': 32768,
                    'download': True,
                }
            },
            'type': 'dir',
        }
        ti = TorrentInfo(filename, filetree=2, force_bt_version=1)
        assert ti.files_tree == files_tree2
        torrent_test = files_tree2['contents']['torrent_test']
        torrent_test['length'] -= torrent_test['contents']['.pad']['length']
        del torrent_test['contents']['.pad']
        torrent_test['contents']['還在一個人無聊嗎~還不趕緊上來聊天美.txt']['index'] = 1
        ti = TorrentInfo(filename, filetree=2, force_bt_version=2)
        assert ti.files_tree == files_tree2
