/*!
 * Deluge.preferences.PreferencesWindow.js
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
Ext.namespace('Deluge.preferences');

PreferencesRecord = Ext.data.Record.create([{name:'name', type:'string'}]);

/**
 * @class Deluge.preferences.PreferencesWindow
 * @extends Ext.Window
 */
Deluge.preferences.PreferencesWindow = Ext.extend(Ext.Window, {

	/**
	 * @property {String} currentPage The currently selected page.
	 */
	currentPage: null,

	title: _('Preferences'),
	layout: 'border',
	width: 485,
	height: 500,

	buttonAlign: 'right',
	closeAction: 'hide',
	closable: true,
	iconCls: 'x-deluge-preferences',
	plain: true,
	resizable: false,

	pages: {},

	initComponent: function() {
		Deluge.preferences.PreferencesWindow.superclass.initComponent.call(this);

		this.categoriesGrid = this.add({
			xtype: 'grid',
			region: 'west',
			title: _('Categories'),
			store: new Ext.data.Store(),
			columns: [{
				id: 'name',
				renderer: fplain,
				dataIndex: 'name'
			}],
			sm: new Ext.grid.RowSelectionModel({
				singleSelect: true,
				listeners: {
					'rowselect': {
						fn: this.onPageSelect, scope: this
					}
				}
			}),
			hideHeaders: true,
			autoExpandColumn: 'name',
			deferredRender: false,
			autoScroll: true,
			margins: '5 0 5 5',
			cmargins: '5 0 5 5',
			width: 120,
			collapsible: true
		});

		this.configPanel = this.add({
			type: 'container',
			autoDestroy: false,
			region: 'center',
			layout: 'card',
			autoScroll: true,
			width: 300,
			margins: '5 5 5 5',
			cmargins: '5 5 5 5'
		});

		this.addButton(_('Close'), this.onClose, this);
		this.addButton(_('Apply'), this.onApply, this);
		this.addButton(_('Ok'), this.onOk, this);
		
		this.optionsManager = new Deluge.OptionsManager();
		this.on('afterrender', this.onAfterRender, this);
		this.on('show', this.onShow, this);

		this.initPages();
	},

	initPages: function() {
		deluge.preferences = this;
		this.addPage(new Deluge.preferences.Downloads());
		//this.addPage(new Deluge.preferences.Network());
		this.addPage(new Deluge.preferences.Encryption());
		this.addPage(new Deluge.preferences.Bandwidth());
		this.addPage(new Deluge.preferences.Interface());
		this.addPage(new Deluge.preferences.Other());
		this.addPage(new Deluge.preferences.Daemon());
		this.addPage(new Deluge.preferences.Queue());
		this.addPage(new Deluge.preferences.Proxy());
		this.addPage(new Deluge.preferences.Cache());
		this.addPage(new Deluge.preferences.Plugins());
	},
	
	onApply: function(e) {
		var changed = this.optionsManager.getDirty();
		if (!Ext.isObjectEmpty(changed)) {
			deluge.client.core.set_config(changed, {
				success: this.onSetConfig,
				scope: this
			});
		}
		
		for (var page in this.pages) {
			if (this.pages[page].onApply) this.pages[page].onApply();
		}
	},
	
	
	/**
	 * Return the options manager for the preferences window.
	 * @returns {Deluge.OptionsManager} the options manager
	 */
	getOptionsManager: function() {
		return this.optionsManager;
	},
	
	/**
	 * Adds a page to the preferences window.
	 * @param {Mixed} page
	 */
	addPage: function(page) {
		var store = this.categoriesGrid.getStore();
		var name = page.title;
		store.add([new PreferencesRecord({name: name})]);
		page['bodyStyle'] = 'padding: 5px';
		page.preferences = this;
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
	 * Select which preferences page is displayed.
	 * @param {String} page The page name to change to
	 */
	selectPage: function(page) {
		var index = this.configPanel.items.indexOf(this.pages[page]);
		this.configPanel.getLayout().setActiveItem(index);
		this.currentPage = page;
	},
	
	// private
	onGotConfig: function(config) {
		this.getOptionsManager().set(config);
	},
	
	// private
	onPageSelect: function(selModel, rowIndex, r) {
		this.selectPage(r.get('name'));
	},
	
	// private
	onSetConfig: function() {
		this.getOptionsManager().commit();
	},

	// private
	onAfterRender: function() {
		if (!this.categoriesGrid.getSelectionModel().hasSelection()) {
			this.categoriesGrid.getSelectionModel().selectFirstRow();
		}
		this.configPanel.getLayout().setActiveItem(0);
	},
	
	// private
	onShow: function() {
		if (!deluge.client.core) return;
		deluge.client.core.get_config({
			success: this.onGotConfig,
			scope: this
		})
	},

	// private
	onClose: function() {
		this.hide();
	},

	// private
	onOk: function() {
		deluge.client.core.set_config(this.optionsManager.getDirty());
		this.hide();
	}
});
