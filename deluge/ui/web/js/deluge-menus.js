Deluge.Menus = {}

Deluge.Menus.Connections = new Ext.menu.Menu({
	id: 'connectionsMenu',
	items: [{
		id: '50',
		text: '50',
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '100',
		text: '100',
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '200',
		text: '200',
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '300',
		text: '300',
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '500',
		text: '500',
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '-1',
		text: 'Unlimited',
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	},'-',{
		id: 'other',
		text: 'Other',
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	}]
});

Deluge.Menus.Download = new Ext.menu.Menu({
	id: 'downspeedMenu',
	items: [{
		id: '5',
		text: '5 KiB/s',
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '10',
		text: '10 KiB/s',
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '30',
		text: '30 KiB/s',
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '80',
		text: '80 KiB/s',
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '300',
		text: '300 KiB/s',
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '-1',
		text: 'Unlimited',
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	},'-',{
		id: 'other',
		text: 'Other',
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	}]
});

Deluge.Menus.Upload = new Ext.menu.Menu({
	id: 'upspeedMenu',
	items: [{
		id: '5',
		text: '5 KiB/s',
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '10',
		text: '10 KiB/s',
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '30',
		text: '30 KiB/s',
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '80',
		text: '80 KiB/s',
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '300',
		text: '300 KiB/s',
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	},{
		id: '-1',
		text: 'Unlimited',
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	},'-',{
		id: 'other',
		text: 'Other',
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	}]
});

function onLimitChanged(item, checked) {
	if (item.id == "other") {
	} else {
		config = {}
		config[item.group] = item.id
		Deluge.Client.core.set_config(config, {
			onSuccess: function() {
				Deluge.Ui.update();
			}
		});
	}
}