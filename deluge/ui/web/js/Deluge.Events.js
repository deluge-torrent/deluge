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
 *
 * @class Deluge.Events
 * <p>Class for holding global events that occur within the UI.</p>
 * @singleton
 */

(function() {
    Events = Ext.extend(Ext.util.Observable, {
        constructor: function() {
            Events.superclass.constructor.call(this);
        },
        
        addListener: function(eventName, fn, scope, o) {
            this.addEvents(eventName);
            Events.superclass.addListener.call(this, eventName, fn, scope, o);
        }
    });
    Events.prototype.on = Events.prototype.addListener
    Events.prototype.fire = Events.prototype.fireEvent
    Deluge.Events = new Events();
})();