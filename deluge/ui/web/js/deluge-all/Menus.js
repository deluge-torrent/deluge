/*!
 * Deluge.Menus.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
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
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */

deluge.menus = {
    onTorrentActionSetOpt: function(item, e) {
        var ids = deluge.torrents.getSelectedIds();
        var action = item.initialConfig.torrentAction;
        var opts = {};
        opts[action[0]] = action[1];
        deluge.client.core.set_torrent_options(ids, opts);
    },

    onTorrentActionMethod: function(item, e) {
        var ids = deluge.torrents.getSelectedIds();
        var action = item.initialConfig.torrentAction;
        deluge.client.core[action](ids, {
            success: function() {
                deluge.ui.update();
            }
        });
    },

    onTorrentActionShow: function(item, e) {
        var ids = deluge.torrents.getSelectedIds();
        var action = item.initialConfig.torrentAction;
        switch (action) {
            case 'edit_trackers':
                deluge.editTrackers.show();
                break;
            case 'remove':
                deluge.removeWindow.show(ids);
                break;
            case 'move':
                deluge.moveStorage.show(ids);
                break;
        }
    },
}

deluge.menus.torrent = new Ext.menu.Menu({
    id: 'torrentMenu',
    items: [{
        torrentAction: 'pause_torrent',
        text: _('Pause'),
        iconCls: 'icon-pause',
        handler: deluge.menus.onTorrentActionMethod,
        scope: deluge.menus
    }, {
        torrentAction: 'resume_torrent',
        text: _('Resume'),
        iconCls: 'icon-resume',
        handler: deluge.menus.onTorrentActionMethod,
        scope: deluge.menus
    }, '-', {
        text: _('Options'),
        iconCls: 'icon-options',
        hideOnClick: false,
        menu: new Ext.menu.Menu({
            items: [{
                text: _('D/L Speed Limit'),
                iconCls: 'x-deluge-downloading',
                hideOnClick: false,
                menu: new Ext.menu.Menu({
                    items: [{
                        torrentAction: ['max_download_speed', 5],
                        text: _('5 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_download_speed', 10],
                        text: _('10 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_download_speed', 30],
                        text: _('30 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_download_speed', 80],
                        text: _('80 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_download_speed', 300],
                        text: _('300 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    },{
                        torrentAction: ['max_download_speed', -1],
                        text: _('Unlimited'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }]
                })
            }, {
                text: _('U/L Speed Limit'),
                iconCls: 'x-deluge-seeding',
                hideOnClick: false,
                menu: new Ext.menu.Menu({
                    items: [{
                        torrentAction: ['max_upload_speed', 5],
                        text: _('5 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_speed', 10],
                        text: _('10 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_speed', 30],
                        text: _('30 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_speed', 80],
                        text: _('80 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_speed', 300],
                        text: _('300 KiB/s'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    },{
                        torrentAction: ['max_upload_speed', -1],
                        text: _('Unlimited'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }]
                })
            }, {
                text: _('Connection Limit'),
                iconCls: 'x-deluge-connections',
                hideOnClick: false,
                menu: new Ext.menu.Menu({
                    items: [{
                        torrentAction: ['max_connections', 50],
                        text: _('50'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_connections', 100],
                        text: _('100'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_connections', 200],
                        text: _('200'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_connections', 300],
                        text: _('300'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_connections', 500],
                        text: _('500'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    },{
                        torrentAction: ['max_connections', -1],
                        text: _('Unlimited'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }]
                })
            }, {
                text: _('Upload Slot Limit'),
                iconCls: 'icon-upload-slots',
                hideOnClick: false,
                menu: new Ext.menu.Menu({
                    items: [{
                        torrentAction: ['max_upload_slots', 0],
                        text: _('0'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_slots', 1],
                        text: _('1'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_slots', 2],
                        text: _('2'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_slots', 3],
                        text: _('3'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['max_upload_slots', 5],
                        text: _('5'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    },{
                        torrentAction: ['max_upload_slots', -1],
                        text: _('Unlimited'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }]
                })
            }, {
                id: 'auto_managed',
                text: _('Auto Managed'),
                hideOnClick: false,
                menu: new Ext.menu.Menu({
                    items: [{
                        torrentAction: ['auto_managed', true],
                        text: _('On'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }, {
                        torrentAction: ['auto_managed', false],
                        text: _('Off'),
                        handler: deluge.menus.onTorrentActionSetOpt,
                        scope: deluge.menus
                    }]
                })
            }]
        })
    }, '-', {
        text: _('Queue'),
        iconCls: 'icon-queue',
        hideOnClick: false,
        menu: new Ext.menu.Menu({
            items: [{
                torrentAction: 'queue_top',
                text: _('Top'),
                iconCls: 'icon-top',
                handler: deluge.menus.onTorrentActionMethod,
                scope: deluge.menus
            },{
                torrentAction: 'queue_up',
                text: _('Up'),
                iconCls: 'icon-up',
                handler: deluge.menus.onTorrentActionMethod,
                scope: deluge.menus
            },{
                torrentAction: 'queue_down',
                text: _('Down'),
                iconCls: 'icon-down',
                handler: deluge.menus.onTorrentActionMethod,
                scope: deluge.menus
            },{
                torrentAction: 'queue_bottom',
                text: _('Bottom'),
                iconCls: 'icon-bottom',
                handler: deluge.menus.onTorrentActionMethod,
                scope: deluge.menus
            }]
        })
    }, '-', {
        torrentAction: 'force_reannounce',
        text: _('Update Tracker'),
        iconCls: 'icon-update-tracker',
        handler: deluge.menus.onTorrentActionMethod,
        scope: deluge.menus
    }, {
        torrentAction: 'edit_trackers',
        text: _('Edit Trackers'),
        iconCls: 'icon-edit-trackers',
        handler: deluge.menus.onTorrentActionShow,
        scope: deluge.menus
    }, '-', {
        torrentAction: 'remove',
        text: _('Remove Torrent'),
        iconCls: 'icon-remove',
        handler: deluge.menus.onTorrentActionShow,
        scope: deluge.menus
    }, '-', {
        torrentAction: 'force_recheck',
        text: _('Force Recheck'),
        iconCls: 'icon-recheck',
        handler: deluge.menus.onTorrentActionMethod,
        scope: deluge.menus
    }, {
        torrentAction: 'move',
        text: _('Move Download Folder'),
        iconCls: 'icon-move',
        handler: deluge.menus.onTorrentActionShow,
        scope: deluge.menus
    }]
});

deluge.menus.filePriorities = new Ext.menu.Menu({
    id: 'filePrioritiesMenu',
    items: [{
        id: 'expandAll',
        text: _('Expand All'),
        iconCls: 'icon-expand-all'
    }, '-', {
        id: 'no_download',
        text: _('Do Not Download'),
        iconCls: 'icon-do-not-download',
        filePriority: FILE_PRIORITY['Do Not Download']
    }, {
        id: 'normal',
        text: _('Normal Priority'),
        iconCls: 'icon-normal',
        filePriority: FILE_PRIORITY['Normal Priority']
    }, {
        id: 'high',
        text: _('High Priority'),
        iconCls: 'icon-high',
        filePriority: FILE_PRIORITY['High Priority']
    }, {
        id: 'highest',
        text: _('Highest Priority'),
        iconCls: 'icon-highest',
        filePriority: FILE_PRIORITY['Highest Priority']
    }]
});
