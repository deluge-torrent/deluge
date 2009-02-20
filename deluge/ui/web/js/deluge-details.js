Deluge.Details = {}

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
	        if(this.textTopEl){
	            //textTopEl should be the same width as the bar so overflow will clip as the bar moves
	            this.textTopEl.removeClass('x-hidden').setWidth(w);
	        }
		}
		this.fireEvent('update', this, value, text);
		return this;
	}
});
Ext.reg('deluge-progress', Deluge.ProgressBar);

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
		var fsize = Deluge.Formatters.size, ftime = Deluge.Formatters.timeRemaining, fspeed = Deluge.Formatters.speed;
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
			url: '/render/tab_details.html'
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