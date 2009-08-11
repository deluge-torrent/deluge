/*
Script: Deluge.Toolbar.js
    Contains the Deluge toolbar.

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

(function() {
	Ext.deluge.Toolbar = Ext.extend(Ext.Toolbar, {
		constructor: function(config) {
			config = Ext.apply({
				items: [
					{
						id: 'create',
						cls: 'x-btn-text-icon',
						disabled: true,
						text: _('Create'),
						icon: '/icons/create.png',
						handler: this.onTorrentAction
					},{
						id: 'add',
						cls: 'x-btn-text-icon',
						disabled: true,
						text: _('Add'),
						icon: '/icons/add.png',
						handler: this.onTorrentAdd
					},{
						id: 'remove',
						cls: 'x-btn-text-icon',
						disabled: true,
						text: _('Remove'),
						icon: '/icons/remove.png',
						handler: this.onTorrentAction
					},'|',{
						id: 'pause',
						cls: 'x-btn-text-icon',
						disabled: true,
						text: _('Pause'),
						icon: '/icons/pause.png',
						handler: this.onTorrentAction
					},{
						id: 'resume',
						cls: 'x-btn-text-icon',
						disabled: true,
						text: _('Resume'),
						icon: '/icons/start.png',
						handler: this.onTorrentAction
					},'|',{
						id: 'up',
						cls: 'x-btn-text-icon',
						disabled: true,
						text: _('Up'),
						icon: '/icons/up.png',
						handler: this.onTorrentAction
					},{
						id: 'down',
						cls: 'x-btn-text-icon',
						disabled: true,
						text: _('Down'),
						icon: '/icons/down.png',
						handler: this.onTorrentAction
					},'|',{
						id: 'preferences',
						cls: 'x-btn-text-icon',
						text: _('Preferences'),
						icon: '/icons/preferences.png',
						handler: this.onPreferencesClick,
						scope: this
					},{
						id: 'connectionman',
						cls: 'x-btn-text-icon',
						text: _('Connection Manager'),
						iconCls: 'x-deluge-connections',
						handler: this.onConnectionManagerClick,
						scope: this
					},'->',{
						id: 'help',
						cls: 'x-btn-text-icon',
						disabled: true,
						icon: '/icons/help.png',
						text: _('Help'),
						handler: this.onHelpClick,
						scope: this
					},{
						id: 'logout',
						cls: 'x-btn-text-icon',
						icon: '/icons/logout.png',
						disabled: true,
						text: _('Logout'),
						handler: this.onLogout,
						scope: this
					}
				]
			}, config);
			Ext.deluge.Toolbar.superclass.constructor.call(this, config);
		},

		connectedButtons: [
			'add', 'remove', 'pause', 'resume', 'up', 'down'
		],
		
		initComponent: function() {
			Ext.deluge.Toolbar.superclass.initComponent.call(this);
			Deluge.Events.on('connect', this.onConnect, this);
			Deluge.Events.on('login', this.onLogin, this);
		},
		
		onConnect: function() {
			Ext.each(this.connectedButtons, function(buttonId) {
				this.items.get(buttonId).enable();
			}, this);
		},
		
		onDisconnect: function() {
			Ext.each(this.connectedButtons, function(buttonId) {
				this.items.get(buttonId).disable();
			}, this);
		},
		
		onLogin: function() {
			this.items.get('logout').enable();
		},
		
		onLogout: function() {
			this.items.get('logout').disable();
			Deluge.Login.logout();
		},
		
		onConnectionManagerClick: function() {
			Deluge.ConnectionManager.show();
		},
		
		onPreferencesClick: function() {
			Deluge.Preferences.show();
		},
		
		onTorrentAction: function(item) {
			var selection = Deluge.Torrents.getSelections();
			var ids = [];
			Ext.each(selection, function(record) {
				ids.push(record.id);
			});
			
			switch (item.id) {
				case 'remove':
					Deluge.RemoveWindow.show(ids);
					break;
				case 'pause':
				case 'resume':
					Deluge.Client.core[item.id + '_torrent'](ids, {
						success: function() {
							Deluge.UI.update();
						}
					});
					break;
				case 'up':
				case 'down':
					Deluge.Client.core['queue_' + item.id](ids, {
						success: function() {
							Deluge.UI.update();
						}
					});
					break;
			}
		},
		
		onTorrentAdd: function() {
			Deluge.Add.show();
		}
	});
	
	Deluge.Toolbar = new Ext.deluge.Toolbar();
})();