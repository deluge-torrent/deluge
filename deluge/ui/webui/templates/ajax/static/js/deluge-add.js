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
        width: 550,
        height: 500,
        title: Deluge.Strings.get('Add Torrents'),
        url: '/template/render/html/window_add_torrent.html'
    },
    
    initialize: function() {
        this.parent();
        this.bound = {
            onLoad: this.onLoad.bindWithEvent(this),
            onSave: this.onSave.bindWithEvent(this),
            onCancel: this.onCancel.bindWithEvent(this),
            onTorrentAdded: this.onTorrentAdded.bindWithEvent(this),
            onTorrentChanged: this.onTorrentChanged.bindWithEvent(this)
        }
        this.addEvent('loaded', this.bound.onLoad);
    },
    
    onLoad: function(e) {
        this.content.id = 'addTorrent';
        this.torrents = this.content.getElement('select');
        this.torrents.addEvent('change', this.bound.onTorrentChanged);
        this.torrentInfo = new Hash();
        
        this.tabs = new Widgets.Tabs(this.content.getElement('div.moouiTabs'));
        this.filesTab = new Deluge.Widgets.AddTorrent.FilesTab();
        this.tabs.addPage(this.filesTab);
        this.tabs.addPage(new Widgets.TabPage('Options', {
            url: '/template/render/html/add_torrent_options.html'
        }));
        
        this.urlWindow = new Deluge.Widgets.AddTorrent.Url();
        this.urlWindow.addEvent('torrentAdded', this.bound.onTorrentAdded);     
        this.urlButton = this.content.getElement('button.url');
        this.urlButton.addEvent('click', function(e) {
            this.urlWindow.show();
        }.bindWithEvent(this));
        
        this.content.getElement('button.save').addEvent('click', this.bound.onSave);
        this.content.getElement('button.cancel').addEvent('click', this.bound.onCancel);
    },
    
    onTorrentAdded: function(torrentInfo) {
        var option = new Element('option');
        option.set('value', torrentInfo['info_hash']);
        var filename = torrentInfo['filename'].split('/');
        filename = filename[filename.length - 1];
        option.set('text', torrentInfo['name'] + ' (' + filename + ')');
        this.torrents.grab(option);
        this.torrentInfo[torrentInfo['info_hash']] = torrentInfo;
    },
    
    onTorrentChanged: function(e) {
        this.filesTab.setTorrent(this.torrentInfo[this.torrents.value]);
    },
    
    onSave: function(e) {
        torrents = new Array();
        $each(this.torrentInfo, function(torrent) {
            torrents.include({
                path: torrent['filename'],
                options: {}
            });
        }, this);
        Deluge.Client.add_torrents(torrents);
        this.onCancel()
    },
    
    onCancel: function(e) {
        this.hide();
        this.torrents.empty();
        this.torrentInfo.empty();
        this.filesTab.table.empty();
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
            onCancelClick: this.onCancelClick.bindWithEvent(this),
            onDownloadSuccess: this.onDownloadSuccess.bindWithEvent(this),
            onGetInfoSuccess: this.onGetInfoSuccess.bindWithEvent(this)
        };
        
        this.form = new Element('form');
        this.urlInput = new Element('input', {
            type: 'text'
        });
        this.okButton = new Element('button');
        this.okButton.set('text', Deluge.Strings.get('Ok'));
        this.cancelButton = new Element('button');
        this.cancelButton.set('text', Deluge.Strings.get('Cancel'));
        this.form.grab(new Element('label').set('text', 'Url').addClass('fluid'));
        this.form.grab(this.urlInput).grab(new Element('br'));
        this.form.grab(this.okButton).grab(this.cancelButton);
        this.content.grab(this.form);
        
        this.okButton.addEvent('click', this.bound.onOkClick);
        this.cancelButton.addEvent('click', this.bound.onCancelClick);
    },
    
    onOkClick: function(e) {
        e.stop();
        var url = this.urlInput.get('value');
        Deluge.Client.download_torrent_from_url(url, {
            onSuccess: this.bound.onDownloadSuccess
        });
        this.hide();
    },
    
    onCancelClick: function(e) {
        e.stop();
        this.urlInput.set('value', '');
        this.hide();
    },
    
    onDownloadSuccess: function(filename) {
        Deluge.Client.get_torrent_info(filename, {
            onSuccess: this.bound.onGetInfoSuccess
        });
    },
    
    onGetInfoSuccess: function(info) {
        this.fireEvent('torrentAdded', info);
    }
});

Deluge.Widgets.AddTorrent.FilesTab = new Class({
    Extends: Widgets.TabPage,
    
    options: {
        url: '/template/render/html/add_torrent_files.html'
    },
    
    initialize: function() {
        this.parent('Files');
        this.addEvent('loaded', this.onLoad.bindWithEvent(this));
    },
    
    onLoad: function(e) {
        this.table = this.element.getElement('table');
    },
    
    setTorrent: function(torrent) {
        this.table.empty();
        $each(torrent['files'], function(file) {
            row = new Element('tr');
            new Element('td').inject(row);
            new Element('td').set('text', file['path']).inject(row);
            new Element('td').set('text', file['size'].toBytes()).inject(row);
            this.table.grab(row);
        }, this);
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
