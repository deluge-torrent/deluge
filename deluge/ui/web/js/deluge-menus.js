/*
Script: deluge-menus.js
    Contains all the menus contained within the UI for easy access and editing.

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

Deluge.Menus = {
	onTorrentAction: function(e) {
		
	}
}

Deluge.Menus.Torrent = new Ext.menu.Menu({
	id: 'torrentMenu',
	items: [{
		id: 'pause',
		text: _('Pause'),
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus,
		icon: '/icons/16/pause.png'
	}, {
		id: 'resume',
		text: _('Resume'),
		icon: '/icons/16/start.png'
	}, '-', {
		id: 'options',
		text: _('Options'),
		icon: '/icons/16/preferences.png',
		menu: new Ext.menu.Menu({
			items: [{
				text: _('D/L Speed Limit'),
				iconCls: 'x-deluge-downloading',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('5 KiB/s'),
					}, {
						text: _('10 KiB/s'),
					}, {
						text: _('30 KiB/s'),
					}, {
						text: _('80 KiB/s'),
					}, {
						text: _('300 KiB/s'),
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('U/L Speed Limit'),
				iconCls: 'x-deluge-seeding',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('5 KiB/s'),
					}, {
						text: _('10 KiB/s'),
					}, {
						text: _('30 KiB/s'),
					}, {
						text: _('80 KiB/s'),
					}, {
						text: _('300 KiB/s'),
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('Connection Limit'),
				icon: '/icons/16/connections.png',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('50'),
					}, {
						text: _('100'),
					}, {
						text: _('200'),
					}, {
						text: _('300'),
					}, {
						text: _('500'),
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('Upload Slot Limit'),
				icon: '/icons/16/upload_slots.png',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('0'),
					}, {
						text: _('1'),
					}, {
						text: _('2'),
					}, {
						text: _('3'),
					}, {
						text: _('5'),
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('Auto Managed'),
				checked: false
			}]
		})
	}, '-', {
		text: _('Queue'),
		icon: '/icons/16/queue.png',
		menu: new Ext.menu.Menu({
			items: [{
				text: _('Top'),
				icon: '/icons/16/top.png'
			},{
				text: _('Up'),
				icon: '/icons/16/up.png'
			},{
				text: _('Down'),
				icon: '/icons/16/down.png'
			},{
				text: _('Bottom'),
				icon: '/icons/16/bottom.png'
			}]
		})
	}, '-', {
		text: _('Update Tracker'),
		icon: '/icons/16/update.png'
	}, {
		text: _('Edit Trackers'),
		icon: '/icons/16/edit_trackers.png'
	}, '-', {
		text: _('Remove Torrent'),
		icon: '/icons/16/remove.png'
	}, '-', {
		text: _('Force Recheck'),
		icon: '/icons/16/recheck.png'
	}, {
		text: _('Move Storage'),
		icon: '/icons/16/move.png'
	}]
});

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