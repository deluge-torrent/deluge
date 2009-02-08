Deluge.ToolBar = new Ext.Toolbar({
	items: [
		{
			id: 'create',
			cls: 'x-btn-text-icon',
			text: _('Create'),
			icon: '/icons/16/create.png',
			handler: torrentAction
		},{
			id: 'add',
			cls: 'x-btn-text-icon',
			text: _('Add'),
			icon: '/icons/16/add.png',
			handler: torrentAction
		},{
			id: 'remove',
			cls: 'x-btn-text-icon',
			text: _('Remove'),
			icon: '/icons/16/remove.png',
			handler: torrentAction
		},{
			id: 'pause',
			cls: 'x-btn-text-icon',
			text: _('Pause'),
			icon: '/icons/16/pause.png',
			handler: torrentAction
		},{
			id: 'resume',
			cls: 'x-btn-text-icon',
			text: _('Resume'),
			icon: '/icons/16/start.png',
			handler: torrentAction
		},{
			id: 'up',
			cls: 'x-btn-text-icon',
			text: _('Up'),
			icon: '/icons/16/up.png',
			handler: torrentAction
		},{
			id: 'down',
			cls: 'x-btn-text-icon',
			text: _('Down'),
			icon: '/icons/16/down.png',
			handler: torrentAction
		},{
			id: 'preferences',
			cls: 'x-btn-text-icon',
			text: _('Preferences'),
			icon: '/icons/16/preferences.png',
			handler: torrentAction
		},{
			id: 'connectionman',
			cls: 'x-btn-text-icon',
			text: _('Connection Manager'),
			icon: '/icons/16/connection_manager.png',
			handler: torrentAction
		}
	]
});

function torrentAction(item) {
	var selection = Deluge.Torrents.getSelectionModel().getSelections();
	var ids = new Array();
	$each(selection, function(record) {
		ids.include(record.id);
	});
	
	switch (item.id) {
		case "remove":
			Deluge.Client.core.remove_torrent(ids, null, {
				onSuccess: function() {
					Deluge.Ui.update();
				}
			});
			break;
		case "pause":
			Deluge.Client.core.pause_torrent(ids, {
				onSuccess: function() {
					Deluge.Ui.update();
				}
			});
			break;
		case "resume":
			Deluge.Client.core.resume_torrent(ids, {
				onSuccess: function() {
					Deluge.Ui.update();
				}
			});
			break;
		case "up":
			Deluge.Client.core.queue_up(ids, {
				onSuccess: function() {
					Deluge.Ui.update();
				}
			});
			break;
		case "down":
			Deluge.Client.core.queue_down(ids, {
				onSuccess: function() {
					Deluge.Ui.update();
				}
			});
			break;
	}	
}

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
	statusAlign: 'left',
	items: [{
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
	}]
});