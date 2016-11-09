# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.internet.defer import inlineCallbacks, maybeDeferred, succeed

import deluge.component as component
import deluge.ui.sessionproxy
from deluge.ui.sessionproxy import TorrrentsState

from .basetest import BaseTestCase


class Core(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.torrents = {}
        # The download_payload_rate decides if these are considered active or not
        # With download_payload_rate == 0, a is not active
        self.torrents['a'] = {'key1': 1, 'key2': 2, 'key3': 3, 'owner': 'tester', 'tracker_status': '',
                              'download_payload_rate': 0, 'torrent_id': 'a', 'state': 'Seeding'}
        self.torrents['b'] = {'key1': 1, 'key2': 2, 'key3': 3, 'owner': 'tester', 'tracker_status': '',
                              'download_payload_rate': 1, 'torrent_id': 'b', 'state': 'Seeding'}
        self.torrents['c'] = {'key1': 1, 'key2': 2, 'key3': 3, 'owner': 'tester', 'tracker_status': 'Error:',
                              'download_payload_rate': 1, 'torrent_id': 'c', 'state': 'Seeding'}
        self.updated = set()

    def get_session_state(self):
        return maybeDeferred(self.torrents.keys)

    def get_torrent_status(self, torrent_id, keys):
        if not keys:
            keys = self.torrents[torrent_id].keys()

        ret = {}
        for key in keys:
            ret[key] = self.torrents[torrent_id][key]
        return succeed(ret)

    def get_torrents_status(self, keys, only_updated=False):
        if only_updated:
            torrents = self.updated
            self.updated = set()
        else:
            torrents = self.torrents.keys()

        if not keys:
            keys = self.torrents['a'].keys()

        ret = {}
        for torrent in torrents:
            ret[torrent] = {}
            for key in keys:
                ret[torrent][key] = self.torrents[torrent][key]
        return succeed(ret)


class Client(object):

    def __init__(self):
        self.core = Core()

    def __noop__(self, *args, **kwargs):
        return None

    def __getattr__(self, *args, **kwargs):
        return self.__noop__

client = Client()


class SessionProxyTestCase(BaseTestCase):

    def set_up(self):
        self.patch(deluge.ui.sessionproxy, 'client', client)
        self.sp = deluge.ui.sessionproxy.SessionProxy()
        client.core.reset()
        d = self.sp.start()
        self.torrents_state = TorrrentsState()
        self.inital_keys = ['key1', 'key2', 'key3', 'owner', 'tracker_status',
                            'download_payload_rate', 'torrent_id', 'state']

        def do_get_torrents_status(torrent_ids):
            self.torrents_state.filter = {'id': torrent_ids}
            return self.sp.get_torrents_status(self.torrents_state, self.inital_keys)

        d.addCallback(do_get_torrents_status)
        return d

    def tear_down(self):
        return component.shutdown()

    def test_startup(self):
        self.assertEquals(client.core.torrents['a'], self.sp.torrents['a'])

    def test_get_torrent_status_no_change(self):
        d = self.sp.get_torrent_status('a', [])
        d.addCallback(self.assertEquals, client.core.torrents['a'])
        return d

    def test_get_torrent_status_change(self):
        client.core.torrents['a']['key1'] = 2
        d = self.sp.get_torrent_status('a', ['key1'])
        d.addCallback(self.assertEquals, {'key1': 2})
        return d

    @inlineCallbacks
    def test_get_torrent_status_multiple_keys(self):
        client.core.torrents['a']['key1'] = 2
        keys = ['key1', 'owner']
        status = yield self.sp.get_torrent_status('a', keys)
        self.assertEquals(sorted(status.keys()), sorted(keys))
        self.assertEquals(status[keys[0]], 2)
        self.assertEquals(status[keys[1]], 'tester')

    @inlineCallbacks
    def test_get_torrents_status_from_cache(self):
        current_ids = set()
        self.torrents_state.visible_torrents = current_ids
        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=True)
        keys_list = ['a', 'b', 'c']
        self.assertEquals(sorted(state_update.status.keys()), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'a': {'key2': 2}, 'c': {'key2': 2}, 'b': {'key2': 2}})

        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=True)
        keys_list = []
        self.assertEquals(state_update.status.keys(), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {})

    @inlineCallbacks
    def test_get_torrents_status_key_updated_from_cache(self):
        current_ids = set()
        self.torrents_state.visible_torrents = current_ids
        # We set 'a' to be updated in core
        # A will not be returned by the first callback because from_cache=True hence 'a' will be updated in
        # sessionproxy (sp) after the callback (to the caller of sp.get_torrents_status) is issued.
        # On the next call to sp.get_torrents_status, 'a' would have been updated so it should then be
        # returned on the status callback.
        client.core.updated.add('a')
        client.core.torrents['a']['key2'] = 99

        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=True)
        keys_list = ['a', 'b', 'c']
        self.assertEquals(sorted(state_update.status.keys()), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'a': {'key2': 2}, 'c': {'key2': 2}, 'b': {'key2': 2}})

        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=True)
        keys_list = ['a']
        self.assertEquals(state_update.status.keys(), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'a': {'key2': 99}})

    @inlineCallbacks
    def test_get_torrents_status_updated_ids_not_from_cache(self):
        current_ids = set()
        self.torrents_state.visible_torrents = current_ids
        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=False, only_updated=True)
        # Since this is the first call, it will return all the torrents, even then only_updated is True
        keys_list = ['a', 'b', 'c']
        self.assertEquals(sorted(state_update.status.keys()), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'a': {'key2': 2}, 'c': {'key2': 2}, 'b': {'key2': 2}})

        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=False, only_updated=True)
        # On the second call, none have changed, and with only_updated == True:
        # - status will be empty
        # - updated_ids will be empty
        keys_list = []
        self.assertEquals(state_update.status.keys(), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {})

        current_ids = set(['a'])
        self.torrents_state.visible_torrents = current_ids
        self.sp.updated_ids = set('b')
        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=False, only_updated=True)
        # On the third call, b has changed, and with only_updated == True:
        # - status will contain b
        # - updated_ids will contain b
        keys_list = ['b']
        self.assertEquals(state_update.status.keys(), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'b': {'key2': 2}})

    @inlineCallbacks
    def test_get_torrents_status_filter_matching_only_updated_false(self):
        self.torrents_state.filter = {'state': 'Active'}
        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=False)
        # We have none in the current_ids, therefore not_matching should be
        # empty, and 'b' and 'c' should exist in status.
        keys_list = ['b', 'c']
        self.assertEquals(sorted(state_update.status.keys()), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'c': {'key2': 2}, 'b': {'key2': 2}})

    @inlineCallbacks
    def test_get_torrents_status_filter_matching_only_updated_false_current_ids_not_empty(self):
        current_ids = set('a')
        self.torrents_state.visible_torrents = current_ids
        self.torrents_state.filter = {'state': 'Active'}
        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=False)
        # We have 'a' in the current_ids, but 'a' is not active and
        # does not match. Therefore 'a' is returned in not_matching
        # and 'b' and 'c' should exist in status.
        keys_list = ['b', 'c']
        self.assertEquals(sorted(state_update.status.keys()), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set('a'))
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'c': {'key2': 2}, 'b': {'key2': 2}})

    @inlineCallbacks
    def test_get_torrents_status_filter_matching_only_updated_true(self):
        current_ids = set()
        self.sp.updated_ids = set('b')
        self.torrents_state.filter = {'state': 'Active'}
        self.torrents_state.visible_torrents = current_ids
        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=True)
        # We have a in the current_ids, but 'a' is not active and
        # does not match. Therefore 'a' is returned in not_matching
        # and 'b' and 'c' should exist in status.
        keys_list = ['b']
        self.assertEquals(state_update.status.keys(), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set())
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'b': {'key2': 2}})

    @inlineCallbacks
    def test_get_torrents_status_filter_matching_only_updated_true_current_ids_not_empty(self):
        current_ids = set(['a'])
        self.sp.updated_ids = set('b')
        self.torrents_state.filter = {'state': 'Active'}
        self.torrents_state.visible_torrents = current_ids
        state_update = yield self.sp.get_torrents_status(self.torrents_state, ['key2'],
                                                         from_cache=True, only_updated=True)
        # We have 'a' in the current_ids, but 'a' is not active and
        # does not match. Therefore 'a' is returned in not_matching
        # and 'b' and 'c' should exist in status.
        keys_list = ['b']
        self.assertEquals(state_update.status.keys(), keys_list)
        self.assertEquals(state_update.keys, ['key2'])
        self.assertEquals(state_update.updated_ids, set(keys_list))
        self.assertEquals(state_update.not_matching, set('a'))
        self.assertEquals(state_update.new_matching, set(keys_list))
        self.assertEquals(state_update.status, {'b': {'key2': 2}})

    @inlineCallbacks
    def test_get_torrents_status_filter_match_zero_torrents(self):
        current_ids = set(['a', 'b', 'c'])
        self.torrents_state.visible_torrents = current_ids
        update = yield self.sp.get_torrents_status(self.torrents_state, ['torrent_id', 'state'], from_cache=True,
                                                   only_updated=not self.torrents_state.filter_changed)
        self.torrents_state.update_status(update)
        client.core.torrents['a']['state'] = 'Checking'
        client.core.updated = set(['a'])
        self.torrents_state.set_filter({'state': 'Checking'})
        self.sp.on_torrent_state_changed('a', 'Checking')
        update = yield self.sp.get_torrents_status(self.torrents_state, ['torrent_id', 'state'], from_cache=False,
                                                   only_updated=not self.torrents_state.filter_changed)
        self.torrents_state.update_status(update)

        client.core.torrents['a']['state'] = 'Seeding'
        client.core.updated = set(['a'])

        update = yield self.sp.get_torrents_status(self.torrents_state, ['torrent_id', 'state'], from_cache=False,
                                                   only_updated=not self.torrents_state.filter_changed)
        self.torrents_state.update_status(update)
        # When state changes back to seeding, not torrents match
        self.assertEquals(update.updated_ids, set())
        self.assertEquals(update.new_matching, set())
        self.assertEquals(update.not_matching, set(['a']))
        self.assertEquals(self.torrents_state.visible_torrents, set())
