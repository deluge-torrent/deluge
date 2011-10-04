/*!
 * Deluge.details.PeersTab.js
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

Ext.define('Deluge.details.PeersTab', {
    extend: 'Ext.grid.Panel',
    title: _('Peers'),
    cls: 'x-deluge-peers',
    viewConfig: {
        loadMask: false,
    },
    invalidateScrollerOnRefresh: false,

    store: {
        model: 'Deluge.data.Peer',
        proxy: {
            type: 'ajax',
            url: 'peers/',
            reader: {
                type: 'json',
                root: 'peers'
            }
        }
    },

    columns: [{
        text: '&nbsp;',
        dataIndex: 'country',
        width: 30,
        sortable: true,
        renderer: function(v) {
            if (!v.replace(' ', '').replace(' ', '')) {
                return '';
            }
            return Ext.String.format('<img src="flag/{0}" />', v);
        }
    }, {
        text: 'Address',
        dataIndex: 'ip',
        width: 125,
        sortable: true,
        renderer: function(v, p, r) {
            var cls = (r.data['seed'] == 1024) ? 'x-deluge-seed': 'x-deluge-peer';
            return Ext.String.format('<div class="{0}">{1}</div>', cls, v);
        }
    }, {
        text: 'Client',
        dataIndex: 'client',
        width: 125,
        sortable: true,
        renderer: function(v) { return fplain(v) }
    }, {
        text: 'Progress',
        dataIndex: 'progress',
        width: 150,
        sortable: true,
        renderer: function(v) {
            var progress = (v * 100).toFixed(0);
            return Deluge.progressBar(progress, this.width - 8, progress + '%');
        }
    }, {
        text: 'Down Speed',
        dataIndex: 'down_speed',
        width: 100,
        sortable: true,
        renderer: function(v) { return fspeed(v) }
    }, {
        text: 'Up Speed',
        dataIndex: 'up_speed',
        width: 100,
        sortable: true,
        renderer: function(v) { return fspeed(v) }
    }],

    autoScroll: true,
    deferredRender: false,
    stripeRows: true,

    clear: function() {
        this.getStore().removeAll();
    },

    update: function(torrentId) {
        var store = this.getStore(),
            view  = this.getView();

        if (torrentId != this.torrentId) {
            store.removeAll();
            store.getProxy().url = 'peers/' + torrentId;
            this.torrentId = torrentId;
        }
        store.load();
    }
});
