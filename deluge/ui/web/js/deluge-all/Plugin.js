/*!
 * Deluge.Plugin.js
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

	constructor: function(config) {
		this.isDelugePlugin = true;
		this.addEvents({
			/**
			 * @event enabled
			 * @param {Plugin} plugin the plugin instance
			 */
			"enabled": true,

			/**
			 * @event disabled
			 * @param {Plugin} plugin the plugin instance
			 */
			"disabled": true
		});
		Deluge.Plugin.superclass.constructor.call(this, config);
	},
	
	/**
	 * Disables the plugin, firing the "{@link #disabled}" event and
	 * then executing the plugins clean up method onDisabled.
	 */
	disable: function() {
		this.fireEvent("disabled", this);
		if (this.onDisable) this.onDisable();
	},
	
	/**
	 * Enables the plugin, firing the "{@link #enabled}" event and
	 * then executes the plugins setup method, onEnabled.
	 */
	enable: function() {
		this.fireEvent("enable", this);
		if (this.onEnable) this.onEnable();
	},

	registerTorrentStatus: function(key, header, options) {
		options = options || {};
		var cc = options.colCfg || {}, sc = options.storeCfg || {};
		sc = Ext.apply(sc, {name: key});
		deluge.torrents.meta.fields.push(sc);
		deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);

		cc = Ext.apply(cc, {
			header: header,
			dataIndex: key
		});
		var cols = deluge.torrents.columns.slice(0);
		cols.push(cc);
		deluge.torrents.colModel.setConfig(cols);
		deluge.torrents.columns = cols;

		Deluge.Keys.Grid.push(key);
		deluge.torrents.getView().refresh(true);
	},

	deregisterTorrentStatus: function(key) {
		var fields = [];
		Ext.each(deluge.torrents.meta.fields, function(field) {
			if (field.name != key) fields.push(field);
		});
		deluge.torrents.meta.fields = fields;
		deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);

		var cols = [];
		Ext.each(deluge.torrents.columns, function(col) {
			if (col.dataIndex != key) cols.push(col);
		});
		deluge.torrents.colModel.setConfig(cols);
		deluge.torrents.columns = cols;

		var keys = [];
		Ext.each(Deluge.Keys.Grid, function(k) {
			if (k == key) keys.push(k);
		});
		Deluge.Keys.Grid = keys;
		deluge.torrents.getView().refresh(true);
	}
});

Ext.ns('Deluge.plugins');
