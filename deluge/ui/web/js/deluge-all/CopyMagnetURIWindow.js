/*
 * Deluge.CopyMagnetURI.js
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
Deluge.CopyMagnetURI = Ext.extend(Ext.Window, {
    title: _("Copy Magnet URI"),
    width: 375,
    height: 110,
    layout: "fit",
    buttonAlign: "right",
    closeAction: "hide",
    closable: true,
    iconCls: "x-deluge-copy-magnet-uri-icon",
    plain: true,
    html: "",
    resizable: false,
  
    initComponent: function() {
        Deluge.CopyMagnetURI.superclass.initComponent.call(this);
        this.form = this.add({
            xtype: "form",
            border: false,
            defaultType: "textfield",
            width: 300,
            bodyStyle: "padding: 5px"
        });
        this.magnetURI = this.form.add({
            fieldLabel: _("URI"),
            name: "URI",
            width: 240,
        })
        this.addButton(_("Copy"), this.onCopy, this);
        this.addButton(_("Close"), this.onClose, this);
    },
    show: function(a) {
        Deluge.CopyMagnetURI.superclass.show.call(this);
        var a = deluge.torrents.getSelected();
        this.torrentId = a.id;
        deluge.client.core.get_torrent_status(a.id, ["name","trackers"], {
            success: this.onRequestComplete,
            scope: this
        })
    },
    onRequestComplete: function(a) {
        var url = ["magnet:?xt=urn:btih:" + this.torrentId];
        url.push("dn="+encodeURIComponent(a.name));
        Ext.each(a.trackers, function(i) {
          url.push("tr="+encodeURIComponent(i.url));
        } );
        this.magnetURI.setValue( url.join("&") );
    },
    onCopy: function() {
        this.magnetURI.focus();
        this.magnetURI.el.dom.select();
        document.execCommand("copy");
    },
    onClose: function() {
        this.hide();
    },
});

deluge.copyMagnetWindow = new Deluge.CopyMagnetURI();