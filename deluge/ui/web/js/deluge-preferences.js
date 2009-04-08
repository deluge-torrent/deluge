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
			text: _('Close'),
			handler: this.onCloseButtonClick,
			scope: this
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
			title: ' ',
			layout: 'fit',
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
			this.pages = {};
			this.on('show', this.onShow.bindWithEvent(this));
		},
		
		onCloseButtonClick: function() {
			this.hide();
		},
		
		addPage: function(name, page) {
			var store = this.categoriesGrid.getStore();
			store.loadData([[name]], true);
			this.pages[name] = page;
		},
		
		onPageSelect: function(selModel, rowIndex, r) {
			this.configPanel.removeAll();
			this.currentPage = rowIndex;
			var name = r.get('name');
			this.configPanel.setTitle(name);
			this.pages[name] = this.configPanel.add(this.pages[name]);
			this.doLayout();
		},
		
		onShow: function() {
			if (!this.categoriesGrid.getSelectionModel().hasSelection()) {
				this.categoriesGrid.getSelectionModel().selectFirstRow();
			}
		}
	});
	
	Deluge.Preferences = new PreferencesWindow();
})();
Deluge.Preferences.addPage(_('Downloads'), {
	border: false,
	html: 'downloads'
});
Deluge.Preferences.addPage(_('Network'), {
	border: false,
	html: 'network'
});
Deluge.Preferences.addPage(_('Bandwidth'), {
	border: false,
	html: 'bandwidth'
});
Deluge.Preferences.addPage(_('Interface'), {
	border: false,
	html: 'interface'
});
Deluge.Preferences.addPage(_('Other'), {
	border: false,
	html: 'other'
});
Deluge.Preferences.addPage(_('Daemon'), {
	border: false,
	html: 'daemon'
});
Deluge.Preferences.addPage(_('Queue'), {
	border: false,
	html: 'queue'
});
Deluge.Preferences.addPage(_('Proxy'), {
	border: false,
	html: 'proxy'
});
Deluge.Preferences.addPage(_('Notification'), {
	border: false,
	html: 'notification'
});
Deluge.Preferences.addPage(_('Plugins'), {
	border: false,
	html: 'plugins'
});