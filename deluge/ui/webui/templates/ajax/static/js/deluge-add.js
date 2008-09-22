/*
 * Script: deluge-add.js
 *  Contains the add torrent window and (eventually) the torrent creator
 *
 * Copyright:
 *   Damien Churchill (c) 2008
 */

Deluge.Widgets.AddWindow = new Class({
    Extends: Widgets.Window,
    options: {
        width: 400,
        height: 200,
        title: 'Add Torrents',
        url: '/template/render/html/window_add_torrent.html'
    },
    
    initialize: function() {
        this.parent();
        this.addEvent('loaded', this.loaded.bindWithEvent(this));
    },
    
    loaded: function(event) {
        this.formfile = this.content.getChildren()[0];
        this.formurl = this.content.getChildren()[1];
        this.formurl.addEvent('submit', function(e) {
            e.stop();
            Deluge.Client.add_torrent_url(this.formurl.url.value, {});
            this.hide();
        }.bindWithEvent(this))
    }
});
