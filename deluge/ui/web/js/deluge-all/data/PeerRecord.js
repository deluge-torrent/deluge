/**
 * Deluge.data.PeerRecord.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.data');

/**
 * Deluge.data.Peer record
 *
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 *
 * @class Deluge.data.Peer
 * @extends Ext.data.Record
 * @constructor
 * @param {Object} data The peer data
 */
Deluge.data.Peer = Ext.data.Record.create([
    {
        name: 'country',
        type: 'string',
    },
    {
        name: 'ip',
        type: 'string',
        sortType: Deluge.data.SortTypes.asIPAddress,
    },
    {
        name: 'client',
        type: 'string',
    },
    {
        name: 'progress',
        type: 'float',
    },
    {
        name: 'down_speed',
        type: 'int',
    },
    {
        name: 'up_speed',
        type: 'int',
    },
    {
        name: 'seed',
        type: 'int',
    },
]);
