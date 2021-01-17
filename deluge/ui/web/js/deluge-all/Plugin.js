/**
 * Deluge.Plugin.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * @class Deluge.Plugin
 * @extends Ext.util.Observable
 */
Deluge.Plugin = Ext.extend(Ext.util.Observable, {
    /**
     * The plugins name
     * @property name
     * @type {String}
     */
    name: null,

    constructor: function (config) {
        this.isDelugePlugin = true;
        this.addEvents({
            /**
             * @event enabled
             * @param {Plugin} plugin the plugin instance
             */
            enabled: true,

            /**
             * @event disabled
             * @param {Plugin} plugin the plugin instance
             */
            disabled: true,
        });
        Deluge.Plugin.superclass.constructor.call(this, config);
    },

    /**
     * Disables the plugin, firing the "{@link #disabled}" event and
     * then executing the plugins clean up method onDisabled.
     */
    disable: function () {
        this.fireEvent('disabled', this);
        if (this.onDisable) this.onDisable();
    },

    /**
     * Enables the plugin, firing the "{@link #enabled}" event and
     * then executes the plugins setup method, onEnabled.
     */
    enable: function () {
        deluge.client.reloadMethods();
        this.fireEvent('enable', this);
        if (this.onEnable) this.onEnable();
    },

    registerTorrentStatus: function (key, header, options) {
        options = options || {};
        var cc = options.colCfg || {},
            sc = options.storeCfg || {};
        sc = Ext.apply(sc, { name: key });
        deluge.torrents.meta.fields.push(sc);
        deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);

        cc = Ext.apply(cc, {
            header: header,
            dataIndex: key,
        });
        var cols = deluge.torrents.columns.slice(0);
        cols.push(cc);
        deluge.torrents.colModel.setConfig(cols);
        deluge.torrents.columns = cols;

        Deluge.Keys.Grid.push(key);
        deluge.torrents.getView().refresh(true);
    },

    deregisterTorrentStatus: function (key) {
        var fields = [];
        Ext.each(deluge.torrents.meta.fields, function (field) {
            if (field.name != key) fields.push(field);
        });
        deluge.torrents.meta.fields = fields;
        deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);

        var cols = [];
        Ext.each(deluge.torrents.columns, function (col) {
            if (col.dataIndex != key) cols.push(col);
        });
        deluge.torrents.colModel.setConfig(cols);
        deluge.torrents.columns = cols;

        var keys = [];
        Ext.each(Deluge.Keys.Grid, function (k) {
            if (k == key) keys.push(k);
        });
        Deluge.Keys.Grid = keys;
        deluge.torrents.getView().refresh(true);
    },
});

Ext.ns('Deluge.plugins');
