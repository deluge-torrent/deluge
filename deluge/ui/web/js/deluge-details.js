Deluge.Details = {}

Deluge.Details.Status = {
	onRender: function(panel) {
		this.panel = panel;
		this.progressBar = new Ext.ProgressBar({
			text: "0% Stopped",
			id: "pbar-status",
			cls: 'deluge-status-progressbar'
		});
		this.panel.add(this.progressBar);
		this.panel.add({
			id: 'status-details',
			cls: 'deluge-status',
			border: false,
			listeners: {'render': Deluge.Details.Status.onStatusRender}
		});
		this.panel.update = this.update.bind(this);
	},
	
	onStatusRender: function(panel) {
		this.status = panel;
		this.status.load({
			url: "/render/tab_statistics.html",
			text: _("Loading") + "..."
		});
	},
	
	update: function(torrentId) {
		alert(torrentId);
	}
}

Deluge.Details.Details = {
	onRender: function(panel) {
		this.panel = panel.load({
			url: "/render/tab_details.html"
		});
	}
}

$extend(Deluge.Details, {

	update: function() {		
		var torrent = Deluge.Torrents.getSelected();
		if (!torrent) return;
		
		var tab = this.Panel.getActiveTab();
		if (tab.update) {
			tab.update(torrent.id);
		}
	},
	
	Panel: new Ext.TabPanel({
		region: 'south',
		split: true,
		height: 200,
		minSize: 100,
		collapsible: true,
		margins: '0 5 5 5',
		activeTab: 0,
		items: [{
			id: 'status',
			title: _('Status'),
			listeners: {'render': {fn: Deluge.Details.Status.onRender, scope: Deluge.Details.Status}}
		},{
			id: 'details',
			title: _('Details'),
			listeners: {'render': {fn: Deluge.Details.Details.onRender, scope: Deluge.Details.Status}}
		},{
			id: 'files',
			title: _('Files')
		},{
			id: 'peers',
			title: _('Peers')
		},{
			id: 'options',
			title: _('Options')
		}]
	})
});