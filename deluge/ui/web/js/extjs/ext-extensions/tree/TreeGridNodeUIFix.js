/**
 * Ext.ux.tree.TreeGridNodeUIFix.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.override(Ext.ux.tree.TreeGridNodeUI, {
    updateColumns: function () {
        if (!this.rendered) return;

        var a = this.node.attributes,
            t = this.node.getOwnerTree(),
            cols = t.columns,
            c = cols[0];

        // Update the first column
        this.anchor.firstChild.innerHTML = c.tpl
            ? c.tpl.apply(a)
            : a[c.dataIndex] || c.text;

        // Update the remaining columns
        for (i = 1, len = cols.length; i < len; i++) {
            c = cols[i];
            this.elNode.childNodes[i].firstChild.innerHTML = c.tpl
                ? c.tpl.apply(a)
                : a[c.dataIndex] || c.text;
        }
    },
});
