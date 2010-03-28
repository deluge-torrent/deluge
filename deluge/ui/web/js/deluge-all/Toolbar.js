/*!
 * Deluge.Toolbar.js
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

/**
 * An extension of the <tt>Ext.Toolbar</tt> class that provides an extensible toolbar for Deluge.
 * @class Deluge.Toolbar
 * @extends Ext.Toolbar
 */
Deluge.Toolbar = Ext.extend(Ext.Toolbar, {
	constructor: function(config) {
		config = Ext.apply({
			items: [
				{
					id: 'create',
					disabled: true,
					text: _('Create'),
					iconCls: 'icon-create',
					handler: this.onTorrentAction
				},{
					id: 'add',
					disabled: true,
					text: _('Add'),
					iconCls: 'icon-add',
					handler: this.onTorrentAdd
				},{
					id: 'remove',
					disabled: true,
					text: _('Remove'),
					iconCls: 'icon-remove',
					handler: this.onTorrentAction
				},'|',{
					id: 'pause',
					disabled: true,
					text: _('Pause'),
					iconCls: 'icon-pause',
					handler: this.onTorrentAction
				},{
					id: 'resume',
					disabled: true,
					text: _('Resume'),
					iconCls: 'icon-resume',
					handler: this.onTorrentAction
				},'|',{
					id: 'up',
					cls: 'x-btn-text-icon',
					disabled: true,
					text: _('Up'),
					iconCls: 'icon-up',
					handler: this.onTorrentAction
				},{
					id: 'down',
					disabled: true,
					text: _('Down'),
					iconCls: 'icon-down',
					handler: this.onTorrentAction
				},'|',{
					id: 'preferences',
					text: _('Preferences'),
					iconCls: 'x-deluge-preferences',
					handler: this.onPreferencesClick,
					scope: this
				},{
					id: 'connectionman',
					text: _('Connection Manager'),
					iconCls: 'x-deluge-connection-manager',
					handler: this.onConnectionManagerClick,
					scope: this
				},'->',{
					id: 'help',
					iconCls: 'icon-help',
					text: _('Help'),
					handler: this.onHelpClick,
					scope: this
				},{
					id: 'logout',
					iconCls: 'icon-logout',
					disabled: true,
					text: _('Logout'),
					handler: this.onLogout,
					scope: this
				}
			]
		}, config);
		Deluge.Toolbar.superclass.constructor.call(this, config);
	},

	connectedButtons: [
		'add', 'remove', 'pause', 'resume', 'up', 'down'
	],
	
	initComponent: function() {
		Deluge.Toolbar.superclass.initComponent.call(this);
		deluge.events.on('connect', this.onConnect, this);
		deluge.events.on('login', this.onLogin, this);
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
		deluge.login.logout();
	},
	
	onConnectionManagerClick: function() {
		deluge.connectionManager.show();
	},
	
	onHelpClick: function() {
		window.open('http://dev.deluge-torrent.org/wiki/UserGuide');
	},
	
	onPreferencesClick: function() {
		deluge.preferences.show();
	},
	
	onTorrentAction: function(item) {
		var selection = deluge.torrents.getSelections();
		var ids = [];
		Ext.each(selection, function(record) {
			ids.push(record.id);
		});
		
		switch (item.id) {
			case 'remove':
				deluge.removeWindow.show(ids);
				break;
			case 'pause':
			case 'resume':
				deluge.client.core[item.id + '_torrent'](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'up':
			case 'down':
				deluge.client.core['queue_' + item.id](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
		}
	},
	
	onTorrentAdd: function() {
		deluge.add.show();
	}
});

deluge.toolbar = new Deluge.Toolbar();
