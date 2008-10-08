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
    
    loaded: function(e) {
        this.urlWindow = new Deluge.Widgets.AddTorrent.Url();
        
        this.urlButton = this.content.getElement('button.url');
        this.urlButton.addEvent('click', function(e) {
            this.urlWindow.show();
        }.bindWithEvent(this));
    }
});

Deluge.Widgets.AddTorrent = {}

Deluge.Widgets.AddTorrent.Url = new Class({
    Extends: Widgets.Window,
    
    options: {
        width: 300,
        height: 100,
        title: Deluge.Strings.get('From Url')
    },
    
    initialize: function() {
        this.parent();
        this.bound = {
            onOkClick: this.onOkClick.bindWithEvent(this),
            onCancelClick: this.onCancelClick.bindWithEvent(this)
        };
        
        this.form = new Element('form');
        this.urlInput = new Element('input', {
            type: 'text'
        });
        this.okButton = new Element('button');
        this.okButton.set('text', Deluge.Strings.get('Ok'));
        this.cancelButton = new Element('button');
        this.cancelButton.set('text', Deluge.Strings.get('Cancel'));
        this.form.grab(new Element('label').set('text', 'Url'));
        this.form.grab(this.urlInput).grab(new Element('br'));
        this.form.grab(this.okButton).grab(this.cancelButton);
        this.content.grab(this.form);
        
        this.okButton.addEvent('click', this.bound.onOkClick);
        this.cancelButton.addEvent('click', this.bound.onCancelClick);
    },
    
    onOkClick: function(e) {
        var url = this.urlInput.get('value');
        Deluge.Client.add_torrent_url(url, {});
        e.stop();
    },
    
    onCancelClick: function(e) {
        this.urlInput.set('value', '');
        this.hide();
        e.stop();
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
        this.bound = {
            onLoad: this.onLoad.bindWithEvent(this),
            onFileClick: this.onFileClick.bindWithEvent(this),
            onFilesPicked: this.onFilesPicked.bind(this)
        }
        this.addEvent('loaded', this.bound.onLoad);
    },
    
    onLoad: function(e) {
        this.tabs = new Deluge.Widgets.CreateTorrent.Tabs(this.content.getElement('.moouiTabs'));
        this.fileButton = this.content.getElement('button.file');
        this.folderButton = this.content.getElement('button.folder');
        this.content.id = 'createTorrent';
        
        this.fileButton.addEvent('click', this.bound.onFileClick);
    },
    
    onFileClick: function(e) {
        var desktop = google.gears.factory.create('beta.desktop');
        desktop.openFiles(this.onFilesPicked.bind(this));
    },
    
    onFilesPicked: function(files) {
        for (var i = 0; i < files.length; i++) {
            alert(files[i].blob);
        };
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
