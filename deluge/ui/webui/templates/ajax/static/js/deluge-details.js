/*
Script: deluge-details.js
    Contains the tabs for the torrent details.

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

Deluge.Widgets.Details = new Class({
    Extends: Widgets.Tabs,

    initialize: function() {
        this.parent($$('#details .mooui-tabs')[0]);

        this.statistics = new Deluge.Widgets.StatisticsPage();
        this.details = new Deluge.Widgets.DetailsPage();
        this.files = new Deluge.Widgets.FilesPage();
        this.peers = new Deluge.Widgets.PeersPage();
        this.options = new Deluge.Widgets.OptionsPage();

        this.addPage(this.statistics);
        this.addPage(this.details);
        this.addPage(this.files);
        this.addPage(this.peers);
        this.addPage(this.options);
        this.addEvent('pageChanged', function(e) {
            this.update(this.torrentId);
        }.bindWithEvent(this));
        this.addEvent('resize', this.resized.bindWithEvent(this));

        this.files.addEvent('menuAction', function(e) {
            files = [];
            this.files.grid.getSelected().each(function(file) {
                files.push(file.fileIndex);
            });
            e.files = files;
            this.fireEvent('filesAction', e);
        }.bindWithEvent(this));
    },

    keys: {
        0: Deluge.Keys.Statistics,
        1: Deluge.Keys.Details,
        2: Deluge.Keys.Files,
        3: Deluge.Keys.Peers,
        4: Deluge.Keys.Options
    },

    clear: function() {
        this.pages.each(function(page) {
            page.element.getChildren().each(function(el) {
                el.set('opacity', 0.5);
            });
            if (page.clear) page.clear();
        });
    },

    update: function(torrentId) {
        this.torrentId = torrentId;
        if (!this.torrentId) {
            this.clear();
            return;
        };
        var keys = this.keys[this.currentPage], page = this.pages[this.currentPage];
        Deluge.Client.get_torrent_status(torrentId, keys, {
            onSuccess: function(torrent) {
                torrent.id = torrentId;
                if (page.update) page.update(torrent);
                page.element.getChildren().each(function(el) {
                    el.set('opacity', 1);
                });
            }.bindWithEvent(this)
        });
    },

    resized: function(event) {
        this.pages.each(function(page) {
            page.getSizeModifiers();
            page.sets({
                width: event.width - page.element.modifiers.x,
                height: event.height - page.element.modifiers.y - 28
            });
        });
    }
});

Deluge.Widgets.StatisticsPage = new Class({
    Extends: Widgets.TabPage,

    options: {
        url: '/template/render/html/tab_statistics.html'
    },

    initialize: function() {
        this.parent(_('Statistics'));
        this.addEvent('loaded', this.onLoad.bindWithEvent(this));
    },

    onLoad: function(e) {
        this.element.id = 'statistics';
        this.bar = new Widgets.ProgressBar();
        this.bar.element.inject(this.element, 'top');
        this.bar.set('width', this.getWidth() - 12);
        this.bar.update('', 0);
        this.addEvent('resize', this.onResize.bindWithEvent(this));
    },

    onResize: function(e) {
        if (!$defined(this.bar)) return;
        this.bar.set('width', this.getWidth() - 12);
    },

    clear: function() {
        if (this.bar) this.bar.update('', 0);
        this.element.getElements('dd').each(function(item) {
            item.set('text', '');
        }, this);
    },

    update: function(torrent) {
        var data = {
            downloaded: torrent.total_done.toBytes()+' ('+torrent.total_payload_download.toBytes()+')',
            uploaded: torrent.total_uploaded.toBytes()+' ('+torrent.total_payload_upload.toBytes()+')',
            share: torrent.ratio.toFixed(3),
            announce: torrent.next_announce.toTime(),
            tracker_status: torrent.tracker_status,
            downspeed: torrent.download_payload_rate.toSpeed(),
            upspeed: torrent.upload_payload_rate.toSpeed(),
            eta: torrent.eta.toTime(),
            pieces: torrent.num_pieces + ' (' + torrent.piece_length.toBytes() + ')',
            seeders: torrent.num_seeds + ' (' + torrent.total_seeds + ')',
            peers: torrent.num_peers + ' (' + torrent.total_peers + ')',
            avail: torrent.distributed_copies.toFixed(3),
            active_time: torrent.active_time.toTime(),
            seeding_time: torrent.seeding_time.toTime(),
            seed_rank: torrent.seed_rank
        }
        var text = torrent.state + ' ' + torrent.progress.toFixed(2) + '%';
        this.bar.update(text, torrent.progress);

        if (torrent.is_auto_managed) {data.auto_managed = 'True'}
        else {data.auto_managed = 'False'};

        this.element.getElements('dd').each(function(item) {
            item.set('text', data[item.getProperty('class')]);
        }, this);
    }
});

Deluge.Widgets.DetailsPage = new Class({
    Extends: Widgets.TabPage,

    options: {
        url: '/template/render/html/tab_details.html'
    },

    initialize: function() {
        this.parent(_('Details'));
    },

    clear: function() {
        this.element.getElements('dd').each(function(item) {
            item.set('text', '');
        }, this);
    },

    update: function(torrent) {
        var data = {
            torrent_name: torrent.name,
            hash: torrent.id,
            path: torrent.save_path,
            size: torrent.total_size.toBytes(),
            files: torrent.num_files,
            status: torrent.tracker_status,
            tracker: torrent.tracker
        };
        this.element.getElements('dd').each(function(item) {
            item.set('text', data[item.getProperty('class')])
        }, this);
    }
});

Deluge.Widgets.FilesGrid = new Class({
    Extends: Widgets.DataGrid,

    options: {
        columns: [
            {name: 'filename',text: 'Filename',type:'text',width: 350},
            {name: 'size',text: 'Size',type:'bytes',width: 80},
            {name: 'progress',text: 'Progress',type:'progress',width: 180},
            {name: 'priority',text: 'Priority',type:'icon',width: 150}
        ]
    },

    priority_texts: {
        0: 'Do Not Download',
        1: 'Normal Priority',
        2: 'High Priority',
        5: 'Highest Priority'
    },

    priority_icons: {
        0: '/static/images/16/process-stop.png',
        1: '/template/static/icons/16/gtk-yes.png',
        2: '/static/images/16/queue-down.png',
        5: '/static/images/16/go-bottom.png'
    },

    initialize: function(element, options) {
        this.parent(element, options);
        var menu = new Widgets.PopupMenu();
        $A([0,1,2,5]).each(function(index) {
            menu.add({
                type:'text',
                action: index,
                text: this.priority_texts[index],
                icon: this.priority_icons[index]
            });
        }, this);

        menu.addEvent('action', function(e) {
            e = {
                action: e.action,
                torrentId: menu.row.torrentId
            };
            this.fireEvent('menuAction', e);
        }.bind(this));

        this.addEvent('rowMenu', function(e) {
            e.stop();
            menu.row = e.row;
            menu.show(e);
        })
    },

    clear: function() {
        this.rows.empty();
        this.body.empty();
        this.render();
    },

    updateFiles: function(torrent) {
        torrent.files.each(function(file) {
            var p = torrent.file_priorities[file.index];
            var priority = {
                text:this.priority_texts[p],
                icon:this.priority_icons[p]
            };

            var percent = torrent.file_progress[file.index]*100.0;
            row = {
                id: torrent.id + '-' + file.index,
                data: {
                    filename: file.path,
                    size: file.size,
                    progress: {percent: percent, text: percent.toFixed(2) + '%'},
                    priority: priority
                },
                fileIndex: file.index,
                torrentId: torrent.id

            };
            if (this.has(row.id)) {
                this.updateRow(row, true);
            } else {
                this.addRow(row, true);
            };
        }, this);
        this.render();
    }
});

Deluge.Widgets.FilesPage = new Class({
    Extends: Widgets.TabPage,

    options: {
        url: '/template/render/html/tab_files.html'
    },

    initialize: function(el) {
        this.parent(_('Files'));
        this.torrentId = -1;
        this.addEvent('loaded', this.loaded.bindWithEvent(this));
        this.addEvent('resize', this.resized.bindWithEvent(this));
    },

    loaded: function(event) {
        this.grid = new Deluge.Widgets.FilesGrid('files');
        this.grid.addEvent('menuAction', this.menuAction.bindWithEvent(this));

        if (this.beenResized) {
            this.resized(this.beenResized);
            delete this.beenResized;
        };
    },

    clear: function() {
        if (this.grid) this.grid.clear();
    },

    resized: function(e) {
        if (!this.grid) {
            this.beenResized = e;
            return;
        };

        this.element.getPadding();
        this.grid.sets({
            width: e.width - this.element.padding.x,
            height: e.height - this.element.padding.y
        });
    },

    menuAction: function(e) {
        this.fireEvent('menuAction', e);
    },

    update: function(torrent) {
        if (this.torrentId != torrent.id) {
            this.torrentId = torrent.id;
            this.grid.rows.empty();
            this.grid.body.empty();
        }
        this.grid.updateFiles(torrent);
    }
});

Deluge.Widgets.PeersPage = new Class({
    Extends: Widgets.TabPage,

    options: {
        url: '/template/render/html/tab_peers.html'
    },

    initialize: function(el) {
        this.parent(_('Peers'));
        this.addEvent('resize', this.resized.bindWithEvent(this));
        this.addEvent('loaded', this.loaded.bindWithEvent(this));
    },

    loaded: function(event) {
        this.grid = new Widgets.DataGrid($('peers'), {
            columns: [
                {name: 'country',type:'image',width: 20},
                {name: 'address',text: 'Address',type:'text',width: 80},
                {name: 'client',text: 'Client',type:'text',width: 180},
                {name: 'downspeed',text: 'Down Speed',type:'speed',width: 100},
                {name: 'upspeed',text: 'Up Speed',type:'speed',width: 100},
            ]});
        this.torrentId = -1;
        if (this.been_resized) {
            this.resized(this.been_resized);
            delete this.been_resized;
        };
    },

    resized: function(e) {
        if (!this.grid) {
            this.been_resized = e;
            return;
        };

        this.element.getPadding();
        this.grid.sets({
            width: e.width - this.element.padding.x,
            height: e.height - this.element.padding.y
        });
    },

    clear: function() {
        if (!this.grid) return;
        this.grid.rows.empty();
        this.grid.body.empty();
    },

    update: function(torrent) {
        if (this.torrentId != torrent.id) {
            this.torrentId = torrent.id;
            this.grid.rows.empty();
            this.grid.body.empty();
        }
        var peers = [];
        torrent.peers.each(function(peer) {
            if (peer.country.strip() != '') {
                peer.country = '/pixmaps/flags/' + peer.country.toLowerCase() + '.png'
            } else {
                peer.country = '/templates/static/images/spacer.gif'
            };
            row = {
                id: peer.ip,
                data: {
                    country: peer.country,
                    address: peer.ip,
                    client: peer.client,
                    downspeed: peer.down_speed,
                    upspeed: peer.up_speed
                    }
                }
            if (this.grid.has(row.id)) {
                this.grid.updateRow(row, true);
            } else {
                this.grid.addRow(row, true);
            }
            peers.include(peer.ip);
        }, this);

        this.grid.rows.each(function(row) {
            if (!peers.contains(row.id)) {
                row.element.destroy();
                this.grid.rows.erase(row);
            };
        }, this);
        this.grid.render();
    }
});

Deluge.Widgets.OptionsPage = new Class({
    Extends: Widgets.TabPage,

    options: {
        url: '/template/render/html/tab_options.html'
    },

    initialize: function() {
        if (!this.element)
            this.parent(_('Options'));
        this.addEvent('loaded', function(event) {
            this.loaded(event);
        }.bindWithEvent(this));
    },

    loaded: function(event) {
        this.bound = {
            apply: this.apply.bindWithEvent(this),
            reset: this.reset.bindWithEvent(this)
        };
        this.form = this.element.getElement('form');
        this.changed = new Hash();
        this.form.getElements('input').each(function(el) {
            if (el.type == 'button') return;
            el.focused = false;
            el.addEvent('change', function(e) {
                if (!this.changed[this.torrentId])
                    this.changed[this.torrentId] = {};
                if (el.type == 'checkbox')
                    this.changed[this.torrentId][el.name] = el.checked;
                else
                    this.changed[this.torrentId][el.name] = el.value;
            }.bindWithEvent(this));
            el.addEvent('focus', function(e) {
                el.focused = true;
            });
            el.addEvent('blur', function(e) {
                el.focused = false;
            });
        }, this);

        new Widgets.Spinner(this.form.max_download_speed, {
            step: 10,
            precision: 1,
            limit: {
                high: null,
                low: -1
            }
        });
        new Widgets.Spinner(this.form.max_upload_speed, {
            step: 10,
            precision: 1,
            limit: {
                high: null,
                low: -1
            }
        });
        new Widgets.Spinner(this.form.max_connections, {
            step: 1,
            precision: 0,
            limit: {
                high: null,
                low: -1
            }
        });
        new Widgets.Spinner(this.form.max_upload_slots, {
            step: 1,
            precision: 0,
            limit: {
                high: null,
                low: -1
            }
        });
        new Widgets.Spinner(this.form.stop_ratio, {
            step: 1,
            precision: 1,
            limit: {
                high: null,
                low: -1
            }
        });

        this.form.apply_options.addEvent('click', this.bound.apply);
        this.form.reset_options.addEvent('click', this.bound.reset);
    },

    apply: function(event) {
        if (!this.torrentId) return;
        var changed = this.changed[this.torrentId];
        if ($defined(changed['is_auto_managed'])) {
            changed['auto_managed'] = changed['is_auto_managed'];
            delete changed['is_auto_managed'];
        };
        Deluge.Client.set_torrent_options(this.torrentId, changed, {
            onSuccess: function(event) {
                delete this.changed[this.torrentId];
            }.bindWithEvent(this)
        });
    },

    clear: function() {
        if (!this.form) return;
        $$W(this.form.max_download_speed).setValue(0);
        $$W(this.form.max_upload_speed).setValue(0);
        $$W(this.form.max_connections).setValue(0);
        $$W(this.form.max_upload_slots).setValue(0);
        $$W(this.form.stop_ratio).setValue(2);
        this.form.is_auto_managed.checked = false;
        this.form.stop_at_ratio.checked = false;
        this.form.remove_at_ratio.checked = false;
        this.form.private.checked = false;
        this.form.private.disabled = false;
        this.form.prioritize_first_last.checked = false;
    },

    reset: function(event) {
        if (this.torrentId) {
            delete this.changed[this.torrentId];
        }
        Deluge.Client.get_torrent_status(this.torrentId, Deluge.Keys.Options, {
            onSuccess: function(torrent) {
                torrent.id = this.torrentId;
                this.update(torrent);
            }.bindWithEvent(this)
        });
    },

    update: function(torrent) {
        this.torrentId = torrent.id;
        $each(torrent, function(value, key) {
            var changed = this.changed[this.torrentId];
            if (changed && $defined(changed[key])) return;
            var type = $type(value);
            if (type == 'boolean') {
                this.form[key].checked = value;
            } else {
                if (!this.form[key].focused) {
                    widget = $$W(this.form[key]);
                    if (widget) {
                        widget.setValue(value);
                    } else {
                        this.form[key].value = value;
                    };
                };
            };
            if (key == 'private' && value == 0) {
                this.form[key].disabled = true;
                this.form[key].getParent().addClass('opt-disabled');
            };
        }, this);
    }
});
