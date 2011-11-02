/*!
 * Deluge.details.StatusTab.js
 *
 * Copyright (c) Damien Churchill 2009-2011 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */

/**
 * @class Deluge.details.StatusTab
 * @extends Ext.panel.Panel
 */
Ext.define('Deluge.details.StatusTab', {
    extend: 'Ext.panel.Panel',

    title: _('Status'),
    autoScroll: true,
    bodyPadding: 10,
    layout: {
        type: 'vbox',
        align: 'stretch'
    },

    initComponent: function() {
        this.callParent(arguments);

        this.fields = {};
        this.progressBar = this.add({
            xtype: 'progressbar',
            cls: 'x-deluge-torrent-progressbar'
        });
        this.add({
            xtype: 'container',
            margins: 10,
            border: false,
            flex: 1,
            layout: {
                type: 'hbox',
                align: 'stretch'
            },
            defaultType: 'container',
            defaults: {
                flex: 1,
                layout: 'vbox',
                border: false,
                defaultType: 'statusitem'
            },

            items: [{
                defaults: {
                    labelWidth: 100,
                    width: 300
                },
                items: [{
                    label: _('Downloaded'),
                    dataIndex: 'downloaded'
                }, {
                    label: _('Uploaded'),
                    dataIndex: 'uploaded'
                }, {
                    label: _('Share Ratio'),
                    dataIndex: 'share'
                }, {
                    label: _('Next Announce'),
                    dataIndex: 'announce'
                }, {
                    label: _('Tracker Status'),
                    dataIndex: 'tracker'
                }]
            }, {
                defaults: {
                    labelWidth: 55,
                    width: 300
                },
                items: [{
                    label: _('Speed'),
                    dataIndex: 'downspeed'
                }, {
                    label: _('Speed'),
                    dataIndex: 'upspeed'
                }, {
                    label: _('ETA'),
                    dataIndex: 'eta'
                }, {
                    label: _('Pieces'),
                    dataIndex: 'pieces'
                }]
            }, {
                defaults: {
                    labelWidth: 130,
                    width: 300
                },
                items: [{
                    label: _('Seeders'),
                    dataIndex: 'seeders'
                }, {
                    label: _('Peers'),
                    dataIndex: 'peers'
                }, {
                    label: _('Availability'),
                    dataIndex: 'avail'
                }, {
                    label: _('Auto Managed'),
                    dataIndex: 'auto_managed'
                }, {
                    label: _('Last Seen Complete'),
                    dataIndex: 'last_seen_complete'
                }]
            }, {
                defaults: {
                    labelWidth: 100,
                    width: 300
                },
                items: [{
                    label: _('Active Time'),
                    dataIndex: 'active_time'
                }, {
                    label: _('Seeding Time'),
                    dataIndex: 'seeding_time'
                }, {
                    label: _('Seed Rank'),
                    dataIndex: 'seed_rank'
                }, {
                    label: _('Date Added'),
                    dataIndex: 'time_rank'
                }]
            }]
        });
    },

    update: function(torrentId) {
        deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Status, {
            success: this.onRequestComplete,
            scope: this
        });
    },

    clear: function() {
        this.progressBar.updateProgress(0, ' ');
        for (var k in this.fields) {
            this.fields[k].innerHTML = '';
        }
    },

    onRequestComplete: function(torrent) {
        var me = this;

        var text = torrent.state + ' ' + torrent.progress.toFixed(2) + '%';
        me.progressBar.updateProgress(torrent.progress / 100.0, text);

        seeders = torrent.total_seeds > -1 ? torrent.num_seeds + ' (' + torrent.total_seeds + ')' : torrent.num_seeds;
        peers = torrent.total_peers > -1 ? torrent.num_peers + ' (' + torrent.total_peers + ')' : torrent.num_peers;
        last_seen_complete = torrent.last_seen_complete > 0.0 ? fdate(torrent.last_seen_complete) : "Never";
        var data = {
            downloaded: fsize(torrent.total_done, true),
            uploaded: fsize(torrent.total_uploaded, true),
            share: (torrent.ratio == -1) ? '&infin;' : torrent.ratio.toFixed(3),
            announce: ftime(torrent.next_announce),
            tracker_torrent: torrent.tracker_torrent,
            downspeed: (torrent.download_payload_rate) ? fspeed(torrent.download_payload_rate) : '0.0 KiB/s',
            upspeed: (torrent.upload_payload_rate) ? fspeed(torrent.upload_payload_rate) : '0.0 KiB/s',
            eta: ftime(torrent.eta),
            pieces: torrent.num_pieces + ' (' + fsize(torrent.piece_length) + ')',
            seeders: seeders,
            peers: peers,
            avail: torrent.distributed_copies.toFixed(3),
            active_time: ftime(torrent.active_time),
            seeding_time: ftime(torrent.seeding_time),
            seed_rank: torrent.seed_rank,
            time_added: fdate(torrent.time_added),
            last_seen_complete: last_seen_complete
        }
        data.auto_managed = _((torrent.is_auto_managed) ? 'True' : 'False');

        data.downloaded += ' (' + ((torrent.total_payload_download) ? fsize(torrent.total_payload_download) : '0.0 KiB') + ')';
        data.uploaded += ' (' + ((torrent.total_payload_download) ? fsize(torrent.total_payload_download): '0.0 KiB') + ')';

        Ext.Array.each(me.query('statusitem'), function(item) {
            item.setText(data[item.dataIndex]);
        }, me);
    }
});
