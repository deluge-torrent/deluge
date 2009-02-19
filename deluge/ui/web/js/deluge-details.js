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
	},
	
	onStatusRender: function(panel) {
		this.status = panel;
		this.status.load({
			url: "/render/tab_statistics.html",
			text: _("Loading") + "...",
			callback: this.onStatusLoaded
		});
	},
	
	onStatusLoaded: function() {
		alert("loaded");
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

	update: function(torrentId) {
		
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
			listeners: {'render': Deluge.Details.Status.onRender}
		},{
			id: 'details',
			title: _('Details'),
			listeners: {'render': Deluge.Details.Details.onRender}
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

/*Deluge.Details.Status = {
	onShow: function(panel) {
		this.panel = panel;
	},
	
	initialize: function() {
		this.Panel = Deluge.Details.Panel.items.get('status');
		this.ProgressBar = new Ext.ProgressBar({
			text: "0% Stopped",
			id: "pbar-status",
			cls: 'deluge-status-progressbar'
		});
		this.Panel.add(this.ProgressBar);
		
		
		this.Panel.add({
			id: 'status-details',
			cls: 'deluge-status',
			border: false
		});
		
		//this.Details = Deluge.Details.Status.Panel.items.get("status-details").load({
		//	url: "/render/tab_statistics.html"
		//});
		
	}
}*/