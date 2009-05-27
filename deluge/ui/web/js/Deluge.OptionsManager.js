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
	
	initComponent: function() {
		Deluge.OptionsManager.superclass.initComponent.call(this);
		this.changed = {};
		this.options = {};
	},

	/**
	 * Add a set of options and values for an id to the options manager
	 * @param {String} id
	 * @param {Object} options The default options for the id.
	 */
	addOptions: function(id, options) {
		this.options[id] = options;
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
	 * @param {Object...} value The new value for the option
	 */
	setOption: function(id, option, value) {
		if (!this.changed[id]) this.changed[id] = {};
		this.changed[id][option] = value;
	},
	
	/**
	 * Set the specified options for the passed in id.
	 * @param {String} id
	 * @param {object} options The option values to change.
	 */
	setOptions: function(id, options) {
		if (!this.changed[id]) this.changed[id] = {};
		this.changed[id] = Ext.extend(this.changed[id], options);
	}
});