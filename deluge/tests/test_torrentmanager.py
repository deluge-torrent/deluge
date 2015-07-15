import base64
import os
import warnings

from twisted.trial import unittest

from deluge import component
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.error import InvalidTorrentError

from . import common

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.resetwarnings()


class TorrentmanagerTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        common.set_tmp_config_dir()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.torrentManager = self.core.torrentmanager
        return component.start()

    def tearDown(self):  # NOQA
        def on_shutdown(result):
            component._ComponentRegistry.components = {}
            del self.rpcserver
            del self.core
            del self.torrentManager
        return component.shutdown().addCallback(on_shutdown)

    def test_remove_torrent(self):
        filename = os.path.join(os.path.dirname(__file__), "test.torrent")
        torrent_id = self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), {})
        self.assertTrue(self.torrentManager.remove(torrent_id, False))

    def test_remove_torrent_false(self):
        """Test when remove_torrent returns False"""
        raise unittest.SkipTest("")

    def test_remove_invalid_torrent(self):
        self.assertRaises(InvalidTorrentError, self.torrentManager.remove, "torrentidthatdoesntexist")
