function queue(value) {
	return value + 1;
}

function name(value, p, r) {
	return String.format('<div class="torrent-name {0}">{1}</div>', r.data['state'].toLowerCase(), value);
}

function progress(value, p, r) {
	return String.format('<div class="deluge-torrent-progress">{1} {0}%</div>', value.toFixed(2), r.data['state']);
}

function seeds(value, p, r) {
	return String.format("{0} ({1})", value, r.data['total_seeds']);
}

function peers(value, p, r) {
	return String.format("{0} ({1})", value, r.data['total_peers']);
}

function avail(value) {
	return value.toFixed(3);
}

var torrentStore = new Ext.data.SimpleStore({
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
		{name: 'avail', type: 'float'}
	],
	id: 14
});
torrentStore.setDefaultSort("queue");

Deluge.Torrents = new Ext.grid.GridPanel({
	region: 'center',
	store: torrentStore,
	cls: 'deluge-torrents',
	columns: [
		{id:'queue',header: "#", width: 30, sortable: true, renderer: queue, dataIndex: 'queue'},
		{id:'name', header: "Name", width: 150, sortable: true, renderer: name, dataIndex: 'name'},
		{header: "Size", width: 75, sortable: true, renderer: Deluge.Formatters.size, dataIndex: 'size'},
		{header: "Progress", width: 125, sortable: true, renderer: progress, dataIndex: 'progress'},
		{header: "Seeds", width: 60, sortable: true, renderer: seeds, dataIndex: 'seeds'},
		{header: "Peers", width: 60, sortable: true, renderer: peers, dataIndex: 'peers'},
		{header: "Down Speed", width: 80, sortable: true, renderer: Deluge.Formatters.speed, dataIndex: 'downspeed'},
		{header: "Up Speed", width: 80, sortable: true, renderer: Deluge.Formatters.speed, dataIndex: 'upspeed'},
		{header: "ETA", width: 60, sortable: true, renderer: Deluge.Formatters.timeRemaining, dataIndex: 'eta'},
		{header: "Ratio", width: 60, sortable: true, renderer: avail, dataIndex: 'ratio'},
		{header: "Avail.", width: 60, sortable: true, renderer: avail, dataIndex: 'avail'}
	],	
	stripeRows: true,
	autoExpandColumn: 'name',
	deferredRender:false,
	contentEl: 'torrents',
	autoScroll:true,
	margins: '5 5 0 0'
})