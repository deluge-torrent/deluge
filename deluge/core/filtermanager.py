# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from six import string_types

import deluge.component as component
from deluge.common import TORRENT_STATE

log = logging.getLogger(__name__)

STATE_SORT = ['All', 'Active'] + TORRENT_STATE


# Special purpose filters:
def filter_keywords(torrent_ids, values):
    # Cleanup
    keywords = ','.join([v.lower() for v in values])
    keywords = keywords.split(',')

    for keyword in keywords:
        torrent_ids = filter_one_keyword(torrent_ids, keyword)
    return torrent_ids


def filter_one_keyword(torrent_ids, keyword):
    """
    search torrent on keyword.
    searches title,state,tracker-status,tracker,files
    """
    all_torrents = component.get('TorrentManager').torrents

    for torrent_id in torrent_ids:
        torrent = all_torrents[torrent_id]
        if keyword in torrent.filename.lower():
            yield torrent_id
        elif keyword in torrent.state.lower():
            yield torrent_id
        elif torrent.trackers and keyword in torrent.trackers[0]['url']:
            yield torrent_id
        elif keyword in torrent_id:
            yield torrent_id
        # Want to find broken torrents (search on "error", or "unregistered")
        elif keyword in torrent.tracker_status.lower():
            yield torrent_id
        else:
            for t_file in torrent.get_files():
                if keyword in t_file['path'].lower():
                    yield torrent_id
                    break


def filter_by_name(torrent_ids, search_string):
    all_torrents = component.get('TorrentManager').torrents
    try:
        search_string, match_case = search_string[0].split('::match')
    except ValueError:
        search_string = search_string[0]
        match_case = False

    if match_case is False:
        search_string = search_string.lower()

    for torrent_id in torrent_ids:
        torrent_name = all_torrents[torrent_id].get_name()
        if match_case is False:
            torrent_name = all_torrents[torrent_id].get_name().lower()
        else:
            torrent_name = all_torrents[torrent_id].get_name()

        if search_string in torrent_name:
            yield torrent_id


def tracker_error_filter(torrent_ids, values):
    filtered_torrent_ids = []
    tm = component.get('TorrentManager')

    # If this is a tracker_host, then we need to filter on it
    if values[0] != 'Error':
        for torrent_id in torrent_ids:
            if values[0] == tm[torrent_id].get_status(['tracker_host'])['tracker_host']:
                filtered_torrent_ids.append(torrent_id)
        return filtered_torrent_ids

    # Check torrent's tracker_status for 'Error:' and return those torrent_ids
    for torrent_id in torrent_ids:
        if 'Error:' in tm[torrent_id].get_status(['tracker_status'])['tracker_status']:
            filtered_torrent_ids.append(torrent_id)
    return filtered_torrent_ids


class FilterManager(component.Component):
    """FilterManager"""

    def __init__(self, core):
        component.Component.__init__(self, 'FilterManager')
        log.debug('FilterManager init..')
        self.core = core
        self.torrents = core.torrentmanager
        self.registered_filters = {}
        self.register_filter('keyword', filter_keywords)
        self.register_filter('name', filter_by_name)
        self.tree_fields = {}

        self.register_tree_field('state', self._init_state_tree)

        def _init_tracker_tree():
            return {'Error': 0}

        self.register_tree_field('tracker_host', _init_tracker_tree)

        self.register_filter('tracker_host', tracker_error_filter)

        def _init_users_tree():
            return {'': 0}

        self.register_tree_field('owner', _init_users_tree)

    def filter_torrent_ids(self, filter_dict):
        """
        returns a list of torrent_id's matching filter_dict.
        core filter method
        """
        if not filter_dict:
            return self.torrents.get_torrent_list()

        # Sanitize input: filter-value must be a list of strings
        for key, value in filter_dict.items():
            if isinstance(value, string_types):
                filter_dict[key] = [value]

        # Optimized filter for id
        if 'id' in filter_dict:
            torrent_ids = list(filter_dict['id'])
            del filter_dict['id']
        else:
            torrent_ids = self.torrents.get_torrent_list()

        # Return if there's nothing more to filter
        if not filter_dict:
            return torrent_ids

        # Special purpose, state=Active.
        if 'state' in filter_dict:
            # We need to make sure this is a list for the logic below
            filter_dict['state'] = list(filter_dict['state'])

        if 'state' in filter_dict and 'Active' in filter_dict['state']:
            filter_dict['state'].remove('Active')
            if not filter_dict['state']:
                del filter_dict['state']
            torrent_ids = self.filter_state_active(torrent_ids)

        if not filter_dict:
            return torrent_ids

        # Registered filters
        for field, values in list(filter_dict.items()):
            if field in self.registered_filters:
                # Filters out doubles
                torrent_ids = list(
                    set(self.registered_filters[field](torrent_ids, values))
                )
                del filter_dict[field]

        if not filter_dict:
            return torrent_ids

        torrent_keys, plugin_keys = self.torrents.separate_keys(
            list(filter_dict), torrent_ids
        )
        # Leftover filter arguments, default filter on status fields.
        for torrent_id in list(torrent_ids):
            status = self.core.create_torrent_status(
                torrent_id, torrent_keys, plugin_keys
            )
            for field, values in filter_dict.items():
                if field in status and status[field] in values:
                    continue
                elif torrent_id in torrent_ids:
                    torrent_ids.remove(torrent_id)
        return torrent_ids

    def get_filter_tree(self, show_zero_hits=True, hide_cat=None):
        """
        returns {field: [(value,count)] }
        for use in sidebar.
        """
        torrent_ids = self.torrents.get_torrent_list()
        tree_keys = list(self.tree_fields)
        if hide_cat:
            for cat in hide_cat:
                tree_keys.remove(cat)

        torrent_keys, plugin_keys = self.torrents.separate_keys(tree_keys, torrent_ids)
        items = {field: self.tree_fields[field]() for field in tree_keys}

        for torrent_id in list(torrent_ids):
            status = self.core.create_torrent_status(
                torrent_id, torrent_keys, plugin_keys
            )  # status={key:value}
            for field in tree_keys:
                value = status[field]
                items[field][value] = items[field].get(value, 0) + 1

        if 'tracker_host' in items:
            items['tracker_host']['All'] = len(torrent_ids)
            items['tracker_host']['Error'] = len(
                tracker_error_filter(torrent_ids, ('Error',))
            )

        if not show_zero_hits:
            for cat in ['state', 'owner', 'tracker_host']:
                if cat in tree_keys:
                    self._hide_state_items(items[cat])

        # Return a dict of tuples:
        sorted_items = {field: sorted(items[field].items()) for field in tree_keys}

        if 'state' in tree_keys:
            sorted_items['state'].sort(key=self._sort_state_item)

        return sorted_items

    def _init_state_tree(self):
        init_state = {}
        init_state['All'] = len(self.torrents.get_torrent_list())
        for state in TORRENT_STATE:
            init_state[state] = 0
        init_state['Active'] = len(
            self.filter_state_active(self.torrents.get_torrent_list())
        )
        return init_state

    def register_filter(self, filter_id, filter_func, filter_value=None):
        self.registered_filters[filter_id] = filter_func

    def deregister_filter(self, filter_id):
        del self.registered_filters[filter_id]

    def register_tree_field(self, field, init_func=lambda: {}):
        self.tree_fields[field] = init_func

    def deregister_tree_field(self, field):
        if field in self.tree_fields:
            del self.tree_fields[field]

    def filter_state_active(self, torrent_ids):
        for torrent_id in list(torrent_ids):
            status = self.torrents[torrent_id].get_status(
                ['download_payload_rate', 'upload_payload_rate']
            )
            if status['download_payload_rate'] or status['upload_payload_rate']:
                pass
            else:
                torrent_ids.remove(torrent_id)
        return torrent_ids

    def _hide_state_items(self, state_items):
        """For hide(show)-zero hits"""
        for value, count in list(state_items.items()):
            if value != 'All' and count == 0:
                del state_items[value]

    def _sort_state_item(self, item):
        try:
            return STATE_SORT.index(item[0])
        except ValueError:
            return 99
