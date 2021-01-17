/**
 * Deluge.add.Window.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge.add');

/**
 * @class Deluge.add.Window
 * @extends Ext.Window
 * Base class for an add Window
 */
Deluge.add.Window = Ext.extend(Ext.Window, {
    initComponent: function () {
        Deluge.add.Window.superclass.initComponent.call(this);
        this.addEvents('beforeadd', 'add', 'addfailed');
    },

    /**
     * Create an id for the torrent before we have any info about it.
     */
    createTorrentId: function () {
        return new Date().getTime().toString();
    },
});
