/*
 * Deluge.CopyMagnet.js
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
Deluge.CopyMagnet = Ext.extend(Ext.Window, {
    title: _('Copy Magnet URI'),
    width: 375,
    closeAction: 'hide',
    iconCls: 'icon-magnet-copy',

    initComponent: function () {
        Deluge.CopyMagnet.superclass.initComponent.call(this);
        form = this.add({
            xtype: 'form',
            defaultType: 'textfield',
            hideLabels: true,
        });
        this.magnetURI = form.add({
            name: 'URI',
            anchor: '100%',
        });
        this.addButton(_('Close'), this.onClose, this);
        this.addButton(_('Copy'), this.onCopy, this);
    },
    show: function (a) {
        Deluge.CopyMagnet.superclass.show.call(this);
        const torrent = deluge.torrents.getSelected();
        deluge.client.core.get_magnet_uri(torrent.id, {
            success: this.onRequestComplete,
            scope: this,
        });
    },
    onRequestComplete: function (uri) {
        this.magnetURI.setValue(uri);
    },
    onCopy: function () {
        this.magnetURI.focus();
        this.magnetURI.el.dom.select();
        document.execCommand('copy');
    },
    onClose: function () {
        this.hide();
    },
});

deluge.copyMagnetWindow = new Deluge.CopyMagnet();
