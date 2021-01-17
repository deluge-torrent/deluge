/**
 * Deluge.AboutWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.namespace('Deluge.about');

/**
 * @class Deluge.about.AboutWindow
 * @extends Ext.Window
 */
Deluge.about.AboutWindow = Ext.extend(Ext.Window, {
    id: 'AboutWindow',
    title: _('About Deluge'),
    height: 330,
    width: 270,
    iconCls: 'x-deluge-main-panel',
    resizable: false,
    plain: true,
    layout: {
        type: 'vbox',
        align: 'center',
    },
    buttonAlign: 'center',

    initComponent: function () {
        Deluge.about.AboutWindow.superclass.initComponent.call(this);
        this.addEvents({
            build_ready: true,
        });

        var self = this;
        var libtorrent = function () {
            deluge.client.core.get_libtorrent_version({
                success: function (lt_version) {
                    comment += '<br/>' + _('libtorrent:') + ' ' + lt_version;
                    Ext.getCmp('about_comment').setText(comment, false);
                    self.fireEvent('build_ready');
                },
            });
        };

        var client_version = deluge.version;

        var comment =
            _(
                'A peer-to-peer file sharing program\nutilizing the BitTorrent protocol.'
            ).replace('\n', '<br/>') +
            '<br/><br/>' +
            _('Client:') +
            ' ' +
            client_version +
            '<br/>';
        deluge.client.web.connected({
            success: function (connected) {
                if (connected) {
                    deluge.client.daemon.get_version({
                        success: function (server_version) {
                            comment +=
                                _('Server:') + ' ' + server_version + '<br/>';
                            libtorrent();
                        },
                    });
                } else {
                    this.fireEvent('build_ready');
                }
            },
            failure: function () {
                this.fireEvent('build_ready');
            },
            scope: this,
        });

        this.add([
            {
                xtype: 'box',
                style: 'padding-top: 5px',
                height: 80,
                width: 240,
                cls: 'x-deluge-logo',
                hideLabel: true,
            },
            {
                xtype: 'label',
                style: 'padding-top: 10px; font-weight: bold; font-size: 16px;',
                text: _('Deluge') + ' ' + client_version,
            },
            {
                xtype: 'label',
                id: 'about_comment',
                style: 'padding-top: 10px; text-align:center; font-size: 12px;',
                html: comment,
            },
            {
                xtype: 'label',
                style: 'padding-top: 10px; font-size: 10px;',
                text: _('Copyright 2007-2018 Deluge Team'),
            },
            {
                xtype: 'label',
                style: 'padding-top: 5px; font-size: 12px;',
                html:
                    '<a href="https://deluge-torrent.org" target="_blank">deluge-torrent.org</a>',
            },
        ]);
        this.addButton(_('Close'), this.onCloseClick, this);
    },

    show: function () {
        this.on('build_ready', function () {
            Deluge.about.AboutWindow.superclass.show.call(this);
        });
    },

    onCloseClick: function () {
        this.close();
    },
});

Ext.namespace('Deluge');

Deluge.About = function () {
    new Deluge.about.AboutWindow().show();
};
