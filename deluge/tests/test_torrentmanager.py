# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

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

warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.resetwarnings()


class TorrentmanagerTestCase(BaseTestCase):

    def set_up(self):
        common.set_tmp_config_dir()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        self.core.config.config['lsd'] = False
        return component.start()

    def tear_down(self):

        def on_shutdown(result):
            del self.rpcserver
            del self.core

        return component.shutdown().addCallback(on_shutdown)

    @defer.inlineCallbacks
    def test_remove_torrent(self):
        filename = common.get_test_data_file('test.torrent')
        with open(filename) as _file:
            filedump = base64.encodestring(_file.read())
        torrent_id = yield self.core.add_torrent_file_async(filename, filedump, {})
        self.assertTrue(self.core.torrentmanager.remove(torrent_id, False))

    @pytest.mark.todo
    def test_remove_torrent_false(self):
        """Test when remove_torrent returns False"""
        common.todo_test(self)

    def test_remove_invalid_torrent(self):
        self.assertRaises(InvalidTorrentError, self.core.torrentmanager.remove, 'torrentidthatdoesntexist')
