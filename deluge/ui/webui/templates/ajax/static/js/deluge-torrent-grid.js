/*
Script: deluge-torrent-grid.js
    Contains the Deluge torrent grid.

 *
 * Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
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
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

 *


    Class: Deluge.Widgets.TorrentGrid
        Extending Widgest.DataGrid to manage the torrents in the main
        grid.

    Example:
        grid = new Deluge.Widgets.TorrentGrid('torrentGrid');

    Returns:
        An instance of the class wrapped about the torrent grid.
*/
Deluge.Widgets.TorrentGrid = new Class({
    Extends: Widgets.DataGrid,

    options: {
        columns: [
            {name: 'number',text: '#',type:'number',width: 20},
            {name: 'name',text: 'Name',type:'icon',width: 350},
            {name: 'size',text: 'Size',type:'bytes',width: 80},
            {name: 'progress',text: 'Progress',type:'progress',width: 180},
            {name: 'seeders',text: 'Seeders',type:'text',width: 80},
            {name: 'peers',text: 'Peers',type:'text',width: 80},
            {name: 'down',text: 'Down Speed',type:'speed',width: 100},
            {name: 'up',text: 'Up Speed',type:'speed',width: 100},
            {name: 'eta',text: 'ETA',type:'time',width: 80},
            {name: 'ratio',text: 'Ratio',type:'number',width: 60},
            {name: 'avail',text: 'Avail.',type:'number',width: 60}
        ]
    },

    icons: {
        'Downloading': '/pixmaps/downloading16.png',
        'Seeding': '/pixmaps/seeding16.png',
        'Queued': '/pixmaps/queued16.png',
        'Paused': '/pixmaps/inactive16.png',
        'Error': '/pixmaps/alert16.png',
        'Checking': '/pixmaps/checking16.png'
    },

    /*
        Property: getSelectedTorrentIds
            Helper function to quickly return the torrent ids of the currently
            selected torrents in the grid.

        Example:
            var ids = '';
            grid.getSelectedTorrentIds.each(function(id) {
                ids += id + '\n';
            });
            alert(ids);

        Returns:
            A list containing the currently selected torrent ids.
    */
    getSelectedTorrentIds: function() {
        var torrentIds = [];
        this.getSelected().each(function(row) {
            torrentIds.include(row.id);
        });
        return torrentIds;
    },

    /*
        Property: updateTorrents
            Event handler for when a list item is clicked

        Arguments:
            e - The event args

        Example:
            listItem.addEvent('click', this.clicked.bindWithEvent(this));
    */
    updateTorrents: function(torrents) {
        torrents.each(function(torrent, id) {
            torrent.queue = (torrent.queue > -1) ? torrent.queue + 1 : '';
            torrent.icon = this.icons[torrent.state];
            row = {
                id: id,
                data: {
                    number: torrent.queue,
                    name: {text: torrent.name, icon: torrent.icon},
                    size: torrent.total_size,
                    progress: {percent: torrent.progress, text: torrent.state + ' ' + torrent.progress.toFixed(2) + '%'},
                    seeders: torrent.num_seeds + ' (' + torrent.total_seeds + ')',
                    peers: torrent.num_peers + ' (' + torrent.total_peers + ')',
                    down: torrent.download_payload_rate,
                    up: torrent.upload_payload_rate,
                    eta: torrent.eta,
                    ratio: torrent.ratio.toFixed(3),
                    avail: torrent.distributed_copies.toFixed(3)
                },
                torrent: torrent
            };
            if (this.has(row.id)) {
                this.updateRow(row, true);
            } else {
                this.addRow(row, true);
            };
        }, this);

        // remove any torrents no longer in the grid.
        this.rows.each(function(row) {
            if (!torrents.has(row.id)) {
                if (this.selectedRow && this.selectedRow.id == row.id) {
                    this.deselectRow(row);
                };
                delete this.rows[this.rows.indexOf(row)];
            };
        }, this);
        this.render();
    }
});
