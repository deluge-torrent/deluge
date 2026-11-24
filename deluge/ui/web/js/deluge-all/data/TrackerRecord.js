/**
 * Deluge.data.TrackerRecord.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.data');

/**
 * Deluge.data.Tracker record
 *
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 *
 * @class Deluge.data.Tracker
 * @extends Ext.data.Record
 * @constructor
 * @param {Object} data The tracker data
 */
Deluge.data.Tracker = Ext.data.Record.create([
    {
        name: 'tracker',
        type: 'string',
    },
    {
        name: 'status',
        type: 'string',
    },
    {
        name: 'peers',
        type: 'int',
    },
    {
        name: 'message',
        type: 'string',
    },
]);
