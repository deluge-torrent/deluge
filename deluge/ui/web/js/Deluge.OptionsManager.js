/*
Script:
	Deluge.OptionsManager.js

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
 * @description A class that can be used to manage options throughout the ui.
 * @namespace Deluge
 * @class Deluge.OptionsManager
 */
Deluge.OptionsManager = Ext.extend(Ext.util.Observable, {
	
	constructor: function(config) {
		this.changed = {};
		this.options = {};
		Deluge.OptionsManager.superclass.constructor.call(this);
		
		this.addEvents({
			'add': true,
			'changed': true,
			'reset': true
		});
	},

	/**
	 * Add a set of default options and values for an id to the options manager
	 * @param {String} id
	 * @param {Object} options The default options for the id.
	 */
	addOptions: function(id, options) {
		this.options[id] = options;
	},
	
	/**
	 * Returns the changed values for a specified id.
	 * @param {String} id
	 * @returns {Object} the changed options
	 */
	getChanged: function(id) {
		return (this.changed[id]) ? this.changed[id] : {};
	},
	
	/**
	 * Get the default value for an option given an id and option name
	 * @param {String} id
	 * @param {String} option
	 * @returns {Object} the value of the option
	 */
	getDefault: function(id, option) {
		return this.options[id][option];
	},
	
	/**
	 * Get the value for an option given an id and option name.
	 * @param {String} id
	 * @param {String} option
	 * @returns {Object} the options value.
	 */
	 getValue: function(id, option) {
	 	return (this.hasChanged(id, option)) ? this.changed[id][option] : this.options[id][option];
	 },
	
	/**
	 * Check to see if the option has been changed.
	 * @param {String} id
	 * @param {String} option
	 * @returns {Boolean} true if the option has been changed, else false.
	 */
	hasChanged: function(id, option) {
		return (this.changed[id] && !Ext.isEmpty(this.changed[id][option]));
	},

	/**
	 * Reset the options back to the default values for the specified id.
	 * @param {String} id
	 */
	resetOptions: function(id) {
		if (!this.changed[id]) return;
		delete this.changed[id];
	},
	
	/**
	 * Set the specified option for the passed in id.
	 * @param {String} id
	 * @param {String} option
	 * @param {Object} value The new value for the option
	 */
	setOption: function(id, option, value) {
		if (!this.changed[id]) this.changed[id] = {};
		
		var oldValue = this.getValue(id, option);
		if (this.options[id][option] == value) {
			if (!Ext.isEmpty(this.changed[id][option])) delete this.changed[id][option];
			this.fireEvent('changed', id, option, value, oldValue);
			return;
		}
		
		if (Ext.type(this.options[id][option]) != Ext.type(value)) {
			switch (Ext.type(this.options[id][option])) {
				case 'string':
					value = String(value);
					break;
				case 'number':
					value = Number(value);
					break;
				case 'boolean':
					value = Boolean(value);
					break;
			}
		}

		this.changed[id][option] = value;
		this.fireEvent('changed', id, option, value, oldValue);
	},
	
	/**
	 * Set the specified options for the passed in id.
	 * @param {String} id
	 * @param {Object} options The option values to change.
	 */
	setOptions: function(id, options) {
		if (!this.changed[id]) this.changed[id] = {};
		for (var key in options) {
			this.setOption(id, key, options[key]);
		}
	},
	
	/**
	 * Update the default value for the specified option and id.
	 * @param {String} id
	 * @param {String} option
	 * @param {Object} value;
	 */
	updateOption: function(id, option, value) {
		this.options[id][option] = value;
	},
	
	/**
	 * Update the defaults for the specified id.
	 * @param {String} id
	 * @param {Object} options The option defaults to change.
	 */
	updateOptions: function(id, options) {
		if (!this.options[id]) {
			this.addOptions(id, options);
		} else {
			for (var key in options) {
				this.updateOption(id, key, options[key]);
			}
		}
	}
});
