/*
Script: Deluge.Torrents.js
	Contains all objects and functions related to the torrent grid.

Copyright:
	(C) Damien Churchill 2009 <damoxc@gmail.com>
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
	/* Renderers for the Torrent Grid */
	function queueRenderer(value) {
		return (value == 99999) ? '' : value + 1;
	}
	function torrentNameRenderer(value, p, r) {
		return String.format('<div class="torrent-name x-deluge-{0}">{1}</div>', r.data['state'].toLowerCase(), value);
	}
	function torrentSpeedRenderer(value) {
		if (!value) return;
		return fspeed(value);
	}
	function torrentProgressRenderer(value, p, r) {
		value = new Number(value);
		var progress = value;
		var text = r.data['state'] + ' ' + value.toFixed(2) + '%'
		return Deluge.progressBar(value, this.width - 8, text);
	}
	function seedsRenderer(value, p, r) {
		if (r.data['total_seeds'] > -1) {
			return String.format('{0} ({1})', value, r.data['total_seeds']);
		} else {
			return value;
		}
	}
	function peersRenderer(value, p, r) {
		if (r.data['total_peers'] > -1) {
			return String.format('{0} ({1})', value, r.data['total_peers']);
		} else {
			return value;
		}
	}
	function availRenderer(value, p, r)	{
		return (value < 0) ? '∞' : new Number(value).toFixed(3);
	}
	function trackerRenderer(value, p, r) {
		return String.format('<div style="background: url(/tracker/{0}) no-repeat; padding-left: 20px;">{0}</div>', value);
	}
	
	function etaSorter(eta) {
		return eta * -1;
	}

	/**
	 * Ext.deluge.TorrentGrid Class
	 *
	 * @author Damien Churchill <damoxc@gmail.com>
	 * @version 1.3
	 *
	 * @class Ext.deluge.TorrentGrid
	 * @extends Ext.grid.GridPanel
	 * @constructor
	 * @param {Object} config Configuration options
	 */
	Ext.deluge.TorrentGrid = Ext.extend(Ext.grid.GridPanel, {
		constructor: function(config) {
			config = Ext.apply({
				id: 'torrentGrid',
				store: new Ext.data.JsonStore({
					root: 'torrents',
					idProperty: 'id',
					fields: [
						{name: 'queue'},
						{name: 'name'},
						{name: 'total_size', type: 'int'},
						{name: 'state'},
						{name: 'progress', type: 'float'},
						{name: 'num_seeds', type: 'int'},
						{name: 'total_seeds', type: 'int'},
						{name: 'num_peers', type: 'int'},
						{name: 'total_peers', type: 'int'},
						{name: 'download_payload_rate', type: 'int'},
						{name: 'upload_payload_speed', type: 'int'},
						{name: 'eta', type: 'int', sortType: etaSorter},
						{name: 'ratio', type: 'float'},
						{name: 'distributed_copies', type: 'float'},
						{name: 'time_added', type: 'int'},
						{name: 'tracker_host'}
					]
				}),
				columns: [{
					id:'queue',
					header: _('#'), 
					width: 30, 
					sortable: true, 
					renderer: queueRenderer,
					dataIndex: 'queue'
				}, {
					id:'name',
					header: _('Name'),
					width: 150,
					sortable: true,
					renderer: torrentNameRenderer,
					dataIndex: 'name'
				}, {
					header: _('Size'),
					width: 75,
					sortable: true,
					renderer: fsize,
					dataIndex: 'total_size'
				}, {
					header: _('Progress'),
					width: 150, 
					sortable: true, 
					renderer: torrentProgressRenderer,
					dataIndex: 'progress'
				}, {
					header: _('Seeders'),
					width: 60,
					sortable: true,
					renderer: seedsRenderer,
					dataIndex: 'num_seeds'
				}, {
					header: _('Peers'),
					width: 60,
					sortable: true,
					renderer: peersRenderer,
					dataIndex: 'num_peers'
				}, {
					header: _('Down Speed'),
					width: 80,
					sortable: true,
					renderer: torrentSpeedRenderer,
					dataIndex: 'download_payload_rate'
				}, {
					header: _('Up Speed'),
					width: 80,
					sortable: true,
					renderer: torrentSpeedRenderer,
					dataIndex: 'upload_payload_rate'
				}, {
					header: _('ETA'),
					width: 60,
					sortable: true,
					renderer: ftime,
					dataIndex: 'eta'
				}, {
					header: _('Ratio'),
					width: 60,
					sortable: true,
					renderer: availRenderer,
					dataIndex: 'ratio'
				}, {
					header: _('Avail'),
					width: 60,
					sortable: true,
					renderer: availRenderer,
					dataIndex: 'distributed_copies'
				}, {
					header: _('Added'),
					width: 80,
					sortable: true,
					renderer: fdate,
					dataIndex: 'time_added'
				}, {
					header: _('Tracker'),
					width: 120,
					sortable: true,
					renderer: trackerRenderer,
					dataIndex: 'tracker_host'
				}],
				region: 'center',
				cls: 'deluge-torrents',
				stripeRows: true,
				autoExpandColumn: 'name',
				deferredRender:false,
				autoScroll:true,
				margins: '5 5 0 0',
				stateful: true
			}, config);
			Ext.deluge.TorrentGrid.superclass.constructor.call(this, config);
		},

	initComponent: function() {
		Ext.deluge.TorrentGrid.superclass.initComponent.call(this);
		Deluge.Events.on('torrentRemoved', this.onTorrentRemoved, this);
		Deluge.Events.on('logout', this.onDisconnect, this);

		this.on('rowcontextmenu', function(grid, rowIndex, e) {
			e.stopEvent();
			var selection = grid.getSelectionModel();
			if (!selection.hasSelection()) {
				selection.selectRow(rowIndex);
			}
			Deluge.Menus.Torrent.showAt(e.getPoint());
		});
	},

	/**
	 * Returns the record representing the torrent at the specified index.
	 *
	 * @param index {int} The row index of the torrent you wish to retrieve.
	 * @return {Ext.data.Record} The record representing the torrent.
	 */
	getTorrent: function(index) {
		return this.getStore().getAt(index);
	},

	getSelected: function() {
	return this.getSelectionModel().getSelected();
	},

	getSelections: function() {
		return this.getSelectionModel().getSelections();
	},

	update: function(torrents, bulk) {
		if (bulk) {
			this.getStore().loadData({"torrents": Ext.values(torrents)});
		} else {
			this.getStore().loadData({"torrents": Ext.values(torrents)});
		}
	},

	onDisconnect: function() {
		this.getStore().removeAll();
	},

	// private
	onTorrentRemoved: function(torrentIds) {
		var selModel = this.getSelectionModel();
		Ext.each(torrentIds, function(torrentId) {
			var record = this.getStore().getById(torrentId);
			if (selModel.isSelected(record)) {
				selModel.deselectRow(this.getStore().indexOf(record));
			}
			this.getStore().remove(record);
		}, this);
	}
});
Deluge.Torrents = new Ext.deluge.TorrentGrid();
})();
