/*
 * Script: deluge-ui.js
 *  The main UI script.
 *
 * Copyright:
 *   Damien Churchill (c) 2008
 */

Deluge.UI = {
    initialize: function() {
        this.torrents = {};
        this.torrentIds = [];
        Deluge.Client = new JSON.RPC('/json/rpc');
        
        var theme = Cookie.read('theme');
        if (theme) this.setTheme(theme);
        else this.setTheme('classic');
        
        this.bound = {
            updated: this.updated.bindWithEvent(this),
            resized: this.resized.bindWithEvent(this),
            toolbarClick: this.toolbarClick.bindWithEvent(this),
            filePriorities: this.filePriorities.bindWithEvent(this),
            labelsChanged: this.labelsChanged.bindWithEvent(this)
        };
        this.loadUi.delay(250, this);
    },
    
    loadUi: function() {
        this.vbox = new Widgets.VBox('page', {expand: true});
        
        this.toolbar = new Deluge.Widgets.Toolbar();
        this.addWindow = new Deluge.Widgets.AddWindow();
        if (Browser.Engine.name != 'trident') {
            this.prefsWindow = new Deluge.Widgets.PreferencesWindow();
        }
        
        this.statusbar = new Deluge.Widgets.StatusBar();
        this.labels = new Deluge.Widgets.Labels()
        this.details = new Deluge.Widgets.Details()
        
        this.initializeGrid()
        
        this.split_horz = new Widgets.SplitPane('top', this.labels, this.grid, {
            pane1: {min: 150},
            pane2: {min: 100, expand: true}
        });
        var details = $W('details')
        this.splitVert = new Widgets.SplitPane('main', this.split_horz, details, {
            direction: 'vertical',
            pane1: {min: 100, expand: true},
            pane2: {min: 200}
        });
        
        this.vbox.addBox(this.toolbar, {fixed: true});
        this.vbox.addBox(this.splitVert);
        this.vbox.addBox(this.statusbar, {fixed: true});
        this.vbox.calculatePositions();
        this.details.expand()
        
        this.toolbar.addEvent('buttonClick', this.bound.toolbarClick);
        this.details.addEvent('filesAction', this.bound.filePriorities)
        this.labels.addEvent('stateChanged', this.bound.labelsChanged)
        details.addEvent('resize', function(e) {
            this.details.expand()
        }.bindWithEvent(this))
        
        window.addEvent('resize', this.bound.resized);
        Deluge.UI.update();
        this.overlay = $('overlay').dispose();
    },
    
    initializeGrid: function() {
        this.grid = new Deluge.Widgets.TorrentGrid('torrents')
        
        var menu = new Widgets.PopupMenu()
        menu.add(Deluge.Menus.Torrents);
        menu.addEvent('action', function(e) {
            this.torrentAction(e.action, e.value)
        }.bind(this))

        this.grid.addEvent('row_menu', function(e) {
            e.stop()
            var value = this.grid.selectedRow.torrent.is_auto_managed;
            menu.items[3].items[4].set(value)
            menu.torrent_id = e.row_id
            menu.show(e)
        }.bindWithEvent(this))
        
        this.grid.addEvent('selectedchanged', function(e) {
            if ($chk(this.grid.selectedRow)) {
                this.details.update(this.grid.selectedRow.id);
            } else {
                this.details.update(null);
            }
        }.bindWithEvent(this))
    },
    
    setTheme: function(name, fn) {
        if (this.overlay) {
            this.overlay.inject(document.body);
        }
        this.theme = name;
        if (this.themecss) this.themecss.destroy();
        this.themecss = new Asset.css('/template/static/themes/' + name + '/style.css');
        Cookie.write('theme', name);
        if (this.overlay) {
            var refresh = function() {
                this.vbox.refresh();
                this.vbox.calculatePositions();
                this.overlay.dispose();
            }.bind(this);
            var check = function() {
                if (document.styleSheets[2]) {
                    if (document.styleSheets[2].href == this.themecss.href) {
                        refresh();
                        $clear(check);
                    }
                }
            }.periodical(50, this);
        };
    },
    
    run: function() {
        if (!this.running) {
            this.running = this.update.periodical(2000, this);
        }
    },
    
    stop: function() {
        if (this.running) {
            $clear(this.running);
            this.running = false;
        }
    },
    
    update: function() {
        filter = {};
        //if (this.labels.state != 'All') filter['state'] = this.labels.state;
        Deluge.Client.update_ui(Deluge.Keys.Grid, filter, {
            onSuccess: this.bound.updated
        });
    },
    
    updated: function(data) {
        this.torrents = new Hash(data.torrents);
        this.stats = data.stats;
        this.filters = data.filters;
        this.torrents.each(function(torrent, torrent_id) {
            torrent.id = torrent_id;
        })
        this.grid.updateTorrents(this.torrents);
        this.statusbar.update(this.stats);
        
        if ($chk(this.grid.selectedRow)) {
            this.details.update(this.grid.selectedRow.id);
        } else {
            this.details.update(null);
        }
        this.labels.update(this.filters);
    },
    
    filePriorities: function(event) {
        Deluge.Client.get_torrent_status(event.torrentId, ['file_priorities'], {
            onSuccess: function(result) {
                var priorities = result.file_priorities
                priorities.each(function(priority, index) {
                    if (event.files.contains(index)) {
                        priorities[index] = event.action;
                    }
                })
                Deluge.Client.set_torrent_file_priorities(event.torrentId, priorities, {
                    onSuccess: function(response) {
                        this.details.update(event.torrentId)
                    }.bindWithEvent(this)    
                })
            }.bindWithEvent(this)
        })
    },
    
    resized: function(event) {
        this.vbox.calculatePositions();
    },
    
    toolbarClick: function(event) {
        this.torrentAction(event.action);
    },
    
    labelsChanged: function(event) {
        this.update()
    },
    
    torrentAction: function(action, value) {
        var torrentIds = this.grid.getSelectedTorrents();
        var client = Deluge.Client;
        switch (action) {
            case 'resume':
                client.resume_torrent(torrentIds);
                break;
            case 'pause':
                client.pause_torrent(torrentIds);
                break;
            case 'top':
                client.queue_top(torrentIds);
                break;
            case 'up':
                client.queue_up(torrentIds);
                break;
            case 'down':
                client.queue_down(torrentIds);
                break;
            case 'bottom':
                client.queue_bottom(torrentIds);
                break;
            case 'force_recheck':
                client.force_recheck(torrentIds);
                break;
            case 'update_tracker':
                client.force_reannounce(torrentIds);
                break;
            case 'max_download_speed':
                value = value.toInt();
                torrentIds.each(function(torrentId) {
                    client.set_torrent_max_download_speed(torrentId, value);
                });
                break;
            case 'max_upload_speed':
                value = value.toInt();
                torrentIds.each(function(torrentId) {
                    client.set_torrent_max_upload_speed(torrentId, value);
                });
                break;
            case 'max_connections':
                value = value.toInt();
                torrentIds.each(function(torrentId) {
                    client.set_torrent_max_connections(torrentId, value);
                });
                break;
            case 'max_upload_slots':
                value = value.toInt();
                torrentIds.each(function(torrentId) {
                    client.set_torrent_max_upload_slots(torrentId, value);
                });
                break;
            case 'auto_managed':
                torrentIds.each(function(torrentId) {
                    client.set_torrent_auto_managed(torrentId, value);
                });
                break;
            case 'add':
                this.addWindow.show();
                break;
            case 'remove':
                var removeTorrent = false, removeFiles = false;
                if (value == 1) removeTorrent = true;
                else if (value == 2) removeFiles = true;
                else if (value > 3) {
                    removeTorrent = true;
                    removeFiles = true;
                }
                client.remove_torrent(torrentIds, removeTorrent, removeFiles);
                break;
            case 'preferences':
                this.prefsWindow.show();
                break;
            default:
                break;
        }
        this.update();
    }
};

window.addEvent('domready', function(e) {
    Deluge.UI.initialize();
    Deluge.UI.run();
});
