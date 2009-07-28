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

Ext.namespace('Deluge');

/**
 * @description A class that can be used to manage options throughout the ui.
 * @namespace Deluge
 * @class Deluge.OptionsManager
 */
Deluge.OptionsManager = Ext.extend(Ext.util.Observable, {
	
	constructor: function(config) {
		config = config || {};
		this.binds = {};
		this.changed = {};
		this.options = (config && config['options']) || {};
		this.focused = null;
		
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
	addOptions: function(options) {
		this.options = Ext.applyIf(this.options, options);
	},
	
	/**
	 * Binds a form field to the specified option.
	 * @param {String} option
	 * @param {Ext.form.Field} field
	 */
	bind: function(option, field) {
		this.binds[option] = field;
		this.binds[field] = option;
		
		field.on('focus', this.onFieldFocus, this);
		field.on('blur', this.onFieldBlur, this);
		field.on('change', this.onFieldChange, this);
	},
	
	/**
	 * Get the value for an option or options.
	 * @param {String} [option] A single option or an array of options to return.
	 * @returns {Object} the options value.
	 */
	get: function() {
		var options = {};
		Ext.each(arguments, function(option) {
			if (!this.has(option)) return;
			options[option] = (this.isDirty(option)) ? this.changed[option] : this.options[option];
		}, this);
		return options;
	},
	
	/**
	 * Get the default value for an option or options.
	 * @param {String|Array} [option] A single option or an array of options to return.
	 * @returns {Object} the value of the option
	 */
	getDefault: function(option) {
		return this.options[option];
	},
	
	/**
	 * Returns the dirty (changed) values.
	 * @returns {Object} the changed options
	 */
	getDirty: function() {
		return this.changed;
	},
	
	/**
	 * @param {String} [option] The option to check
	 * @returns {Boolean} true if the option has been changed from the default.
	 */
	isDirty: function(option) {
		return !Ext.isEmpty(this.changed[option]);
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
	 * Check to see if an option exists in the options manager
	 * @param {String} option
	 * @returns {Boolean} true if the option exists, else false.
	 */
	has: function(option) {
		return (this.options[option]);
	},

	/**
	 * Reset the options back to the default values.
	 * @param {String} id
	 */
	reset: function() {
		this.changed = {};
	},
	
	/**
	 * Sets the value of specified option for the passed in id.
	 * @param {String} option
	 * @param {Object} value The value for the option
	 */
	set: function(option, value) {
		this.options[option] = value;
	},
	
	/**
	 * Update the value for the specified option and id.
	 * @param {String|Object} option or options to update
	 * @param {Object} [value];
	 */
	update: function(option, value) {
		if (typeof value === undefined) {
			for (var key in option) {
				this.update(key, option[key]);
			}
		} else {
			var oldValue = this.get(option);
			if (oldValue == value) return;
			
			var defaultValue = this.getDefault(option);
			if (defaultValue == value) {
				if (this.isDirty(option)) delete this.changed[option];
				this.fireEvent('changed', option, value, oldValue);
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

			this.changed[option] = value;
			this.fireEvent('changed', option, value, oldValue);
		}
	},
	
	/* Event Handlers */
	/**
	 * Lets the option manager know when a field is blurred so if a value
	 * so value changing operations can continue on that field.
	 */
	onFieldBlur: function(field, event) {
		if (this.focused == field) {
			this.focused = null;
		}
	},
	
	/**
	 * Stops a form fields value from being blocked by the change functions
	 * @param {Ext.form.Field} field
	 * @private
	 */
	onFieldChange: function(field, event) {
		var option = this.binds[field];
		this.update(option, field.getValue());
	},
	
	/**
	 * Lets the option manager know when a field is focused so if a value
	 * changing operation is performed it won't change the value of the
	 * field.
	 */
	onFieldFocus: function(field, event) {
		this.focused = field;
	},
	
	onChange: function(option, newValue, oldValue) {
		// If we don't have a bind there's nothing to do.
		if (Ext.isEmpty(this.binds[option])) return;
		
		// The field is currently focused so we don't want to change
		// it.
		if (this.binds[option] == this.focused) return;

		// Set the form field to the new value.
		this.binds[option].setValue(newValue);
	}
});