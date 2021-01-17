/**
 * Deluge.add.FilesTab.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge.add');

/**
 * @class Deluge.add.FilesTab
 * @extends Ext.ux.tree.TreeGrid
 */
Deluge.add.FilesTab = Ext.extend(Ext.ux.tree.TreeGrid, {
    layout: 'fit',
    title: _('Files'),

    autoScroll: false,
    animate: false,
    border: false,
    disabled: true,
    rootVisible: false,

    columns: [
        {
            header: _('Filename'),
            width: 295,
            dataIndex: 'filename',
        },
        {
            header: _('Size'),
            width: 60,
            dataIndex: 'size',
            tpl: new Ext.XTemplate('{size:this.fsize}', {
                fsize: function (v) {
                    return fsize(v);
                },
            }),
        },
        {
            header: _('Download'),
            width: 65,
            dataIndex: 'download',
            tpl: new Ext.XTemplate('{download:this.format}', {
                format: function (v) {
                    return (
                        '<div rel="chkbox" class="x-grid3-check-col' +
                        (v ? '-on' : '') +
                        '"> </div>'
                    );
                },
            }),
        },
    ],

    initComponent: function () {
        Deluge.add.FilesTab.superclass.initComponent.call(this);
        this.on('click', this.onNodeClick, this);
    },

    clearFiles: function () {
        var root = this.getRootNode();
        if (!root.hasChildNodes()) return;
        root.cascade(function (node) {
            if (!node.parentNode || !node.getOwnerTree()) return;
            node.remove();
        });
    },

    setDownload: function (node, value, suppress) {
        node.attributes.download = value;
        node.ui.updateColumns();

        if (node.isLeaf()) {
            if (!suppress) {
                return this.fireEvent('fileschecked', [node], value, !value);
            }
        } else {
            var nodes = [node];
            node.cascade(function (n) {
                n.attributes.download = value;
                n.ui.updateColumns();
                nodes.push(n);
            }, this);
            if (!suppress) {
                return this.fireEvent('fileschecked', nodes, value, !value);
            }
        }
    },

    onNodeClick: function (node, e) {
        var el = new Ext.Element(e.target);
        if (el.getAttribute('rel') == 'chkbox') {
            this.setDownload(node, !node.attributes.download);
        }
    },
});
