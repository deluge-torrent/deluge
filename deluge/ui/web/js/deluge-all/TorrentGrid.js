/*!
 * Deluge.TorrentGrid.js
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
	function torrentLimitRenderer(value) {
		if (value == -1) return '';
		return fspeed(value * 1024.0);
	}
	function torrentProgressRenderer(value, p, r) {
		value = new Number(value);
		var progress = value;
		var text = r.data['state'] + ' ' + value.toFixed(2) + '%';
		if ( this.style ) {
			var style = this.style
		} else {
			var style = p.style
		}
		var width = new Number(style.match(/\w+:\s*(\d+)\w+/)[1]);
		return Deluge.progressBar(value, width - 8, text);
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
		return (value < 0) ? '&infin;' : parseFloat(new Number(value).toFixed(3));
	}
	function trackerRenderer(value, p, r) {
		return String.format('<div style="background: url(' + deluge.config.base + 'tracker/{0}) no-repeat; padding-left: 20px;">{0}</div>', value);
	}

	function etaSorter(eta) {
		return eta * -1;
	}

	/**
	 * Deluge.TorrentGrid Class
	 *
	 * @author Damien Churchill <damoxc@gmail.com>
	 * @version 1.3
	 *
	 * @class Deluge.TorrentGrid
	 * @extends Ext.grid.GridPanel
	 * @constructor
	 * @param {Object} config Configuration options
	 */
	Deluge.TorrentGrid = Ext.extend(Ext.grid.GridPanel, {

		// object to store contained torrent ids
		torrents: {},

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
			dataIndex: 'total_wanted'
		}, {
			header: _('Progress'),
			width: 150,
			sortable: true,
			renderer: torrentProgressRenderer,
			dataIndex: 'progress'
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
			header: _('Seeders'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: seedsRenderer,
			dataIndex: 'num_seeds'
		}, {
			header: _('Peers'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: peersRenderer,
			dataIndex: 'num_peers'
		}, {
			header: _('Ratio'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: availRenderer,
			dataIndex: 'ratio'
		}, {
			header: _('Avail'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: availRenderer,
			dataIndex: 'distributed_copies'
		}, {
			header: _('Added'),
			hidden: true,
			width: 80,
			sortable: true,
			renderer: fdate,
			dataIndex: 'time_added'
		}, {
			header: _('Tracker'),
			hidden: true,
			width: 120,
			sortable: true,
			renderer: trackerRenderer,
			dataIndex: 'tracker_host'
		}, {
			header: _('Save Path'),
			hidden: true,
			width: 120,
			sortable: true,
			renderer: fplain,
			dataIndex: 'save_path'
		}, {
			header: _('Downloaded'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: fsize,
			dataIndex: 'total_done'
		}, {
			header: _('Uploaded'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: fsize,
			dataIndex: 'total_uploaded'
		}, {
			header: _('Down Limit'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: torrentLimitRenderer,
			dataIndex: 'max_download_speed'
		}, {
			header: _('Up Limit'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: torrentLimitRenderer,
			dataIndex: 'max_upload_speed'
		}, {
			header: _('Seeders') + '/' + _('Peers'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: availRenderer,
			dataIndex: 'seeds_peers_ratio'
		}],

		meta: {
			root: 'torrents',
			idProperty: 'id',
			fields: [
				{name: 'queue', sortType: Deluge.data.SortTypes.asQueuePosition},
				{name: 'name', sortType: Deluge.data.SortTypes.asName},
				{name: 'total_wanted', type: 'int'},
				{name: 'state'},
				{name: 'progress', type: 'float'},
				{name: 'num_seeds', type: 'int'},
				{name: 'total_seeds', type: 'int'},
				{name: 'num_peers', type: 'int'},
				{name: 'total_peers', type: 'int'},
				{name: 'download_payload_rate', type: 'int'},
				{name: 'upload_payload_rate', type: 'int'},
				{name: 'eta', type: 'int', sortType: etaSorter},
				{name: 'ratio', type: 'float'},
				{name: 'distributed_copies', type: 'float'},
				{name: 'time_added', type: 'int'},
				{name: 'tracker_host'},
				{name: 'save_path'},
				{name: 'total_done', type: 'int'},
				{name: 'total_uploaded', type: 'int'},
				{name: 'max_download_speed', type: 'int'},
				{name: 'max_upload_speed', type: 'int'},
				{name: 'seeds_peers_ratio', type: 'float'}
			]
		},

		keys: [{
			key: 'a',
			ctrl: true,
			stopEvent: true,
			handler: function() {
				deluge.torrents.getSelectionModel().selectAll();
			}
		}, {
			key: [46],
			stopEvent: true,
			handler: function() {
				ids = deluge.torrents.getSelectedIds();
				deluge.removeWindow.show(ids);
			}
		}],

		constructor: function(config) {
			config = Ext.apply({
				id: 'torrentGrid',
				store: new Ext.data.JsonStore(this.meta),
				columns: this.columns,
				keys: this.keys,
				region: 'center',
				cls: 'deluge-torrents',
				stripeRows: true,
				autoExpandColumn: 'name',
				autoExpandMin: 150,
				deferredRender:false,
				autoScroll:true,
				margins: '5 5 0 0',
				stateful: true,
				view: new Ext.ux.grid.BufferView({
					rowHeight: 26,
					scrollDelay: false
				})
			}, config);
			Deluge.TorrentGrid.superclass.constructor.call(this, config);
		},

	initComponent: function() {
		Deluge.TorrentGrid.superclass.initComponent.call(this);
		deluge.events.on('torrentRemoved', this.onTorrentRemoved, this);
		deluge.events.on('disconnect', this.onDisconnect, this);

		this.on('rowcontextmenu', function(grid, rowIndex, e) {
			e.stopEvent();
			var selection = grid.getSelectionModel();
			if (!selection.isSelected(rowIndex)) {
				selection.selectRow(rowIndex);
			}
			deluge.menus.torrent.showAt(e.getPoint());
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

	/**
	 * Returns the currently selected record.
	 * @ return {Array/Ext.data.Record} The record(s) representing the rows
	 */
	getSelected: function() {
		return this.getSelectionModel().getSelected();
	},

	/**
	 * Returns the currently selected records.
	 */
	getSelections: function() {
		return this.getSelectionModel().getSelections();
	},

	/**
	 * Return the currently selected torrent id.
	 * @return {String} The currently selected id.
	 */
	getSelectedId: function() {
		return this.getSelectionModel().getSelected().id
	},

	/**
	 * Return the currently selected torrent ids.
	 * @return {Array} The currently selected ids.
	 */
	getSelectedIds: function() {
		var ids = [];
		Ext.each(this.getSelectionModel().getSelections(), function(r) {
			ids.push(r.id);
		});
		return ids;
	},

	update: function(torrents, wipe) {
		var store = this.getStore();

		// Need to perform a complete reload of the torrent grid.
		if (wipe) {
			store.removeAll();
			this.torrents = {};
		}

		var newTorrents = [];

		// Update and add any new torrents.
		for (var t in torrents) {
			var torrent = torrents[t];

			if (this.torrents[t]) {
				var record = store.getById(t);
				record.beginEdit();
				for (var k in torrent) {
					if (record.get(k) != torrent[k]) {
						record.set(k, torrent[k]);
					}
				}
				record.endEdit();
			} else {
				var record = new Deluge.data.Torrent(torrent);
				record.id = t;
				this.torrents[t] = 1;
				newTorrents.push(record);
			}
		}
		store.add(newTorrents);

		// Remove any torrents that should not be in the store.
		store.each(function(record) {
			if (!torrents[record.id]) {
				store.remove(record);
				delete this.torrents[record.id];
			}
		}, this);
		store.commitChanges();

		var sortState = store.getSortState()
		if (!sortState) return;
		store.sort(sortState.field, sortState.direction);
	},

	// private
	onDisconnect: function() {
		this.getStore().removeAll();
		this.torrents = {};
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
			delete this.torrents[torrentId];
		}, this);
	}
});
deluge.torrents = new Deluge.TorrentGrid();
})();
