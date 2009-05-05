/*
Script: Deluge.EditTrackers.js
    Contains the edit trackers window.

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

(function() {
	Ext.deluge.AddTracker = Ext.extend(Ext.Window, {
		constructor: function(config) {
			config = Ext.apply({
				title: _('Add Tracker'),
				width: 300,
				height: 150,
				bodyStyle: 'padding: 5px',
				layout: 'fit',
				buttonAlign: 'right',
				closeAction: 'hide',
				closable: true,
				iconCls: 'x-deluge-edit-trackers',
				plain: true,
				resizable: false
			}, config);
			Ext.deluge.AddTracker.superclass.constructor.call(this, config);
		}
	});
	
	Ext.deluge.EditTracker = Ext.extend(Ext.Window, {
		constructor: function(config) {
			config = Ext.apply({
				title: _('Edit Tracker'),
				width: 300,
				height: 150,
				bodyStyle: 'padding: 5px',
				layout: 'fit',
				buttonAlign: 'right',
				closeAction: 'hide',
				closable: true,
				iconCls: 'x-deluge-edit-trackers',
				plain: true,
				resizable: false
			}, config);
			Ext.deluge.EditTracker.superclass.constructor.call(this, config);
		}
	});
	
	Ext.deluge.EditTrackers = Ext.extend(Ext.Window, {
	
		constructor: function(config) {
			config = Ext.apply({
				title: _('Edit Trackers'),
				width: 350,
				height: 220,
				bodyStyle: 'padding: 5px',
				layout: 'fit',
				buttonAlign: 'right',
				closeAction: 'hide',
				closable: true,
				iconCls: 'x-deluge-edit-trackers',
				plain: true,
				resizable: true
			}, config);
			Ext.deluge.EditTrackers.superclass.constructor.call(this, config);
		},
		
		initComponent: function() {
			Ext.deluge.EditTrackers.superclass.initComponent.call(this);
			
			this.addButton(_('Cancel'), this.onCancel, this);
			this.addButton(_('Ok'), this.onOk, this);
			
			this.on('show', this.onShow, this);
			
			this.addWindow = new Ext.deluge.AddTracker();
			this.editWindow = new Ext.deluge.EditTracker();
			
			this.grid = this.add({
				xtype: 'grid',
				store: new Ext.data.SimpleStore({
					fields: [
						{name: 'tier', mapping: 0},
						{name: 'url', mapping: 1}
					]
				}),
				columns: [{
					header: _('Tier'),
					width: 50,
					sortable: true,
					renderer: fplain,
					dataIndex: 'tier'
				}, {
					id:'tracker',
					header: _('Tracker'),
					sortable: true,
					renderer: fplain,
					dataIndex: 'url'
				}],
				stripeRows: true,
				selModel: new Ext.grid.RowSelectionModel({
					singleSelect: true,
					listeners: {
						'rowselect': {fn: this.onSelect, scope: this}
					}
				}),
				autoExpandColumn: 'tracker',
				deferredRender:false,
				autoScroll:true,
				margins: '0 0 0 0',
				bbar: new Ext.Toolbar({
					items: [
						{
							cls: 'x-btn-text-icon',
							text: _('Up'),
							icon: '/icons/up.png',
							handler: this.onUp,
							scope: this
						}, {
							cls: 'x-btn-text-icon',
							text: _('Down'),
							icon: '/icons/down.png',
							handler: this.onDown,
							scope: this
						}, '->', {
							cls: 'x-btn-text-icon',
							text: _('Add'),
							icon: '/icons/add.png',
							handler: this.onAdd,
							scope: this
						}, {
							cls: 'x-btn-text-icon',
							text: _('Edit'),
							icon: '/icons/edit_trackers.png',
							handler: this.onEdit,
							scope: this
						}, {
							cls: 'x-btn-text-icon',
							text: _('Remove'),
							icon: '/icons/remove.png',
							handler: this.onRemove,
							scope: this
						}
					]
				})
			});
		},
		
		onAdd: function() {
			this.addWindow.show();
		},
		
		onCancel: function() {
			this.hide();
		},
		
		onEdit: function() {
			this.editWindow.show();
		},
		
		onHide: function() {
			this.grid.getStore().removeAll();
		},
		
		onOk: function() {
			this.hide();
		},
		
		onRemove: function() {
			// Remove from the grid
			Deluge.Client.core.set_torrent_trackers(this.torrentId, trackers, {
				failure: this.onRemoveFail,
				scope: this
			});
		},
		
		onRemoveFail: function() {
			
		},
		
		onRequestComplete: function(status) {
			var trackers = [];
			Ext.each(status['trackers'], function(tracker) {
				trackers.push([tracker['tier'], tracker['url']]);
			});
			this.grid.getStore().loadData(trackers);
		},
		
		onShow: function() {
			var r = Deluge.Torrents.getSelected();
			this.torrentId = r.id;
			Deluge.Client.core.get_torrent_status(r.id, ['trackers'], {
				success: this.onRequestComplete,
				scope: this
			});
		}
	});
	Deluge.EditTrackers = new Ext.deluge.EditTrackers();
})();