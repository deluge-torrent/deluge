/*
Script: Deluge.Details.Peers.js
    The peers tab displayed in the details panel.

Copyright:
	(C) Damien Churchill 2009-2010 <damoxc@gmail.com>
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, write to:
		The Free Software Foundation, Inc.,
		51 Franklin Street, Fifth Floor
		Boston, MA  02110-1301, USA.

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.

*/

(function() {
	function flagRenderer(value) {
		return String.format('<img src="/flag/{0}" />', value);
	}
	function peerAddressRenderer(value, p, record) {
		var seed = (record.data['seed'] == 1024) ? 'x-deluge-seed' : 'x-deluge-peer'
		return String.format('<div class="{0}">{1}</div>', seed, value);
	}
	function peerProgressRenderer(value) {
		var progress = (value * 100).toFixed(0);
		return Deluge.progressBar(progress, this.width - 8, progress + '%');
	}
	function sort_address(value) {
		var d = value.match(/(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\:(\d+)/);
		return ((((((+d[1])*256)+(+d[2]))*256)+(+d[3]))*256)+(+d[4]);
	}

	Deluge.details.PeersTab = Ext.extend(Ext.grid.GridPanel, {
		
		constructor: function(config) {
			config = Ext.apply({
				title: _('Peers'),
				cls: 'x-deluge-peers',
				store: new Ext.data.SimpleStore({
					fields: [
						{name: 'country'},
						{name: 'address', sortType: sort_address},
						{name: 'client'},
						{name: 'progress', type: 'float'},
						{name: 'downspeed', type: 'int'},
						{name: 'upspeed', type: 'int'},
						{name: 'seed', type: 'int'}
					],
					id: 0
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
					dataIndex: 'address'
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
					dataIndex: 'downspeed'
				}, {
					header: 'Up Speed',
					width: 100,
					sortable: true,
					renderer: fspeed,
					dataIndex: 'upspeed'
				}],	
				stripeRows: true,
				deferredRender:false,
				autoScroll:true
			}, config);
			Deluge.details.PeersTab.superclass.constructor.call(this, config);
		},
		
		onRender: function(ct, position) {
			Deluge.details.PeersTab.superclass.onRender.call(this, ct, position);
		},
		
		clear: function() {
			this.getStore().loadData([]);
		},
		
		update: function(torrentId) {
			deluge.client.core.get_torrent_status(torrentId, Deluge.Keys.Peers, {
				success: this.onRequestComplete,
				scope: this
			});
		},
		
		onRequestComplete: function(torrent, options) {
			if (!torrent) return;
			var peers = new Array();
			Ext.each(torrent.peers, function(peer) {
				peers.push([peer.country, peer.ip, peer.client, peer.progress, peer.down_speed, peer.up_speed, peer.seed]);
			}, this);
			this.getStore().loadData(peers);
		}
	});
	deluge.details.add(new Deluge.details.PeersTab());
})();
