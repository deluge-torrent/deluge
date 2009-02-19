Deluge.ToolBar = {
	connected_buttons: [
		'create', 'add', 'remove', 'pause', 'resume', 'up', 'down'
	],
	
	onConnect: function() {
		$each(this.connected_buttons, function(button_id) {
			this.Bar.items.get(button_id).enable();
		}, this);
	},
	
	onDisconnect: function() {
		$each(this.connected_buttons, function(button_id) {
			this.Bar.items.get(button_id).disable();
		}, this);
	},
	
	onLogin: function() {
		this.Bar.items.get('logout').enable();
		
	},
	
	onLogout: function() {
		this.Bar.items.get('logout').disable();
		Deluge.Events.fire('logout');
		Deluge.Login.Window.show();
	},
	
	onTorrentAction: function(item) {
		var selection = Deluge.Torrents.getSelectionModel().getSelections();
		var ids = new Array();
		$each(selection, function(record) {
			ids.include(record.id);
		});
		
		switch (item.id) {
			case 'remove':
				Deluge.Client.core.remove_torrent(ids, null, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
			case 'pause':
				Deluge.Client.core.pause_torrent(ids, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
			case 'resume':
				Deluge.Client.core.resume_torrent(ids, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
			case 'up':
				Deluge.Client.core.queue_up(ids, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
			case 'down':
				Deluge.Client.core.queue_down(ids, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
			case 'connectionman':
				Deluge.Connections.Window.show();
				break;
		}
	},
	
	onToolbarRender: function(toolbar) {
		Deluge.Events.on('connect', this.onConnect.bindWithEvent(this));
		Deluge.Events.on('login', this.onLogin.bindWithEvent(this));
	}
}

Deluge.ToolBar.Bar = new Ext.Toolbar({
	items: [
		{
			id: 'create',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Create'),
			icon: '/icons/16/create.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'add',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Add'),
			icon: '/icons/16/add.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'remove',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Remove'),
			icon: '/icons/16/remove.png',
			handler: Deluge.ToolBar.onTorrentAction
		},'|',{
			id: 'pause',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Pause'),
			icon: '/icons/16/pause.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'resume',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Resume'),
			icon: '/icons/16/start.png',
			handler: Deluge.ToolBar.onTorrentAction
		},'|',{
			id: 'up',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Up'),
			icon: '/icons/16/up.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'down',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Down'),
			icon: '/icons/16/down.png',
			handler: Deluge.ToolBar.onTorrentAction
		},'|',{
			id: 'preferences',
			cls: 'x-btn-text-icon',
			text: _('Preferences'),
			icon: '/icons/16/preferences.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'connectionman',
			cls: 'x-btn-text-icon',
			text: _('Connection Manager'),
			icon: '/icons/16/connection_manager.png',
			handler: Deluge.ToolBar.onTorrentAction
		},'->',{
			id: 'help',
			cls: 'x-btn-text-icon',
			disabled: true,
			icon: '/icons/16/help.png',
			text: _('Help')
		},{
			id: 'logout',
			cls: 'x-btn-text-icon',
			icon: '/icons/16/logout.png',
			disabled: true,
			text: _('Logout'),
			handler: Deluge.ToolBar.onLogout,
			scope: Deluge.ToolBar
		}
	],		
	listeners: {'render': Deluge.ToolBar.onToolbarRender, scope: Deluge.ToolBar}
});



Deluge.SideBar = {
	region: 'west',
	id: 'sidebar',
	cls: 'deluge-sidebar',
	title: _('Sidebar'),
	split: true,
	width: 200,
	minSize: 175,
	collapsible: true,
	margins: '5 0 0 5'
};

Deluge.StatusBar = new Ext.StatusBar({
	/*items: [{
		id: 'statusbar-connections',
		text: '200 (200)',
		cls: 'x-btn-text-icon',
		icon: '/icons/16/connection_manager.png',
		menu: Deluge.Menus.Connections
	}, '-', {
		id: 'statusbar-downspeed',
		text: '9.8KiB/s (30 KiB/s)',
		cls: 'x-btn-text-icon',
		icon: '/icons/16/downloading.png',
		menu: Deluge.Menus.Download
	}, '-', {
		id: 'statusbar-upspeed',
		text: '9.8KiB/s (30 KiB/s)',
		cls: 'x-btn-text-icon',
		icon: '/icons/16/seeding.png',
		menu: Deluge.Menus.Upload
	}, '-', {
		id: 'statusbar-traffic',
		text: '1.53/2,65 KiB/s',
		cls: 'x-btn-text-icon',
		icon: '/icons/16/traffic.png'
	}, '-', {
		id: 'statusbar-dht',
		text: '161',
		cls: 'x-btn-text-icon',
		icon: '/icons/16/dht.png'
	}]*/
});