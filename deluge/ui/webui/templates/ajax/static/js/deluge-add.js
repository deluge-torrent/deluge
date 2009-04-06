/*
Script: deluge-add.js
    Contains the add torrent window and the torrent creator window.
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
*/

Deluge.Widgets.AddWindow = new Class({
    Extends: Widgets.Window,
    options: {
        width: 550,
        height: 500,
        title: _('Add Torrents'),
        url: '/template/render/html/window_add_torrent.html'
    },

    initialize: function() {
        this.parent();
        this.bound = {
            onLoad: this.onLoad.bindWithEvent(this),
            onAdd: this.onAdd.bindWithEvent(this),
            onShow: this.onShow.bindWithEvent(this),
            onCancel: this.onCancel.bindWithEvent(this),
            onRemoveClick: this.onRemoveClick.bindWithEvent(this),
            onTorrentAdded: this.onTorrentAdded.bindWithEvent(this),
            onTorrentChanged: this.onTorrentChanged.bindWithEvent(this)
        }
        this.addEvent('loaded', this.bound.onLoad);
        this.addEvent('show', this.bound.onShow);
    },

    onLoad: function(e) {
        this.content.id = 'addTorrent';
        this.torrents = this.content.getElement('select');
        this.torrents.addEvent('change', this.bound.onTorrentChanged);
        this.torrentInfo = new Hash();
        this.tabs = new Widgets.Tabs(this.content.getElement('div.moouiTabs'));
        this.filesTab = new Deluge.Widgets.AddTorrent.FilesTab();
        this.optionsTab = new Deluge.Widgets.AddTorrent.OptionsTab();
        this.tabs.addPage(this.filesTab);
        this.tabs.addPage(this.optionsTab);

        this.fileWindow = new Deluge.Widgets.AddTorrent.File();
        this.fileWindow.addEvent('torrentAdded', this.bound.onTorrentAdded);
        this.fileButton = this.content.getElement('button.file');
        this.fileButton.addEvent('click', function(e) {
            this.fileWindow.show();
        }.bindWithEvent(this));

        this.urlWindow = new Deluge.Widgets.AddTorrent.Url();
        this.urlWindow.addEvent('torrentAdded', this.bound.onTorrentAdded);
        this.urlButton = this.content.getElement('button.url');
        this.urlButton.addEvent('click', function(e) {
            this.urlWindow.show();
        }.bindWithEvent(this));

        this.removeButton = this.content.getElement('button.remove');
        this.removeButton.addEvent('click', this.bound.onRemoveClick);

        this.content.getElement('button.add').addEvent('click', this.bound.onAdd);
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

    onAdd: function(e) {
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

    onShow: function(e) {
        this.optionsTab.getDefaults();
    },

    onCancel: function(e) {
        this.hide();
        this.torrents.empty();
        this.torrentInfo.empty();
        this.filesTab.table.empty();
    },

    onRemoveClick: function(e) {
        delete this.torrentInfo[this.torrents.value];
        this.torrents.options[this.torrents.selectedIndex].dispose();
        this.filesTab.setTorrent(null);
    }
});

Deluge.Widgets.AddTorrent = {}

Deluge.Widgets.AddTorrent.File = new Class({
    Extends: Widgets.Window,

    options: {
        width: 400,
        height: 100,
        title: _('From File')
    },

    initialize: function() {
        this.parent();
        this.bound = {
            onLoad: this.onLoad.bindWithEvent(this),
            onCancel: this.onCancel.bindWithEvent(this),
            onSubmit: this.onSubmit.bindWithEvent(this),
            onComplete: this.onComplete.bindWithEvent(this),
            onBeforeShow: this.onBeforeShow.bindWithEvent(this),
            onGetInfoSuccess: this.onGetInfoSuccess.bindWithEvent(this)
        };
        this.addEvent('beforeShow', this.bound.onBeforeShow);
    },

    onBeforeShow: function(e) {
        if (this.iframe) this.iframe.destroy();
        this.iframe = new Element('iframe', {
            src: '/template/render/html/window_add_torrent_file.html',
            height: 65,
            width: 390,
            style: {
                background: 'White',
                overflow: 'hidden'
            }
        });
        this.content.grab(this.iframe);
        this.iframe.addEvent('load', this.bound.onLoad);
    },

    onLoad: function(e) {
        var body = $(this.iframe.contentDocument.body);
        var form = body.getElement('form');
        var cancelButton = form.getElement('button.cancel');
        cancelButton.addEvent('click', this.bound.onCancel);

        var fileInputs = form.getElement('div.fileInputs');
        var fileInput = fileInputs.getElement('input');
        fileInput.set('opacity', 0.000001);
        var fakeFile = fileInputs.getElement('div').getElement('input');

        fileInput.addEvent('change', function(e) {
            fakeFile.value = fileInput.value;
        });

        form.addEvent('submit', this.bound.onSubmit);
        this.iframe.removeEvent('load', this.bound.onLoad);
    },

    onCancel: function(e) {
        this.hide();
    },

    onSubmit: function(e) {
        this.iframe.addEvent('load', this.bound.onComplete);
        this.iframe.set('opacity', 0);
    },

    onComplete: function(e) {
        filename = $(this.iframe.contentDocument.body).get('text');
        this.hide();
        Deluge.Client.get_torrent_info(filename, {
            onSuccess: this.bound.onGetInfoSuccess
        });
    },

    onGetInfoSuccess: function(info) {
        if (info) this.fireEvent('torrentAdded', info);
    }
});

Deluge.Widgets.AddTorrent.Url = new Class({
    Extends: Widgets.Window,

    options: {
        width: 300,
        height: 100,
        title: _('From Url')
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
            'type': 'text',
            'id': 'urlInput',
            'name': 'urlInput'
        });
        this.okButton = new Element('button');
        this.okButton.set('text', _('Ok'));
        this.cancelButton = new Element('button');
        this.cancelButton.set('text', _('Cancel'));
        this.form.grab(new Element('label', {
            'for': 'urlInput',
            'text': _('Url'),
        }).addClass('fluid'));
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
        this.addEvent('loaded', this.onLoad.bindWithEvent(this));
        this.parent('Files');
    },

    onLoad: function(e) {
        this.table = this.element.getElement('table');
    },

    setTorrent: function(torrent) {
        this.table.empty();
        if (!torrent) return;
        $each(torrent['files'], function(file) {
            row = new Element('tr');
            new Element('td').addClass('fileSelect').inject(row).grab(new Element('input', {
                'type': 'checkbox',
                'checked': 'checked'
            }));
            var icon = new Element('td').addClass('fileIcon').inject(row);
            var mimetype = Deluge.Mime.getMimeType(file['path']);
            if (mimetype) icon.addClass(mimetype.replace('/', '_'));
            new Element('td').addClass('fileName').set('text', file['path']).inject(row);
            new Element('td').addClass('fileSize').set('text', file['size'].toBytes()).inject(row);
            this.table.grab(row);
        }, this);
    }
});

Deluge.Widgets.AddTorrent.OptionsTab = new Class({
    Extends: Widgets.TabPage,

    options: {
        url: '/template/render/html/add_torrent_options.html'
    },

    initialize: function() {
        this.parent('Options');
        this.addEvent('loaded', this.onLoad.bindWithEvent(this));
    },

    onLoad: function(e) {
        this.form = this.element.getElement('form');

        new Widgets.Spinner(this.form.max_download_speed_per_torrent, {
            step: 10,
            precision: 1,
            limit: {
                high: null,
                low: -1
            }
        });

        new Widgets.Spinner(this.form.max_upload_speed_per_torrent, {
            step: 10,
            precision: 1,
            limit: {
                high: null,
                low: -1
            }
        });

        new Widgets.Spinner(this.form.max_connections_per_torrent, {
            step: 1,
            precision: 0,
            limit: {
                high: null,
                low: -1
            }
        });

        new Widgets.Spinner(this.form.max_upload_slots_per_torrent, {
            step: 1,
            precision: 0,
            limit: {
                high: null,
                low: -1
            }
        });
    },

    getDefaults: function() {
        var keys = [
            'add_paused',
            'compact_allocation',
            'download_location',
            'max_connections_per_torrent',
            'max_download_speed_per_torrent',
            'max_upload_slots_per_torrent',
            'max_upload_speed_per_torrent',
            'prioritize_first_last_pieces'
        ]
        Deluge.Client.get_config_values(keys, {
            onSuccess: this.onGetConfigSuccess.bindWithEvent(this)
        });
    },

    onGetConfigSuccess: function(config) {
        this.default_config = config;
        this.setFormToDefault();
    },

    setFormToDefault: function() {
        this.form.add_paused.checked = config['add_paused'];
        $each(this.form.compact_allocation, function(el) {
            if (el.value == config['compact_allocation'].toString()) {
                el.checked = true;
            } else {
                el.checked = false;
            }
        });
        this.form.prioritize_first_last_pieces.checked = config['prioritize_first_last_pieces'];
        $$W(this.form.max_download_speed_per_torrent).setValue(config['max_download_speed_per_torrent']);
        $$W(this.form.max_upload_speed_per_torrent).setValue(config['max_upload_speed_per_torrent']);
        $$W(this.form.max_connections_per_torrent).setValue(config['max_connections_per_torrent']);
        $$W(this.form.max_upload_slots_per_torrent).setValue(config['max_upload_slots_per_torrent']);
    },

    setTorrent: function(torrent) {

    }
});

Deluge.Widgets.CreateTorrent = new Class({
    Extends: Widgets.Window,

    options: {
        width: 400,
        height: 400,
        title: _('Create Torrent'),
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
