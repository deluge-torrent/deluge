/*!
 * Deluge.add.UrlWindow.js
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

Ext.namespace('Deluge.add');
Deluge.add.UrlWindow = Ext.extend(Deluge.add.Window, {

    title: _('Add from Url'),
    modal: true,
    plain: true,
    layout: 'fit',
    width: 350,
    height: 155,

    buttonAlign: 'center',
    closeAction: 'hide',
    bodyStyle: 'padding: 10px 5px;',
    iconCls: 'x-deluge-add-url-window-icon',

    initComponent: function() {
        Deluge.add.UrlWindow.superclass.initComponent.call(this);
        this.addButton(_('Add'), this.onAddClick, this);

        var form = this.add({
            xtype: 'form',
            defaultType: 'textfield',
            baseCls: 'x-plain',
            labelWidth: 55
        });

        this.urlField = form.add({
            fieldLabel: _('Url'),
            id: 'url',
            name: 'url',
            width: '97%'
        });
        this.urlField.on('specialkey', this.onAdd, this);

        this.cookieField = form.add({
            fieldLabel: _('Cookies'),
            id: 'cookies',
            name: 'cookies',
            width: '97%'
        });
        this.cookieField.on('specialkey', this.onAdd, this);
    },

    onAddClick: function(field, e) {
        if ((field.id == 'url' || field.id == 'cookies') && e.getKey() != e.ENTER) return;

        var field = this.urlField;
        var url = field.getValue();
        var cookies = this.cookieField.getValue();
        var torrentId = this.createTorrentId();

        if (url.substring(0,20) == 'magnet:?xt=urn:btih:') {
            deluge.client.web.get_magnet_info(url, {
                success: this.onGotInfo,
                scope: this,
                filename: url,
                torrentId: torrentId
            });
        } else {
            deluge.client.web.download_torrent_from_url(url, cookies, {
                success: this.onDownload,
                scope: this,
                torrentId: torrentId
            });
        }

        this.hide();
        this.urlField.setValue('');
        this.fireEvent('beforeadd', torrentId, url);
    },

    onDownload: function(filename, obj, resp, req) {
        deluge.client.web.get_torrent_info(filename, {
            success: this.onGotInfo,
            scope: this,
            filename: filename,
            torrentId: req.options.torrentId
        });
    },

    onGotInfo: function(info, obj, response, request) {
        info['filename'] = request.options.filename;
        this.fireEvent('add', request.options.torrentId, info);
    }
});
