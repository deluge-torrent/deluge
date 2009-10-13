/*
Script:
	Deluge.MultiOptionsManager.js

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
 * @class Deluge.MultiOptionsManager
 */
Deluge.MultiOptionsManager = Ext.extend(Deluge.OptionsManager, {

	constructor: function(config) {
		this.currentId = null;
		this.stored = {};
		Deluge.MultiOptionsManager.superclass.constructor.call(this, config);
	},
	
	/**
	 * Changes bound fields to use the specified id.
	 * @param {String} id
	 */
	changeId: function(id) {
		this.currentId = id;
		for (var option in this.options) {
			if (!this.binds[option]) continue;
			Ext.each(this.binds[option], function(bind) {
				bind.setValue(this.get(id, option));
			}, this);
		}
	},

	/**
	 * Changes all the changed values to be the default values
	 * @param {String} id
	 */
	commit: function(id) {
		this.stored[id] = Ext.apply(this.stored[id], this.changed[id]);
		this.reset(id);
	},
	
	/**
	 * Get the value for an option
	 * @param {String} id
	 * @param {String|Array} [option] A single option or an array of options to return.
	 * @returns {Object} the options value.
	 */
	get: function() {
		var id = arguments[0];
		if (arguments.length == 2) {
			var option = arguments[1];
			return (this.isDirty(id, option)) ? this.changed[id][option] : this.getDefault(id, option);
		} else {
			var options = {};
			Ext.each(arguments, function(option) {
				if (option == id) return;
				options[option] = (this.isDirty(id, option)) ? this.changed[id][option] : this.getDefault(id, option);
			}, this);
			return options;
		}
	},

	/**
	 * Get the default value for an option.
	 * @param {String} id
	 * @param {String|Array} [option] A single option or an array of options to return.
	 * @returns {Object} the value of the option
	 */
	getDefault: function(id, option) {
		return (this.has(id, option)) ? this.stored[id][option] : this.options[option];
	},

	/**
	 * Returns the dirty (changed) values.
	 * @param {String} id
	 * @returns {Object} the changed options
	 */
	getDirty: function(id) {
		return (this.changed[id]) ? this.changed[id] : {};
	},

	/**
	 * Check to see if the option has been changed.
	 * @param {String} id
	 * @param {String} option
	 * @returns {Boolean} true if the option has been changed, else false.
	 */
	isDirty: function(id, option) {
		return (this.changed[id] && !Ext.isEmpty(this.changed[id][option]));
	},

	/**
	 * Check to see if an id has had an option set to something other than the
	 * default value.
	 * @param {String} id
	 * @param {String} option
	 * @returns {Boolean} true if the id has an option, else false.
	 */
	has: function(id, option) {
		return (this.stored[id] && !Ext.isEmpty(this.stored[id][option]));
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
			if (!this.changed[id]) this.changed[id] = {};
			this.changed[id][option] = value;
		}
	},

	/**
	 * Update the value for the specified option and id.
	 * @param {String} id
	 * @param {String|Object} option or options to update
	 * @param {Object} [value];
	 */
	update: function(id, option, value) {
		if (value === undefined) {
			for (var key in option) {
				this.update(id, key, option[key]);
			}
		} else {
			if (!this.changed[id]) this.changed[id] = {};

			var defaultValue = this.getDefault(id, option);
			value = this.convertValueType(defaultValue, value);
			
			var oldValue = this.get(id, option);
			if (oldValue == value) return;

			if (defaultValue == value) {
				if (this.isDirty(id, option)) delete this.changed[id][option];
				this.fireEvent('changed', id, option, value, oldValue);
				return;
			} else {
				this.changed[id][option] = value;
				this.fireEvent('changed', id, option, value, oldValue);
			}
		}
	},

	/******************
	 * Event Handlers *
	 ******************/
	/**
	 * Stops a form fields value from being blocked by the change functions
	 * @param {Ext.form.Field} field
	 * @private
	 */
	onFieldChange: function(field, event) {
		this.update(this.currentId, field._doption, field.getValue());
	},

	onChange: function(id, option, newValue, oldValue) {
		// If we don't have a bind there's nothing to do.
		if (Ext.isEmpty(this.binds[option])) return;
		Ext.each(this.binds[option], function(bind) {
			// The field is currently focused so we don't want to 
			// change it.
			if (bind == this.focused) return;
			// Set the form field to the new value.
			bind.setValue(newValue);
		}, this);
	}
});
