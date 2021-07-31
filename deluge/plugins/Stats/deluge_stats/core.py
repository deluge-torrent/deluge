# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
# Copyright (C) 2008 Damien Churchill <damoxc@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007 Marcos Mobley <markybob@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, unicode_literals

import logging
import time

from twisted.internet.task import LoopingCall

from deluge import component, configmanager
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

DEFAULT_PREFS = {
    'test': 'NiNiNi',
    'update_interval': 1,  # 2 seconds.
    'length': 150,  # 2 seconds * 150 --> 5 minutes.
}

DEFAULT_TOTALS = {
    'total_upload': 0,
    'total_download': 0,
    'total_payload_upload': 0,
    'total_payload_download': 0,
    'stats': {},
}

log = logging.getLogger(__name__)


def get_key(config, key):
    try:
        return config[key]
    except KeyError:
        return None


def mean(items):
    try:
        return sum(items) // len(items)
    except Exception:
        return 0


class Core(CorePluginBase):
    totals = {}  # class var to catch only updating this once per session in enable.

    def enable(self):
        log.debug('Stats plugin enabled')
        self.core = component.get('Core')
        self.stats = {}
        self.count = {}
        self.intervals = [1, 5, 30, 300]

        self.last_update = {}
        t = time.time()
        for i in self.intervals:
            self.stats[i] = {}
            self.last_update[i] = t
            self.count[i] = 0

        self.config = configmanager.ConfigManager('stats.conf', DEFAULT_PREFS)
        self.saved_stats = configmanager.ConfigManager('stats.totals', DEFAULT_TOTALS)
        if self.totals == {}:
            self.totals.update(self.saved_stats.config)

        self.length = self.config['length']

        # self.stats = get_key(self.saved_stats, 'stats') or {}

        # keys needed from core.get_session_status
        self.stat_keys = [
            'upload_rate',
            'download_rate',
            'dht.dht_nodes',
            'dht.dht_node_cache',
            'dht.dht_torrents',
            'peer.num_peers_connected',
            'peer.num_peers_half_open',
        ]
        # collected statistics and functions to get them
        self.stat_getters = {
            'upload_rate': lambda s: s['upload_rate'],
            'download_rate': lambda s: s['download_rate'],
            'dht_nodes': lambda s: s['dht.dht_nodes'],
            'dht_cache_nodes': lambda s: s['dht.dht_node_cache'],
            'dht_torrents': lambda s: s['dht.dht_torrents'],
            'num_peers': lambda s: s['peer.num_peers_connected'],
            'num_connections': lambda s: s['peer.num_peers_connected']
            + s['peer.num_peers_half_open'],
        }

        # initialize stats object
        for key in self.stat_getters.keys():
            for i in self.intervals:
                if key not in self.stats[i]:
                    self.stats[i][key] = []

        self.update_stats()

        self.update_timer = LoopingCall(self.update_stats)
        self.update_timer.start(self.config['update_interval'])

        self.save_timer = LoopingCall(self.save_stats)
        self.save_timer.start(60)

    def disable(self):
        self.update_timer.stop() if self.update_timer.running else None
        self.save_timer.stop() if self.save_timer.running else None
        self.save_stats()

    def update_stats(self):
        # Get all possible stats!
        stats = {}
        raw_stats = self.core.get_session_status(self.stat_keys)
        for name, fn in self.stat_getters.items():
            stats[name] = fn(raw_stats)

        # status = self.core.session.status()
        # for stat in dir(status):
        #     if not stat.startswith('_') and stat not in stats:
        #         stats[stat] = getattr(status, stat, None)

        update_time = time.time()
        self.last_update[1] = update_time

        # extract the ones we are interested in
        # adding them to the 1s array
        for stat, stat_list in self.stats[1].items():
            if stat in stats:
                stat_list.insert(0, int(stats[stat]))
            else:
                stat_list.insert(0, 0)
            if len(stat_list) > self.length:
                stat_list.pop()

        def update_interval(interval, base, multiplier):
            self.count[interval] = self.count[interval] + 1
            if self.count[interval] >= interval:
                self.last_update[interval] = update_time
                self.count[interval] = 0
                current_stats = self.stats[interval]
                for stat, stat_list in self.stats[base].items():
                    try:
                        avg = mean(stat_list[0:multiplier])
                    except ValueError:
                        avg = 0
                    current_stats[stat].insert(0, avg)
                    if len(current_stats[stat]) > self.length:
                        current_stats[stat].pop()

        update_interval(5, 1, 5)
        update_interval(30, 5, 6)
        update_interval(300, 30, 10)

    def save_stats(self):
        self.saved_stats['stats'] = self.stats
        self.saved_stats.config.update(self.get_totals())
        self.saved_stats.save()

    # export:
    @export
    def get_stats(self, keys, interval):
        if interval not in self.intervals:
            return None

        stats_dict = {}
        for key in keys:
            if key in self.stats[interval]:
                stats_dict[key] = self.stats[interval][key]

        stats_dict['_last_update'] = self.last_update[interval]
        stats_dict['_length'] = self.config['length']
        stats_dict['_update_interval'] = interval
        return stats_dict

    @export
    def get_totals(self):
        result = {}
        session_totals = self.get_session_totals()
        for key in session_totals:
            result[key] = self.totals[key] + session_totals[key]
        return result

    @export
    def get_session_totals(self):
        return self.core.get_session_status(
            [
                'total_upload',
                'total_download',
                'total_payload_upload',
                'total_payload_download',
            ]
        )

    @export
    def set_config(self, config):
        """Sets the config dictionary."""
        for key in config:
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        """Returns the config dictionary."""
        return self.config.config

    @export
    def get_intervals(self):
        """Returns the available resolutions."""
        return self.intervals
