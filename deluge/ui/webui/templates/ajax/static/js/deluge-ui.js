/*
Script: deluge-ui.js
    Ties all the other scripts together to build up the Deluge AJAX UI.

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


    Object: Deluge.UI
        The object that manages

    Example:
        Deluge.Grid.initialize();
        Deluge.Grid.run();
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
            onUpdate: this.onUpdate.bindWithEvent(this),
            onResize: this.onResize.bindWithEvent(this),
            onToolbarClick: this.onToolbarClick.bindWithEvent(this),
            onFilesAction: this.onFilesAction.bindWithEvent(this),
            onFilterChanged: this.onFilterChanged.bindWithEvent(this)
        };
        this.loadUI.delay(250, this);
        window.addEvent('load', function(e) {
            if (this.vbox) this.vbox.calculatePositions();
        }.bindWithEvent(this));
    },

    /*
        Property: loadUI
            A method to load the UI after a delayed period of time until
            mooui has been fixed to allow a refresh of the widgets to gather
            the new style information.

        Example:
            Deluge.UI.loadUI();
    */
    loadUI: function() {
        this.vbox = new Widgets.VBox('page', {expand: true});

        this.toolbar = new Deluge.Widgets.Toolbar();
        this.addWindow = new Deluge.Widgets.AddWindow();
        this.createWindow = new Deluge.Widgets.CreateTorrent();
        if (Browser.Engine.name != 'trident') {
            this.prefsWindow = new Deluge.Widgets.PreferencesWindow();
        }

        this.statusbar = new Deluge.Widgets.StatusBar();
        this.labels = new Deluge.Widgets.Labels()
        this.details = new Deluge.Widgets.Details()

        this.initializeGrid()

        this.split_horz = new Widgets.SplitPane('top', this.labels, this.grid, {
            pane1: {min: 180},
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

        this.toolbar.addEvent('buttonClick', this.bound.onToolbarClick);
        this.details.addEvent('filesAction', this.bound.onFilesAction);
        this.labels.addEvent('filterChanged', this.bound.onFilterChanged);
        details.addEvent('resize', function(e) {
            this.details.expand();
        }.bindWithEvent(this));

        this.initialized = true;
        window.addEvent('resize', this.bound.onResize);
        Deluge.UI.update();
        this.overlay = $('overlay').dispose();
    },

    /*
        Property: initializeGrid
            Initializes the Deluge torrent grid.

        Example:
            Deluge.UI.initializeGrid();
    */
    initializeGrid: function() {
        this.grid = new Deluge.Widgets.TorrentGrid('torrents')

        var menu = new Widgets.PopupMenu()
        menu.add(Deluge.Menus.Torrents);
        menu.addEvent('action', function(e) {
            this.torrentAction(e.action, e.value)
        }.bind(this))

        this.grid.addEvent('rowMenu', function(e) {
            e.stop()
            var value = this.grid.selectedRow.torrent.is_auto_managed;
            menu.items[3].items[4].set(value)
            menu.torrent_id = e.row_id
            menu.show(e)
        }.bindWithEvent(this))

        this.grid.addEvent('selectedChanged', function(e) {
            if ($chk(this.grid.selectedRow)) {
                this.details.update(this.grid.selectedRow.id);
            } else {
                this.details.update(null);
            }
        }.bindWithEvent(this))
    },


    /*
        Property: setTheme
            Change the theme of the AJAX UI by unloading the current stylesheet
            and reloading a different one.

        Arguments:
            name: the name of the theme to be switched too.

        Example:
            Deluge.UI.setTheme('white');
    */
    setTheme: function(name) {
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

    /*
        Property: run
            Start the Deluge UI polling the server to get the updated torrent
            information.

        Example:
            Deluge.UI.run();
    */
    run: function() {
        if (!this.running) {
            this.running = this.update.periodical(2000, this);
        }
    },

    /*
        Property: stop
            Stop the Deluge UI polling the server to get the updated torrent
            information.

        Example:
            Deluge.UI.stop();
    */
    stop: function() {
        if (this.running) {
            $clear(this.running);
            this.running = false;
        }
    },

    /*
        Property: update
            The function that is called to perform the update to the UI.

        Example:
            Deluge.UI.update();
    */
    update: function() {
        filter = {};
        if (!this.initialized) return;
        var type = this.labels.filterType, name = this.labels.filterName
        if (type && !(type == 'state' && name == 'All')) {
            filter[this.labels.filterType] = this.labels.filterName;
        }
        Deluge.Client.update_ui(Deluge.Keys.Grid, filter, {
            onSuccess: this.bound.onUpdate
        });
    },

    /*
        Property: onUpdate
            Event handler for when the update data is returned from the server.

        Arguments:
            data - The data returned from the server

        Example:
            Deluge.Client.update_ui(Deluge.Keys.Grid, filter, {
                onSuccess: this.onUpdate.bindWithEvent(this)
            });
    */
    onUpdate: function(data) {
        if (!$defined(data)) return;
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

    /*
        Property: onFilesAction
            Event handler for when a torrents file priorities have been changed.

        Arguments:
            e - The event args

        Example:
            details.addEvent('filesAction', this.onFilesAction.bindWithEvent(this));
    */
    onFilesAction: function(event) {
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

    /*
        Property: onResize
            Event handler for when the page is resized

        Arguments:
            e - The event args

        Example:
            window.addEvent('resize', this.onResize.bindWithEvent(this));
    */
    onResize: function(e) {
        this.vbox.calculatePositions();
    },

    /*
        Property: onToolbarClick
            Event handler for when a list item is clicked

        Arguments:
            e - The event args

        Example:
            toolbar.addEvent('buttonClick', this.onToolbarClick.bindWithEvent(this));
    */
    onToolbarClick: function(e) {
        this.torrentAction(e.action);
    },

    /*
        Property: onFilterChanged
            Event handler for when a filter is changed in the sidebar.

        Arguments:
            e - The event args

        Example:
            labels.addEvent('filterChanged', this.onFilterChanged.bindWithEvent(this));
    */
    onFilterChanged: function(e) {
        this.update();
    },

    /*
        Property: torrentAction
            Peform either a global action or and action on selected torrents
            and then update the UI after performing the action.

        Arguments:
            action - The action to perform
            value - The value accompanying the action, if there is one.

        Example:
            Deluge.UI.torrentAction('resume');
    */
    torrentAction: function(action, value) {
        var torrentIds = this.grid.getSelectedTorrentIds();
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
            case 'create':
                alert('Sorry, this hasn\'t been implemented yet.');
                //this.createWindow.show();
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
                client.remove_torrent(torrentIds, removeFiles);
                break;
            case 'preferences':
                this.prefsWindow.show();
                break;
            case 'connections':
                alert('Sorry, this hasn\'t been implemented yet.');
                break;
            case 'edit_trackers':
                alert('Sorry, this hasn\'t been implemented yet.');
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
