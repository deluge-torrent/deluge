# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

from twisted.internet import reactor, task

import deluge.component as component
from deluge.event import SessionProxyUpdateEvent
from deluge.ui.client import client

from .torrentfilter import FilterTree, TorrentFilter

log = logging.getLogger(__name__)


class TorrrentsState(object):

    def __init__(self):
        self.status = None
        self.filter = {}
        self.filter_changed = False
        self.visible_torrents = set()

    def update_status(self, update):
        self.visible_torrents -= update.not_matching
        self.visible_torrents |= update.new_matching
        if self.status is not None:
            self.status.update(update.status)
        self.filter_changed = False

    def set_filter(self, filter_dict):
        """
        Sets the filters for the torrent state

        """
        for k in filter_dict:
            if filter_dict[k] is None:
                if self.filter.pop(k, -1) == -1:
                    self.filter_changed = True
            else:
                if self.filter.get(k, None) != filter_dict[k]:
                    self.filter_changed = True
                self.filter[k] = filter_dict[k]


class StateUpdate(object):

    def __init__(self, keys):
        self.keys = keys
        self.status = {}
        self.updated_ids = set()
        self.not_matching = set()
        self.new_matching = set()


class SessionProxy(component.Component):
    """
    The SessionProxy component is used to cache session information client-side
    to reduce the number of RPCs needed to provide a rich user interface.

    It may query the Core for only the torrents that have been changed
    and will try to satisfy client requests from the cache.

    """
    def __init__(self):
        log.debug('SessionProxy init..')
        component.Component.__init__(self, 'SessionProxy', interval=5)

        # The torrent ids that have been updated from core
        self.updated_ids = set()
        self.torrentfilter = TorrentFilter()
        self.torrents = self.torrentfilter.torrents
        self.filtertree = FilterTree(self.torrentfilter)

    def start(self):
        client.register_event_handler('TorrentStateChangedEvent', self.on_torrent_state_changed)
        client.register_event_handler('TorrentRemovedEvent', self.on_torrent_removed)
        client.register_event_handler('TorrentAddedEvent', self.on_torrent_added)

        def on_get_session_state(torrent_ids):
            for torrent_id in torrent_ids:
                # Let's at least store the torrent ids with empty statuses
                # so that upcoming queries or status updates don't throw errors.
                self.torrents.setdefault(torrent_id, {})
            return torrent_ids
        return client.core.get_session_state().addCallback(on_get_session_state)

    def stop(self):
        client.deregister_event_handler('TorrentStateChangedEvent', self.on_torrent_state_changed)
        client.deregister_event_handler('TorrentRemovedEvent', self.on_torrent_removed)
        client.deregister_event_handler('TorrentAddedEvent', self.on_torrent_added)
        self.torrentfilter.reset()

    def get_torrent_status(self, torrent_id, keys):
        """
        Get the status dict for a torrent

        Args:
            torrent_id (str): the torrent ID to create fetch
            keys      (list): the keys to include in the dict

        Returns:
            dict: The status for the torrent

        """
        if not keys and torrent_id in self.torrents:
            keys = self.torrents[torrent_id].keys()
        d = client.core.get_torrent_status(torrent_id, keys)

        def on_status(status):
            # torrent_id could have been removed from self.torrents in the meanwhile
            if torrent_id not in self.torrents:
                return {}
            self.torrentfilter.update_torrent(torrent_id, status)
            if keys:
                keys_to_use = set(keys) & set(self.torrents[torrent_id].keys())
                status = {k: self.torrents[torrent_id][k] for k in keys_to_use}
            return status
        return d.addCallback(on_status)

    def get_torrents_status(self, torrents_state, keys, only_updated=False, from_cache=False):
        """Get a dict of torrent statuses.

        The filter can take 2 keys, *state* and *id*.  The state filter can be
        one of the torrent states or the special one *Active*.  The *id* key is
        simply a list of torrent_ids.
        With from_cache=False, only_updated will in practice be ignored because all torrents will
        be returned from core and hence be updated, so all torrents will then be returned no matter
        the value of only_updated.

        Args:
            filter_dict (dict): the filter used for the query
            keys (list): the status keys to retrieve for each torrent
            only_updated (bool): If only the torrents that have been updated since last call should be returned
            from_cache (bool): if the results should be returned after requesting an update from core
            current_ids (set): The ids of the torrents currently displayed.

        Returns:
            dict: The status for the torrents

        """
        def on_status(result, torrent_ids, keys, only_updated):
            # Update the internal torrent status dict with the updated values
            for torrent_id, value in result.iteritems():
                self.torrentfilter.update_torrent(torrent_id, value)
                self.updated_ids.add(torrent_id)

        # Remove duplicates
        keys_to_update = list(set(list(keys)))

        def get_filtered_torrents(*args, **kw):
            only_updated = kw.get('only_updated', False)
            visible_torrents = kw.get('visible_torrents', None)
            # Only updated torrents were requested, so pass the updated torrents to create_status_dict
            if only_updated:
                only_updated = self.updated_ids
            torrents_filter = self.torrentfilter.filter_torrents(torrents_state.filter)
            update = StateUpdate(keys)
            try:
                self.torrentfilter.create_status_dict(update, torrents_filter, keys,
                                                      only_updated, visible_torrents)
            except ValueError as ve:
                log.warning('Failed to create status dict!')
                log.exception(ve)
                import traceback
                traceback.print_exc()
            return update

        # Waiting for all the torrents from core
        if from_cache is False:
            # issue update from server
            # We ask only for the updated torrents if from_cache is True
            update_d = client.core.get_torrents_status(keys_to_update, only_updated=only_updated)
            update_d.addCallback(on_status, None, keys_to_update, only_updated)
            update_d.addCallback(get_filtered_torrents, only_updated=only_updated,
                                 visible_torrents=torrents_state.visible_torrents)
            return update_d
        else:
            status_d = task.deferLater(reactor, 0, get_filtered_torrents, only_updated=only_updated,
                                       visible_torrents=torrents_state.visible_torrents)
            # We request updates from core, but we will return results from the cache
            update_d = task.deferLater(reactor, 0, client.core.get_torrents_status, keys_to_update,
                                       only_updated=only_updated)
            update_d.addCallback(on_status, None, keys_to_update, only_updated)
            return status_d

    def get_filter_tree(self, show_zero_hits=True, hide_cat=None):
        """
        Get the filter treeview for the sidebar

        Args:
            show_zero_hits (bool): if categories with zero entries should be included
            hide_cat       (list): categories to exclude from the result

        Returns:
            dict: containing elements of 'field: [(value, count), (value, count)]'

        """
        def fetch_filter_tree():
            return self.filtertree.get_filter_tree(show_zero_hits=show_zero_hits, hide_cat=hide_cat)
        return task.deferLater(reactor, 0, fetch_filter_tree)

    def register_tree_field(self, field, func=lambda: {}):
        self.filtertree.register_tree_field(field, func)

    def deregister_tree_field(self, field):
        self.filtertree.deregister_tree_field(field)

    def on_torrent_state_changed(self, torrent_id, state):
        if torrent_id in self.torrents:
            self.torrentfilter.update_torrent(torrent_id, {'state': state})
            self.updated_ids.add(torrent_id)
            client.emit(SessionProxyUpdateEvent(torrent_id, type='state_change', state=state))

    def on_torrent_added(self, torrent_id, from_state):
        self.torrentfilter.add_torrent(torrent_id)

        def on_status(status):
            self.torrentfilter.update_torrent(torrent_id, status)
            self.updated_ids.add(torrent_id)
            client.emit(SessionProxyUpdateEvent(torrent_id, type='added'))
        if not from_state:
            client.core.get_torrent_status(torrent_id, []).addCallback(on_status)

    def on_torrent_removed(self, torrent_id):
        if torrent_id in self.torrents:
            self.torrentfilter.remove_torrent(torrent_id)
            client.emit(SessionProxyUpdateEvent(torrent_id, type='removed'))
