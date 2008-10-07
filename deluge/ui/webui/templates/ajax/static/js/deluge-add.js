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
        title: Deluge.Strings.get('Add Torrents'),
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

Deluge.Widgets.CreateTorrent = new Class({
    Extends: Widgets.Window,
    
    options: {
        width: 400,
        height: 400,
        title: Deluge.Strings.get('Create Torrent'),
        url: '/template/render/html/window_create_torrent.html'
    },
    
    initialize: function() {
        this.parent();
        this.addEvent('loaded', this.loaded.bindWithEvent(this));
    },
    
    loaded: function(event) {
        this.tabs = new Deluge.Widgets.CreateTorrent.Tabs(this.content.getElement('div'));
        this.content.addClass('createTorrent');
    }
});

Deluge.Widgets.CreateTorrent.Tabs = new Class({
    Extends: Widgets.Tabs,
    
    initialize: function(element) {
        this.parent(element);
        this.info = new Deluge.Widgets.CreateTorrent.InfoTab();
        this.trackers = new Deluge.Widgets.CreateTorrent.TrackersTab();
        this.webseeds = new Deluge.Widgets.CreateTorrent.WebseedsTab();
        this.options = new Deluge.Widgets.CreateTorrent.OptionsTab();
        this.addPage(this.info);
        this.addPage(this.trackers);
        this.addPage(this.webseeds);
        this.addPage(this.options);
    }
});

Deluge.Widgets.CreateTorrent.InfoTab = new Class({
    Extends: Widgets.TabPage,
    
    options: {
        url: '/template/render/html/create_torrent_info.html'
    },
    
    initialize: function() {
        this.parent('Info');
    }
});

Deluge.Widgets.CreateTorrent.TrackersTab = new Class({
    Extends: Widgets.TabPage,
    
    options: {
        url: '/template/render/html/create_torrent_trackers.html'
    },
    
    initialize: function() {
        this.parent('Trackers');
    }
});

Deluge.Widgets.CreateTorrent.WebseedsTab = new Class({
    Extends: Widgets.TabPage,
    
    options: {
        url: '/template/render/html/create_torrent_webseeds.html'
    },
    
    initialize: function() {
        this.parent('Webseeds');
    }
});

Deluge.Widgets.CreateTorrent.OptionsTab = new Class({
    Extends: Widgets.TabPage,
    
    options: {
        url: '/template/render/html/create_torrent_options.html'
    },
    
    initialize: function() {
        this.parent('Options');
    }
});
