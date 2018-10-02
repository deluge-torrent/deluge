# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.internet.defer import maybeDeferred, succeed
from twisted.internet.task import Clock

import deluge.component as component
import deluge.ui.sessionproxy

from .basetest import BaseTestCase


class Core(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.torrents = {}
        self.torrents['a'] = {'key1': 1, 'key2': 2, 'key3': 3}
        self.torrents['b'] = {'key1': 1, 'key2': 2, 'key3': 3}
        self.torrents['c'] = {'key1': 1, 'key2': 2, 'key3': 3}
        self.prev_status = {}

    def get_session_state(self):
        return maybeDeferred(self.torrents.keys)

    def get_torrent_status(self, torrent_id, keys, diff=False):
        if not keys:
            keys = list(self.torrents[torrent_id])

        if not diff:
            ret = {}
            for key in keys:
                ret[key] = self.torrents[torrent_id][key]

            return succeed(ret)

        else:
            ret = {}
            if torrent_id in self.prev_status:
                for key in keys:
                    if (
                        self.prev_status[torrent_id][key]
                        != self.torrents[torrent_id][key]
                    ):
                        ret[key] = self.torrents[torrent_id][key]
            else:
                ret = self.torrents[torrent_id]
            self.prev_status[torrent_id] = dict(self.torrents[torrent_id])
            return succeed(ret)

    def get_torrents_status(self, filter_dict, keys, diff=False):
        if not filter_dict:
            filter_dict['id'] = list(self.torrents)
        if not keys:
            keys = list(self.torrents['a'])
        if not diff:
            if 'id' in filter_dict:
                torrents = filter_dict['id']
                ret = {}
                for torrent in torrents:
                    ret[torrent] = {}
                    for key in keys:
                        ret[torrent][key] = self.torrents[torrent][key]
                return succeed(ret)
        else:
            if 'id' in filter_dict:
                torrents = filter_dict['id']
                ret = {}
                for torrent in torrents:
                    ret[torrent] = {}
                    if torrent in self.prev_status:
                        for key in self.prev_status[torrent]:
                            if (
                                self.prev_status[torrent][key]
                                != self.torrents[torrent][key]
                            ):
                                ret[torrent][key] = self.torrents[torrent][key]
                    else:
                        ret[torrent] = dict(self.torrents[torrent])

                    self.prev_status[torrent] = dict(self.torrents[torrent])
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
        self.clock = Clock()
        self.patch(deluge.ui.sessionproxy, 'time', self.clock.seconds)
        self.patch(deluge.ui.sessionproxy, 'client', client)
        self.sp = deluge.ui.sessionproxy.SessionProxy()
        client.core.reset()
        d = self.sp.start()

        def do_get_torrents_status(torrent_ids):
            inital_keys = ['key1']
            # Advance clock to expire the cache times
            self.clock.advance(2)
            return self.sp.get_torrents_status({'id': torrent_ids}, inital_keys)

        d.addCallback(do_get_torrents_status)
        return d

    def tear_down(self):
        return component.deregister(self.sp)

    def test_startup(self):
        self.assertEqual(client.core.torrents['a'], self.sp.torrents['a'][1])

    def test_get_torrent_status_no_change(self):
        d = self.sp.get_torrent_status('a', [])
        d.addCallback(self.assertEqual, client.core.torrents['a'])
        return d

    def test_get_torrent_status_change_with_cache(self):
        client.core.torrents['a']['key1'] = 2
        d = self.sp.get_torrent_status('a', ['key1'])
        d.addCallback(self.assertEqual, {'key1': 1})
        return d

    def test_get_torrent_status_change_without_cache(self):
        client.core.torrents['a']['key1'] = 2
        self.clock.advance(self.sp.cache_time + 0.1)
        d = self.sp.get_torrent_status('a', [])
        d.addCallback(self.assertEqual, client.core.torrents['a'])
        return d

    def test_get_torrent_status_key_not_updated(self):
        self.clock.advance(self.sp.cache_time + 0.1)
        self.sp.get_torrent_status('a', ['key1'])
        client.core.torrents['a']['key2'] = 99
        d = self.sp.get_torrent_status('a', ['key2'])
        d.addCallback(self.assertEqual, {'key2': 99})
        return d

    def test_get_torrents_status_key_not_updated(self):
        self.clock.advance(self.sp.cache_time + 0.1)
        self.sp.get_torrents_status({'id': ['a']}, ['key1'])
        client.core.torrents['a']['key2'] = 99
        d = self.sp.get_torrents_status({'id': ['a']}, ['key2'])
        d.addCallback(self.assertEqual, {'a': {'key2': 99}})
        return d
