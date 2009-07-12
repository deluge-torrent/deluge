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
		this.binds = {};
		this.changed = {};
		this.defaults = config['defaults'] || {};
		this.options = {};
		this.currentId = null;
		
		this.addEvents({
			'add': true,
			'changed': true,
			'reset': true
		});
		this.on('changed', this.onChange, this);
		
		Deluge.OptionsManager.superclass.constructor.call(this);
	},

	/**
	 * Add a set of default options and values to the options manager
	 * @param {String} id
	 * @param {Object} options The default options.
	 */
	addOptions: function(id, options) {
		this.options[id] = options;
	},
	
	/**
	 * Binds a form field to the specified option.
	 * @param {String} option
	 * @param {Ext.form.Field} field
	 */
	bind: function(option, field) {
		this.binds[option] = field;
		this.binds[field] = option;
		
		switch (field.getXType()) {
			case 'checkbox':
			case 'radiogroup':
				field.on('check', this.onFieldChange, this);
				break;
			case 'uxspinner':
				field.on('spin', this.onFieldChange, this);
				field.on('keypress', this.onFieldChange, this);
				break;
			default:
				break;
		}
	},
	
	/**
	 * Changes bound fields to use the specified id.
	 * @param {String} id
	 */
	changeId: function(id) {
		this.currentId = id;
		for (var option in this.defaults) {
			if (!this.binds[option]) continue;
			this.binds[option].setValue(this.get(id, option));
		}
	},
	
	/**
	 * Get the value for an option
	 * @param {String} id
	 * @param {String|Array} [option] A single option or an array of options to return.
	 * @returns {Object} the options value.
	 */
	get: function(id, option) {
		if (!option) {
			var values = {};
			for (var key in this.defaults) {
				values[key] = this.get(id, key);
			}
			return values;
		} else {
			return (this.hasChanged(id, option)) ? this.changed[id][option] : this.getDefault(id, option);
		}
	},
	
	/**
	 * Returns the changed values.
	 * @param {String} id
	 * @returns {Object} the changed options
	 */
	getChanged: function(id) {
		return (this.changed[id]) ? this.changed[id] : {};
	},
	
	/**
	 * Get the default value for an option.
	 * @param {String} id
	 * @param {String|Array} [option] A single option or an array of options to return.
	 * @returns {Object} the value of the option
	 */
	getDefault: function(id, option) {
		return (this.hasOption(id, option)) ? this.options[id][option] : this.defaults[option];
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
	 * Check to see if an id has had an option set to something other than the
	 * default value.
	 * @param {String} id
	 * @param {String} option
	 * @returns {Boolean} true if the id has an option, else false.
	 */
	hasOption: function(id, option) {
		return (this.options[id] && !Ext.isEmpty(this.options[id][option]));
	},

	/**
	 * Reset the options back to the default values for the specified id.
	 * @param {String} id
	 */
	reset: function(id) {
		if (!this.changed[id]) return;
		delete this.changed[id];
	},
	
	/**
	 * Sets the value of specified option for the passed in id.
	 * @param {String} id
	 * @param {String} option
	 * @param {Object} value The value for the option
	 */
	set: function(id, option, value) {
		if (typeof value === undefined) {
			for (var key in option) {
				this.set(id, key, option[key]);
			}
		} else {
			if (!this.options[id]) this.options[id] = {};
			this.options[id][option] = value;
		}
	},
	
	/**
	 * Update the value for the specified option and id.
	 * @param {String} id
	 * @param {String|Object} option or options to update
	 * @param {Object} [value];
	 */
	update: function(id, option, value) {
		if (typeof value === undefined) {
			for (var key in option) {
				this.update(id, key, option[key]);
			}
		} else {
			if (!this.changed[id]) this.changed[id] = {};
			
			var oldValue = this.get(id, option);
			if (oldValue == value) return;
			
			var defaultValue = this.getDefault(id, option);
			if (defaultValue == value) {
				if (this.hasChanged(id, option)) delete this.changed[id][option];
				this.fireEvent('changed', id, option, value, oldValue);
				return;
			}
			
			if (Ext.type(defaultValue) != Ext.type(value)) {
				switch (Ext.type(defaultValue)) {
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
		}
	},
	
	/* Event Handlers */
	
	/**
	 * Stops a form fields value from being blocked by the change functions
	 * @param {Ext.form.Field} field
	 * @private
	 */
	onFieldChange: function(field) {
		var option = this.binds[field];
		this.update(this.currentId, option, field.getValue());
	},
	
	onChange: function(id, option, newValue, oldValue) {
		// If we don't have a bind there's nothing to do.
		if (Ext.isEmpty(this.binds[option])) return;
		
		// Set the form field to the new value.
		this.binds[option].setValue(newValue);
	}
});
