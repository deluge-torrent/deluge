/**
 * Deluge.details.TrackersTab.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

(function () {
    Deluge.details.TrackersTab = Ext.extend(Ext.grid.GridPanel, {
        // fast way to figure out if we have a tracker already.
        trackers: {},
        can_get_trackers_info: false,

        constructor: function (config) {
            config = Ext.apply(
                {
                    title: _('Trackers'),
                    cls: 'x-deluge-trackers',
                    store: new Ext.data.Store({
                        reader: new Ext.data.JsonReader(
                            {
                                idProperty: 'ip',
                                root: 'peers',
                            },
                            Deluge.data.Tracker
                        ),
                    }),
                    columns: [
                        {
                            header: _('Tracker'),
                            width: 300,
                            sortable: true,
                            renderer: 'htmlEncode',
                            dataIndex: 'tracker',
                        },
                        {
                            header: _('Status'),
                            width: 150,
                            sortable: true,
                            renderer: 'htmlEncode',
                            dataIndex: 'status',
                        },
                        {
                            header: _('Peers'),
                            width: 100,
                            sortable: true,
                            renderer: 'htmlEncode',
                            dataIndex: 'peers',
                        },
                        {
                            header: _('Message'),
                            width: 100,
                            renderer: 'htmlEncode',
                            dataIndex: 'message',
                        },
                    ],
                    stripeRows: true,
                    deferredRender: false,
                    autoScroll: true,
                },
                config
            );
            Deluge.details.TrackersTab.superclass.constructor.call(
                this,
                config
            );
        },

        clear: function () {
            this.getStore().removeAll();
            this.trackers = {};
        },

        update: function (torrentId) {
            this.can_get_trackers_info = deluge.server_version > '2.0.5';

            var trackers_keys = this.can_get_trackers_info
                ? Deluge.Keys.Trackers
                : Deluge.Keys.TrackersRedundant;

            deluge.client.web.get_torrent_status(torrentId, trackers_keys, {
                success: this.onTrackersRequestComplete,
                scope: this,
            });
        },

        onTrackersRequestComplete: function (status, options) {
            if (!status) return;

            var store = this.getStore();
            var newTrackers = [];
            var addresses = {};

            if (!this.can_get_trackers_info) {
                status['trackers'] = [
                    {
                        url: status['tracker_host'],
                        message: '',
                    },
                ];
                var tracker_host = status['tracker_host'];
                status['trackers_status'] = {
                    tracker_host: {
                        status: status['tracker_status'],
                        message: '',
                    },
                };
                status['trackers_peers'] = {};
            }

            // Go through the trackers updating and creating tracker records
            Ext.each(
                status.trackers,
                function (tracker) {
                    var url = tracker.url;
                    var tracker_status =
                        url in status.trackers_status
                            ? status.trackers_status[url]
                            : {};
                    var message = tracker.message ? tracker.message : '';
                    if (!message && 'message' in tracker_status) {
                        message = tracker_status['message'];
                    }
                    var tracker_data = {
                        tracker: url,
                        status:
                            'status' in tracker_status
                                ? tracker_status['status']
                                : '',
                        peers:
                            url in status.trackers_peers
                                ? status.trackers_peers[url]
                                : 0,
                        message: message,
                    };
                    if (this.trackers[tracker.url]) {
                        var record = store.getById(tracker.url);
                        record.beginEdit();
                        for (var k in tracker_data) {
                            if (record.get(k) != tracker_data[k]) {
                                record.set(k, tracker_data[k]);
                            }
                        }
                        record.endEdit();
                    } else {
                        this.trackers[tracker.url] = 1;
                        newTrackers.push(
                            new Deluge.data.Tracker(tracker_data, tracker.url)
                        );
                    }
                    addresses[tracker.url] = 1;
                },
                this
            );
            store.add(newTrackers);

            // Remove any trackers that should not be left in the store.
            store.each(function (record) {
                if (!addresses[record.id] && !this.constantRows[record.id]) {
                    store.remove(record);
                    delete this.trackers[record.id];
                }
            }, this);
            store.commitChanges();

            var sortState = store.getSortState();
            if (!sortState) return;
            store.sort(sortState.field, sortState.direction);
        },
    });
})();
