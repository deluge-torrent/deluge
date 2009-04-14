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
		this.width = 475;
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
			height: 400,
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
			page['bodyStyle'] = 'margin: 5px';
			this.pages[name] = this.configPanel.add(page);
			this.pages[name].hide();
		},
		
		onPageSelect: function(selModel, rowIndex, r) {
			if (this.currentPage) {
				this.currentPage.hide();
			}
			var name = r.get('name');
			
			this.pages[name].show();
			this.configPanel.setTitle(name);
			this.currentPage = this.pages[name];
			this.configPanel.doLayout();
		},
		
		onShow: function() {
			if (!this.categoriesGrid.getSelectionModel().hasSelection()) {
				this.categoriesGrid.getSelectionModel().selectFirstRow();
			}
		}
	});
	
	Deluge.Preferences = new PreferencesWindow();
	Deluge.Preferences.addPage(_('Downloads'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: [{
			xtype: 'fieldset',
			border: false,
			title: _('Folders'),
			labelWidth: 140,
			defaultType: 'textfield',
			autoHeight: true,
			items: [{
				name: 'download_location',
				fieldLabel: _('Download to'),
				width: 125
			}, {
				name: 'move_completed',
				fieldLabel: _('Move completed to'),
				width: 125
			}, {
				name: 'copy_torrent_files',
				fieldLabel: _('Copy of .torrent files to'),
				width: 125
			}]
		}, {
			xtype: 'fieldset',
			border: false,
			title: _('Allocation'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'radio',
			items: [{
				name: 'compact_allocation',
				labelSeparator: '',
				boxLabel: _('Compact')
			}, {
				name: 'compact_allocation',
				labelSeparator: '',
				boxLabel: _('Full')
			}]
		}, {
			xtype: 'fieldset',
			border: false,
			title: _('Options'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox',
			items: [{
				name: 'prioritize_first_last',
				labelSeparator: '',
				boxLabel: _('Prioritize first and last pieces of torrent')
			}, {
				name: 'add_paused',
				labelSeparator: '',
				boxLabel: _('Add torrents in Paused state')
			}]
		}]
	});
	/*Deluge.Preferences.addPage(_('Network'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: []
	});
	Deluge.Preferences.addPage(_('Bandwidth'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: []
	});*/
	Deluge.Preferences.addPage(_('Interface'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: [{
			xtype: 'fieldset',
			border: false,
			title: _('Window'),
			autoHeight: true,
			labelWidth: 1,
			items: [{
				xtype: 'checkbox',
				fieldLabel: '',
				labelSeparator: '',
				boxLabel: _('Show session speed in titlebar'),
				id: 'show_session_speed'
			}]
		}, {
			xtype: 'fieldset',
			border: false,
			title: _('Sidebar'),
			autoHeight: true,
			labelWidth: 1,
			items: [{
				xtype: 'checkbox',
				fieldLabel: '',
				labelSeparator: '',
				boxLabel: _('Hide filters with 0 torrents'),
				id: 'hide_sidebar_zero'
			}]
		}, {
			xtype: 'fieldset',
			border: false,
			title: _('Password'),
			autoHeight: true,
			defaultType: 'textfield',
			items: [{
				fieldLabel: 'New Password',
				inputType: 'password',
				id: 'new_password'
			}, {
				inputType: 'password',
				fieldLabel: 'Confirm Password',
				id: 'confirm_password'
			}]
		}]
	});
	/*Deluge.Preferences.addPage(_('Other'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: []
	});*/
	Deluge.Preferences.addPage(_('Daemon'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: [{
			xtype: 'fieldset',
			border: false,
			title: _('Port'),
			autoHeight: true,
			defaultType: 'uxspinner',
			items: [{
				fieldLabel: _('Daemon port'),
				id: 'daemon_port'
			}]
		}, {
			xtype: 'fieldset',
			border: false,
			title: _('Connections'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox',
			items: [{
				fieldLabel: '',
				labelSeparator: '',
				boxLabel: _('Allow Remote Connections'),
				id: 'allow_remote'
			}]
		}, {
			xtype: 'fieldset',
			border: false,
			title: _('Other'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox',
			items: [{
				fieldLabel: '',
				labelSeparator: '',
				height: 40,
				boxLabel: _('Periodically check the website for new releases'),
				id: 'new_releases'
			}]
		}]
	});
	/*Deluge.Preferences.addPage(_('Queue'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: []
	});
	Deluge.Preferences.addPage(_('Proxy'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: []
	});
	Deluge.Preferences.addPage(_('Notification'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: []
	});
	Deluge.Preferences.addPage(_('Plugins'), {
		border: false,
		xtype: 'form',
		layout: 'form',
		items: []
	});*/
})();