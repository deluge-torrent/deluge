import base64
import os
import sys
import time
import warnings

from mock import MagicMock
import pytest
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet import defer
from twisted.trial import unittest

import deluge.core.torrentmanager
from deluge import component
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.core.torrentmanager import StatusRequest, TorrentsStatus
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

    @inlineCallbacks
    def test_remove_torrent(self):
        filename = common.get_test_data_file('test.torrent')
        with open(filename) as _file:
            filedump = base64.encodestring(_file.read())
        torrent_id = yield self.core.add_torrent_file(filename, filedump, {})
        self.assertTrue(self.core.torrentmanager.remove(torrent_id, False))

    @pytest.mark.todo
    def test_remove_torrent_false(self):
        """Test when remove_torrent returns False"""
        common.todo_test(self)

    def test_remove_invalid_torrent(self):
        self.assertRaises(InvalidTorrentError, self.core.torrentmanager.remove, 'torrentidthatdoesntexist')

    def test_on_alert_state_update(self):
        def stop():
            self.torrentManager.set_timers(False)
        from twisted.python.monkey import MonkeyPatcher
        patcher = MonkeyPatcher((self.torrentManager, 'stop', stop))
        patcher.patch()
        add_tm_torrents(self.torrentManager, count=1, get_status={'storage_mode': None})
        alert = MagicMock()
        alert.message = MagicMock(return_value='Mock alert message')
        t_status = MagicMock()
        t_status.info_hash = '0'
        alert.status = [t_status for s in [1]]
        self.torrentManager.on_alert_state_update(alert)


# This is called by torrent.py when calling component.get("...")
def get(key):
    if key is 'RPCServer':
        rpcserver = MagicMock()
        rpcserver.get_session_id = MagicMock(return_value='0')
        return rpcserver
    else:
        return None


def add_tm_torrents(tm, count=100, get_status=None):
    torrent = MagicMock()
    torrent.get_status = MagicMock(return_value=get_status)
    torrent.update_status = MagicMock()
    keys = [str(i) for i in range(count)]
    tm.torrents = dict([(k, torrent) for k in keys])


class TorrentsStatusTestCase(BaseTestCase):

    def set_up(self):
        # Save component and set back on teardown
        self.original_component = deluge.core.torrentmanager.component
        deluge.core.torrentmanager.component = sys.modules[__name__]

        tm = MagicMock()
        torrent_keys = ['name']
        leftover_keys = []
        tm.separate_torrent_keys = MagicMock(return_value=(torrent_keys, leftover_keys))
        self.t_status = TorrentsStatus(tm)

    def tear_down(self):
        # Set back original value
        deluge.core.torrentmanager.component = self.original_component

    def test_add_request(self):
        request = None
        request = StatusRequest(None, None, None, None, None)
        self.t_status.add_request(None, None, None, None, None)
        self.assertEquals(self.t_status.requests_queue.pop(), request)
        self.assertEquals(len(self.t_status.requests_queue), 0)

    def test_mark_dirty(self):
        torrent_id = '1'
        self.t_status.status_cache['s1'] = {'torrents_status': {torrent_id: None, 'testid': None}, 'keys': {}}
        self.t_status.status_cache['s2'] = {'torrents_status': {torrent_id: None}, 'keys': {}}
        self.t_status.status_cache['s3'] = {'torrents_status': {}, 'keys': {}}

        # Value should be 2
        self.assertEquals(len(self.t_status.status_cache['s1']['torrents_status']), 2)
        self.assertEquals(len(self.t_status.status_cache['s2']['torrents_status']), 1)
        self.assertEquals(len(self.t_status.status_cache['s3']['torrents_status']), 0)
        self.t_status.mark_dirty([torrent_id])
        # Verify that statuses have been removed
        self.assertEquals(len(self.t_status.status_cache['s1']['torrents_status']), 1)
        self.assertEquals(len(self.t_status.status_cache['s2']['torrents_status']), 0)
        self.assertEquals(len(self.t_status.status_cache['s3']['torrents_status']), 0)

    def teset_clear_status_requests(self):
        session_id = 's1'
        self.t_status.add_request(session_id, None, None, None, None)
        self.assertEquals(self.t_status.clear_status_requests(session_id), 1)

    def test_process_status_request(self):
        add_tm_torrents(self.t_status.tm)
        session_id = 's1'
        d = Deferred()

        def verify_values(args):
            torrents_status, plugin_keys = args
            self.assertEquals(torrents_status.keys(), ['1'])
            self.assertEquals(plugin_keys, [])
        d.addCallback(verify_values)
        self.t_status.status_cache[session_id] = {'torrents_status': {'1': None, '2': None}, 'keys': []}

        self.t_status.add_request(session_id, d, {'1': None}, ['name'], only_updated=False)
        self.t_status.process_status_request()

    def test_torrents_status_update_all(self):
        add_tm_torrents(self.t_status.tm)
        req_torrents = {'1': None, '2': None}
        keys = ['name']
        d = self.t_status.torrents_status_update(req_torrents, keys, only_updated=False)
        self.t_status.process_status_request(StatusRequest('0', d, req_torrents, keys, only_updated=False))

        def verify_values(args):
            torrents_status, plugin_keys = args
            self.assertEquals(sorted(torrents_status.keys()), ['1', '2'])
            self.assertEquals(plugin_keys, [])
        d.addCallback(verify_values)
        return d

    def test_torrents_status_update_from_cache(self):
        """
        Return status from cache instead of asking libtorrent for updates.
        """
        add_tm_torrents(self.t_status.tm)
        session_id = '0'
        req_torrents = {'1': None, '2': None}
        keys = ['name']

        # Set last time to now to avoid a libtorrent request
        self.t_status.last_state_update_ts = time.time()

        def add_request(session_id, d, req_torrents, keys, only_updated):
            self.assertTrue(False, 'add_request should not be called!')  # pylint: disable=redundant-unittest-assert

        def process_status_request(request=None):
            expected_request = StatusRequest(session_id, request.d, req_torrents, keys, True)
            request.d.callback(({'1': None, '2': None}, []))
            self.assertEquals(expected_request, request)

        self.t_status.process_status_request = process_status_request
        self.t_status.add_request = add_request
        d = self.t_status.torrents_status_update(req_torrents, keys, only_updated=True)
        return d

    def test_torrents_status_update_only_updated_keys_changed(self):
        add_tm_torrents(self.t_status.tm)
        session_id = '0'
        req_torrents = {'1': None, '2': None}
        keys = ['name']
        # Add "2" to cache which means that "1" is dirty
        self.t_status.status_cache[session_id] = {'torrents_status': {'2': None}, 'keys': []}
        # The keys in cache differ from keys requested.
        d = self.t_status.torrents_status_update(req_torrents, keys, only_updated=True)
        self.t_status.process_status_request()

        # As keys differ, we should get all torrents returned
        def verify_values(args):
            torrents_status, plugin_keys = args
            self.assertEquals(sorted(torrents_status.keys()), ['1', '2'])
            self.assertEquals(plugin_keys, [])
        d.addCallback(verify_values)
        return d

    def test_torrents_status_update_only_updated(self):
        add_tm_torrents(self.t_status.tm)
        session_id = '0'
        req_torrents = {'1': None, '2': None}
        keys = ['name']
        # Add "2" to cache which means that "1" is dirty
        self.t_status.status_cache[session_id] = {'torrents_status': {'2': None}, 'keys': keys}
        d = self.t_status.torrents_status_update(req_torrents, keys, only_updated=True)
        self.t_status.process_status_request()

        def verify_values(args):
            torrents_status, plugin_keys = args
            self.assertEquals(torrents_status.keys(), ['1'])
            self.assertEquals(plugin_keys, [])
        d.addCallback(verify_values)
        return d
