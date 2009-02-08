Deluge.Details = new Ext.TabPanel({
	region: 'south',
	split: true,
	height: 200,
	minSize: 100,
	collapsible: true,
	title: 'Details',
	margins: '0 5 5 5',
	activeTab: 0,
	items: [{
		id: 'status',
		title: 'Status'
	},{
		id: 'details',
		title: 'Details'
	},{
		id: 'files',
		title: 'Files'
	},{
		id: 'peers',
		title: 'Peers'
	},{
		id: 'options',
		title: 'Options'
	}]
});

Deluge.Details.StatusProgressBar = new Ext.ProgressBar({
	text: "0% Stopped",
	id: "pbar-status",
	cls: 'deluge-status-progressbar'
});
Deluge.Details.Status = Deluge.Details.items.get('status');
Deluge.Details.Status.add(Deluge.Details.StatusProgressBar);
Deluge.Details.Status.add({
	id: 'status-details',
	cls: 'deluge-status',
	border: false
});

Deluge.Details.update = function(torrentId) {
	Deluge.Details.getActiveTab().update(torrent);
}