Deluge.Ui = {
	initialize: function() {
		Deluge.Client = new JSON.RPC('/json');
		this.errorCount = 0;
		Ext.state.Manager.setProvider(new Ext.state.CookieProvider());
		
		this.MainPanel = new Ext.Panel({
			id: 'mainPanel',
			title: 'Deluge',
			layout: 'border',
			tbar: Deluge.ToolBar,
			items: [Deluge.SideBar, Deluge.Details,  Deluge.Torrents],
			bbar: Deluge.StatusBar
		});
		
		Deluge.SideBar = this.MainPanel.items.get('sidebar');
		Deluge.SideBar.on('collapse', function(bar) {
			
			//alert(JSON.encode($('sidebar').getSize()));
		});
		
		this.Viewport = new Ext.Viewport({
			layout: 'fit',
			items: [this.MainPanel]
		});
		Deluge.Details.Status.items.get("status-details").load({
			url: "/render/tab_statistics.html"
		});
	},
	
	update: function() {
		Deluge.Client.web.update_ui(Deluge.Keys.Grid, {}, {
			onSuccess: this.onUpdate.bindWithEvent(this),
			onFailure: this.onUpdateError.bindWithEvent(this)
		});
	},
	
	onUpdateError: function(error) {
		if (this.errorCount == 2) {
			Ext.MessageBox.show({
				title: 'Lost Connection',
				msg: 'The connection to the webserver has been lost!',
				buttons: Ext.MessageBox.OK,
				icon: Ext.MessageBox.ERROR
			});
		}
		this.errorCount++;
	},
	
	onUpdate: function(data) {
		var torrents = new Array();
		$each(data['torrents'], function(torrent, id) {
			torrents.include([
				torrent.queue,
				torrent.name,
				torrent.total_size,
				torrent.state,
				torrent.progress,
				torrent.num_seeds,
				torrent.total_seeds,
				torrent.num_peers,
				torrent.total_peers,
				torrent.download_payload_rate,
				torrent.upload_payload_rate,
				torrent.eta,
				torrent.ratio,
				torrent.distributed_copies,
				id
			]);
		});
		Deluge.Torrents.store.loadData(torrents);
		this.updateStatusBar(data['stats']);
		this.errorCount = 0;
	},
	
	updateStatusBar: function(stats) {
		function addSpeed(val) {return val + " KiB/s"}
		
		function updateStat(name, config) {
			var item = Deluge.StatusBar.items.get("statusbar-" + name);
			if (config.limit.value == -1) {
				var str = (config.value.formatter) ? config.value.formatter(config.value.value) : config.value.value;
			} else {
				var value = (config.value.formatter) ? config.value.formatter(config.value.value) : config.value.value;
				var limit = (config.limit.formatter) ? config.limit.formatter(config.limit.value) : config.limit.value;
				var str = String.format(config.format, value, limit);
			}
			item.setText(str);
		}
		
		updateStat("connections", {
			value: {value: stats.num_connections},
			limit: {value: stats.max_num_connections},
			format: "{0} ({1})"
		});

		updateStat("downspeed", {
			value: {
				value: stats.download_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_download,
				formatter: addSpeed
			},
			format: "{0} ({1})"
		});

		updateStat("upspeed", {
			value: {
				value: stats.upload_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_upload,
				formatter: addSpeed
			},
			format: "{0} ({1})"
		});
		
		updateStat("traffic", {
			value: {
				value: stats.payload_download_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.payload_upload_rate,
				formatter: Deluge.Formatters.speed
			},
			format: "{0}/{1}"
		});

		Deluge.StatusBar.items.get('statusbar-dht').setText(stats.dht_nodes);

		function updateMenu(menu, stat) {
			var item = menu.items.get(stat)
			if (!item) {
				item = menu.items.get("other")
			}
			item.setChecked(true);
		}
		
		updateMenu(Deluge.Menus.Connections, stats.max_num_connections);
		updateMenu(Deluge.Menus.Download, stats.max_download);
		updateMenu(Deluge.Menus.Upload, stats.max_upload);
	},
	
	/*
    Property: run
        Start the Deluge UI polling the server to get the updated torrent
        information.

    Example:
        Deluge.UI.run();
    */
	run: function() {
		if (!this.running) {
			this.running = this.update.periodical(2000, this);
			this.update();
		}
	},
	
	/*
    Property: stop
        Stop the Deluge UI polling the server to get the updated torrent
        information.

    Example:
        Deluge.UI.stop();
    */
	stop: function() {
		if (this.running) {
            $clear(this.running);
            this.running = false;
        }
	}
}

document.addEvent('domready', function(e) {
	Deluge.Ui.initialize();
	Deluge.Ui.run();
});