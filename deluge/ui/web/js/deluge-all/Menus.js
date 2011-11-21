/*!
 * Deluge.Menus.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */

deluge.menus = {
	onTorrentAction: function(item, e) {
		var ids = deluge.torrents.getSelectedIds();
		var action = item.initialConfig.torrentAction;
		
		switch (action) {
			case 'pause':
			case 'resume':
				deluge.client.core[action + '_torrent'](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'top':
			case 'up':
			case 'down':
			case 'bottom':
				deluge.client.core['queue_' + action](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'edit_trackers':
				deluge.editTrackers.show();
				break;
			case 'update':
				deluge.client.core.force_reannounce(ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'remove':
				deluge.removeWindow.show(ids);
				break;
			case 'recheck':
				deluge.client.core.force_recheck(ids, {
					success: function() {	
						deluge.ui.update();
					}
				});
				break;
			case 'move':
				deluge.moveStorage.show(ids);
				break;
		}
	}
}

deluge.menus.torrent = new Ext.menu.Menu({
	id: 'torrentMenu',
	items: [{
		torrentAction: 'pause',
		text: _('Pause'),
		iconCls: 'icon-pause',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, {
		torrentAction: 'resume',
		text: _('Resume'),
		iconCls: 'icon-resume',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, '-', {
		text: _('Options'),
		iconCls: 'icon-options',
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
				iconCls: 'icon-upload-slots',
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
		iconCls: 'icon-queue',
		menu: new Ext.menu.Menu({
			items: [{
				torrentAction: 'top',
				text: _('Top'),
				iconCls: 'icon-top',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			},{
				torrentAction: 'up',
				text: _('Up'),
				iconCls: 'icon-up',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			},{
				torrentAction: 'down',
				text: _('Down'),
				iconCls: 'icon-down',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			},{
				torrentAction: 'bottom',
				text: _('Bottom'),
				iconCls: 'icon-bottom',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			}]
		})
	}, '-', {
		torrentAction: 'update',
		text: _('Update Tracker'),
		iconCls: 'icon-update-tracker',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, {
		torrentAction: 'edit_trackers',
		text: _('Edit Trackers'),
		iconCls: 'icon-edit-trackers',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, '-', {
		torrentAction: 'remove',
		text: _('Remove Torrent'),
		iconCls: 'icon-remove',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, '-', {
		torrentAction: 'recheck',
		text: _('Force Recheck'),
		iconCls: 'icon-recheck',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, {
		torrentAction: 'move',
		text: _('Move Storage'),
		iconCls: 'icon-move',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}]
});

deluge.menus.filePriorities = new Ext.menu.Menu({
	id: 'filePrioritiesMenu',
	items: [{
		id: 'expandAll',
		text: _('Expand All'),
		iconCls: 'icon-expand-all'
	}, '-', {
		id: 'no_download',
		text: _('Do Not Download'),
		iconCls: 'icon-do-not-download',
		filePriority: FILE_PRIORITY['Do Not Download']
	}, {
		id: 'normal',
		text: _('Normal Priority'),
		iconCls: 'icon-normal',
		filePriority: FILE_PRIORITY['Normal Priority']
	}, {
		id: 'high',
		text: _('High Priority'),
		iconCls: 'icon-high',
		filePriority: FILE_PRIORITY['High Priority']
	}, {
		id: 'highest',
		text: _('Highest Priority'),
		iconCls: 'icon-highest',
		filePriority: FILE_PRIORITY['Highest Priority']
	}]
});
