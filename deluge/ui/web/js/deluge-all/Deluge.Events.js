/*
Script: Deluge.Events.js
	Class for holding global events that occur within the UI.

Copyright:
	(C) Damien Churchill 2009-2010 <damoxc@gmail.com>
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

(function() {
	/**
	 * @class Deluge.Events
	 * <p>Deluge.Events is a singleton that components of the UI can use to fire global events</p>
	 * @singleton
	 * Class for holding global events that occur within the UI.
	 */
	Deluge.Events = Ext.extend(Ext.util.Observable, {
		constructor: function() {
			this.toRegister = [];
			this.on('login', this.onLogin, this);
			Deluge.Events.superclass.constructor.call(this);
		},
		
		/**
		 * Append an event handler to this object.
		 */
		addListener: function(eventName, fn, scope, o) {
			this.addEvents(eventName);
			if (/[A-Z]/.test(eventName.substring(0, 1))) {
				if (!deluge.client) {
					this.toRegister.push(eventName);
				} else {
					deluge.client.web.register_event_listener(eventName);
				}
			}
			Deluge.Events.superclass.addListener.call(this, eventName, fn, scope, o);
		},
	
		getEvents: function() {
			deluge.client.web.get_events({
				success: this.onGetEventsSuccess,
				failure: this.onGetEventsFailure,
				scope: this
			});
		},
	
		/**
		 * Starts the EventsManager checking for events.
		 */
		start: function() {
			Ext.each(this.toRegister, function(eventName) {
				deluge.client.web.register_event_listener(eventName);
			});
			this.running = true;
			this.getEvents();
		},
	
		/**
		 * Stops the EventsManager checking for events.
		 */
		stop: function() {
			this.running = false;
		},

		// private
		onLogin: function() {
			this.start();
			this.on('PluginEnabledEvent', this.onPluginEnabled, this);
			this.on('PluginDisabledEvent', this.onPluginDisabled, this);
		},

		onGetEventsSuccess: function(events) {
			if (!events) return;
			Ext.each(events, function(event) {
				var name = event[0], args = event[1];
				args.splice(0, 0, name);
				this.fireEvent.apply(this, args);
			}, this);
			if (this.running) this.getEvents();
		},
	
		// private
		onGetEventsFailure: function(events) {
			// the request timed out so we just want to open up another
			// one.
			if (this.running) this.getEvents();
		}
	});

	/**
	 * Appends an event handler to this object (shorthand for {@link #addListener})
	 * @method 
	 */
	Deluge.Events.prototype.on = Deluge.Events.prototype.addListener

	/**
	 * Fires the specified event with the passed parameters (minus the
	 * event name).
	 * @method 
	 */
	Deluge.Events.prototype.fire = Deluge.Events.prototype.fireEvent
	deluge.events = new Deluge.Events();
})();
