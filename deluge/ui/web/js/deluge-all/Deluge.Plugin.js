/*
Script: Deluge.Plugin.js
	Contains a base class for plugins to extend.

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
		this.name = config.name;
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
		this.isDelugePlugin = true;
		Deluge.Plugins[this.name] = this;
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
	}
});
