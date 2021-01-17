/**
 * Deluge.RemoveWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

/**
 * @class Deluge.RemoveWindow
 * @extends Ext.Window
 */
Deluge.RemoveWindow = Ext.extend(Ext.Window, {
    title: _('Remove Torrent'),
    layout: 'fit',
    width: 350,
    height: 100,
    constrainHeader: true,
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    iconCls: 'x-deluge-remove-window-icon',
    plain: true,

    bodyStyle: 'padding: 5px; padding-left: 10px;',
    html: 'Are you sure you wish to remove the torrent (s)?',

    initComponent: function () {
        Deluge.RemoveWindow.superclass.initComponent.call(this);
        this.addButton(_('Cancel'), this.onCancel, this);
        this.addButton(_('Remove With Data'), this.onRemoveData, this);
        this.addButton(_('Remove Torrent'), this.onRemove, this);
    },

    remove: function (removeData) {
        deluge.client.core.remove_torrents(this.torrentIds, removeData, {
            success: function (result) {
                if (result == true) {
                    console.log(
                        'Error(s) occured when trying to delete torrent(s).'
                    );
                }
                this.onRemoved(this.torrentIds);
            },
            scope: this,
            torrentIds: this.torrentIds,
        });
    },

    show: function (ids) {
        Deluge.RemoveWindow.superclass.show.call(this);
        this.torrentIds = ids;
    },

    onCancel: function () {
        this.hide();
        this.torrentIds = null;
    },

    onRemove: function () {
        this.remove(false);
    },

    onRemoveData: function () {
        this.remove(true);
    },

    onRemoved: function (torrentIds) {
        deluge.events.fire('torrentsRemoved', torrentIds);
        this.hide();
        deluge.ui.update();
    },
});

deluge.removeWindow = new Deluge.RemoveWindow();
