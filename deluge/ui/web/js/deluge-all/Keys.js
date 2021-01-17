/**
 * Deluge.Keys.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
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
     * 'is_auto_managed', 'time_added', 'tracker_host', 'download_location', 'last_seen_complete',
     * 'total_done', 'total_uploaded', 'max_download_speed', 'max_upload_speed',
     * 'seeds_peers_ratio', 'total_remaining', 'completed_time', 'time_since_transfer']</pre>
     */
    Grid: [
        'queue',
        'name',
        'total_wanted',
        'state',
        'progress',
        'num_seeds',
        'total_seeds',
        'num_peers',
        'total_peers',
        'download_payload_rate',
        'upload_payload_rate',
        'eta',
        'ratio',
        'distributed_copies',
        'is_auto_managed',
        'time_added',
        'tracker_host',
        'download_location',
        'last_seen_complete',
        'total_done',
        'total_uploaded',
        'max_download_speed',
        'max_upload_speed',
        'seeds_peers_ratio',
        'total_remaining',
        'completed_time',
        'time_since_transfer',
    ],

    /**
     * Keys used in the status tab of the statistics panel.
     * These get updated to include the keys in {@link #Grid}.
     * <pre>['total_done', 'total_payload_download', 'total_uploaded',
     * 'total_payload_upload', 'next_announce', 'tracker_status', 'num_pieces',
     * 'piece_length', 'is_auto_managed', 'active_time', 'seeding_time', 'time_since_transfer',
     * 'seed_rank', 'last_seen_complete', 'completed_time', 'owner', 'public', 'shared']</pre>
     */
    Status: [
        'total_done',
        'total_payload_download',
        'total_uploaded',
        'total_payload_upload',
        'next_announce',
        'tracker_status',
        'num_pieces',
        'piece_length',
        'is_auto_managed',
        'active_time',
        'seeding_time',
        'time_since_transfer',
        'seed_rank',
        'last_seen_complete',
        'completed_time',
        'owner',
        'public',
        'shared',
    ],

    /**
     * Keys used in the files tab of the statistics panel.
     * <pre>['files', 'file_progress', 'file_priorities']</pre>
     */
    Files: ['files', 'file_progress', 'file_priorities'],

    /**
     * Keys used in the peers tab of the statistics panel.
     * <pre>['peers']</pre>
     */
    Peers: ['peers'],

    /**
     * Keys used in the details tab of the statistics panel.
     */
    Details: [
        'name',
        'download_location',
        'total_size',
        'num_files',
        'message',
        'tracker_host',
        'comment',
        'creator',
    ],

    /**
     * Keys used in the options tab of the statistics panel.
     * <pre>['max_download_speed', 'max_upload_speed', 'max_connections', 'max_upload_slots',
     *  'is_auto_managed', 'stop_at_ratio', 'stop_ratio', 'remove_at_ratio', 'private',
     *  'prioritize_first_last']</pre>
     */
    Options: [
        'max_download_speed',
        'max_upload_speed',
        'max_connections',
        'max_upload_slots',
        'is_auto_managed',
        'stop_at_ratio',
        'stop_ratio',
        'remove_at_ratio',
        'private',
        'prioritize_first_last',
        'move_completed',
        'move_completed_path',
        'super_seeding',
    ],
};

// Merge the grid and status keys together as the status keys contain all the
// grid ones.
Ext.each(Deluge.Keys.Grid, function (key) {
    Deluge.Keys.Status.push(key);
});
