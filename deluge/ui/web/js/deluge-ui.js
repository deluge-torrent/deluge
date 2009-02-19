Deluge.Ui = {
	initialize: function() {
		this.errorCount = 0;
		Ext.state.Manager.setProvider(new Ext.state.CookieProvider());
		this.MainPanel = new Ext.Panel({
			id: 'mainPanel',
			title: 'Deluge',
			layout: 'border',
			tbar: Deluge.ToolBar.Bar,
			items: [Deluge.SideBar, Deluge.Details.Panel,  Deluge.Torrents],
			bbar: Deluge.StatusBar.Bar
		});

		this.Viewport = new Ext.Viewport({
			layout: 'fit',
			items: [this.MainPanel]
		});

		Deluge.Login.Window.show();
		Deluge.Events.on("connect", this.onConnect.bindWithEvent(this));
		Deluge.Events.on("disconnect", this.onDisconnect.bindWithEvent(this));
		Deluge.Client = new JSON.RPC('/json');

		Deluge.SideBar = this.MainPanel.items.get('sidebar');
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
		Deluge.StatusBar.update(data['stats']);
		this.errorCount = 0;
	},
	
	/*
    Property: run
        Start the Deluge UI polling the server to get the updated torrent
        information.

    Example:
        Deluge.UI.onConnect();
    */
	onConnect: function() {
		if (!this.running) {
			this.running = this.update.periodical(2000, this);
			this.update();
		}
	},
	
	onDisconnect: function() {
		this.stop();
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
			Deluge.Torrents.store.loadData([]);
        }
	}
}

document.addEvent('domready', function(e) {
	Deluge.Ui.initialize();
});