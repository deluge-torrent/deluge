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

function queue(value) {
	return (value == -1) ? "" : value + 1;
}

function name(value, p, r) {
	return String.format('<div class="torrent-name x-deluge-{0}">{1}</div>', r.data['state'].toLowerCase(), value);
}

function torrent_speed(value) {
	if (!value) return;
	return fspeed(value);
}

var tpl = '<div class="x-progress-wrap">' +
		'<div class="x-progress-inner">' +
			'<div class="x-progress-bar" style="width:{2}%;">' +
				'<div class="x-progress-text">' +
					'<div>&#160;</div>' +
				'</div>' +
			'</div>' +
			'<div class="x-progress-text x-progress-text-back deluge-torrent-progress">' +
				'<div>{1} {0}%</div>' +
			'</div>' +
		'</div>' +
	'</div>';

function progress(value, p, r) {
	var progress = value.toInt();
	return String.format(tpl, value.toFixed(2), r.data['state'], progress);
}

function seeds(value, p, r) {
	if (r.data['total_seeds'] > -1) {
		return String.format("{0} ({1})", value, r.data['total_seeds']);
	} else {
		return value;
	}
}

function peers(value, p, r) {
	if (r.data['total_peers'] > -1) {
		return String.format("{0} ({1})", value, r.data['total_peers']);
	} else {
		return value;
	}
}

function avail(value) {
	return value.toFixed(3);
}

Deluge.Torrents = {
	Store: new Ext.data.SimpleStore({
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
	
	getTorrent: function(rowIndex) {
		return this.Grid.store.getAt(rowIndex);
	},
	
	getSelected: function() {
		return this.Grid.getSelectionModel().getSelected();
	},
	
	getSelections: function() {
		return this.Grid.getSelectionModel().getSelections();
	}
}
Deluge.Torrents.Store.setDefaultSort("queue");

Deluge.Torrents.Grid = new Ext.grid.GridPanel({
	region: 'center',
	store: Deluge.Torrents.Store,
	cls: 'deluge-torrents',
	columns: [
		{id:'queue',header: "#", width: 30, sortable: true, renderer: queue, dataIndex: 'queue'},
		{id:'name', header: "Name", width: 150, sortable: true, renderer: name, dataIndex: 'name'},
		{header: "Size", width: 75, sortable: true, renderer: fsize, dataIndex: 'size'},
		{header: "Progress", width: 150, sortable: true, renderer: progress, dataIndex: 'progress'},
		{header: "Seeds", width: 60, sortable: true, renderer: seeds, dataIndex: 'seeds'},
		{header: "Peers", width: 60, sortable: true, renderer: peers, dataIndex: 'peers'},
		{header: "Down Speed", width: 80, sortable: true, renderer: torrent_speed, dataIndex: 'downspeed'},
		{header: "Up Speed", width: 80, sortable: true, renderer: torrent_speed, dataIndex: 'upspeed'},
		{header: "ETA", width: 60, sortable: true, renderer: ftime, dataIndex: 'eta'},
		{header: "Ratio", width: 60, sortable: true, renderer: avail, dataIndex: 'ratio'},
		{header: "Avail.", width: 60, sortable: true, renderer: avail, dataIndex: 'avail'},
		{header: "Added", width: 80, sortable: true, renderer: fdate, dataIndex: 'added'},
		{header: "Tracker", width: 120, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'tracker'}
	],	
	stripeRows: true,
	autoExpandColumn: 'name',
	deferredRender:false,
	autoScroll:true,
	margins: '5 5 0 0',
	listeners: {
		'rowcontextmenu': {
			fn: function(grid, rowIndex, e) {
				e.stopEvent();
				var selection = grid.getSelectionModel();
				if (!selection.hasSelection()) {
					selection.selectRow(rowIndex);
				}
				Deluge.Menus.Torrent.showAt(e.getPoint());
			}
		}
	}
})
