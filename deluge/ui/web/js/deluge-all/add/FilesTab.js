/*!
 * Deluge.add.FilesTab.js
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
Ext.ns('Deluge.add');

/**
 * @class Deluge.add.FilesTab
 * @extends Ext.ux.tree.TreeGrid
 */
Deluge.add.FilesTab = Ext.extend(Ext.ux.tree.TreeGrid, {

	layout: 'fit',
	title:  _('Files'),

	autoScroll:  true,
	animate:     false,
	border:      false,
	disabled:    true,
	rootVisible: false,

	columns: [{
		header: _('Filename'),
		width: 295,
		dataIndex: 'filename'
	},{
		header: _('Size'),
		width: 60,
		dataIndex: 'size',
		tpl: new Ext.XTemplate('{size:this.fsize}', {
			fsize: function(v) {
				return fsize(v);
			}
		})
	},{
		header: _('Download'),
		width: 65,
		dataIndex: 'download',
		tpl: new Ext.XTemplate('{download:this.format}', {
			format: function(v) {
				return '<div class="x-grid3-check-col'+(v?'-on':'')+'"> </div>';
			}
		})
	}],

	initComponent: function() {
		Deluge.add.FilesTab.superclass.initComponent.call(this);
		this.on('click', this.onNodeClick, this);
	},

	clearFiles: function() {
		var root = this.getRootNode();
		if (!root.hasChildNodes()) return;
		root.cascade(function(node) {
			if (!node.parentNode || !node.getOwnerTree()) return;
			node.remove();
		});
	},

	onNodeClick: function(node, e) {
		node.attributes.download = !node.attributes.download;
		var newNode = new Ext.tree.TreeNode(node.attributes);
		node.parentNode.replaceChild(newNode, node);
		this.fireEvent('filechecked', newNode, node.attributes.download, !node.attributes.download);
	},

	onFolderCheck: function(node, checked) {
		var priorities = this.optionsManager.get('file_priorities');
		node.cascade(function(child) {
			if (!child.ui.checkbox) {
				child.attributes.checked = checked;
			} else {
				child.ui.checkbox.checked = checked;
			}
			priorities[child.attributes.fileindex] = checked;
		}, this);
		this.optionsManager.setDefault('file_priorities', priorities);
	}
});
