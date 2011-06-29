/*!
 * Deluge.details.PeersTab.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
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

(function() {
	function flagRenderer(value) {
		if (!value.replace(' ', '').replace(' ', '')){
            return '';
        }
		return String.format('<img src="flag/{0}" />', value);
	}
	function peerAddressRenderer(value, p, record) {
		var seed = (record.data['seed'] == 1024) ? 'x-deluge-seed' : 'x-deluge-peer';
		// Modify display of IPv6 to include brackets
		var peer_ip = value.split(':');
		if (peer_ip.length > 2) {
			var port = peer_ip.pop();
			var ip = peer_ip.join(":");
			value = "[" + ip + "]:" + port;
		}
		return String.format('<div class="{0}">{1}</div>', seed, value);
	}
	function peerProgressRenderer(value) {
		var progress = (value * 100).toFixed(0);
		return Deluge.progressBar(progress, this.width - 8, progress + '%');
	}

	Deluge.details.PeersTab = Ext.extend(Ext.grid.GridPanel, {

		// fast way to figure out if we have a peer already.
		peers: {},

		constructor: function(config) {
			config = Ext.apply({
				title: _('Peers'),
				cls: 'x-deluge-peers',
				store: new Ext.data.Store({
					reader: new Ext.data.JsonReader({
						idProperty: 'ip',
						root: 'peers'
					}, Deluge.data.Peer)
				}),
				columns: [{
					header: '&nbsp;',
					width: 30,
					sortable: true,
					renderer: flagRenderer,
					dataIndex: 'country'
				}, {
					header: 'Address',
					width: 125,
					sortable: true,
					renderer: peerAddressRenderer,
					dataIndex: 'ip'
				}, {
					header: 'Client',
					width: 125,
					sortable: true,
					renderer: fplain,
					dataIndex: 'client'
				}, {
					header: 'Progress',
					width: 150,
					sortable: true,
					renderer: peerProgressRenderer,
					dataIndex: 'progress'
				}, {
					header: 'Down Speed',
					width: 100,
					sortable: true,
					renderer: fspeed,
					dataIndex: 'down_speed'
				}, {
					header: 'Up Speed',
					width: 100,
					sortable: true,
					renderer: fspeed,
					dataIndex: 'up_speed'
				}],
				stripeRows: true,
				deferredRender:false,
				autoScroll:true
			}, config);
			Deluge.details.PeersTab.superclass.constructor.call(this, config);
		},

		clear: function() {
			this.getStore().removeAll();
			this.peers = {};
		},

		update: function(torrentId) {
			deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Peers, {
				success: this.onRequestComplete,
				scope: this
			});
		},

		onRequestComplete: function(torrent, options) {
			if (!torrent) return;

			var store = this.getStore();
			var newPeers = [];
			var addresses = {};

			// Go through the peers updating and creating peer records
			Ext.each(torrent.peers, function(peer) {
				if (this.peers[peer.ip]) {
                    var record = store.getById(peer.ip);
                    record.beginEdit();
                    for (var k in peer) {
                        if (record.get(k) != peer[k]) {
                            record.set(k, peer[k]);
                        }
                    }
                    record.endEdit();
				} else {
					this.peers[peer.ip] = 1;
					newPeers.push(new Deluge.data.Peer(peer, peer.ip));
				}
				addresses[peer.ip] = 1;
			}, this);
			store.add(newPeers);

			// Remove any peers that shouldn't be left in the store
			store.each(function(record) {
				if (!addresses[record.id]) {
					store.remove(record);
					delete this.peers[record.id];
				}
			}, this);
			store.commitChanges();

			var sortState = store.getSortState();
			if (!sortState) return;
			store.sort(sortState.field, sortState.direction);
		}
	});
})();
