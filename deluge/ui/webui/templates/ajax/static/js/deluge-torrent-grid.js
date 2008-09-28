/*
 * Script: deluge-torrent-grid.js
 *  The class for controlling the main torrent grid.
 *
 * Copyright:
 *   Damien Churchill (c) 2008
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
        'Checking': '/pixmaps/inactive16.png'
    },
    
    getSelectedTorrents: function() {
        var torrentIds = [];
        this.getSelected().each(function(row) {
            torrentIds.include(row.id);
        });
        return torrentIds;
    },
    
    setTorrentFilter: function(state) {
        state = state.replace(' ', '');
        this.filterer = function (r) {
            if (r.torrent.state == state) { return true } else { return false };
        };
        this.render();
    },
    
    updateTorrents: function(torrents) {
        torrents.each(function(torrent, id) {
            torrent.queue = (torrent.queue > -1) ? torrent.queue + 1 : ''
            torrent.icon = this.icons[torrent.state]
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
            }
            if (this.has(row.id)) {
                this.updateRow(row, true);
            } else {
                this.addRow(row, true);
            }
        }, this);
        this.rows.each(function(row) {
            if (!torrents.has(row.id)) {
                delete this.rows[this.rows.indexOf(row)]
            };
        }, this);
        this.render();
    }
});
