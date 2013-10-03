from twisted.trial import unittest
import os

import deluge.core.torrent
import test_torrent
import deluge.tests.common as common
from deluge.core.rpcserver import RPCServer
from deluge.core.core import Core

from deluge._libtorrent import lt

import deluge.component as component
from deluge.core.torrent import Torrent

config_setup = False
core = None
rpcserver = None


# This is called by torrent.py when calling component.get("...")
def get(key):
    if key is "Core":
        return core
    elif key is "RPCServer":
        return rpcserver
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

    def setUp(self):
        # Save component and set back on teardown
        self.original_component = deluge.core.torrent.component
        deluge.core.torrent.component = test_torrent
        self.setup_config()
        global rpcserver
        global core
        rpcserver = RPCServer(listen=False)
        core = Core()
        self.session = lt.session()
        self.torrent = None
        return component.start()

    def tearDown(self):
        deluge.core.torrent.component = self.original_component

        def on_shutdown(result):
            component._ComponentRegistry.components = {}
        return component.shutdown().addCallback(on_shutdown)

    def print_priority_list(self, priorities):
        tmp = ''
        for i, p in enumerate(priorities):
            if i % 100 == 0:
                print tmp
                tmp = ''
            tmp += "%s" % p
        print tmp

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

    def test_set_prioritize_first_last(self):
        piece_indexes = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 2), (50, 52),
                         (51, 53), (110, 112), (111, 114), (200, 203),
                         (202, 203), (212, 213), (212, 218), (457, 463)]
        self.run_test_set_prioritize_first_last("dir_with_6_files.torrent", piece_indexes)

    def run_test_set_prioritize_first_last(self, torrent_file, prioritized_piece_indexes):
        atp = self.get_torrent_atp(torrent_file)
        handle = self.session.add_torrent(atp)

        self.torrent = Torrent(handle, {})
        priorities_original = handle.piece_priorities()
        prioritized_pieces, new_priorites = self.torrent.set_prioritize_first_last(True)
        priorities = handle.piece_priorities()
        non_prioritized_pieces = list(range(len(priorities)))

        # The prioritized indexes are the same as we expect
        self.assertEquals(prioritized_pieces, prioritized_piece_indexes)

        # Test the priority of the prioritized pieces
        for first, last in prioritized_pieces:
            for i in range(first, last):
                if i in non_prioritized_pieces:
                    non_prioritized_pieces.remove(i)
                self.assertEquals(priorities[i], 7)

        # Test the priority of all the non-prioritized pieces
        for i in non_prioritized_pieces:
            self.assertEquals(priorities[i], 1)

        # The length of the list of new priorites is the same as the original
        self.assertEquals(len(priorities_original), len(new_priorites))

        #self.print_priority_list(priorities)

    def test_set_prioritize_first_last_false(self):
        atp = self.get_torrent_atp("dir_with_6_files.torrent")
        handle = self.session.add_torrent(atp)
        self.torrent = Torrent(handle, {})
        # First set some pieces prioritized
        self.torrent.set_prioritize_first_last(True)
        # Reset pirorities
        self.torrent.set_prioritize_first_last(False)
        priorities = handle.piece_priorities()

        # Test the priority of the prioritized pieces
        for i in priorities:
            self.assertEquals(priorities[i], 1)

        #self.print_priority_list(priorities)
