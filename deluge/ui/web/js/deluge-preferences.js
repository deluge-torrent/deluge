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
	PreferencesWindow = Ext.extend(Ext.Window, {
		layout: 'border',
		width: 450,
		height: 450,
		buttonAlign: 'right',
		closeAction: 'hide',
		closable: true,
		iconCls: 'x-deluge-preferences',
		plain: true,
		resizable: false,
		title: _('Preferences'),
		buttons: [{
			text: _('Close')
		},{
			text: _('Apply')
		},{
			text: _('Ok')
		}],
			
		initComponent: function() {
			PreferencesWindow.superclass.initComponent.call(this);
			
			this.categoriesGrid = this.add({
				xtype: 'grid',
				region: 'west',
				title: _('Categories'),
				store: new Ext.data.SimpleStore({
					fields: [{name: 'name', mapping: 0}]
				}),
				columns: [{id: 'name', renderer: fplain, dataIndex: 'name'}],
				/*selModel: new Ext.grid.RowSelectionModel({
					singleSelect: true,
					listeners: {'rowselect': {fn: this.onPageSelect, scope: this}}
				}),*/
				hideHeaders: true,
				autoExpandColumn: 'name',
				margins: '5 0 5 5',
				cmargins: '5 0 5 5',
				width: 120,
				collapsible: true
			});
			
			this.configPanel = this.add({
				region: 'center',
				title: 'Test',
				margins: '5 5 5 5',
				cmargins: '5 5 5 5'
			});
			
			this.currentPage = null;
		},
		
		addPage: function(name, page) {
			var store = this.categoriesGrid.getStore();
			store.loadData([[name]], true);
			
			if (this.currentPage == null) {
				this.configPanel.setTitle(name);
				this.currentPage = 0;
			}
		},
		
		onPageSelect: function(selModel, rowIndex, r) {
			this.configPanel.setTitle(r.get('name'));
		},
		
		onRender: function(ct, position) {
			PreferencesWindow.superclass.onRender.call(this, ct, position);
			//this.categoriesGrid.getSelectionModel().selectFirstRow();
		}
	});
	
	Deluge.Preferences = new PreferencesWindow();
})();
Deluge.Preferences.addPage('Downloads', {});
Deluge.Preferences.addPage('Network', {});
Deluge.Preferences.addPage('Bandwidth', {});
Deluge.Preferences.addPage('Interface', {});
Deluge.Preferences.addPage('Other', {});
Deluge.Preferences.addPage('Daemon', {});
Deluge.Preferences.addPage('Queue', {});
Deluge.Preferences.addPage('Proxy', {});
Deluge.Preferences.addPage('Notification', {});
Deluge.Preferences.addPage('Plugins', {});