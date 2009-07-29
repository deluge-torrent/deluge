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

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.

*/

Deluge.Menus = {
	onTorrentAction: function(item, e) {
		var selection = Deluge.Torrents.getSelections();
		var ids = [];
		Ext.each(selection, function(record) {
			ids.push(record.id);
		});
		
		switch (item.id) {
			case 'pause':
			case 'resume':
				Deluge.Client.core[item.id + '_torrent'](ids, {
					success: function() {
						Deluge.UI.update();
					}
				});
				break;
			case 'top':
			case 'up':
			case 'down':
			case 'bottom':
				Deluge.Client.core['queue_' + item.id](ids, {
					success: function() {
						Deluge.UI.update();
					}
				});
				break;
			case 'edit_trackers':
				Deluge.EditTrackers.show();
				break;
			case 'update':
				Deluge.Client.core.force_reannounce(ids, {
					success: function() {
						Deluge.UI.update();
					}
				});
				break;
			case 'remove':
				Deluge.RemoveWindow.show(ids);
				break;
			case 'recheck':
				Deluge.Client.core.force_recheck(ids, {
					success: function() {	
						Deluge.UI.update();
					}
				});
				break;
		}
	}
}

Deluge.Menus.Torrent = new Ext.menu.Menu({
	id: 'torrentMenu',
	items: [{
		id: 'pause',
		text: _('Pause'),
		icon: '/icons/pause.png',
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus
	}, {
		id: 'resume',
		text: _('Resume'),
		icon: '/icons/start.png',
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus
	}, '-', {
		id: 'options',
		text: _('Options'),
		icon: '/icons/preferences.png',
		menu: new Ext.menu.Menu({
			items: [{
				text: _('D/L Speed Limit'),
				iconCls: 'x-deluge-downloading',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('5 KiB/s')
					}, {
						text: _('10 KiB/s')
					}, {
						text: _('30 KiB/s')
					}, {
						text: _('80 KiB/s')
					}, {
						text: _('300 KiB/s')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('U/L Speed Limit'),
				iconCls: 'x-deluge-seeding',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('5 KiB/s')
					}, {
						text: _('10 KiB/s')
					}, {
						text: _('30 KiB/s')
					}, {
						text: _('80 KiB/s')
					}, {
						text: _('300 KiB/s')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('Connection Limit'),
				iconCls: 'x-deluge-connections',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('50')
					}, {
						text: _('100')
					}, {
						text: _('200')
					}, {
						text: _('300')
					}, {
						text: _('500')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('Upload Slot Limit'),
				icon: '/icons/upload_slots.png',
				menu: new Ext.menu.Menu({
					items: [{
						text: _('0')
					}, {
						text: _('1')
					}, {
						text: _('2')
					}, {
						text: _('3')
					}, {
						text: _('5')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				id: 'auto_managed',
				text: _('Auto Managed'),
				checked: false
			}]
		})
	}, '-', {
		text: _('Queue'),
		icon: '/icons/queue.png',
		menu: new Ext.menu.Menu({
			items: [{
				id: 'top',
				text: _('Top'),
				icon: '/icons/top.png',
				handler: Deluge.Menus.onTorrentAction,
				scope: Deluge.Menus
			},{
				id: 'up',
				text: _('Up'),
				icon: '/icons/up.png',
				handler: Deluge.Menus.onTorrentAction,
				scope: Deluge.Menus
			},{
				id: 'down',
				text: _('Down'),
				icon: '/icons/down.png',
				handler: Deluge.Menus.onTorrentAction,
				scope: Deluge.Menus
			},{
				id: 'bottom',
				text: _('Bottom'),
				icon: '/icons/bottom.png',
				handler: Deluge.Menus.onTorrentAction,
				scope: Deluge.Menus
			}]
		})
	}, '-', {
		id: 'update',
		text: _('Update Tracker'),
		icon: '/icons/update.png',
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus
	}, {
		id: 'edit_trackers',
		text: _('Edit Trackers'),
		icon: '/icons/edit_trackers.png',
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus
	}, '-', {
		id: 'remove',
		text: _('Remove Torrent'),
		icon: '/icons/remove.png',
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus
	}, '-', {
		id: 'recheck',
		text: _('Force Recheck'),
		icon: '/icons/recheck.png',
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus
	/*}, {
		id: 'move',
		text: _('Move Storage'),
		icon: '/icons/move.png',
		handler: Deluge.Menus.onTorrentAction,
		scope: Deluge.Menus*/
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
		text: _('Unlimited'),
		group: 'max_connections_global',
		checked: false,
		checkHandler: onLimitChanged
	},'-',{
		id: 'other',
		text: _('Other'),
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
		text: _('Unlimited'),
		group: 'max_download_speed',
		checked: false,
		checkHandler: onLimitChanged
	},'-',{
		id: 'other',
		text: _('Other'),
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
		text: _('Unlimited'),
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	},'-',{
		id: 'other',
		text: _('Other'),
		group: 'max_upload_speed',
		checked: false,
		checkHandler: onLimitChanged
	}]
});

Deluge.Menus.FilePriorities = new Ext.menu.Menu({
	id: 'filePrioritiesMenu',
	items: [{
		id: 'expandAll',
		text: _('Expand All'),
		icon: '/icons/expand_all.png'
	}, '-', {
		id: 'no_download',
		text: _('Do Not Download'),
		icon: '/icons/no_download.png',
		filePriority: 0
	}, {
		id: 'normal',
		text: _('Normal Priority'),
		icon: '/icons/normal.png',
		filePriority: 1
	}, {
		id: 'high',
		text: _('High Priority'),
		icon: '/icons/high.png',
		filePriority: 2
	}, {
		id: 'highest',
		text: _('Highest Priority'),
		icon: '/icons/highest.png',
		filePriority: 5
	}]
});

function onLimitChanged(item, checked) {
	/*if (item.id == "other") {
	} else {
		config = {}
		config[item.group] = item.id
		Deluge.Client.core.set_config(config, {
			success: function() {
				Deluge.UI.update();
			}
		});
	}*/
}