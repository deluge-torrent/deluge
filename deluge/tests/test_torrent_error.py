from __future__ import print_function

import base64
import os
import sys
import time

from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.trial import unittest

import deluge.component as component
import deluge.core.torrent
import deluge.tests.common as common
from deluge._libtorrent import lt
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.core.torrentmanager import TorrentState

config_setup = False
core = None
rpcserver = None
eventmanager = None


# This is called by torrent.py when calling component.get("...")
def get(key):
    if key is "Core":
        return core
    elif key is "RPCServer":
        return rpcserver
    elif key is "EventManager":
        return core.eventmanager
    elif key is "TorrentManager":
        return core.torrentmanager
    else:
        return None


class TorrentTestCase(unittest.TestCase):

    def setup_config(self):
        global config_setup
        config_setup = True
        config_dir = common.set_tmp_config_dir()
        core_config = deluge.config.Config("core.conf", defaults=deluge.core.preferencesmanager.DEFAULT_PREFS,
                                           config_dir=config_dir)
        core_config.save()

    def setUp(self):  # NOQA
        # Save component and set back on teardown
        self.original_component = deluge.core.torrent.component
        deluge.core.torrent.component = sys.modules[__name__]
        self.setup_config()
        global rpcserver
        global core
        rpcserver = RPCServer(listen=False)
        core = Core()
        return component.start()

    def tearDown(self):  # NOQA
        deluge.core.torrent.component = self.original_component

        def on_shutdown(result):
            component._ComponentRegistry.components = {}
        return component.shutdown().addCallback(on_shutdown)

    def assert_state(self, torrent, state):
        torrent.update_state()
        self.assertEquals(torrent.state, state)

    def get_torrent_atp(self, filename):
        filename = os.path.join(os.path.dirname(__file__), filename)
        e = lt.bdecode(open(filename, 'rb').read())
        info = lt.torrent_info(e)
        atp = {"ti": info}
        atp["save_path"] = os.getcwd()
        atp["storage_mode"] = lt.storage_mode_t.storage_mode_sparse
        atp["add_paused"] = False
        atp["auto_managed"] = True
        atp["duplicate_is_error"] = True
        return atp

    def test_torrent_error_data_missing(self):
        options = {"seed_mode": True}
        filename = os.path.join(os.path.dirname(__file__), "test_torrent.file.torrent")
        torrent_id = core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)
        torrent = core.torrentmanager.torrents[torrent_id]

        self.assert_state(torrent, "Seeding")

        # Force an error by reading (non-existant) piece from disk
        torrent.handle.read_piece(0)
        time.sleep(0.2)  # Delay to wait for alert from lt
        self.assert_state(torrent, "Error")

    def test_torrent_error_resume_original_state(self):
        options = {"seed_mode": True, "add_paused": True}
        filename = os.path.join(os.path.dirname(__file__), "test_torrent.file.torrent")
        torrent_id = core.add_torrent_file(filename, base64.encodestring(open(filename).read()), options)
        torrent = core.torrentmanager.torrents[torrent_id]

        orig_state = "Paused"
        self.assert_state(torrent, orig_state)

        # Force an error by reading (non-existant) piece from disk
        torrent.handle.read_piece(0)
        time.sleep(0.2)  # Delay to wait for alert from lt
        self.assert_state(torrent, "Error")

        # Clear error and verify returned to original state
        torrent.force_recheck()
        return deferLater(reactor, 0.1, self.assert_state, torrent, orig_state)

    def test_torrent_error_resume_data_unaltered(self):
        resume_data = {'active_time': 13399L, 'num_incomplete': 16777215L, 'announce_to_lsd': 1L, 'seed_mode': 0L,
                       'pieces': '\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01', 'paused': 0L,
                       'seeding_time': 13399L, 'last_scrape': 13399L,
                       'info-hash': '-\xc5\xd0\xe7\x1af\xfeid\x9ad\r9\xcb\x00\xa2YpIs', 'max_uploads': 16777215L,
                       'max_connections': 16777215L, 'num_downloaders': 16777215L, 'total_downloaded': 0L,
                       'file-format': 'libtorrent resume file', 'peers6': '', 'added_time': 1411826665L,
                       'banned_peers6': '', 'file_priority': [1L], 'last_seen_complete': 0L, 'total_uploaded': 0L,
                       'piece_priority': '\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01',
                       'file-version': 1L, 'announce_to_dht': 1L, 'auto_managed': 1L, 'upload_rate_limit': 0L,
                       'completed_time': 1411826665L, 'allocation': 'sparse', 'blocks per piece': 2L,
                       'download_rate_limit': 0L, 'libtorrent-version': '0.16.17.0', 'banned_peers': '',
                       'num_seeds': 16777215L, 'sequential_download': 0L, 'announce_to_trackers': 1L,
                       'peers': '\n\x00\x02\x0f=\xc6SC\x17]\xd8}\x7f\x00\x00\x01=\xc6', 'finished_time': 13399L,
                       'last_upload': 13399L, 'trackers': [[]], 'super_seeding': 0L,
                       'file sizes': [[512000L, 1411826586L]], 'last_download': 13399L}
        torrent_state = TorrentState(
            torrent_id='2dc5d0e71a66fe69649a640d39cb00a259704973',
            filename='test_torrent.file.torrent',
            name='',
            save_path='/home/ubuntu/Downloads',
            file_priorities=[1],
            is_finished=True,
        )

        filename = os.path.join(os.path.dirname(__file__), "test_torrent.file.torrent")
        filedump = open(filename).read()
        torrent_id = core.torrentmanager.add(state=torrent_state, filedump=filedump,
                                             resume_data=lt.bencode(resume_data))
        torrent = core.torrentmanager.torrents[torrent_id]

        def assert_resume_data():
            self.assert_state(torrent, "Error")
            tm_resume_data = lt.bdecode(core.torrentmanager.resume_data[torrent.torrent_id])
            self.assertEquals(tm_resume_data, resume_data)

        return deferLater(reactor, 0.5, assert_resume_data)
