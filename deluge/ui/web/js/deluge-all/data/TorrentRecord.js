/*!
 * Deluge.data.TorrentRecord.js
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
Deluge.data.Torrent = Ext.data.Record.create([{
		name: 'queue',
		type: 'int'
	}, {
		name: 'name',
		type: 'string',
		sortType: Deluge.data.SortTypes.asName
	}, {
		name: 'total_wanted',
		type: 'int'
	}, {
		name: 'state',
		type: 'string'
	}, {
		name: 'progress',
		type: 'int'
	}, {
		name: 'num_seeds',
		type: 'int'
	}, {
		name: 'total_seeds',
		type: 'int'
	}, {
		name: 'num_peers',
		type: 'int'
	}, {
		name: 'total_peers',
		type: 'int'
	}, {
		name: 'download_payload_rate',
		type: 'int'
	}, {
		name: 'upload_payload_rate',
		type: 'int'
	}, {
		name: 'eta',
		type: 'int'
	}, {
		name: 'ratio',
		type: 'float'
	}, {
		name: 'distributed_copies',
		type: 'float'
	}, {
		name: 'time_added',
		type: 'int'
	}, {
		name: 'tracker_host',
		type: 'string'
	}, {
		name: 'save_path',
		type: 'string'
	}, {
		name: 'total_done',
		type: 'int'
	}, {
		name: 'total_uploaded',
		type: 'int'
	}, {
		name: 'max_download_speed',
		type: 'int'
	}, {
		name: 'max_upload_speed',
		type: 'int'
	}, {
		name: 'seeds_peers_ratio',
		type: 'float'
	}
]);
