# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (c) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.component as component
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.filterdb import FilterDB

log = logging.getLogger(__name__)


class FilterManager(object):
    """
    FilterManager is used to keep track of which users have access to
    the different torrents.

    """
    def __init__(self, core):
        log.debug('FilterManager init..')
        self.core = core
        self.torrents = core.torrentmanager
        self.filter_db = FilterDB()

        component.get('EventManager').register_event_handler('TorrentAddedEvent', self.on_torrent_added)
        component.get('EventManager').register_event_handler('TorrentRemovedEvent', self.on_torrent_removed)

    def on_torrent_added(self, torrent_id, from_state):
        status = self.torrents[torrent_id].get_status(['owner', 'shared'])
        status['torrent_id'] = torrent_id
        self.filter_db.insert(**status)

    def on_torrent_removed(self, torrent_id):
        records = self.filter_db(torrent_id=torrent_id)
        if not records:
            return
        self.filter_db.delete(records[0])

    def get_torrents_filter(self):
        """
        Get a filter for the torrents this user has permissions to view.

        Returns:
            pydblite.common.Filter: a filter for the torrent IDs this user has access to
        """
        if component.get('RPCServer').get_session_auth_level() == AUTH_LEVEL_ADMIN:
            return self.filter_db.filter()
        user = component.get('RPCServer').get_session_user()
        return (self.filter_db('owner') == user) | (self.filter_db('shared') == True)  # noqa pylint: disable=singleton-comparison

    def get_torrent_list(self):
        """
        Get the list of torrents.

        Returns:
            dict: A dictionary with {torrent_id: Torrent, ...}
        """
        torrents_filter = self.get_torrents_filter()
        # It's not filtered, so use the torrentmanagers dict keys instead
        # to avoid unecessary work i the database
        if not torrents_filter.is_filtered():
            return self.torrents.torrents
        return torrents_filter.db.get_unique_ids('torrent_id', db_filter=torrents_filter)
