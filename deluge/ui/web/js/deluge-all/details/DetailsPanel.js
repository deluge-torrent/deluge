/**
 * Deluge.details.DetailsPanel.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.details');

/**
 * @class Deluge.details.DetailsPanel
 */
Deluge.details.DetailsPanel = Ext.extend(Ext.TabPanel, {
    id: 'torrentDetails',
    activeTab: 0,

    initComponent: function () {
        Deluge.details.DetailsPanel.superclass.initComponent.call(this);
        this.add(new Deluge.details.StatusTab());
        this.add(new Deluge.details.DetailsTab());
        this.add(new Deluge.details.FilesTab());
        this.add(new Deluge.details.PeersTab());
        this.add(new Deluge.details.OptionsTab());
    },

    clear: function () {
        this.items.each(function (panel) {
            if (panel.clear) {
                panel.clear.defer(100, panel);
                panel.disable();
            }
        });
    },

    update: function (tab) {
        var torrent = deluge.torrents.getSelected();
        if (!torrent) {
            this.clear();
            return;
        }

        this.items.each(function (tab) {
            if (tab.disabled) tab.enable();
        });

        tab = tab || this.getActiveTab();
        if (tab.update) tab.update(torrent.id);
    },

    /* Event Handlers */

    // We need to add the events in onRender since Deluge.Torrents has not been created yet.
    onRender: function (ct, position) {
        Deluge.details.DetailsPanel.superclass.onRender.call(
            this,
            ct,
            position
        );
        deluge.events.on('disconnect', this.clear, this);
        deluge.torrents.on('rowclick', this.onTorrentsClick, this);
        this.on('tabchange', this.onTabChange, this);

        deluge.torrents.getSelectionModel().on(
            'selectionchange',
            function (selModel) {
                if (!selModel.hasSelection()) this.clear();
            },
            this
        );
    },

    onTabChange: function (panel, tab) {
        this.update(tab);
    },

    onTorrentsClick: function (grid, rowIndex, e) {
        this.update();
    },
});
