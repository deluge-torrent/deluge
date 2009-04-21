/*
Script: deluge-torrents.js
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
*/

(function() {
	
	/* Renderers for the Torrent Grid */
	function queueRenderer(value) {
		return (value == -1) ? '' : value + 1;
	}
	function torrentNameRenderer(value, p, r) {
		return String.format('<div class="torrent-name x-deluge-{0}">{1}</div>', r.data['state'].toLowerCase(), value);
	}
	function torrentSpeedRenderer(value) {
		if (!value) return;
		return fspeed(value);
	}
	function torrentProgressRenderer(value, p, r) {
		var progress = value.toInt();
		var text = r.data['state'] + ' ' + value.toFixed(2) + '%'
		var width = this.style.match(/\w+:\s*(\d+)\w+/)[1].toInt() - 8;
		return Deluge.progressBar(value.toInt(), width, text);
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
		value.toFixed(3);
	}
	function trackerRenderer(value, p, r) {
		return String.format('<div style="background: url(/tracker/{0}) no-repeat; padding-left: 20px;">{0}</div>', value);
	}
	
	Ext.namespace("Ext.deluge");
	Ext.deluge.TorrentGrid = function(config) {
		Ext.deluge.TorrentGrid.superclass.constructor.call(this, {
			id: 'torrentGrid',
			store: new Ext.data.SimpleStore({
				fields: [
					{name: 'queue'},
					{name: 'name'},
					{name: 'size', type: 'int'},
					{name: 'state'},
					{name: 'progress', type: 'float'},
					{name: 'seeds', type: 'int'},
					{name: 'total_seeds', type: 'int'},
					{name: 'peers', type: 'int'},
					{name: 'total_peers', type: 'int'},
					{name: 'downspeed', type: 'int'},
					{name: 'upspeed', type: 'int'},
					{name: 'eta', type: 'int'},
					{name: 'ratio', type: 'float'},
					{name: 'avail', type: 'float'},
					{name: 'added', type: 'int'},
					{name: 'tracker'}
				],
				id: 16
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
				dataIndex: 'size'
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
				dataIndex: 'seeds'
			}, {
				header: _('Peers'),
				width: 60,
				sortable: true,
				renderer: peersRenderer,
				dataIndex: 'peers'
			}, {
				header: _('Down Speed'),
				width: 80,
				sortable: true,
				renderer: torrentSpeedRenderer,
				dataIndex: 'downspeed'
			}, {
				header: _('Up Speed'),
				width: 80,
				sortable: true,
				renderer: torrentSpeedRenderer,
				dataIndex: 'upspeed'
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
				dataIndex: 'avail'
			}, {
				header: _('Added'),
				width: 80,
				sortable: true,
				renderer: fdate,
				dataIndex: 'added'
			}, {
				header: _('Tracker'),
				width: 120,
				sortable: true,
				renderer: trackerRenderer,
				dataIndex: 'tracker'
			}],
			region: 'center',
			cls: 'deluge-torrents',
			stripeRows: true,
			autoExpandColumn: 'name',
			deferredRender:false,
			autoScroll:true,
			margins: '5 5 0 0'
		});
	}
	
	Ext.extend(Ext.deluge.TorrentGrid, Ext.grid.GridPanel, {
		initComponent: function() {
			Ext.deluge.TorrentGrid.superclass.initComponent.call(this);
			Deluge.Events.on('torrentRemoved', this.onTorrentRemoved, this);
			this.on('rowcontextmenu', function(grid, rowIndex, e) {
				e.stopEvent();
				var selection = grid.getSelectionModel();
				if (!selection.hasSelection()) {
					selection.selectRow(rowIndex);
				}
				Deluge.Menus.Torrent.showAt(e.getPoint());
			});
		},
		
		getTorrent: function(rowIndex) {
			return this.getStore().getAt(rowIndex);
		},
		
		getSelected: function() {
		return this.getSelectionModel().getSelected();
		},
		
		getSelections: function() {
			return this.getSelectionModel().getSelections();
		},
		
		onTorrentRemoved: function(torrentIds) {
			var selModel = this.Grid.getSelectionModel();
			$each(torrentIds, function(torrentId) {
				var record = this.Store.getById(torrentId);
				if (selModel.isSelected(record)) {
					selModel.deselectRow(this.Store.indexOf(record));
				}
				this.Store.remove(record);
				
			}, this);
		}
	});
	Deluge.Torrents = new Ext.deluge.TorrentGrid();
})();