/*
Script: deluge-details.js
    Contains all objects and functions related to the lower details panel and
	it's containing tabs.

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

Deluge.ProgressBar = Ext.extend(Ext.ProgressBar, {
	initComponent: function() {
		Deluge.ProgressBar.superclass.initComponent.call(this);
	},
	
	updateProgress: function(value, text, animate) {
		this.value = value || 0;
		if (text) {
			this.updateText(text);
		}
		
		if (this.rendered) {
			var w = Math.floor(value*this.el.dom.firstChild.offsetWidth / 100.0);
	        this.progressBar.setWidth(w, animate === true || (animate !== false && this.animate));
	        if (this.textTopEl) {
	            //textTopEl should be the same width as the bar so overflow will clip as the bar moves
	            this.textTopEl.removeClass('x-hidden').setWidth(w);
	        }
		}
		this.fireEvent('update', this, value, text);
		return this;
	}
});
Ext.reg('deluge-progress', Deluge.ProgressBar);

Deluge.Details = {
	update: function(tab) {	
		var torrent = Deluge.Torrents.getSelected();
		if (!torrent) return;
		
		tab = tab || this.Panel.getActiveTab();
		if (tab.update) {
			tab.update(torrent.id);
		}
	},

	onRender: function(panel) {
		Deluge.Torrents.Grid.on('rowclick', this.onTorrentsClick.bindWithEvent(this));
	},
	
	onTabChange: function(panel, tab) {
		this.update(tab);
	},
	
	onTorrentsClick: function(grid, rowIndex, e) {
		this.update();
	}
}

Deluge.Details.Status = {
	onRender: function(panel) {
		this.panel = panel;
		this.progressBar = new Deluge.ProgressBar({
			id: 'pbar-status',
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
			url: '/render/tab_status.html',
			text: _('Loading') + '...'
		});
	},
	
	onRequestComplete: function(status) {
		var data = {
			downloaded: fsize(status.total_done) + ' (' + fsize(status.total_payload_download) + ')',
            uploaded: fsize(status.total_uploaded) + ' (' + fsize(status.total_payload_upload) + ')',
            share: status.ratio.toFixed(3),
            announce: ftime(status.next_announce),
            tracker_status: status.tracker_status,
            downspeed: fspeed(status.download_payload_rate),
            upspeed: fspeed(status.upload_payload_rate),
            eta: ftime(status.eta),
            pieces: status.num_pieces + ' (' + fsize(status.piece_length) + ')',
            seeders: status.num_seeds + ' (' + status.total_seeds + ')',
            peers: status.num_peers + ' (' + status.total_peers + ')',
            avail: status.distributed_copies.toFixed(3),
            active_time: ftime(status.active_time),
            seeding_time: ftime(status.seeding_time),
            seed_rank: status.seed_rank,
			auto_managed: 'False'
		}
		if (status.is_auto_managed) {data.auto_managed = 'True'}
		this.fields.each(function(value, key) {
			value.set('text', data[key]);
		}, this);
		var text = status.state + ' ' + status.progress.toFixed(2) + '%';
		this.progressBar.updateProgress(status.progress, text);
	},
	
	getFields: function() {
		var panel = this.panel.items.get('status-details');
		this.fields = new Hash();
		panel.body.dom.getElements('dd').each(function(item) {
			this.fields[item.getProperty('class')] = item;
		}, this);
	},
	
	update: function(torrentId) {
		if (!this.fields) this.getFields();
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Status, {
			onSuccess: this.onRequestComplete.bind(this)
		});
	}
}

Deluge.Details.Details = {
	onRender: function(panel) {
		this.panel = panel.load({
			url: '/render/tab_details.html',
			text: _('Loading') + '...',
			callback: this.onLoaded.bindWithEvent(this)
		});
		this.doUpdate = false;
		this.panel.update = this.update.bind(this);
	},
	
	onLoaded: function() {
		this.getFields();
		this.doUpdate = true;
		if (Deluge.Details.Panel.getActiveTab() == this.panel) {
			Deluge.Details.update(this.panel);
		}
	},
	
	onRequestComplete: function(torrent, torrentId) {
		var data = {
            torrent_name: torrent.name,
            hash: torrentId,
            path: torrent.save_path,
            size: fsize(torrent.total_size),
            files: torrent.num_files,
            status: torrent.tracker_status,
            tracker: torrent.tracker
        };
		this.fields.each(function(value, key) {
			value.set('text', data[key]);
		}, this);
	},
	
	getFields: function() {
		this.fields = new Hash();
		this.panel.body.dom.getElements('dd').each(function(item) {
			this.fields[item.getProperty('class')] = item;
		}, this);
	},
	
	update: function(torrentId) {
		if (!this.doUpdate) return;
		if (!this.fields) this.getFields();
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Details, {
			onSuccess: this.onRequestComplete.bindWithEvent(this, torrentId)
		});
	}
}

Deluge.Details.Files = {
	onRender: function(panel) {
		this.panel = panel;
	},
	
	update: function(torrentId) {
		
	}
}

Deluge.Details.Peers = {
	onRender: function(panel) {
		this.panel = panel;
		this.panel.update = this.update.bind(this);
	},
	
	onRequestComplete: function(torrent) {
		var peers = new Array();
		torrent.peers.each(function(peer) {
			peers.include([peer.country, peer.ip, peer.client, peer.down_speed, peer.up_speed]);
		}, this);
		this.Store.loadData(peers);
	},
	
	update: function(torrentId) {
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Peers, {
			onSuccess: this.onRequestComplete.bindWithEvent(this, torrentId)
		});
	}
}

function flag(val) {
	return String.format('<img src="/flag/{0}" />', val);
}

function progress(val) {
	return val.toFixed(1);
}

Deluge.Details.Peers.Store = new Ext.data.SimpleStore({
	fields: [
		{name: 'country'},
		{name: 'address'},
		{name: 'client'},
		{name: 'progress', type: 'float'},
		{name: 'downspeed', type: 'int'},
		{name: 'upspeed', type: 'int'}
	],
	id: 0
});

Deluge.Details.Panel = new Ext.TabPanel({
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
		cls: 'deluge-status',
		listeners: {'render': {fn: Deluge.Details.Details.onRender, scope: Deluge.Details.Details}}
	}, new Ext.tree.ColumnTree({
		id: 'files',
		title: _('Files'),
		rootVisible: false,
		autoScroll: true,
		
		columns: [{
			header: _('Filename'),
			width: 330,
			dataIndex: 'filename'
		},{
			header: _('Size'),
			width: 150,
			dataIndex: 'size'
		},{
			header: _('Progress'),
			width: 150,
			dataIndex: 'progress'
		},{
			header: _('Priority'),
			width: 150,
			dataIndex: 'priority'
		}],
		
		root: new Ext.tree.AsyncTreeNode({
            text:'Tasks'
        })
	}), new Ext.grid.GridPanel({
		id: 'peers',
		title: _('Peers'),
		store: Deluge.Details.Peers.Store,
		columns: [
			{header: '&nbsp;', width: 30, sortable: true, renderer: flag, dataIndex: 'country'},
			{header: 'Address', width: 125, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'address'},
			{header: 'Client', width: 125, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'client'},
			{header: 'Progress', width: 150, sortable: true, renderer: progress, dataIndex: 'progress'},
			{header: 'Down Speed', width: 100, sortable: true, renderer: fspeed, dataIndex: 'downspeed'},
			{header: 'Up Speed', width: 100, sortable: true, renderer: fspeed, dataIndex: 'upspeed'}
		],	
		stripeRows: true,
		deferredRender:false,
		autoScroll:true,
		margins: '0 0 0 0',
		listeners: {'render': {fn: Deluge.Details.Peers.onRender, scope: Deluge.Details.Peers}}
	}),{
		id: 'options',
		title: _('Options')
	}],
	listeners: {
		'render': {fn: Deluge.Details.onRender, scope: Deluge.Details},
		'tabchange': {fn: Deluge.Details.onTabChange, scope: Deluge.Details}
	}
});