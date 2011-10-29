/*!
 * Deluge.preferences.PreferencesWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2011 <damoxc@gmail.com>
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
 * @class Deluge.preferences.PreferencesWindow
 * @extends Ext.Window
 */
Ext.define('Deluge.preferences.PreferencesWindow', {
    extend: 'Ext.Window',

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
        this.callParent(arguments);

        this.list = Ext.create('Ext.list.ListView', {
            store: Ext.create('Ext.data.Store', {
                model: 'Deluge.data.Preferences'
            }),
            columns: [{
                renderer: fplain,
                dataIndex: 'name',
                flex: 1
            }],
            singleSelect: true,
            listeners: {
                'selectionchange': {
                    fn: this.onPageSelect, scope: this
                }
            },
            hideHeaders: true,
            deferredRender: false,
            autoScroll: true,
            collapsible: true
        });
        this.add({
            region: 'west',
            title: _('Categories'),
            items: [this.list],
            width: 120,
            margins: '5 0 5 5',
            cmargins: '5 0 5 5'
        });

        this.configPanel = this.add({
            type: 'container',
            autoDestroy: false,
            region: 'center',
            layout: 'card',
            layoutConfig: {
                deferredRender: true
            },
            autoScroll: true,
            width: 300,
            margins: '5 5 5 5',
            cmargins: '5 5 5 5'
        });

        //this.addButton(_('Close'), this.onClose, this);
        //this.addButton(_('Apply'), this.onApply, this);
        //this.addButton(_('Ok'), this.onOk, this);

        this.optionsManager = Ext.create('Deluge.OptionsManager');
        this.on('afterrender', this.onAfterRender, this);

        this.afterMethod('onShow', this.afterShown, this);
        this.initPages();
    },

    initPages: function() {
        deluge.preferences = this;
        this.addPage(Ext.create('Deluge.preferences.Downloads'));
        //this.addPage(Ext.create('Deluge.preferences.Network'));
        this.addPage(Ext.create('Deluge.preferences.Encryption'));
        this.addPage(Ext.create('Deluge.preferences.Bandwidth'));
        this.addPage(Ext.create('Deluge.preferences.Interface'));
        this.addPage(Ext.create('Deluge.preferences.Other'));
        this.addPage(Ext.create('Deluge.preferences.Daemon'));
        this.addPage(Ext.create('Deluge.preferences.Queue'));
        this.addPage(Ext.create('Deluge.preferences.Proxy'));
        this.addPage(Ext.create('Deluge.preferences.Cache'));
        this.addPage(Ext.create('Deluge.preferences.Plugins'));
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
        var store = this.list.getStore();
        var name = page.title;
        store.add({name: name});
        page['bodyStyle'] = 'padding: 5px';
        page.preferences = this;
        this.pages[name] = this.configPanel.add(page);
        this.pages[name].index = -1;
        return this.pages[name];
    },

    /**
     * Removes a preferences page from the window.
     * @param {mixed} name
     */
    removePage: function(page) {
        var name = page.title;
        var store = this.list.getStore();
        store.removeAt(store.find('name', name));
        this.configPanel.remove(page);
        delete this.pages[page.title];
    },

    /**
     * Select which preferences page is displayed.
     * @param {String} page The page name to change to
     */
    selectPage: function(page) {
        if (this.pages[page].index < 0) {
            this.pages[page].index = this.configPanel.items.indexOf(this.pages[page]);
        }
        this.list.select(this.pages[page].index);
    },

    // private
    doSelectPage: function(page) {
        if (this.pages[page].index < 0) {
            this.pages[page].index = this.configPanel.items.indexOf(this.pages[page]);
        }
        this.configPanel.getLayout().setActiveItem(this.pages[page].index);
        this.currentPage = page;
    },

    // private
    onGotConfig: function(config) {
        this.getOptionsManager().set(config);
    },

    // private
    onPageSelect: function(list, selections) {
        var r = list.getRecord(selections[0]);
        this.doSelectPage(r.get('name'));
    },

    // private
    onSetConfig: function() {
        this.getOptionsManager().commit();
    },

    // private
    onAfterRender: function() {
        if (!this.list.getSelectionCount()) {
            this.list.select(0);
        }
        this.configPanel.getLayout().setActiveItem(0);
    },

    // private
    afterShown: function() {
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
