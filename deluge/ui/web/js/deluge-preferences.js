/*
Script: deluge-preferences.js
    Contains the preferences window.

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
	PreferencesWindow = function(config) {
		Ext.apply(this, config);
		this.layout = 'border';
		this.width = 450;
		this.height = 450;
		this.buttonAlign = 'right';
		this.closeAction = 'hide';
		this.closable = true;
		this.iconCls = 'x-deluge-preferences';
		this.plain = true;
		this.resizable = false;
		this.title = _('Preferences');
		this.buttons = [{
			text: _('Close')
		},{
			text: _('Apply')
		},{
			text: _('Ok')
		}];
		this.currentPage = false;
		this.items = [{
			xtype: 'grid',
			region: 'west',
			title: _('Categories'),
			store: new Ext.data.SimpleStore({
				fields: [{name: 'name', mapping: 0}]
			}),
			columns: [{id: 'name', renderer: fplain, dataIndex: 'name'}],
			sm: new Ext.grid.RowSelectionModel({
				singleSelect: true,
				listeners: {'rowselect': {fn: this.onPageSelect, scope: this}}
			}),
			hideHeaders: true,
			autoExpandColumn: 'name',
			deferredRender: false,
			autoScroll: true,
			margins: '5 0 5 5',
			cmargins: '5 0 5 5',
			width: 120,
			collapsible: true
		}, {
			region: 'center',
			title: 'Test',
			margins: '5 5 5 5',
			cmargins: '5 5 5 5'
		}];
		PreferencesWindow.superclass.constructor.call(this);
	};
	
	Ext.extend(PreferencesWindow, Ext.Window, {			
		initComponent: function() {
			PreferencesWindow.superclass.initComponent.call(this);
			this.categoriesGrid = this.items.get(0);
			this.configPanel = this.items.get(1);
			this.on('show', this.onShow.bindWithEvent(this));
		},
		
		addPage: function(name, page) {
			var store = this.categoriesGrid.getStore();
			store.loadData([[name]], true);
		},
		
		onPageSelect: function(selModel, rowIndex, r) {
			this.currentPage = rowIndex;
			this.configPanel.setTitle(r.get('name'));
		},
		
		onShow: function() {
			if (!this.categoriesGrid.getSelectionModel().hasSelection()) {
				this.categoriesGrid.getSelectionModel().selectFirstRow();
			}
		}
	});
	
	Deluge.Preferences = new PreferencesWindow();
})();
Deluge.Preferences.addPage('Downloads', {
	
});
Deluge.Preferences.addPage('Network', {});
Deluge.Preferences.addPage('Bandwidth', {});
Deluge.Preferences.addPage('Interface', {});
Deluge.Preferences.addPage('Other', {});
Deluge.Preferences.addPage('Daemon', {});
Deluge.Preferences.addPage('Queue', {});
Deluge.Preferences.addPage('Proxy', {});
Deluge.Preferences.addPage('Notification', {});
Deluge.Preferences.addPage('Plugins', {});