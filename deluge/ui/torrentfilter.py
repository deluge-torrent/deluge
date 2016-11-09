# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (c) 2015 Bendik Rønning Opstad <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import copy
import logging
import operator

import deluge.component as component
from deluge.filterdb import FilterDB

STATE_SORT = ['All', 'Downloading', 'Seeding', 'Active', 'Paused', 'Queued']

log = logging.getLogger(__name__)


def tracker_error_filter(torrents_filter, values):
    for v in values:
        if v == 'Error':
            torrents_filter |= (torrents_filter.db('tracker_error') == True)  # noqa pylint: disable=singleton-comparison
        else:
            torrents_filter |= (torrents_filter.db('tracker_host') == values[0])
    return torrents_filter


def state_filter(torrents_filter, values):
    for v in values:
        if v == 'Active':
            torrents_filter |= (torrents_filter.db('active') == True)  # noqa pylint: disable=singleton-comparison
        else:
            torrents_filter |= (torrents_filter.db('state') == v)
    return torrents_filter


def owner_filter(torrents_filter, values):
    for v in values:
        torrents_filter |= (torrents_filter.db('owner') == v)
    return torrents_filter


def search_filter(torrents_filter, values):
    exp = values['expression']
    if values['match_case']:
        col_filter = (torrents_filter.db('name').ilike(exp))
    else:
        col_filter = (torrents_filter.db('name').like(exp))
    torrents_filter = (torrents_filter & col_filter)
    return torrents_filter


class TorrentFilter(component.Component):
    """
    TorrentFilter is used by the sessionproxy to efficiently generate
    query results of torrents based on an input filter.

    """
    def __init__(self,):
        component.Component.__init__(self, 'TorrentFilter')
        log.debug('TorrentFilter init..')
        self.registered_filters = {}
        self.register_filter('state', state_filter)
        self.register_filter('tracker_host', tracker_error_filter)
        self.register_filter('owner', owner_filter)
        self.register_filter('search', search_filter)
        self.torrents = {}
        self.reset()

    def reset(self):
        """
        Reset the database.

        """
        self.filter_db = FilterDB()
        self.torrents.clear()

    def add_torrent(self, torrent_id):
        """
        Add a torrent to the filter database.

        Args:
            torrent_id (str): the torrent id to add

        """
        self.torrents[torrent_id] = {}
        self.filter_db.insert(torrent_id=torrent_id)

    def remove_torrent(self, torrent_id):
        """
        Remove a torrent from the filter database.

        Args:
            torrent_id (str): the torrent id to remove

        """
        del self.torrents[torrent_id]
        records = self.filter_db(torrent_id=torrent_id)  # noqa pylint: disable=not-callable
        self.filter_db.delete(records)

    def update_keys(self, keys):
        """
        Updates the fields in the filter database.

        Args:
            keys (list): the columns to have in the database

        """
        if not isinstance(keys, list):
            raise TypeError("Input value has invalid type. Excpected '%s', found '%s'" % (list, type(keys)))

        missing = set(keys) - set(self.filter_db.fields)
        if missing:
            for field in missing:
                self.filter_db.add_field(field)

    def update_torrent(self, torrent_id, status):
        """
        Updates the filter database with the values from the torrent status

        Args:
            torrent_id (str): the torrent ID
            status (dict): the status dict of the torrent

        """
        # Update torrents dict
        if torrent_id in self.torrents:
            self.torrents[torrent_id].update(status)
        else:
            self.torrents[torrent_id] = status

        # Update filter db
        keys = set(status.keys()) & set(self.filter_db.fields)
        update = dict((k, status[k]) for k in keys)

        update['tracker_error'] = False

        if 'download_payload_rate' in update or 'upload_payload_rate' in update:
            update['active'] = False
            if 'download_payload_rate' in update and update['download_payload_rate']:
                update['active'] = True
            elif 'upload_payload_rate' in update and update['upload_payload_rate']:
                update['active'] = True

        if 'tracker_status' in update and 'Error:' in update['tracker_status']:
            update['tracker_error'] = True

        records = self.filter_db(torrent_id=torrent_id)  # noqa pylint: disable=not-callable
        if not records:
            update['torrent_id'] = torrent_id
            self.filter_db.insert(**update)
        else:
            self.filter_db.update(records[0], **update)

    def get_torrents_filter(self):
        """
        Create an empty filter object that can be used to create a query for
        a subset of the torrent list.

        Returns:
            Filter: an instance of pydblite.common.Filter

        """
        return self.filter_db.filter()

    def filter_torrents(self, filter_dict):
        """
        Create a new Filter based on the filter_dict

        Args:
            filter_dict (dict): the filter options

        Returns:
            Filter: an instance of pydblite.common.Filter

        """
        torrents_filter = self.get_torrents_filter()

        if filter_dict:
            # Sanitize input: filter-value must be a list of strings
            for key, value in filter_dict.items():
                if isinstance(value, basestring):
                    filter_dict[key] = [value]

            # Optimized filter for id
            if 'id' in filter_dict:
                torrent_ids = list(filter_dict['id'])
                torrents_filter = (self.filter_db('torrent_id') == torrent_ids)  # noqa pylint: disable=not-callable

            # Registered filters
            for field, values in filter_dict.items():
                if field in self.registered_filters:
                    new_filter = self.get_torrents_filter()
                    new_filter = self.registered_filters[field](new_filter, values)
                    torrents_filter &= new_filter

        return torrents_filter

    def create_status_dict(self, update, torrents_filter, keys, only_updated_ids, current_ids):
        """
        Create the status dict based on the input arguments.

        Args:
            update (StateUpdate): The StateUpdate object to store the result
            torrents_filter (Filter): used to filter which torrents to return
            keys (list): the keys to include in the status for each torrent
            only_updated_ids (bool): If only updated IDs should be returned
            current_ids (list): The torrents the client currently has visible in the list

        """
        if only_updated_ids is False:
            # All the torrents matching the filter should be added to the state dict
            matching_torrent_ids = []
            for record in torrents_filter:
                torrent = self.torrents[record['torrent_id']]
                update.status[record['torrent_id']] = {key: torrent[key] for key in keys if key in torrent}
                update.updated_ids.add(record['torrent_id'])
            matching_torrent_ids = set(update.updated_ids)
            update.not_matching = current_ids - matching_torrent_ids
            update.new_matching = matching_torrent_ids - current_ids
        else:
            matching_torrent_ids = self.filter_db.get_unique_ids('torrent_id', db_filter=torrents_filter)
            # Filter on only the torrents that have been updated since last time
            filter_only_updated = (self.filter_db('torrent_id') == only_updated_ids)  # noqa pylint: disable=not-callable

            # Filter on the current torrent filter
            records = (filter_only_updated & torrents_filter)

            # Update all the matching torrents in the status dict and remove from the only_updated_ids dict
            for record in records:
                update.updated_ids.add(record['torrent_id'])
                only_updated_ids.discard(record['torrent_id'])
                torrent = self.torrents[record['torrent_id']]
                update.status[record['torrent_id']] = {key: torrent[key] for key in keys if key in torrent}

            # Create lists of the torrents that no longer matches the filter and
            # of new torrents that match the filter (e.g if a torrent changes state)
            update.not_matching = current_ids - matching_torrent_ids
            update.new_matching = update.updated_ids - current_ids

    def register_filter(self, filter_id, filter_func):
        """
        Register a new filter function.

        Args:
            filter_id (str): The name of id of the filter func
            filter_func (func): The function that performs the filtering

        """
        if filter_id in self.registered_filters:
            log.warn("Filter with id '%s' already exists!", filter_id)
            return
        self.registered_filters[filter_id] = filter_func

    def deregister_filter(self, filter_id):
        """
        Deregister a filter function.

        Args:
            id (str): The name of id of the filter func

        """
        del self.registered_filters[filter_id]

    def register_filter_field(self, field, field_type):
        """
        Register a new field in the filter database.

        Args:
            field (str): The name of the database field
            field_type (str): The data type for the field

        """
        if field not in self.filter_db.fields:
            self.filter_db.add_field(field, column_type=field_type)
            log.debug('Added filter field: %s', (field, field_type))


class FilterTree(object):
    """
    The FilterTree is used by the sessionproxy to generate the sidebar
    tree filter.

    """
    def __init__(self, torrentfilter):
        self.tf = torrentfilter
        self.tree_fields = {}
        self.register_tree_field('state', self._create_state_tree)
        self.register_tree_field('tracker_host', self._create_tracker_tree)
        self.register_tree_field('owner', self._create_owners_tree)

    def get_filter_tree(self, show_zero_hits=True, hide_cat=None):
        """
        Get the filter treeview for the sidebar

        Args:
            show_zero_hits (bool): if categories with zero entries should be included
            hide_cat (list): categories to exclude from the result

        Returns:
            dict: containing elements of 'field: [(value, count), (value, count)]'

        """
        tree_keys = list(self.tree_fields.keys())

        if hide_cat:
            for cat in hide_cat:
                tree_keys.remove(cat)

        torrents_filter = self.tf.get_torrents_filter()
        filter_tree_items = dict((field, self.tree_fields[field](torrents_filter)) for field in tree_keys)
        items = copy.deepcopy(filter_tree_items)

        if show_zero_hits is False:
            for cat in ['state', 'owner', 'tracker_host']:
                if cat in tree_keys:
                    self._hide_state_items(items[cat])

        # Return a dict of tuples:
        sorted_items = {}
        for field in tree_keys:
            if field == 'state':
                sorted_items[field] = items[field].items()
                sorted_items[field].sort(self._sort_state_items)
            else:
                sorted_items[field] = sorted(items[field].iteritems(), key=operator.itemgetter(0))

        return sorted_items

    def register_tree_field(self, field, func):
        """
        Register a new field in the tree filter

        Args:
            field (str): The name of the field
            func (func): The filter function

        """
        self.tree_fields[field] = func

    def deregister_tree_field(self, field):
        """
        Deregister a field from the tree filter.

        Args:
            field (str): The name of field

        """
        if field in self.tree_fields:
            del self.tree_fields[field]

    def _create_state_tree(self, torrents_filter):
        tree = {'All': len(torrents_filter),
                'Active': len(torrents_filter & (self.tf.filter_db('active') == True)),  # noqa pylint: disable=singleton-comparison
                'Downloading': 0, 'Seeding': 0, 'Paused': 0, 'Checking': 0, 'Queued': 0, 'Error': 0}
        result = self.tf.filter_db.get_group_count('state', db_filter=torrents_filter)
        for state in result:
            tree[state[0]] = state[1]
        return tree

    def _create_tracker_tree(self, torrents_filter):
        items = {}
        result = self.tf.filter_db.get_group_count('tracker_host', db_filter=torrents_filter)
        for tracker in result:
            items[tracker[0]] = tracker[1]
        items['All'] = len(torrents_filter)
        items['Error'] = len(torrents_filter & (self.tf.filter_db('tracker_error') == True))  # noqa pylint: disable=singleton-comparison
        return items

    def _create_owners_tree(self, torrents_filter):
        items = {'All': len(torrents_filter)}
        result = self.tf.filter_db.get_group_count('owner', db_filter=torrents_filter)
        for owner in result:
            items[owner[0]] = owner[1]
        return items

    def _hide_state_items(self, state_items):
        'for hide(show)-zero hits'
        for (value, count) in state_items.items():
            if value != 'All' and count == 0:
                del state_items[value]

    def _sort_state_items(self, x, y):
        if x[0] in STATE_SORT:
            ix = STATE_SORT.index(x[0])
        else:
            ix = 99
        if y[0] in STATE_SORT:
            iy = STATE_SORT.index(y[0])
        else:
            iy = 99

        return ix - iy
