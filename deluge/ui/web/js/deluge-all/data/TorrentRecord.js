/**
 * Deluge.data.TorrentRecord.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.data');

/**
 * Deluge.data.Torrent record
 *
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 *
 * @class Deluge.data.Torrent
 * @extends Ext.data.Record
 * @constructor
 * @param {Object} data The torrents data
 */
Deluge.data.Torrent = Ext.data.Record.create([
    {
        name: 'queue',
        type: 'int',
    },
    {
        name: 'name',
        type: 'string',
        sortType: Deluge.data.SortTypes.asName,
    },
    {
        name: 'total_wanted',
        type: 'int',
    },
    {
        name: 'state',
        type: 'string',
    },
    {
        name: 'progress',
        type: 'int',
    },
    {
        name: 'num_seeds',
        type: 'int',
    },
    {
        name: 'total_seeds',
        type: 'int',
    },
    {
        name: 'num_peers',
        type: 'int',
    },
    {
        name: 'total_peers',
        type: 'int',
    },
    {
        name: 'download_payload_rate',
        type: 'int',
    },
    {
        name: 'upload_payload_rate',
        type: 'int',
    },
    {
        name: 'eta',
        type: 'int',
    },
    {
        name: 'ratio',
        type: 'float',
    },
    {
        name: 'distributed_copies',
        type: 'float',
    },
    {
        name: 'time_added',
        type: 'int',
    },
    {
        name: 'tracker_host',
        type: 'string',
    },
    {
        name: 'save_path',
        type: 'string',
    },
    {
        name: 'total_done',
        type: 'int',
    },
    {
        name: 'total_uploaded',
        type: 'int',
    },
    {
        name: 'total_remaining',
        type: 'int',
    },
    {
        name: 'max_download_speed',
        type: 'int',
    },
    {
        name: 'max_upload_speed',
        type: 'int',
    },
    {
        name: 'seeds_peers_ratio',
        type: 'float',
    },
    {
        name: 'time_since_transfer',
        type: 'int',
    },
]);
