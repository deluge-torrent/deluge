/*
Script: Deluge.Preferences.js
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

Ext.deluge.PreferencesWindow = Ext.extend(Ext.Window, {

	currentPage: null,

	constructor: function(config) {
		config = Ext.apply({
			layout: 'border',
			width: 485,
			height: 500,
			buttonAlign: 'right',
			closeAction: 'hide',
			closable: true,
			iconCls: 'x-deluge-preferences',
			plain: true,
			resizable: false,
			title: _('Preferences'),

			items: [{
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
			}, ]
		}, config);
		Ext.deluge.PreferencesWindow.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.PreferencesWindow.superclass.initComponent.call(this);
		this.categoriesGrid = this.items.get(0);
		this.configPanel = this.add({
			region: 'center',
			header: false,
			layout: 'fit',
			height: 400,
			autoScroll: true,
			margins: '5 5 5 5',
			cmargins: '5 5 5 5'
		});

		this.addButton(_('Close'), this.onClose, this);
		this.addButton(_('Apply'), this.onApply, this);
		this.addButton(_('Ok'), this.onOk, this);
		
		this.pages = {};
		this.optionsManager = new Deluge.OptionsManager();
		this.on('show', this.onShow, this);
	},
	
	onApply: function(e) {
		var changed = this.optionsManager.getDirty();
		if (!Ext.isObjectEmpty(changed)) {
			Deluge.Client.core.set_config(changed, {
				success: this.onSetConfig,
				scope: this
			});
		}
		
		for (var page in this.pages) {
			if (this.pages[page].onApply) this.pages[page].onApply();
		}
	},
	
	onClose: function() {
		this.hide();
	},

	onOk: function() {
		Deluge.Client.core.set_config(this.optionsManager.getDirty());
		this.hide();
	},
	
	/**
	 * Adds a page to the preferences window.
	 * @param {mixed} page
	 */
	addPage: function(page) {
		var store = this.categoriesGrid.getStore();
		var name = page.title;
		store.loadData([[name]], true);
		page['bodyStyle'] = 'margin: 5px';
		this.pages[name] = this.configPanel.add(page);
		return this.pages[name];
	},
	
	/**
	 * Removes a preferences page from the window.
	 * @param {mixed} name
	 */
	removePage: function(page) {
	    var name = page.title;
	    var store = this.categoriesGrid.getStore();
	    store.removeAt(store.find('name', name));
	    this.configPanel.remove(page);
	    delete this.pages[page.title];
	},
	
	/**
	 * Return the options manager for the preferences window.
	 * @returns {Deluge.OptionsManager} the options manager
	 */
	getOptionsManager: function() {
		return this.optionsManager;
	},
	
	onGotConfig: function(config) {
		this.getOptionsManager().set(config);
	},
	
	onPageSelect: function(selModel, rowIndex, r) {
		if (this.currentPage == null) {
			for (var page in this.pages) {
				this.pages[page].hide();
			}
		} else {
			this.currentPage.hide();
		}

		var name = r.get('name');
		
		this.pages[name].show();
		this.currentPage = this.pages[name];
		this.configPanel.doLayout();
	},
	
	onSetConfig: function() {
		this.getOptionsManager().commit();
	},
	
	onShow: function() {
		if (!this.categoriesGrid.getSelectionModel().hasSelection()) {
			this.categoriesGrid.getSelectionModel().selectFirstRow();
		}
		
		Deluge.Client.core.get_config({
			success: this.onGotConfig,
			scope: this
		})
	}
});

Deluge.Preferences = new Ext.deluge.PreferencesWindow();
