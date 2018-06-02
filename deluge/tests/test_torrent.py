# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

import base64
import os
import time

from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.trial import unittest

import deluge.component as component
import deluge.core.torrent
import deluge.tests.common as common
from deluge._libtorrent import lt
from deluge.common import utf8_encode_structure, windows_check
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.core.torrent import Torrent
from deluge.core.torrentmanager import TorrentState

from .basetest import BaseTestCase


class TorrentTestCase(BaseTestCase):

    def setup_config(self):
        config_dir = common.set_tmp_config_dir()
        core_config = deluge.config.Config(
            'core.conf', defaults=deluge.core.preferencesmanager.DEFAULT_PREFS,
            config_dir=config_dir,
        )
        core_config.save()

    def set_up(self):
        self.setup_config()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.session = lt.session()
        self.torrent = None
        return component.start()

    def tear_down(self):
        def on_shutdown(result):
            del self.rpcserver
            del self.core

        return component.shutdown().addCallback(on_shutdown)

    def print_priority_list(self, priorities):
        tmp = ''
        for i, p in enumerate(priorities):
            if i % 100 == 0:
                print(tmp)
                tmp = ''
            tmp += '%s' % p
        print(tmp)

    def assert_state(self, torrent, state):
        torrent.update_state()
        self.assertEqual(torrent.state, state)

    def get_torrent_atp(self, filename):
        filename = common.get_test_data_file(filename)
        with open(filename, 'rb') as _file:
            info = lt.torrent_info(lt.bdecode(_file.read()))
        atp = {'ti': info}
        atp['save_path'] = os.getcwd()
        atp['storage_mode'] = lt.storage_mode_t.storage_mode_sparse
        atp['add_paused'] = False
        atp['auto_managed'] = True
        atp['duplicate_is_error'] = True
        return atp

    def test_set_prioritize_first_last_pieces(self):
        piece_indexes = [
            0, 1, 50, 51, 52, 110, 111, 112, 113, 200, 201, 202, 212,
            213, 214, 215, 216, 217, 457, 458, 459, 460, 461, 462,
        ]
        self.run_test_set_prioritize_first_last_pieces('dir_with_6_files.torrent', piece_indexes)

    def run_test_set_prioritize_first_last_pieces(self, torrent_file, prioritized_piece_indexes):
        atp = self.get_torrent_atp(torrent_file)
        handle = self.session.add_torrent(atp)

        self.torrent = Torrent(handle, {})
        priorities_original = handle.piece_priorities()
        self.torrent.set_prioritize_first_last_pieces(True)
        priorities = handle.piece_priorities()

        # The length of the list of new priorites is the same as the original
        self.assertEqual(len(priorities_original), len(priorities))

        # Test the priority of all the pieces against the calculated indexes.
        for idx, priority in enumerate(priorities):
            if idx in prioritized_piece_indexes:
                self.assertEqual(priorities[idx], 7)
            else:
                self.assertEqual(priorities[idx], 4)

        # self.print_priority_list(priorities)

    def test_set_prioritize_first_last_pieces_false(self):
        atp = self.get_torrent_atp('dir_with_6_files.torrent')
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        # First set some pieces prioritized
        self.torrent.set_prioritize_first_last_pieces(True)
        # Reset pirorities
        self.torrent.set_prioritize_first_last_pieces(False)
        priorities = handle.piece_priorities()

        # Test the priority of the prioritized pieces
        for i in priorities:
            self.assertEqual(priorities[i], 4)

        # self.print_priority_list(priorities)

    def test_torrent_error_data_missing(self):
        if windows_check():
            raise unittest.SkipTest('unexpected end of file in bencoded string')
        options = {'seed_mode': True}
        filename = common.get_test_data_file('test_torrent.file.torrent')
        with open(filename) as _file:
            filedump = base64.encodestring(_file.read())
        torrent_id = self.core.add_torrent_file(filename, filedump, options)
        torrent = self.core.torrentmanager.torrents[torrent_id]

        time.sleep(0.5)  # Delay to wait for lt to finish check on Travis.
        self.assert_state(torrent, 'Seeding')

        # Force an error by reading (non-existant) piece from disk
        torrent.handle.read_piece(0)
        time.sleep(0.2)  # Delay to wait for alert from lt
        self.assert_state(torrent, 'Error')

    def test_torrent_error_resume_original_state(self):
        if windows_check():
            raise unittest.SkipTest('unexpected end of file in bencoded string')
        options = {'seed_mode': True, 'add_paused': True}
        filename = common.get_test_data_file('test_torrent.file.torrent')
        with open(filename) as _file:
            filedump = base64.encodestring(_file.read())
        torrent_id = self.core.add_torrent_file(filename, filedump, options)
        torrent = self.core.torrentmanager.torrents[torrent_id]

        orig_state = 'Paused'
        self.assert_state(torrent, orig_state)

        # Force an error by reading (non-existant) piece from disk
        torrent.handle.read_piece(0)
        time.sleep(0.2)  # Delay to wait for alert from lt
        self.assert_state(torrent, 'Error')

        # Clear error and verify returned to original state
        torrent.force_recheck()

    def test_torrent_error_resume_data_unaltered(self):
        if windows_check():
            raise unittest.SkipTest('unexpected end of file in bencoded string')
        resume_data = {
            'active_time': 13399, 'num_incomplete': 16777215, 'announce_to_lsd': 1, 'seed_mode': 0,
            'pieces': '\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01', 'paused': 0,
            'seeding_time': 13399, 'last_scrape': 13399,
            'info-hash': '-\xc5\xd0\xe7\x1af\xfeid\x9ad\r9\xcb\x00\xa2YpIs', 'max_uploads': 16777215,
            'max_connections': 16777215, 'num_downloaders': 16777215, 'total_downloaded': 0,
            'file-format': 'libtorrent resume file', 'peers6': '', 'added_time': 1411826665,
            'banned_peers6': '', 'file_priority': [1], 'last_seen_complete': 0, 'total_uploaded': 0,
            'piece_priority': '\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01',
            'file-version': 1, 'announce_to_dht': 1, 'auto_managed': 1, 'upload_rate_limit': 0,
            'completed_time': 1411826665, 'allocation': 'sparse', 'blocks per piece': 2,
            'download_rate_limit': 0, 'libtorrent-version': '0.16.17.0', 'banned_peers': '',
            'num_seeds': 16777215, 'sequential_download': 0, 'announce_to_trackers': 1,
            'peers': '\n\x00\x02\x0f=\xc6SC\x17]\xd8}\x7f\x00\x00\x01=\xc6', 'finished_time': 13399,
            'last_upload': 13399, 'trackers': [[]], 'super_seeding': 0,
            'file sizes': [[512000, 1411826586]], 'last_download': 13399,
        }
        torrent_state = TorrentState(
            torrent_id='2dc5d0e71a66fe69649a640d39cb00a259704973',
            filename='test_torrent.file.torrent',
            name='',
            save_path='/home/ubuntu/Downloads',
            file_priorities=[1],
            is_finished=True,
        )

        filename = common.get_test_data_file('test_torrent.file.torrent')
        with open(filename) as _file:
            filedump = _file.read()
        resume_data = utf8_encode_structure(resume_data)
        torrent_id = self.core.torrentmanager.add(
            state=torrent_state, filedump=filedump, resume_data=lt.bencode(resume_data),
        )
        torrent = self.core.torrentmanager.torrents[torrent_id]

        def assert_resume_data():
            self.assert_state(torrent, 'Error')
            tm_resume_data = lt.bdecode(self.core.torrentmanager.resume_data[torrent.torrent_id])
            self.assertEqual(tm_resume_data, resume_data)

        return deferLater(reactor, 0.5, assert_resume_data)
