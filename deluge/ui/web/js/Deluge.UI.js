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
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
*/

Deluge.UI = {

	cookies: new Ext.state.CookieProvider(),
	
	errorCount: 0,
	
	initialize: function() {
		Ext.state.Manager.setProvider(this.cookies);		
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
		
		Deluge.Events.on("connect", this.onConnect, this);
		Deluge.Events.on("disconnect", this.onDisconnect, this);
		Deluge.Client = new Ext.ux.util.RpcClient({
			url: '/json'
		});
		Deluge.Client.on('connected', function(e) {
			Deluge.Login.show();
		});
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
		Deluge.Torrents.update(data['torrents']);
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