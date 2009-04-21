/**
 *
 * @script Deluge.Events.js
 *
 * (C) Damien Churchill 2009 <damoxc@gmail.com>
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
 *		The Free Software Foundation, Inc.,
 *		51 Franklin Street, Fifth Floor
 *		Boston, MA  02110-1301, USA.
 **
 * @class Deluge.Events
 * <p>Class for holding global events that occur within the UI.</p>
 * @singleton
 */
Deluge.Events = {
	
	// private
	__events: {},
	
	/**
	 * Fires an event, calling any listening event handlers and passing the
	 * given arguments.
	 * @param {String} name The name of the event to call.
	 * @param eventArg1 (optional)
	 * @param eventArg2 (optional)...
	 */
	fire: function() {
		var args = [];
		Ext.each(arguments, function(arg) {
			args.push(arg);
		});
		
		var eventName = args.shift();
		if (!this.__events[eventName]) return;
		
		var eventArgs = arguments;
		Ext.each(this.__events[eventName], function(cb) {
			try {
				cb.fn.apply(cb.scope || this, eventArgs);
			} catch (e) {
				alert(e);
			}
		});
	},
	
	/**
	 * Attachs an event listener.
	 *
	 */
	on: function(eventName, fn, scope) {
		var e = this.__events[eventName] || new Array();
		e.push({
			'fn': fn,
			'scope': scope
		});
		this.__events[eventName] = e;
	},
	
	/**
	 * Removes an event listener.
	 */
	removeListener: function(eventName, fn) {
		if (!this.__events[eventName]) return;
		this.__events[eventName].remove(fn);
	},
	
	/**
	 * Alias to removeListener
	 *
	 */
	un: this.removeListener
};