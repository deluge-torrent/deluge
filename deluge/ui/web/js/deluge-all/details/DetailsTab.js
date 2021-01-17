/**
 * Deluge.Details.Details.js
 *      The details tab displayed in the details panel.
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Deluge.details.DetailsTab = Ext.extend(Ext.Panel, {
    title: _('Details'),

    fields: {},
    autoScroll: true,
    queuedItems: {},

    oldData: {},

    initComponent: function () {
        Deluge.details.DetailsTab.superclass.initComponent.call(this);
        this.addItem('torrent_name', _('Name:'));
        this.addItem('hash', _('Hash:'));
        this.addItem('path', _('Download Folder:'));
        this.addItem('size', _('Total Size:'));
        this.addItem('files', _('Total Files:'));
        this.addItem('comment', _('Comment:'));
        this.addItem('status', _('Status:'));
        this.addItem('tracker', _('Tracker:'));
        this.addItem('creator', _('Created By:'));
    },

    onRender: function (ct, position) {
        Deluge.details.DetailsTab.superclass.onRender.call(this, ct, position);
        this.body.setStyle('padding', '10px');
        this.dl = Ext.DomHelper.append(this.body, { tag: 'dl' }, true);

        for (var id in this.queuedItems) {
            this.doAddItem(id, this.queuedItems[id]);
        }
    },

    addItem: function (id, label) {
        if (!this.rendered) {
            this.queuedItems[id] = label;
        } else {
            this.doAddItem(id, label);
        }
    },

    // private
    doAddItem: function (id, label) {
        Ext.DomHelper.append(this.dl, { tag: 'dt', cls: id, html: label });
        this.fields[id] = Ext.DomHelper.append(
            this.dl,
            { tag: 'dd', cls: id, html: '' },
            true
        );
    },

    clear: function () {
        if (!this.fields) return;
        for (var k in this.fields) {
            this.fields[k].dom.innerHTML = '';
        }
        this.oldData = {};
    },

    update: function (torrentId) {
        deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Details, {
            success: this.onRequestComplete,
            scope: this,
            torrentId: torrentId,
        });
    },

    onRequestComplete: function (torrent, request, response, options) {
        var data = {
            torrent_name: torrent.name,
            hash: options.options.torrentId,
            path: torrent.download_location,
            size: fsize(torrent.total_size),
            files: torrent.num_files,
            status: torrent.message,
            tracker: torrent.tracker_host,
            comment: torrent.comment,
            creator: torrent.creator,
        };

        for (var field in this.fields) {
            if (!Ext.isDefined(data[field])) continue; // This is a field we are not responsible for.
            if (data[field] == this.oldData[field]) continue;
            this.fields[field].dom.innerHTML = Ext.escapeHTML(data[field]);
        }
        this.oldData = data;
    },
});
