/**
 * Deluge.details.StatusTab.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge.details');

/**
 * @class Deluge.details.StatusTab
 * @extends Ext.Panel
 */
Deluge.details.StatusTab = Ext.extend(Ext.Panel, {
    title: _('Status'),
    autoScroll: true,

    onRender: function (ct, position) {
        Deluge.details.StatusTab.superclass.onRender.call(this, ct, position);

        this.progressBar = this.add({
            xtype: 'progress',
            cls: 'x-deluge-status-progressbar',
        });

        this.status = this.add({
            cls: 'x-deluge-status',
            id: 'deluge-details-status',

            border: false,
            width: 1000,
            listeners: {
                render: {
                    fn: function (panel) {
                        panel.load({
                            url: deluge.config.base + 'render/tab_status.html',
                            text: _('Loading') + '...',
                        });
                        panel
                            .getUpdater()
                            .on('update', this.onPanelUpdate, this);
                    },
                    scope: this,
                },
            },
        });
    },

    clear: function () {
        this.progressBar.updateProgress(0, ' ');
        for (var k in this.fields) {
            this.fields[k].innerHTML = '';
        }
    },

    update: function (torrentId) {
        if (!this.fields) this.getFields();
        deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Status, {
            success: this.onRequestComplete,
            scope: this,
        });
    },

    onPanelUpdate: function (el, response) {
        this.fields = {};
        Ext.each(
            Ext.query('dd', this.status.body.dom),
            function (field) {
                this.fields[field.className] = field;
            },
            this
        );
    },

    onRequestComplete: function (status) {
        seeds =
            status.total_seeds > -1
                ? status.num_seeds + ' (' + status.total_seeds + ')'
                : status.num_seeds;
        peers =
            status.total_peers > -1
                ? status.num_peers + ' (' + status.total_peers + ')'
                : status.num_peers;
        last_seen_complete =
            status.last_seen_complete > 0.0
                ? fdate(status.last_seen_complete)
                : 'Never';
        completed_time =
            status.completed_time > 0.0 ? fdate(status.completed_time) : '';

        var data = {
            downloaded: fsize(status.total_done, true),
            uploaded: fsize(status.total_uploaded, true),
            share: status.ratio == -1 ? '&infin;' : status.ratio.toFixed(3),
            announce: ftime(status.next_announce),
            tracker_status: status.tracker_status,
            downspeed: status.download_payload_rate
                ? fspeed(status.download_payload_rate)
                : '0.0 KiB/s',
            upspeed: status.upload_payload_rate
                ? fspeed(status.upload_payload_rate)
                : '0.0 KiB/s',
            eta: status.eta < 0 ? '&infin;' : ftime(status.eta),
            pieces: status.num_pieces + ' (' + fsize(status.piece_length) + ')',
            seeds: seeds,
            peers: peers,
            avail: status.distributed_copies.toFixed(3),
            active_time: ftime(status.active_time),
            seeding_time: ftime(status.seeding_time),
            seed_rank: status.seed_rank,
            time_added: fdate(status.time_added),
            last_seen_complete: last_seen_complete,
            completed_time: completed_time,
            time_since_transfer: ftime(status.time_since_transfer),
        };
        data.auto_managed = _(status.is_auto_managed ? 'True' : 'False');

        var translate_tracker_status = {
            Error: _('Error'),
            Warning: _('Warning'),
            'Announce OK': _('Announce OK'),
            'Announce Sent': _('Announce Sent'),
        };
        for (var key in translate_tracker_status) {
            if (data.tracker_status.indexOf(key) != -1) {
                data.tracker_status = data.tracker_status.replace(
                    key,
                    translate_tracker_status[key]
                );
                break;
            }
        }

        data.downloaded +=
            ' (' +
            (status.total_payload_download
                ? fsize(status.total_payload_download)
                : '0.0 KiB') +
            ')';
        data.uploaded +=
            ' (' +
            (status.total_payload_upload
                ? fsize(status.total_payload_upload)
                : '0.0 KiB') +
            ')';

        for (var field in this.fields) {
            this.fields[field].innerHTML = data[field];
        }
        var text = status.state + ' ' + status.progress.toFixed(2) + '%';
        this.progressBar.updateProgress(status.progress / 100.0, text);
    },
});
