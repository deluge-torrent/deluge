/*!
 * Deluge.add.FilesTab.js
 *
 * Copyright (c) Damien Churchill 2009-2011 <damoxc@gmail.com>
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

/**
 * @class Deluge.add.FilesTab
 * @extends Ext.ux.tree.TreeGrid
 */
Ext.define('Deluge.add.FilesTab', {
    extend: 'Ext.tree.Panel',

    layout: 'fit',
    title:  _('Files'),

    autoScroll:  true,
    animate:     false,
    border:      false,
    disabled:    true,
    rootVisible: false,

    columns: [{
        xtype: 'treecolumn',
        header: _('Filename'),
        width: 295,
        dataIndex: 'filename'
    },{
        xtype: 'templatecolumn',
        header: _('Size'),
        width: 60,
        dataIndex: 'size',
        tpl: Ext.create('Ext.XTemplate', '{size:this.fsize}', {
            fsize: function(v) {
                return fsize(v);
            }
        })
    },{
        xtype: 'templatecolumn',
        header: _('Download'),
        width: 65,
        dataIndex: 'download',
        tpl: Ext.create('Ext.XTemplate', '{download:this.format}', {
            format: function(v) {
                return '<div rel="chkbox" class="x-grid3-check-col'+(v?'-on':'')+'"> </div>';
            }
        })
    }],

    store: Ext.create('Ext.data.TreeStore', {
        model: 'Deluge.data.AddTorrentFile',
        proxy: {
            type: 'memory'
        }
    }),

    initComponent: function() {
        this.callParent(arguments);
        this.on('click', this.onNodeClick, this);
    },

    clearFiles: function() {
        this.getStore().removeAll();
    },

    setDownload: function(node, value, suppress) {
        node.attributes.download = value;
        node.ui.updateColumns();

        if (node.isLeaf()) {
            if (!suppress) {
                return this.fireEvent('fileschecked', [node], value, !value);
            }
        } else {
            var nodes = [node];
            node.cascade(function(n) {
                n.attributes.download = value;
                n.ui.updateColumns();
                nodes.push(n);
            }, this);
            if (!suppress) {
                return this.fireEvent('fileschecked', nodes, value, !value);
            }
        }
    },

    onNodeClick: function(node, e) {
        var el = Ext.fly(e.target);
        if (el.getAttribute('rel') == 'chkbox') {
            this.setDownload(node, !node.attributes.download);
        }
    }
});
