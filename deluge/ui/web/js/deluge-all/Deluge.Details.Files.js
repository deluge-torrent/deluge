/*
Script: Deluge.Details.Files.js
    The files tab displayed in the details panel.

Copyright:
	(C) Damien Churchill 2009-2010 <damoxc@gmail.com>
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, write to:
		The Free Software Foundation, Inc.,
		51 Franklin Street, Fifth Floor
		Boston, MA  02110-1301, USA.

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
*/
(function() {
	/* Renderers for the column tree */
	function fileProgressRenderer(value) {
		var progress = value * 100;
		return Deluge.progressBar(progress, this.col.width, progress.toFixed(2) + '%', 0);
	}
	function priorityRenderer(value) {
		if (isNaN(value)) return '';
		return String.format('<div class="{0}">{1}</div>', FILE_PRIORITY_CSS[value], _(FILE_PRIORITY[value]));
	}
	
	Ext.deluge.details.FilesTab = Ext.extend(Ext.ux.tree.TreeGrid, {
		
		constructor: function(config) {
			config = Ext.apply({
				title: _('Files'),
				rootVisible: false,
				autoScroll: true,
				selModel: new Ext.tree.MultiSelectionModel(),
				
				columns: [{
					header: _('Filename'),
					width: 330,
					dataIndex: 'filename'
				}, {
					xtype: 'tgrendercolumn',
					header: _('Size'),
					width: 150,
					dataIndex: 'size',
					renderer: fsize
				}, {
					xtype: 'tgrendercolumn',
					header: _('Progress'),
					width: 150,
					dataIndex: 'progress',
					renderer: fileProgressRenderer
				}, {
					xtype: 'tgrendercolumn',
					header: _('Priority'),
					width: 150,
					dataIndex: 'priority',
					renderer: priorityRenderer
				}],
				
				root: new Ext.tree.TreeNode({
					text: 'Files'
				})
			}, config);

			Ext.deluge.details.FilesTab.superclass.constructor.call(this, config);
		},

		initComponent: function() {
			
			Ext.deluge.details.FilesTab.superclass.initComponent.call(this);
		},
		
		onRender: function(ct, position) {
			Ext.deluge.details.FilesTab.superclass.onRender.call(this, ct, position);
			Deluge.Menus.FilePriorities.on('itemclick', this.onItemClick, this);
			this.on('contextmenu', this.onContextMenu, this);
			this.sorter = new Ext.tree.TreeSorter(this, {
				folderSort: true
			});
		},
		
		clear: function() {
			var root = this.getRootNode();
			if (!root.hasChildNodes()) return;
			root.cascade(function(node) {
				var parent = node.parentNode;
				if (!parent) return;
				if (!parent.ownerTree) return;
				parent.removeChild(node);
			});
		},
		
		update: function(torrentId) {
			if (this.torrentId != torrentId) {
				this.clear();
				this.torrentId = torrentId;
			}
			
			Deluge.Client.web.get_torrent_files(torrentId, {
				success: this.onRequestComplete,
				scope: this,
				torrentId: torrentId
			});
		},
		
		onContextMenu: function(node, e) {
			e.stopEvent();
			var selModel = this.getSelectionModel();
			if (selModel.getSelectedNodes().length < 2) {
				selModel.clearSelections();
				node.select();
			}
			Deluge.Menus.FilePriorities.showAt(e.getPoint());
		},
		
		onItemClick: function(baseItem, e) {
			switch (baseItem.id) {
				case 'expandAll':
					this.expandAll();
					break;
				default:
					var indexes = {};
					function walk(node) {
						if (Ext.isEmpty(node.attributes.fileIndex)) return;
						indexes[node.attributes.fileIndex] = node.attributes.priority;
					}
					this.getRootNode().cascade(walk);

					var nodes = this.getSelectionModel().getSelectedNodes();
					Ext.each(nodes, function(node) {
						if (!node.isLeaf()) {
							function setPriorities(node) {
								if (Ext.isEmpty(node.attributes.fileIndex)) return;
								indexes[node.attributes.fileIndex] = baseItem.filePriority;
							}
							node.cascade(setPriorities);
						} else if (!Ext.isEmpty(node.attributes.fileIndex)) {
							indexes[node.attributes.fileIndex] = baseItem.filePriority;
							return;
						}
					});
					
					var priorities = new Array(Ext.keys(indexes).length);
					for (var index in indexes) {
						priorities[index] = indexes[index];
					}

					Deluge.Client.core.set_torrent_file_priorities(this.torrentId, priorities, {
						success: function() {
							Ext.each(nodes, function(node) {
								node.setColumnValue(3, baseItem.filePriority);
							});
						},
						scope: this
					});
					break;
			}
		},
		
		onRequestComplete: function(files, options) {
			function walk(files, parent) {
				for (var file in files.contents) {
					var item = files.contents[file];
					var child = parent.findChild('id', file);
					if (item.type == 'dir') {
						if (!child) {
							child = new Ext.tree.TreeNode({
								id: file,
								text: file,
								filename: file,
								size: item['size'],
								progress: item['progress'],
								priority: item['priority']
							});
							parent.appendChild(child);
						}
						walk(item, child);
					} else {
						if (!child) {
							child = new Ext.tree.TreeNode({
								id: file,
								filename: file,
								text: file, // this needs to be here for sorting
								fileIndex: item['index'],
								size: item['size'],
								progress: item['progress'],
								priority: item['priority'],
								leaf: true,
								iconCls: 'x-deluge-file',
								uiProvider: Ext.ux.tree.TreeGridNodeUI
							});
							parent.appendChild(child);
						}
					}
				}
			}
			var root = this.getRootNode();
			walk(files, root);
			root.firstChild.expand();
		}
	});
	Deluge.Details.add(new Ext.deluge.details.FilesTab());
})();
