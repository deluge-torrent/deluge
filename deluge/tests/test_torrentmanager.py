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
        RPCServer(listen=False)
        self.core = Core()
        return component.start()

    def tear_down(self):
        return component.shutdown()

    @defer.inlineCallbacks
    def test_remove_torrent(self):
        filename = common.get_test_data_file('test.torrent')
        with open(filename) as _file:
            filedump = base64.encodestring(_file.read())
        torrent_id = yield self.core.add_torrent_file(filename, filedump, {})
        self.assertTrue(self.core.torrentmanager.remove(torrent_id, False))

    @defer.inlineCallbacks
    def test_prefetch_metadata(self):
        # TODO: need to mock lt add_torrent as need to run and pass test without using internet.
        magnet = 'magnet:?xt=urn:btih:6HANPB4ELB55IPJ52GZPGV2AMPNPBQ6B'
        torrent_id, torrent_info = yield self.core.torrentmanager.prefetch_metadata(magnet)
        print(torrent_id, torrent_info)

    @defer.inlineCallbacks
    def test_prefetch_metadata_timeout(self):
        magnet = 'magnet:?xt=urn:btih:6HANPB4ELB55IPJ52GZPGV2AMPNPBQ6B'
        torrent_id, metadata = yield self.core.torrentmanager.prefetch_metadata(magnet, timeout=0)
        self.assertEqual(metadata, None)

    @pytest.mark.todo
    def test_remove_torrent_false(self):
        """Test when remove_torrent returns False"""
        common.todo_test(self)

    def test_remove_invalid_torrent(self):
        self.assertRaises(InvalidTorrentError, self.core.torrentmanager.remove, 'torrentidthatdoesntexist')
