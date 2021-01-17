/**
 * Script: autoadd.js
 *      The client-side javascript code for the AutoAdd plugin.
 *
 * Copyright (C) 2009 GazpachoKing <chase.sterling@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.ns('Deluge.ux.AutoAdd');
Deluge.ux.AutoAdd.onClickFunctions = {};

Ext.ns('Deluge.ux.preferences');

/**
 * @class Deluge.ux.preferences.AutoAddPage
 * @extends Ext.Panel
 */
Deluge.ux.preferences.AutoAddPage = Ext.extend(Ext.Panel, {
    title: _('AutoAdd'),
    header: false,
    layout: 'fit',
    border: false,
    watchdirs: {},

    initComponent: function () {
        Deluge.ux.preferences.AutoAddPage.superclass.initComponent.call(this);

        var autoAdd = this;

        this.list = new Ext.list.ListView({
            store: new Ext.data.JsonStore({
                fields: ['id', 'enabled', 'owner', 'path'],
            }),
            columns: [
                {
                    id: 'enabled',
                    header: _('Active'),
                    sortable: true,
                    dataIndex: 'enabled',
                    tpl: new Ext.XTemplate('{enabled:this.getCheckbox}', {
                        getCheckbox: function (checked, selected) {
                            Deluge.ux.AutoAdd.onClickFunctions[
                                selected.id
                            ] = function () {
                                if (selected.enabled) {
                                    deluge.client.autoadd.disable_watchdir(
                                        selected.id
                                    );
                                    checked = false;
                                } else {
                                    deluge.client.autoadd.enable_watchdir(
                                        selected.id
                                    );
                                    checked = true;
                                }
                                autoAdd.updateWatchDirs();
                            };
                            return (
                                '<input id="enabled-' +
                                selected.id +
                                '" type="checkbox"' +
                                (checked ? ' checked' : '') +
                                ' onclick="Deluge.ux.AutoAdd.onClickFunctions[' +
                                selected.id +
                                ']()" />'
                            );
                        },
                    }),
                    width: 0.15,
                },
                {
                    id: 'owner',
                    header: _('Owner'),
                    sortable: true,
                    dataIndex: 'owner',
                    width: 0.2,
                },
                {
                    id: 'path',
                    header: _('Path'),
                    sortable: true,
                    dataIndex: 'path',
                },
            ],
            singleSelect: true,
            autoExpandColumn: 'path',
        });
        this.list.on('selectionchange', this.onSelectionChange, this);

        this.panel = this.add({
            items: [this.list],
            bbar: {
                items: [
                    {
                        text: _('Add'),
                        iconCls: 'icon-add',
                        handler: this.onAddClick,
                        scope: this,
                    },
                    {
                        text: _('Edit'),
                        iconCls: 'icon-edit',
                        handler: this.onEditClick,
                        scope: this,
                        disabled: true,
                    },
                    '->',
                    {
                        text: _('Remove'),
                        iconCls: 'icon-remove',
                        handler: this.onRemoveClick,
                        scope: this,
                        disabled: true,
                    },
                ],
            },
        });

        this.on('show', this.onPreferencesShow, this);
    },

    updateWatchDirs: function () {
        deluge.client.autoadd.get_watchdirs({
            success: function (watchdirs) {
                this.watchdirs = watchdirs;
                var watchdirsArray = [];
                for (var id in watchdirs) {
                    if (watchdirs.hasOwnProperty(id)) {
                        var watchdir = {};
                        watchdir['id'] = id;
                        watchdir['enabled'] = watchdirs[id].enabled;
                        watchdir['owner'] =
                            watchdirs[id].owner || 'localclient';
                        watchdir['path'] = watchdirs[id].path;

                        watchdirsArray.push(watchdir);
                    }
                }
                this.list.getStore().loadData(watchdirsArray);
            },
            scope: this,
        });
    },

    onAddClick: function () {
        if (!this.addWin) {
            this.addWin = new Deluge.ux.AutoAdd.AddAutoAddCommandWindow();
            this.addWin.on(
                'watchdiradd',
                function () {
                    this.updateWatchDirs();
                },
                this
            );
        }
        this.addWin.show();
    },

    onEditClick: function () {
        if (!this.editWin) {
            this.editWin = new Deluge.ux.AutoAdd.EditAutoAddCommandWindow();
            this.editWin.on(
                'watchdiredit',
                function () {
                    this.updateWatchDirs();
                },
                this
            );
        }
        var id = this.list.getSelectedRecords()[0].id;
        this.editWin.show(id, this.watchdirs[id]);
    },

    onPreferencesShow: function () {
        this.updateWatchDirs();
    },

    onRemoveClick: function () {
        var record = this.list.getSelectedRecords()[0];
        deluge.client.autoadd.remove(record.id, {
            success: function () {
                this.updateWatchDirs();
            },
            scope: this,
        });
    },

    onSelectionChange: function (dv, selections) {
        if (selections.length) {
            this.panel.getBottomToolbar().items.get(1).enable();
            this.panel.getBottomToolbar().items.get(3).enable();
        } else {
            this.panel.getBottomToolbar().items.get(1).disable();
            this.panel.getBottomToolbar().items.get(3).disable();
        }
    },
});

Deluge.plugins.AutoAddPlugin = Ext.extend(Deluge.Plugin, {
    name: 'AutoAdd',

    static: {
        prefsPage: null,
    },

    onDisable: function () {
        deluge.preferences.removePage(Deluge.plugins.AutoAddPlugin.prefsPage);
        Deluge.plugins.AutoAddPlugin.prefsPage = null;
    },

    onEnable: function () {
        /*
         * Called for each of the JavaScript files.
         * This will prevent adding unnecessary tabs to the preferences window.
         */
        if (!Deluge.plugins.AutoAddPlugin.prefsPage) {
            Deluge.plugins.AutoAddPlugin.prefsPage = deluge.preferences.addPage(
                new Deluge.ux.preferences.AutoAddPage()
            );
        }
    },
});

Deluge.registerPlugin('AutoAdd', Deluge.plugins.AutoAddPlugin);
