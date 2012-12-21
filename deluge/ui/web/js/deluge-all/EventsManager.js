/*!
 * Deluge.EventsManager.js
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

/**
 * @class Deluge.EventsManager
 * @extends Ext.util.Observable
 * <p>Deluge.EventsManager is instantated as <tt>deluge.events</tt> and can be used by components of the UI to fire global events</p>
 * Class for holding global events that occur within the UI.
 */
Deluge.EventsManager = Ext.extend(Ext.util.Observable, {
	constructor: function() {
		this.toRegister = [];
		this.on('login', this.onLogin, this);
		Deluge.EventsManager.superclass.constructor.call(this);
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
		Deluge.EventsManager.superclass.addListener.call(this, eventName, fn, scope, o);
	},

	getEvents: function() {
		deluge.client.web.get_events({
			success: this.onGetEventsSuccess,
			failure: this.onGetEventsFailure,
			scope: this
		});
	},

	/**
	 * Starts the EventsManagerManager checking for events.
	 */
	start: function() {
		Ext.each(this.toRegister, function(eventName) {
			deluge.client.web.register_event_listener(eventName);
		});
		this.running = true;
		this.errorCount = 0;
		this.getEvents();
	},

	/**
	 * Stops the EventsManagerManager checking for events.
	 */
	stop: function() {
		this.running = false;
	},

	// private
	onLogin: function() {
		this.start();
	},

	onGetEventsSuccess: function(events) {
        if (!this.running) return;
		if (events) {
            Ext.each(events, function(event) {
                var name = event[0], args = event[1];
                args.splice(0, 0, name);
                this.fireEvent.apply(this, args);
            }, this);
        }
		this.getEvents();
	},

	// private
	onGetEventsFailure: function(result, error) {
		// the request timed out or we had a communication failure
		if (!this.running) return;
		if (!error.isTimeout && this.errorCount++ >= 3) {
			this.stop();
			return;
		}
		this.getEvents();
	}
});

/**
 * Appends an event handler to this object (shorthand for {@link #addListener})
 * @method 
 */
Deluge.EventsManager.prototype.on = Deluge.EventsManager.prototype.addListener

/**
 * Fires the specified event with the passed parameters (minus the
 * event name).
 * @method 
 */
Deluge.EventsManager.prototype.fire = Deluge.EventsManager.prototype.fireEvent
deluge.events = new Deluge.EventsManager();
