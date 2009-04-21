/*
Script: deluge-ui.js
    The core ui module that builds up the ui layout and controls the polling
	of the server.

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

Deluge.UI = {
	initialize: function() {
		this.errorCount = 0;
		Ext.state.Manager.setProvider(new Ext.state.CookieProvider());
		this.MainPanel = new Ext.Panel({
			id: 'mainPanel',
			iconCls: 'x-deluge-main-panel',
			title: 'Deluge',
			layout: 'border',
			tbar: Deluge.Toolbar,
			items: [
				Deluge.Sidebar,
				Deluge.Details,
				Deluge.Torrents
			],
			bbar: Deluge.Statusbar
		});

		this.Viewport = new Ext.Viewport({
			layout: 'fit',
			items: [this.MainPanel]
		});

		Deluge.Login.show();
		
		Deluge.Events.on("connect", this.onConnect, this);
		Deluge.Events.on("disconnect", this.onDisconnect, this);
		Deluge.Client = new Ext.ux.util.RpcClient({url: '/json'});
		this.update = this.update.bind(this);
	},
	
	update: function() {
		var filters = Deluge.Sidebar.getFilters();
		Deluge.Client.web.update_ui(Deluge.Keys.Grid, filters, {
			success: this.onUpdate,
			failure: this.onUpdateError,
			scope: this
		});
		Deluge.Details.update();
		Deluge.Client.web.connected({
			success: this.onConnectedCheck,
			scope: this
		});
	},
	
	onConnectedCheck: function(connected) {
		if (!connected) {
			Deluge.Events.fire('disconnect');
		}
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
		var torrents = [];
		for (var torrentId in data['torrents']) {
			var torrent = data['torrents'][torrentId];
			torrents.push([torrent.queue,
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
				torrent.time_added,
				torrent.tracker_host,
				torrentId
			]);
		}
		Deluge.Torrents.getStore().loadData(torrents);
		Deluge.Statusbar.update(data['stats']);
		Deluge.Sidebar.update(data['filters']);
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
			this.running = setInterval(this.update, 2000);
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
            clearInterval(this.running);
            this.running = false;
			Deluge.Torrents.getStore().loadData([]);
        }
	}
}

Ext.onReady(function(e) {
	Deluge.UI.initialize();
});