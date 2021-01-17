/**
 * Deluge.FileBrowser.js
 *
 * Copyright (c) Damien Churchill 2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.namespace('Deluge');
Deluge.FileBrowser = Ext.extend(Ext.Window, {
    title: _('File Browser'),

    width: 500,
    height: 400,

    initComponent: function () {
        Deluge.FileBrowser.superclass.initComponent.call(this);

        this.add({
            xtype: 'toolbar',
            items: [
                {
                    text: _('Back'),
                    iconCls: 'icon-back',
                },
                {
                    text: _('Forward'),
                    iconCls: 'icon-forward',
                },
                {
                    text: _('Up'),
                    iconCls: 'icon-up',
                },
                {
                    text: _('Home'),
                    iconCls: 'icon-home',
                },
            ],
        });
    },
});
