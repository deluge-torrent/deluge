import base64
import warnings

import pytest
from twisted.internet import defer

from deluge import component
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.error import InvalidTorrentError

from . import common
from .basetest import BaseTestCase

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.resetwarnings()


class TorrentmanagerTestCase(BaseTestCase):

    def set_up(self):
        common.set_tmp_config_dir()
        RPCServer(listen=False)
        self.core = Core()
        return component.start()

    def tear_down(self):
        return component.shutdown()

    @defer.inlineCallbacks
    def test_remove_torrent(self):
        filename = common.rpath("test.torrent")
        torrent_id = yield self.core.add_torrent_file(filename, base64.encodestring(open(filename).read()), {})
        self.assertTrue(self.core.torrentmanager.remove(torrent_id, False))

    @pytest.mark.todo
    def test_remove_torrent_false(self):
        """Test when remove_torrent returns False"""
        common.todo_test(self)

    def test_remove_invalid_torrent(self):
        self.assertRaises(InvalidTorrentError, self.core.torrentmanager.remove, "torrentidthatdoesntexist")
