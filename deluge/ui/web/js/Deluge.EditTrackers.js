/*
Script: Deluge.EditTrackers.js
    Contains the edit trackers window.

Copyright:
	(C) Damien Churchill 2009-2010 <damoxc@gmail.com>
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
	Ext.deluge.AddTracker = Ext.extend(Ext.Window, {
		constructor: function(config) {
			config = Ext.apply({
				title: _('Add Tracker'),
				width: 375,
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
		},
		
		initComponent: function() {
			Ext.deluge.AddTracker.superclass.initComponent.call(this);
			
			this.addButton(_('Cancel'), this.onCancel, this);
			this.addButton(_('Add'), this.onAdd, this);
			this.addEvents('add');
			
			this.form = this.add({
				xtype: 'form',
				defaultType: 'textarea',
				baseCls: 'x-plain',
				labelWidth: 55,
				items: [{
					fieldLabel: _('Trackers'),
					name: 'trackers',
					anchor: '100%'
				}]
			})
		},
		
		onCancel: function() {
			this.form.getForm().findField('trackers').setValue('');
			this.hide();
		},
		
		onAdd: function() {
			var trackers = this.form.getForm().findField('trackers').getValue();
			trackers = trackers.split('\n');
			
			var cleaned = [];
			Ext.each(trackers, function(tracker) {
				if (Ext.form.VTypes.url(tracker)) {
					cleaned.push(tracker);
				}
			}, this);
			this.fireEvent('add', cleaned);
			this.hide();
			this.form.getForm().findField('trackers').setValue('');
		}
	});
	
	Ext.deluge.EditTracker = Ext.extend(Ext.Window, {
		constructor: function(config) {
			config = Ext.apply({
				title: _('Edit Tracker'),
				width: 375,
				height: 110,
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
		},
		
		initComponent: function() {
			Ext.deluge.EditTracker.superclass.initComponent.call(this);
			
			this.addButton(_('Cancel'), this.onCancel, this);
			this.addButton(_('Save'), this.onSave, this);
			this.on('hide', this.onHide, this);
			
			this.form = this.add({
				xtype: 'form',
				defaultType: 'textfield',
				baseCls: 'x-plain',
				labelWidth: 55,
				items: [{
					fieldLabel: _('Tracker'),
					name: 'tracker',
					anchor: '100%'
				}]
			});
		},
		
		show: function(record) {
			Ext.deluge.EditTracker.superclass.show.call(this);
			
			this.record = record;
			this.form.getForm().findField('tracker').setValue(record.data['url']);
		},
		
		onCancel: function() {
			this.hide();
		},
		
		onHide: function() {
			this.form.getForm().findField('tracker').setValue('');
		},
		
		onSave: function() {
			var url = this.form.getForm().findField('tracker').getValue();
			this.record.set('url', url);
			this.record.commit();
			this.hide();
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
			this.addEvents('save');
			
			this.on('show', this.onShow, this);
			this.on('save', this.onSave, this);
			
			this.addWindow = new Ext.deluge.AddTracker();
			this.addWindow.on('add', this.onAddTrackers, this);
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
						'selectionchange': {fn: this.onSelect, scope: this}
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
		
		onAddTrackers: function(trackers) {
			var store = this.grid.getStore();
			Ext.each(trackers, function(tracker) {
				var duplicate = false, heightestTier = -1;
				store.each(function(record) {
					if (record.get('tier') > heightestTier) {
						heightestTier = record.get('tier');
					}
					if (tracker == record.get('tracker')) {
						duplicate = true;
						return false;
					}
				}, this);
				if (!duplicate) {
					store.loadData([[heightestTier + 1, tracker]], true);
				}
			}, this);
		},
		
		onCancel: function() {
			this.hide();
		},
		
		onEdit: function() {
			var r = this.grid.getSelectionModel().getSelected();
			this.editWindow.show(r);
		},
		
		onHide: function() {
			this.grid.getStore().removeAll();
		},
		
		onOk: function() {
			var trackers = [];
			this.grid.getStore().each(function(record) {
				trackers.push({
					'tier': record.get('tier'),
					'url': record.get('url')
				})
			}, this);
			
			Deluge.Client.core.set_torrent_trackers(this.torrentId, trackers, {
				failure: this.onSaveFail,
				scope: this
			});

			this.hide();
		},
		
		onRemove: function() {
			// Remove from the grid
			var r = this.grid.getSelectionModel().getSelected();
			this.grid.getStore().remove(r);
		},
		
		onRequestComplete: function(status) {
			var trackers = [];
			Ext.each(status['trackers'], function(tracker) {
				trackers.push([tracker['tier'], tracker['url']]);
			});
			this.grid.getStore().loadData(trackers);
		},
		
		onSaveFail: function() {
			
		},
		
		onSelect: function(sm) {
			if (sm.hasSelection()) {
				this.grid.getBottomToolbar().items.get(4).enable();
			}
		},
		
		onShow: function() {
			this.grid.getBottomToolbar().items.get(4).disable();
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