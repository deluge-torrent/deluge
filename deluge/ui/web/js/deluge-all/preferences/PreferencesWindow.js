/**
 * Deluge.preferences.PreferencesWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

PreferencesRecord = Ext.data.Record.create([{ name: 'name', type: 'string' }]);

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
    border: false,
    constrainHeader: true,
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    iconCls: 'x-deluge-preferences',
    plain: true,
    resizable: false,

    pages: {},

    initComponent: function () {
        Deluge.preferences.PreferencesWindow.superclass.initComponent.call(
            this
        );

        this.list = new Ext.list.ListView({
            store: new Ext.data.Store(),
            columns: [
                {
                    id: 'name',
                    renderer: fplain,
                    dataIndex: 'name',
                },
            ],
            singleSelect: true,
            listeners: {
                selectionchange: {
                    fn: this.onPageSelect,
                    scope: this,
                },
            },
            hideHeaders: true,
            autoExpandColumn: 'name',
            deferredRender: false,
            autoScroll: true,
            collapsible: true,
        });
        this.add({
            region: 'west',
            items: [this.list],
            width: 120,
            margins: '0 5 0 0',
            cmargins: '0 5 0 0',
        });

        this.configPanel = this.add({
            type: 'container',
            autoDestroy: false,
            region: 'center',
            layout: 'card',
            layoutConfig: {
                deferredRender: true,
            },
            autoScroll: true,
            width: 300,
        });

        this.addButton(_('Close'), this.onClose, this);
        this.addButton(_('Apply'), this.onApply, this);
        this.addButton(_('OK'), this.onOk, this);

        this.optionsManager = new Deluge.OptionsManager();
        this.on('afterrender', this.onAfterRender, this);
        this.on('show', this.onShow, this);

        this.initPages();
    },

    initPages: function () {
        deluge.preferences = this;
        this.addPage(new Deluge.preferences.Downloads());
        this.addPage(new Deluge.preferences.Network());
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

    onApply: function (e) {
        var changed = this.optionsManager.getDirty();
        if (!Ext.isObjectEmpty(changed)) {
            // Workaround for only displaying single listen port but still pass array to core.
            if ('listen_ports' in changed) {
                changed.listen_ports = [
                    changed.listen_ports,
                    changed.listen_ports,
                ];
            }
            deluge.client.core.set_config(changed, {
                success: this.onSetConfig,
                scope: this,
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
    getOptionsManager: function () {
        return this.optionsManager;
    },

    /**
     * Adds a page to the preferences window.
     * @param {Mixed} page
     */
    addPage: function (page) {
        var store = this.list.getStore();
        var name = page.title;
        store.add([new PreferencesRecord({ name: name })]);
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
    removePage: function (page) {
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
    selectPage: function (page) {
        if (this.pages[page].index < 0) {
            this.pages[page].index = this.configPanel.items.indexOf(
                this.pages[page]
            );
        }
        this.list.select(this.pages[page].index);
    },

    // private
    doSelectPage: function (page) {
        if (this.pages[page].index < 0) {
            this.pages[page].index = this.configPanel.items.indexOf(
                this.pages[page]
            );
        }
        this.configPanel.getLayout().setActiveItem(this.pages[page].index);
        this.currentPage = page;
    },

    // private
    onGotConfig: function (config) {
        this.getOptionsManager().set(config);
    },

    // private
    onPageSelect: function (list, selections) {
        var r = list.getRecord(selections[0]);
        this.doSelectPage(r.get('name'));
    },

    // private
    onSetConfig: function () {
        this.getOptionsManager().commit();
    },

    // private
    onAfterRender: function () {
        if (!this.list.getSelectionCount()) {
            this.list.select(0);
        }
        this.configPanel.getLayout().setActiveItem(0);
    },

    // private
    onShow: function () {
        if (!deluge.client.core) return;
        deluge.client.core.get_config({
            success: this.onGotConfig,
            scope: this,
        });
    },

    // private
    onClose: function () {
        this.hide();
    },

    // private
    onOk: function () {
        var changed = this.optionsManager.getDirty();
        if (!Ext.isObjectEmpty(changed)) {
            deluge.client.core.set_config(changed, {
                success: this.onSetConfig,
                scope: this,
            });
        }

        for (var page in this.pages) {
            if (this.pages[page].onOk) this.pages[page].onOk();
        }

        this.hide();
    },
});
