/*!
 * Deluge.Keys.js
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
 * @description The torrent status keys that are commonly used around the UI.
 * @class Deluge.Keys
 * @singleton
 */
Deluge.Keys = {

	/**
	 * Keys that are used within the torrent grid.
	 * <pre>['queue', 'name', 'total_wanted', 'state', 'progress', 'num_seeds',
	 * 'total_seeds', 'num_peers', 'total_peers', 'download_payload_rate',
	 * 'upload_payload_rate', 'eta', 'ratio', 'distributed_copies',
	 * 'is_auto_managed', 'time_added', 'tracker_host', 'save_path',
	 * 'total_done', 'total_uploaded', 'max_download_speed', 'max_upload_speed',
	 * 'seeds_peers_ratio']</pre>
	 */
    Grid: [
        'queue', 'name', 'total_wanted', 'state', 'progress', 'num_seeds',
        'total_seeds', 'num_peers', 'total_peers', 'download_payload_rate',
        'upload_payload_rate', 'eta', 'ratio', 'distributed_copies',
        'is_auto_managed', 'time_added', 'tracker_host', 'save_path',
        'total_done', 'total_uploaded', 'max_download_speed', 'max_upload_speed',
        'seeds_peers_ratio'
    ],

    /**
     * Keys used in the status tab of the statistics panel.
     * These get updated to include the keys in {@link #Grid}.
	 * <pre>['total_done', 'total_payload_download', 'total_uploaded',
	 * 'total_payload_upload', 'next_announce', 'tracker_status', 'num_pieces',
	 * 'piece_length', 'is_auto_managed', 'active_time', 'seeding_time',
	 * 'seed_rank']</pre>
	 */
    Status: [
        'total_done', 'total_payload_download', 'total_uploaded',
        'total_payload_upload', 'next_announce', 'tracker_status', 'num_pieces',
        'piece_length', 'is_auto_managed', 'active_time', 'seeding_time',
        'seed_rank'
    ],

    /**
     * Keys used in the files tab of the statistics panel.
     * <pre>['files', 'file_progress', 'file_priorities']</pre>
	 */
    Files: [
        'files', 'file_progress', 'file_priorities'
    ],

    /**
     * Keys used in the peers tab of the statistics panel.
     * <pre>['peers']</pre>
	 */
    Peers: [
        'peers'
    ],

    /**
     * Keys used in the details tab of the statistics panel.
	 */
    Details: [
        'name', 'save_path', 'total_size', 'num_files', 'message',
        'tracker', 'comment'
    ],

    /**
	 * Keys used in the options tab of the statistics panel.
	 * <pre>['max_download_speed', 'max_upload_speed', 'max_connections', 'max_upload_slots',
	 *  'is_auto_managed', 'stop_at_ratio', 'stop_ratio', 'remove_at_ratio', 'private',
	 *  'prioritize_first_last']</pre>
	 */
    Options: [
        'max_download_speed', 'max_upload_speed', 'max_connections',
        'max_upload_slots','is_auto_managed', 'stop_at_ratio', 'stop_ratio',
        'remove_at_ratio', 'private', 'prioritize_first_last',
        'move_completed', 'move_completed_path'
    ]
};

// Merge the grid and status keys together as the status keys contain all the
// grid ones.
Ext.each(Deluge.Keys.Grid, function(key) {
    Deluge.Keys.Status.push(key);
});
