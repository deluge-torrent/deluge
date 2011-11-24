/*!
 * Deluge.details.DetailsTab.js
 *
 * Copyright (c) Damien Churchill 2009-2011 <damoxc@gmail.com>
 *
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

Ext.define('Deluge.details.DetailsTab', {
    extend: 'Ext.Panel',

    title: _('Details'),
    autoScroll: true,
    fields: {},
    queuedItems: {},
    oldData: {},

    initComponent: function() {
        this.callParent(arguments);
        this.addItem('torrent_name', _('Name'));
        this.addItem('hash', _('Hash'));
        this.addItem('path', _('Path'));
        this.addItem('size', _('Total Size'));
        this.addItem('files', _('# of files'));
        this.addItem('comment', _('Comment'));
        this.addItem('status', _('Status'));
        this.addItem('tracker', _('Tracker'));
        this.addItem('owner', _('Owner'));
        this.addItem('shared', _('Shared'));
    },

    onRender: function(ct, position) {
        this.callParent(arguments);
        this.body.setStyle('padding', '10px');
        this.dl = Ext.core.DomHelper.append(this.body, {tag: 'dl'}, true);

        for (var id in this.queuedItems) {
            this.doAddItem(id, this.queuedItems[id]);
        }
    },

    addItem: function(id, label) {
        if (!this.rendered) {
            this.queuedItems[id] = label;
        } else {
            this.doAddItem(id, label);
        }
    },

    // private
    doAddItem: function(id, label) {
        Ext.core.DomHelper.append(this.dl, {tag: 'dt', cls: id, html: label + ':'});
        this.fields[id] = Ext.core.DomHelper.append(this.dl, {tag: 'dd', cls: id, html: ''}, true);
    },

    clear: function() {
        if (!this.fields) return;
        for (var k in this.fields) {
            this.fields[k].dom.innerHTML = '';
        }
        this.oldData = {}
    },

    update: function(torrentId) {
        deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Details, {
            success: this.onRequestComplete,
            scope: this,
            torrentId: torrentId
        });
    },

    onRequestComplete: function(torrent, request, response, options) {
        var data = {
            torrent_name: torrent.name,
            hash: options.options.torrentId,
            path: torrent.save_path,
            size: fsize(torrent.total_size),
            files: torrent.num_files,
            status: torrent.message,
            tracker: torrent.tracker,
            comment: torrent.comment,
            owner: torrent.owner,
            shared: torrent.shared
        };

        for (var field in this.fields) {
            // this is a field we aren't responsible for.
            if (!Ext.isDefined(data[field])) continue;
            if (data[field] == this.oldData[field]) continue;
            this.fields[field].dom.innerHTML = Ext.escapeHTML(data[field]);
        }
        this.oldData = data;
    }
});
