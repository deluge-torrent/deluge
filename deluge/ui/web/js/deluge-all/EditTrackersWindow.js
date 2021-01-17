/**
 * Deluge.EditTrackers.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * @class Deluge.EditTrackersWindow
 * @extends Ext.Window
 */
Deluge.EditTrackersWindow = Ext.extend(Ext.Window, {
    title: _('Edit Trackers'),
    layout: 'fit',
    width: 350,
    height: 220,
    plain: true,
    closable: true,
    resizable: true,
    constrainHeader: true,

    bodyStyle: 'padding: 5px',
    buttonAlign: 'right',
    closeAction: 'hide',
    iconCls: 'x-deluge-edit-trackers',

    initComponent: function () {
        Deluge.EditTrackersWindow.superclass.initComponent.call(this);

        this.addButton(_('Cancel'), this.onCancelClick, this);
        this.addButton(_('OK'), this.onOkClick, this);
        this.addEvents('save');

        this.on('show', this.onShow, this);
        this.on('save', this.onSave, this);

        this.addWindow = new Deluge.AddTrackerWindow();
        this.addWindow.on('add', this.onAddTrackers, this);
        this.editWindow = new Deluge.EditTrackerWindow();

        this.list = new Ext.list.ListView({
            store: new Ext.data.JsonStore({
                root: 'trackers',
                fields: ['tier', 'url'],
            }),
            columns: [
                {
                    header: _('Tier'),
                    width: 0.1,
                    dataIndex: 'tier',
                },
                {
                    header: _('Tracker'),
                    width: 0.9,
                    dataIndex: 'url',
                },
            ],
            columnSort: {
                sortClasses: ['', ''],
            },
            stripeRows: true,
            singleSelect: true,
            listeners: {
                dblclick: { fn: this.onListNodeDblClicked, scope: this },
                selectionchange: { fn: this.onSelect, scope: this },
            },
        });

        this.panel = this.add({
            items: [this.list],
            autoScroll: true,
            bbar: new Ext.Toolbar({
                items: [
                    {
                        text: _('Up'),
                        iconCls: 'icon-up',
                        handler: this.onUpClick,
                        scope: this,
                    },
                    {
                        text: _('Down'),
                        iconCls: 'icon-down',
                        handler: this.onDownClick,
                        scope: this,
                    },
                    '->',
                    {
                        text: _('Add'),
                        iconCls: 'icon-add',
                        handler: this.onAddClick,
                        scope: this,
                    },
                    {
                        text: _('Edit'),
                        iconCls: 'icon-edit-trackers',
                        handler: this.onEditClick,
                        scope: this,
                    },
                    {
                        text: _('Remove'),
                        iconCls: 'icon-remove',
                        handler: this.onRemoveClick,
                        scope: this,
                    },
                ],
            }),
        });
    },

    onAddClick: function () {
        this.addWindow.show();
    },

    onAddTrackers: function (trackers) {
        var store = this.list.getStore();
        Ext.each(
            trackers,
            function (tracker) {
                var duplicate = false,
                    heightestTier = -1;
                store.each(function (record) {
                    if (record.get('tier') > heightestTier) {
                        heightestTier = record.get('tier');
                    }
                    if (tracker == record.get('tracker')) {
                        duplicate = true;
                        return false;
                    }
                }, this);
                if (duplicate) return;
                store.add(
                    new store.recordType({
                        tier: heightestTier + 1,
                        url: tracker,
                    })
                );
            },
            this
        );
    },

    onCancelClick: function () {
        this.hide();
    },

    onEditClick: function () {
        var selected = this.list.getSelectedRecords()[0];
        if (!selected) return;
        this.editWindow.show(selected);
    },

    onHide: function () {
        this.list.getStore().removeAll();
    },

    onListNodeDblClicked: function (list, index, node, e) {
        this.editWindow.show(this.list.getRecord(node));
    },

    onOkClick: function () {
        var trackers = [];
        this.list.getStore().each(function (record) {
            trackers.push({
                tier: record.get('tier'),
                url: record.get('url'),
            });
        }, this);

        deluge.client.core.set_torrent_trackers(this.torrentId, trackers, {
            failure: this.onSaveFail,
            scope: this,
        });

        this.hide();
    },

    onRemoveClick: function () {
        // Remove from the grid
        var selected = this.list.getSelectedRecords()[0];
        if (!selected) return;
        this.list.getStore().remove(selected);
    },

    onRequestComplete: function (status) {
        this.list.getStore().loadData(status);
        this.list.getStore().sort('tier', 'ASC');
    },

    onSaveFail: function () {},

    onSelect: function (list) {
        if (list.getSelectionCount()) {
            this.panel.getBottomToolbar().items.get(4).enable();
        }
    },

    onShow: function () {
        this.panel.getBottomToolbar().items.get(4).disable();
        var r = deluge.torrents.getSelected();
        this.torrentId = r.id;
        deluge.client.core.get_torrent_status(r.id, ['trackers'], {
            success: this.onRequestComplete,
            scope: this,
        });
    },

    onDownClick: function () {
        var r = this.list.getSelectedRecords()[0];
        if (!r) return;

        r.set('tier', r.get('tier') + 1);
        r.store.sort('tier', 'ASC');
        r.store.commitChanges();

        this.list.select(r.store.indexOf(r));
    },

    onUpClick: function () {
        var r = this.list.getSelectedRecords()[0];
        if (!r) return;

        if (r.get('tier') == 0) return;
        r.set('tier', r.get('tier') - 1);
        r.store.sort('tier', 'ASC');
        r.store.commitChanges();

        this.list.select(r.store.indexOf(r));
    },
});
