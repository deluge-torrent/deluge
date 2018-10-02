# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import unicode_literals

import logging
from time import time

from twisted.internet.defer import maybeDeferred, succeed

import deluge.component as component
from deluge.ui.client import client

log = logging.getLogger(__name__)


class SessionProxy(component.Component):
    """
    The SessionProxy component is used to cache session information client-side
    to reduce the number of RPCs needed to provide a rich user interface.

    It will query the Core for only changes in the status of the torrents
    and will try to satisfy client requests from the cache.

    """

    def __init__(self):
        log.debug('SessionProxy init..')
        component.Component.__init__(self, 'SessionProxy', interval=5)

        # Set the cache time in seconds
        # This is how long data will be valid before re-fetching from the core
        self.cache_time = 1.5

        # Hold the torrents' status.. {torrent_id: [time, {status_dict}], ...}
        self.torrents = {}

        # Holds the time of the last key update.. {torrent_id: {key1, time, ...}, ...}
        self.cache_times = {}

    def start(self):
        client.register_event_handler(
            'TorrentStateChangedEvent', self.on_torrent_state_changed
        )
        client.register_event_handler('TorrentRemovedEvent', self.on_torrent_removed)
        client.register_event_handler('TorrentAddedEvent', self.on_torrent_added)

        def on_get_session_state(torrent_ids):
            for torrent_id in torrent_ids:
                # Let's at least store the torrent ids with empty statuses
                # so that upcoming queries or status updates don't throw errors.
                self.torrents.setdefault(torrent_id, [time(), {}])
                self.cache_times.setdefault(torrent_id, {})
            return torrent_ids

        return client.core.get_session_state().addCallback(on_get_session_state)

    def stop(self):
        client.deregister_event_handler(
            'TorrentStateChangedEvent', self.on_torrent_state_changed
        )
        client.deregister_event_handler('TorrentRemovedEvent', self.on_torrent_removed)
        client.deregister_event_handler('TorrentAddedEvent', self.on_torrent_added)
        self.torrents = {}

    def create_status_dict(self, torrent_ids, keys):
        """
        Creates a status dict from the cache.

        :param torrent_ids: the torrent_ids
        :type torrent_ids: list of strings
        :param keys: the status keys
        :type keys: list of strings

        :returns: a dict with the status information for the *torrent_ids*
        :rtype: dict

        """
        sd = {}
        keys = set(keys)
        keys_len = (
            -1
        )  # The number of keys for the current cache (not the len of keys_diff_cached)
        keys_diff_cached = []

        for torrent_id in torrent_ids:
            try:
                if keys:
                    sd[torrent_id] = self.torrents[torrent_id][1].copy()

                    # Have to remove the keys that weren't requested
                    if len(sd[torrent_id]) == keys_len:
                        # If the number of keys are equal they are the same keys
                        # so we use the cached diff of the keys we need to remove
                        keys_to_remove = keys_diff_cached
                    else:
                        # Not the same keys so create a new diff
                        keys_to_remove = set(sd[torrent_id]) - keys
                        # Update the cached diff
                        keys_diff_cached = keys_to_remove
                        keys_len = len(sd[torrent_id])

                    # Usually there are no keys to remove, so it's cheaper with
                    # this if-test than a for-loop with no iterations.
                    if keys_to_remove:
                        for k in keys_to_remove:
                            del sd[torrent_id][k]
                else:
                    sd[torrent_id] = dict(self.torrents[torrent_id][1])
            except KeyError:
                continue
        return sd

    def get_torrent_status(self, torrent_id, keys):
        """
        Get a status dict for one torrent.

        :param torrent_id: the torrent_id
        :type torrent_id: string
        :param keys: the status keys
        :type keys: list of strings

        :returns: a dict of status information
        :rtype: dict

        """
        if torrent_id in self.torrents:
            # Keep track of keys we need to request from the core
            keys_to_get = []
            if not keys:
                keys = list(self.torrents[torrent_id][1])

            for key in keys:
                if (
                    time() - self.cache_times[torrent_id].get(key, 0.0)
                    > self.cache_time
                ):
                    keys_to_get.append(key)
            if not keys_to_get:
                return succeed(self.create_status_dict([torrent_id], keys)[torrent_id])
            else:
                d = client.core.get_torrent_status(torrent_id, keys_to_get, True)

                def on_status(result, torrent_id):
                    t = time()
                    self.torrents[torrent_id][0] = t
                    self.torrents[torrent_id][1].update(result)
                    for key in keys_to_get:
                        self.cache_times[torrent_id][key] = t
                    return self.create_status_dict([torrent_id], keys)[torrent_id]

                return d.addCallback(on_status, torrent_id)
        else:
            d = client.core.get_torrent_status(torrent_id, keys, True)

            def on_status(result):
                if result:
                    t = time()
                    self.torrents[torrent_id] = (t, result)
                    self.cache_times[torrent_id] = {}
                    for key in result:
                        self.cache_times[torrent_id][key] = t

                return result

            return d.addCallback(on_status)

    def get_torrents_status(self, filter_dict, keys):
        """
        Get a dict of torrent statuses.

        The filter can take 2 keys, *state* and *id*.  The state filter can be
        one of the torrent states or the special one *Active*.  The *id* key is
        simply a list of torrent_ids.

        :param filter_dict: the filter used for this query
        :type filter_dict: dict
        :param keys: the status keys
        :type keys: list of strings

        :returns: a dict of torrent_ids and their status dicts
        :rtype: dict

        """
        # Helper functions and callbacks ---------------------------------------
        def on_status(result, torrent_ids, keys):
            # Update the internal torrent status dict with the update values
            t = time()
            for key, value in result.items():
                try:
                    self.torrents[key][0] = t
                    self.torrents[key][1].update(value)
                    for k in value:
                        self.cache_times[key][k] = t
                except KeyError:
                    # The torrent was removed
                    continue

            # Create the status dict
            if not torrent_ids:
                torrent_ids = list(result)

            return self.create_status_dict(torrent_ids, keys)

        def find_torrents_to_fetch(torrent_ids):
            to_fetch = []
            t = time()
            for torrent_id in torrent_ids:
                torrent = self.torrents[torrent_id]
                if t - torrent[0] > self.cache_time:
                    to_fetch.append(torrent_id)
                else:
                    # We need to check if a key is expired
                    for key in keys:
                        if (
                            t - self.cache_times[torrent_id].get(key, 0.0)
                            > self.cache_time
                        ):
                            to_fetch.append(torrent_id)
                            break

            return to_fetch

        # -----------------------------------------------------------------------

        if not filter_dict:
            # This means we want all the torrents status
            # We get a list of any torrent_ids with expired status dicts
            torrents_list = list(self.torrents)
            to_fetch = find_torrents_to_fetch(torrents_list)
            if to_fetch:
                d = client.core.get_torrents_status({'id': to_fetch}, keys, True)
                return d.addCallback(on_status, torrents_list, keys)

            # Don't need to fetch anything
            return maybeDeferred(self.create_status_dict, torrents_list, keys)

        if len(filter_dict) == 1 and 'id' in filter_dict:
            # At this point we should have a filter with just "id" in it
            to_fetch = find_torrents_to_fetch(filter_dict['id'])
            if to_fetch:
                d = client.core.get_torrents_status({'id': to_fetch}, keys, True)
                return d.addCallback(on_status, filter_dict['id'], keys)
            else:
                # Don't need to fetch anything, so just return data from the cache
                return maybeDeferred(self.create_status_dict, filter_dict['id'], keys)
        else:
            # This is a keyworded filter so lets just pass it onto the core
            # XXX: Add more caching here.
            d = client.core.get_torrents_status(filter_dict, keys, True)
            return d.addCallback(on_status, None, keys)

    def on_torrent_state_changed(self, torrent_id, state):
        if torrent_id in self.torrents:
            self.torrents[torrent_id][1].setdefault('state', state)
            self.cache_times.setdefault(torrent_id, {}).update(state=time())

    def on_torrent_added(self, torrent_id, from_state):
        self.torrents[torrent_id] = [time() - self.cache_time - 1, {}]
        self.cache_times[torrent_id] = {}

        def on_status(status):
            self.torrents[torrent_id][1].update(status)
            t = time()
            for key in status:
                self.cache_times[torrent_id][key] = t

        client.core.get_torrent_status(torrent_id, []).addCallback(on_status)

    def on_torrent_removed(self, torrent_id):
        if torrent_id in self.torrents:
            del self.torrents[torrent_id]
            del self.cache_times[torrent_id]
