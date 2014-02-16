# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#               2014 bro <bro.development@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

from deluge import component
from deluge.ui.client import client

log = logging.getLogger(__name__)


class LabelClientBase(object):

    def setup_label_filter(self):
        component.get('SessionProxy').register_tree_field('label', self.create_filter_dict)
        component.get('TorrentFilter').register_filter('label', self.label_filter)
        component.get('TorrentFilter').register_filter_field('label', 'TEXT')

        client.register_event_handler('LabelAddedEvent', self.on_label_added_event)
        client.register_event_handler('LabelRemovedEvent', self.on_label_removed_event)

        self.labels = {}

        def cb_labels(labels):
            self.labels = dict((l, 0) for l in labels)
        client.label.get_labels().addCallback(cb_labels)

    def disable_label_filter(self):
        component.get('SessionProxy').deregister_tree_field('label')
        component.get('TorrentFilter').deregister_filter('label')

    def on_label_added_event(self, label_id):
        self.labels[label_id] = 0

    def on_label_removed_event(self, label_id):
        if label_id in self.labels:
            del self.labels[label_id]

    def label_filter(self, torrents_filter, values):
        for v in values:
            if v != 'All':
                torrents_filter |= (torrents_filter.db('label') == v)
        return torrents_filter

    def create_filter_dict(self, torrents_filter):
        filter_dict = {'All': len(torrents_filter)}
        for label in self.labels:
            filter_dict[label] = 0

        result = torrents_filter.db.get_group_count('label', db_filter=torrents_filter)
        for label in result:
            filter_dict[label[0]] = label[1]
        return filter_dict
