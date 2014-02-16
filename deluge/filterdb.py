# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 bendikro <bro.develop+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

log = logging.getLogger(__name__)


class FilterDB(object):

    index_columns = ['torrent_id', 'name', 'state', 'tracker_error', 'tracker_status',
                     'owner', 'shared', 'tracker_host', 'active']

    def __new__(cls, sqlite=True):
        if sqlite:
            try:
                return FilterDB.init_sqlite()
            except ImportError, e:
                log.debug('Failed to setup SQLite, using pure python filter instead. (%s)', e)
        return FilterDB.init_python_db()

    @staticmethod
    def init_sqlite():
        from pydblite.sqlite import Database, Table
        db = Database(':memory:')
        filter_db = Table('deluge', db)
        filter_db.create(('torrent_id', 'TEXT'), ('name', 'TEXT'), ('state', 'TEXT'), ('tracker_error', 'INTEGER'),
                         ('tracker_status', 'TEXT'), ('owner', 'TEXT'), ('shared', 'INTEGER'), ('tracker_host', 'TEXT'),
                         ('active', 'INTEGER'), ('total_wanted', 'INTEGER DEFAULT 0'),
                         ('all_time_download', 'INTEGER DEFAULT 0'), ('total_uploaded', 'INTEGER'),
                         ('progress', 'REAL'), ('num_seeds', 'INTEGER'), ('total_seeds', 'INTEGER'),
                         ('num_peers', 'INTEGER'), ('total_peers', 'INTEGER'), ('seeds_peers_ratio', 'REAL'),
                         ('download_payload_rate', 'REAL'), ('upload_payload_rate', 'REAL'),
                         ('max_download_speed', 'REAL'), ('max_upload_speed', 'REAL'), ('eta', 'INTEGER'),
                         ('ratio', 'REAL'), ('distributed_copies', 'REAL'), ('time_added', 'REAL'),
                         ('completed_time', 'REAL'), ('last_seen_complete', 'REAL'),
                         ('num_pieces', 'INTEGER DEFAULT 0'), ('piece_length', 'INTEGER DEFAULT 0'),
                         ('total_payload_download', 'INTEGER DEFAULT 0'), ('total_payload_upload', 'INTEGER DEFAULT 0'),
                         ('next_announce', 'INTEGER DEFAULT 0'), ('active_time', 'INTEGER DEFAULT 0'),
                         ('seeding_time', 'INTEGER DEFAULT 0'))
        filter_db.create_index(*FilterDB.index_columns)
        return filter_db

    @staticmethod
    def init_python_db():
        """
        download_payload_rate/upload_payload_rate: Needed to set the value of field 'active'
        active: Filter on active in sidebar
        tracker_status: Needed to set value in 'tracker_error' field if there is a tracker status error (in the sidebar)
        owner: Filter on owner in sidebar
        state: Filter on state in the sidebar
        """
        from pydblite.pydblite import Base
        filter_db = Base('python_database', save_to_file=False)
        filter_db.create('torrent_id', 'name', 'state', 'tracker_error', 'tracker_status',
                         'owner', 'shared', 'tracker_host', 'active', 'download_payload_rate',
                         'upload_payload_rate', mode='override')
        filter_db.create_index(*FilterDB.index_columns)
        return filter_db
