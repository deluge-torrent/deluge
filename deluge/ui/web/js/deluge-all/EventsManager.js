/**
 * Deluge.EventsManager.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

/**
 * @class Deluge.EventsManager
 * @extends Ext.util.Observable
 * <p>Deluge.EventsManager is instantated as <tt>deluge.events</tt> and can be used by components of the UI to fire global events</p>
 * Class for holding global events that occur within the UI.
 */
Deluge.EventsManager = Ext.extend(Ext.util.Observable, {
    constructor: function () {
        this.toRegister = [];
        this.on('login', this.onLogin, this);
        Deluge.EventsManager.superclass.constructor.call(this);
    },

    /**
     * Append an event handler to this object.
     */
    addListener: function (eventName, fn, scope, o) {
        this.addEvents(eventName);
        if (/[A-Z]/.test(eventName.substring(0, 1))) {
            if (!deluge.client) {
                this.toRegister.push(eventName);
            } else {
                deluge.client.web.register_event_listener(eventName);
            }
        }
        Deluge.EventsManager.superclass.addListener.call(
            this,
            eventName,
            fn,
            scope,
            o
        );
    },

    getEvents: function () {
        deluge.client.web.get_events({
            success: this.onGetEventsSuccess,
            failure: this.onGetEventsFailure,
            scope: this,
        });
    },

    /**
     * Starts the EventsManagerManager checking for events.
     */
    start: function () {
        Ext.each(this.toRegister, function (eventName) {
            deluge.client.web.register_event_listener(eventName);
        });
        this.running = true;
        this.errorCount = 0;
        this.getEvents();
    },

    /**
     * Stops the EventsManagerManager checking for events.
     */
    stop: function () {
        this.running = false;
    },

    // private
    onLogin: function () {
        this.start();
    },

    onGetEventsSuccess: function (events) {
        if (!this.running) return;
        if (events) {
            Ext.each(
                events,
                function (event) {
                    var name = event[0],
                        args = event[1];
                    args.splice(0, 0, name);
                    this.fireEvent.apply(this, args);
                },
                this
            );
        }
        this.getEvents();
    },

    // private
    onGetEventsFailure: function (result, error) {
        // the request timed out or we had a communication failure
        if (!this.running) return;
        if (!error.isTimeout && this.errorCount++ >= 3) {
            this.stop();
            return;
        }
        this.getEvents();
    },
});

/**
 * Appends an event handler to this object (shorthand for {@link #addListener})
 * @method
 */
Deluge.EventsManager.prototype.on = Deluge.EventsManager.prototype.addListener;

/**
 * Fires the specified event with the passed parameters (minus the
 * event name).
 * @method
 */
Deluge.EventsManager.prototype.fire = Deluge.EventsManager.prototype.fireEvent;
deluge.events = new Deluge.EventsManager();
