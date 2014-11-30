/*!
 * Deluge.data.SortTypes.js
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
Ext.namespace('Deluge.data');

/**
 * Common sort functions that can be used for data Stores.
 *
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 *
 * @class Deluge.data.SortTypes
 * @singleton
 */
Deluge.data.SortTypes = {
	asIPAddress: function(value) {
		var d = value.match(/(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\:(\d+)/);
		return ((((((+d[1])*256)+(+d[2]))*256)+(+d[3]))*256)+(+d[4]);
	},

	asQueuePosition: function(value) {
		return (value > -1) ? value : Number.MAX_VALUE;
	},

	asName: function(value) {
		return String(value).toLowerCase();
	}
}
/*!
 * Deluge.data.PeerRecord.js
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
Ext.namespace('Deluge.data');

/**
 * Deluge.data.Peer record
 *
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 *
 * @class Deluge.data.Peer
 * @extends Ext.data.Record
 * @constructor
 * @param {Object} data The peer data
 */
Deluge.data.Peer = Ext.data.Record.create([
	{
		name: 'country',
		type: 'string'
	}, {
		name: 'ip',
		type: 'string',
		sortType: Deluge.data.SortTypes.asIPAddress
	}, {
		name: 'client',
		type: 'string'
	}, {
		name: 'progress',
		type: 'float'
	}, {
		name: 'down_speed',
		type: 'int'
	}, {
		name: 'up_speed',
		type: 'int'
	}, {
		name: 'seed',
		type: 'int'
	}
]);
/*!
 * Deluge.data.TorrentRecord.js
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
Ext.namespace('Deluge.data');

/**
 * Deluge.data.Torrent record
 *
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 *
 * @class Deluge.data.Torrent
 * @extends Ext.data.Record
 * @constructor
 * @param {Object} data The torrents data
 */
Deluge.data.Torrent = Ext.data.Record.create([{
		name: 'queue',
		type: 'int'
	}, {
		name: 'name',
		type: 'string',
		sortType: Deluge.data.SortTypes.asName
	}, {
		name: 'total_wanted',
		type: 'int'
	}, {
		name: 'state',
		type: 'string'
	}, {
		name: 'progress',
		type: 'int'
	}, {
		name: 'num_seeds',
		type: 'int'
	}, {
		name: 'total_seeds',
		type: 'int'
	}, {
		name: 'num_peers',
		type: 'int'
	}, {
		name: 'total_peers',
		type: 'int'
	}, {
		name: 'download_payload_rate',
		type: 'int'
	}, {
		name: 'upload_payload_rate',
		type: 'int'
	}, {
		name: 'eta',
		type: 'int'
	}, {
		name: 'ratio',
		type: 'float'
	}, {
		name: 'distributed_copies',
		type: 'float'
	}, {
		name: 'time_added',
		type: 'int'
	}, {
		name: 'tracker_host',
		type: 'string'
	}, {
		name: 'save_path',
		type: 'string'
	}, {
		name: 'total_done',
		type: 'int'
	}, {
		name: 'total_uploaded',
		type: 'int'
	}, {
		name: 'max_download_speed',
		type: 'int'
	}, {
		name: 'max_upload_speed',
		type: 'int'
	}, {
		name: 'seeds_peers_ratio',
		type: 'float'
	}
]);
/*!
 * Deluge.details.DetailsPanel.js
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
Ext.namespace('Deluge.details');

/**
 * @class Deluge.details.DetailsPanel
 */
Deluge.details.DetailsPanel = Ext.extend(Ext.TabPanel, {

	id: 'torrentDetails',
	activeTab: 0,

	initComponent: function() {
		Deluge.details.DetailsPanel.superclass.initComponent.call(this);
		this.add(new Deluge.details.StatusTab());
		this.add(new Deluge.details.DetailsTab());
		this.add(new Deluge.details.FilesTab());
		this.add(new Deluge.details.PeersTab());
		this.add(new Deluge.details.OptionsTab());
	},
	
	clear: function() {
		this.items.each(function(panel) {
			if (panel.clear) {
				panel.clear.defer(100, panel);
				panel.disable();
			}
		});
	},
	
	
	update: function(tab) {
		var torrent = deluge.torrents.getSelected();
		if (!torrent) {
			this.clear();
			return;
		}
		
		this.items.each(function(tab) {
			if (tab.disabled) tab.enable();
		});
		
		tab = tab || this.getActiveTab();
		if (tab.update) tab.update(torrent.id);
	},
	
	/* Event Handlers */
	
	// We need to add the events in onRender since Deluge.Torrents hasn't
	// been created yet.
	onRender: function(ct, position) {
		Deluge.details.DetailsPanel.superclass.onRender.call(this, ct, position);
		deluge.events.on('disconnect', this.clear, this);
		deluge.torrents.on('rowclick', this.onTorrentsClick, this);
		this.on('tabchange', this.onTabChange, this);
		
		deluge.torrents.getSelectionModel().on('selectionchange', function(selModel) {
			if (!selModel.hasSelection()) this.clear();
		}, this);
	},
	
	onTabChange: function(panel, tab) {
		this.update(tab);
	},
	
	onTorrentsClick: function(grid, rowIndex, e) {
		this.update();
	}
});
/*
Script: Deluge.Details.Details.js
	The details tab displayed in the details panel.

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

Deluge.details.DetailsTab = Ext.extend(Ext.Panel, {
	title: _('Details'),

	fields: {},
	autoScroll: true,
	queuedItems: {},

	oldData: {},

	initComponent: function() {
		Deluge.details.DetailsTab.superclass.initComponent.call(this);
		this.addItem('torrent_name', _('Name'));
		this.addItem('hash', _('Hash'));
		this.addItem('path', _('Path'));
		this.addItem('size', _('Total Size'));
		this.addItem('files', _('# of files'));
		this.addItem('comment', _('Comment'));
		this.addItem('status', _('Status'));
		this.addItem('tracker', _('Tracker'));
	},

	onRender: function(ct, position) {
		Deluge.details.DetailsTab.superclass.onRender.call(this, ct, position);
		this.body.setStyle('padding', '10px');
		this.dl = Ext.DomHelper.append(this.body, {tag: 'dl'}, true);

		for (var id in this.queuedItems) {
			this.doAddItem(id, this.queuedItems[id]);
		}
	},

	addItem: function(id, label) {
		if (!this.rendered) {
			this.queuedItems[id] = label;
		} else {
			this.doAddItem(id, label);
		}
	},

	// private
	doAddItem: function(id, label) {
		Ext.DomHelper.append(this.dl, {tag: 'dt', cls: id, html: label + ':'});
		this.fields[id] = Ext.DomHelper.append(this.dl, {tag: 'dd', cls: id, html: ''}, true);
	},

	clear: function() {
		if (!this.fields) return;
		for (var k in this.fields) {
			this.fields[k].dom.innerHTML = '';
		}
		this.oldData = {}
	},

	update: function(torrentId) {
		deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Details, {
			success: this.onRequestComplete,
			scope: this,
			torrentId: torrentId
		});
	},

	onRequestComplete: function(torrent, request, response, options) {
		var data = {
			torrent_name: torrent.name,
			hash: options.options.torrentId,
			path: torrent.save_path,
			size: fsize(torrent.total_size),
			files: torrent.num_files,
			status: torrent.message,
			tracker: torrent.tracker,
			comment: torrent.comment
		};

		for (var field in this.fields) {
			if (!Ext.isDefined(data[field])) continue; // this is a field we aren't responsible for.
			if (data[field] == this.oldData[field]) continue;
			this.fields[field].dom.innerHTML = Ext.escapeHTML(data[field]);
		}
		this.oldData = data;
	}
});
/*!
 * Deluge.details.FilesTab.js
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

Deluge.details.FilesTab = Ext.extend(Ext.ux.tree.TreeGrid, {

	title: _('Files'),

	rootVisible: false,

	columns: [{
		header: _('Filename'),
		width: 330,
		dataIndex: 'filename'
	}, {
		header: _('Size'),
		width: 150,
		dataIndex: 'size',
		tpl: new Ext.XTemplate('{size:this.fsize}', {
			fsize: function(v) { return fsize(v); }
		})
	}, {
		xtype: 'tgrendercolumn',
		header: _('Progress'),
		width: 150,
		dataIndex: 'progress',
		renderer: function(v) {
			var progress = v * 100;
			return Deluge.progressBar(progress, this.col.width, progress.toFixed(2) + '%', 0);
		}
	}, {
		header: _('Priority'),
		width: 150,
		dataIndex: 'priority',
		tpl: new Ext.XTemplate('<tpl if="!isNaN(priority)">' +
			'<div class="{priority:this.getClass}">' +
				'{priority:this.getName}' +
			'</div></tpl>', {
			getClass: function(v) {
				return FILE_PRIORITY_CSS[v];
			},

			getName: function(v) {
				return _(FILE_PRIORITY[v]);
			}
		})
	}],

	selModel: new Ext.tree.MultiSelectionModel(),

	initComponent: function() {
		Deluge.details.FilesTab.superclass.initComponent.call(this);
		this.setRootNode(new Ext.tree.TreeNode({text: 'Files'}));
	},

	clear: function() {
		var root = this.getRootNode();
		if (!root.hasChildNodes()) return;
		root.cascade(function(node) {
			var parentNode = node.parentNode;
			if (!parentNode) return;
			if (!parentNode.ownerTree) return;
			parentNode.removeChild(node);
		});
	},

	createFileTree: function(files) {
		function walk(files, parentNode) {
			for (var file in files.contents) {
				var item = files.contents[file];
				if (item.type == 'dir') {
					walk(item, parentNode.appendChild(new Ext.tree.TreeNode({
						text: file,
						filename: file,
						size: item.size,
						progress: item.progress,
						priority: item.priority
					})));
				} else {
					parentNode.appendChild(new Ext.tree.TreeNode({
						text: file,
						filename: file,
						fileIndex: item.index,
						size: item.size,
						progress: item.progress,
						priority: item.priority,
						leaf: true,
						iconCls: 'x-deluge-file',
						uiProvider: Ext.ux.tree.TreeGridNodeUI
					}));
				}
			}
		}
		var root = this.getRootNode();
		walk(files, root);
		root.firstChild.expand();
	},

	update: function(torrentId) {
		if (this.torrentId != torrentId) {
			this.clear();
			this.torrentId = torrentId;
		}

		deluge.client.web.get_torrent_files(torrentId, {
			success: this.onRequestComplete,
			scope: this,
			torrentId: torrentId
		});
	},

	updateFileTree: function(files) {
		function walk(files, parentNode) {
			for (var file in files.contents) {
				var item = files.contents[file];
				var node = parentNode.findChild('filename', file);
				node.attributes.size     = item.size;
				node.attributes.progress = item.progress;
				node.attributes.priority = item.priority;
				node.ui.updateColumns();
				if (item.type == 'dir') {
					walk(item, node);
				}
			}
		}
		walk(files, this.getRootNode());
	},

	onRender: function(ct, position) {
		Deluge.details.FilesTab.superclass.onRender.call(this, ct, position);
		deluge.menus.filePriorities.on('itemclick', this.onItemClick, this);
		this.on('contextmenu', this.onContextMenu, this);
		this.sorter = new Ext.tree.TreeSorter(this, {
			folderSort: true
		});
	},

	onContextMenu: function(node, e) {
		e.stopEvent();
		var selModel = this.getSelectionModel();
		if (selModel.getSelectedNodes().length < 2) {
			selModel.clearSelections();
			node.select();
		}
		deluge.menus.filePriorities.showAt(e.getPoint());
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

				deluge.client.core.set_torrent_file_priorities(this.torrentId, priorities, {
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
		if (!this.getRootNode().hasChildNodes()) {
			this.createFileTree(files);
		} else {
			this.updateFileTree(files);
		}
	}
});
/*!
 * Deluge.details.OptionsTab.js
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


Deluge.details.OptionsTab = Ext.extend(Ext.form.FormPanel, {

	constructor: function(config) {
		config = Ext.apply({
			autoScroll: true,
			bodyStyle: 'padding: 5px;',
			border: false,
			cls: 'x-deluge-options',
			defaults: {
				autoHeight: true,
				labelWidth: 1,
				defaultType: 'checkbox'
			},
			deferredRender: false,
			layout: 'column',
			title: _('Options')
		}, config);
		Deluge.details.OptionsTab.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Deluge.details.OptionsTab.superclass.initComponent.call(this);

		this.fieldsets = {}, this.fields = {};
		this.optionsManager = new Deluge.MultiOptionsManager({
			options: {
				'max_download_speed': -1,
				'max_upload_speed': -1,
				'max_connections': -1,
				'max_upload_slots': -1,
				'auto_managed': false,
				'stop_at_ratio': false,
				'stop_ratio': 2.0,
				'remove_at_ratio': false,
				'move_completed': false,
                'move_completed_path': '',
				'private': false,
				'prioritize_first_last': false
			}
		});

		/*
		 * Bandwidth Options
		 */
		this.fieldsets.bandwidth = this.add({
			xtype: 'fieldset',
			defaultType: 'spinnerfield',
			bodyStyle: 'padding: 5px',

			layout: 'table',
			layoutConfig: {columns: 3},
			labelWidth: 150,

			style: 'margin-left: 10px; margin-right: 5px; padding: 5px',
			title: _('Bandwidth'),
			width: 250
		});

		/*
		 * Max Download Speed
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Download Speed'),
			forId: 'max_download_speed',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_download_speed = this.fieldsets.bandwidth.add({
			id: 'max_download_speed',
			name: 'max_download_speed',
			width: 70,
			strategy: {
				xtype: 'number',
				decimalPrecision: 1,
				minValue: -1,
				maxValue: 99999
			}
		});
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('KiB/s'),
			style: 'margin-left: 10px'
		});

		/*
		 * Max Upload Speed
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Upload Speed'),
			forId: 'max_upload_speed',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_upload_speed = this.fieldsets.bandwidth.add({
			id: 'max_upload_speed',
			name: 'max_upload_speed',
			width: 70,
			value: -1,
			strategy: {
				xtype: 'number',
				decimalPrecision: 1,
				minValue: -1,
				maxValue: 99999
			}
		});
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('KiB/s'),
			style: 'margin-left: 10px'
		});

		/*
		 * Max Connections
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Connections'),
			forId: 'max_connections',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_connections = this.fieldsets.bandwidth.add({
			id: 'max_connections',
			name: 'max_connections',
			width: 70,
			value: -1,
			strategy: {
				xtype: 'number',
				decimalPrecision: 0,
				minValue: -1,
				maxValue: 99999
			},
			colspan: 2
		});

		/*
		 * Max Upload Slots
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Upload Slots'),
			forId: 'max_upload_slots',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_upload_slots = this.fieldsets.bandwidth.add({
			id: 'max_upload_slots',
			name: 'max_upload_slots',
			width: 70,
			value: -1,
			strategy: {
				xtype: 'number',
				decimalPrecision: 0,
				minValue: -1,
				maxValue: 99999
			},
			colspan: 2
		});

		/*
		 * Queue Options
		 */
		this.fieldsets.queue = this.add({
			xtype: 'fieldset',
			title: _('Queue'),
			style: 'margin-left: 5px; margin-right: 5px; padding: 5px',
			width: 210,

			layout: 'table',
			layoutConfig: {columns: 2},
			labelWidth: 0,

			defaults: {
				fieldLabel: '',
				labelSeparator: ''
			}
		});

		this.fields.auto_managed = this.fieldsets.queue.add({
			xtype: 'checkbox',
			fieldLabel: '',
			labelSeparator: '',
			name: 'is_auto_managed',
			boxLabel: _('Auto Managed'),
			width: 200,
			colspan: 2
		});

		this.fields.stop_at_ratio = this.fieldsets.queue.add({
			fieldLabel: '',
			labelSeparator: '',
			id: 'stop_at_ratio',
			width: 120,
			boxLabel: _('Stop seed at ratio'),
			handler: this.onStopRatioChecked,
			scope: this
		});

		this.fields.stop_ratio = this.fieldsets.queue.add({
			xtype: 'spinnerfield',
			id: 'stop_ratio',
			name: 'stop_ratio',
			disabled: true,
			width: 50,
			value: 2.0,
			strategy: {
				xtype: 'number',
				minValue: -1,
				maxValue: 99999,
				incrementValue: 0.1,
				alternateIncrementValue: 1,
				decimalPrecision: 1
			}
		});

		this.fields.remove_at_ratio = this.fieldsets.queue.add({
			fieldLabel: '',
			labelSeparator: '',
			id: 'remove_at_ratio',
			ctCls: 'x-deluge-indent-checkbox',
			bodyStyle: 'padding-left: 10px',
			boxLabel: _('Remove at ratio'),
			disabled: true,
			colspan: 2
		});

		this.fields.move_completed = this.fieldsets.queue.add({
			fieldLabel: '',
			labelSeparator: '',
			id: 'move_completed',
			boxLabel: _('Move Completed'),
			colspan: 2,
            handler: this.onMoveCompletedChecked,
            scope: this
		});

        this.fields.move_completed_path = this.fieldsets.queue.add({
            xtype: 'textfield',
            fieldLabel: '',
            id: 'move_completed_path',
            colspan: 3,
			bodyStyle: 'margin-left: 20px',
            width: 180,
            disabled: true
        });


		/*
		 * General Options
		 */
		this.rightColumn =  this.add({
			border: false,
			autoHeight: true,
			style: 'margin-left: 5px',
			width: 210
		});

		this.fieldsets.general = this.rightColumn.add({
			xtype: 'fieldset',
			autoHeight: true,
			defaultType: 'checkbox',
			title: _('General'),
			layout: 'form'
		});

		this.fields['private'] = this.fieldsets.general.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Private'),
			id: 'private',
			disabled: true
		});

		this.fields.prioritize_first_last = this.fieldsets.general.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Prioritize First/Last'),
			id: 'prioritize_first_last'
		});

		// Bind the fields so the options manager can manage them.
		for (var id in this.fields) {
			this.optionsManager.bind(id, this.fields[id]);
		}

		/*
		 * Buttons
		 */
		this.buttonPanel = this.rightColumn.add({
			layout: 'hbox',
			xtype: 'panel',
			border: false
		});

		/*
		 * Edit Trackers button
		 */
		this.buttonPanel.add({
			id: 'edit_trackers',
			xtype: 'button',
			text: _('Edit Trackers'),
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-edit-trackers',
			border: false,
			width: 100,
			handler: this.onEditTrackers,
			scope: this
		});

		/*
		 * Apply button
		 */
		this.buttonPanel.add({
			id: 'apply',
			xtype: 'button',
			text: _('Apply'),
			style: 'margin-left: 10px;',
			border: false,
			width: 100,
			handler: this.onApply,
			scope: this
		});
	},

	onRender: function(ct, position) {
		Deluge.details.OptionsTab.superclass.onRender.call(this, ct, position);

		// This is another hack I think, so keep an eye out here when upgrading.
		this.layout = new Ext.layout.ColumnLayout();
		this.layout.setContainer(this);
		this.doLayout();
	},

	clear: function() {
		if (this.torrentId == null) return;
		this.torrentId = null;
		this.optionsManager.changeId(null);
	},

	reset: function() {
		if (this.torrentId) this.optionsManager.reset();
	},

	update: function(torrentId) {
		if (this.torrentId && !torrentId) this.clear(); // we want to clear the pane if we get a null torrent torrentIds

		if (!torrentId) return; // we don't care about null torrentIds

		if (this.torrentId != torrentId) {
			this.torrentId = torrentId;
			this.optionsManager.changeId(torrentId);
		}
		deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Options, {
			success: this.onRequestComplete,
			scope: this
		});
	},

	onApply: function() {
		var changed = this.optionsManager.getDirty();
		if (!Ext.isEmpty(changed['prioritize_first_last'])) {
			var value = changed['prioritize_first_last'];
			deluge.client.core.set_torrent_prioritize_first_last(this.torrentId, value, {
				success: function() {
					this.optionsManager.set('prioritize_first_last', value);
				},
				scope: this
			});
		}
		deluge.client.core.set_torrent_options([this.torrentId], changed, {
			success: function() {
				this.optionsManager.commit();
			},
			scope: this
		});
	},

	onEditTrackers: function() {
		deluge.editTrackers.show();
	},

    onMoveCompletedChecked: function(checkbox, checked) {
        this.fields.move_completed_path.setDisabled(!checked);

        if (!checked) return;
        this.fields.move_completed_path.focus();
    },

	onStopRatioChecked: function(checkbox, checked) {
		this.fields.remove_at_ratio.setDisabled(!checked);
		this.fields.stop_ratio.setDisabled(!checked);
	},

	onRequestComplete: function(torrent, options) {
		this.fields['private'].setValue(torrent['private']);
		this.fields['private'].setDisabled(true);
		delete torrent['private'];
		torrent['auto_managed'] = torrent['is_auto_managed'];
		this.optionsManager.setDefault(torrent);
		var stop_at_ratio = this.optionsManager.get('stop_at_ratio');
		this.fields.remove_at_ratio.setDisabled(!stop_at_ratio);
		this.fields.stop_ratio.setDisabled(!stop_at_ratio);
        this.fields.move_completed_path.setDisabled(!this.optionsManager.get('move_completed'));
	}
});
/*!
 * Deluge.details.PeersTab.js
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

(function() {
	function flagRenderer(value) {
		if (!value.replace(' ', '').replace(' ', '')){
            return '';
        }
		return String.format('<img src="{0}flag/{1}" />', deluge.config.base, value);
	}
	function peerAddressRenderer(value, p, record) {
		var seed = (record.data['seed'] == 1024) ? 'x-deluge-seed' : 'x-deluge-peer';
		// Modify display of IPv6 to include brackets
		var peer_ip = value.split(':');
		if (peer_ip.length > 2) {
			var port = peer_ip.pop();
			var ip = peer_ip.join(":");
			value = "[" + ip + "]:" + port;
		}
		return String.format('<div class="{0}">{1}</div>', seed, value);
	}
	function peerProgressRenderer(value) {
		var progress = (value * 100).toFixed(0);
		return Deluge.progressBar(progress, this.width - 8, progress + '%');
	}

	Deluge.details.PeersTab = Ext.extend(Ext.grid.GridPanel, {

		// fast way to figure out if we have a peer already.
		peers: {},

		constructor: function(config) {
			config = Ext.apply({
				title: _('Peers'),
				cls: 'x-deluge-peers',
				store: new Ext.data.Store({
					reader: new Ext.data.JsonReader({
						idProperty: 'ip',
						root: 'peers'
					}, Deluge.data.Peer)
				}),
				columns: [{
					header: '&nbsp;',
					width: 30,
					sortable: true,
					renderer: flagRenderer,
					dataIndex: 'country'
				}, {
					header: 'Address',
					width: 125,
					sortable: true,
					renderer: peerAddressRenderer,
					dataIndex: 'ip'
				}, {
					header: 'Client',
					width: 125,
					sortable: true,
					renderer: fplain,
					dataIndex: 'client'
				}, {
					header: 'Progress',
					width: 150,
					sortable: true,
					renderer: peerProgressRenderer,
					dataIndex: 'progress'
				}, {
					header: 'Down Speed',
					width: 100,
					sortable: true,
					renderer: fspeed,
					dataIndex: 'down_speed'
				}, {
					header: 'Up Speed',
					width: 100,
					sortable: true,
					renderer: fspeed,
					dataIndex: 'up_speed'
				}],
				stripeRows: true,
				deferredRender:false,
				autoScroll:true
			}, config);
			Deluge.details.PeersTab.superclass.constructor.call(this, config);
		},

		clear: function() {
			this.getStore().removeAll();
			this.peers = {};
		},

		update: function(torrentId) {
			deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Peers, {
				success: this.onRequestComplete,
				scope: this
			});
		},

		onRequestComplete: function(torrent, options) {
			if (!torrent) return;

			var store = this.getStore();
			var newPeers = [];
			var addresses = {};

			// Go through the peers updating and creating peer records
			Ext.each(torrent.peers, function(peer) {
				if (this.peers[peer.ip]) {
                    var record = store.getById(peer.ip);
                    record.beginEdit();
                    for (var k in peer) {
                        if (record.get(k) != peer[k]) {
                            record.set(k, peer[k]);
                        }
                    }
                    record.endEdit();
				} else {
					this.peers[peer.ip] = 1;
					newPeers.push(new Deluge.data.Peer(peer, peer.ip));
				}
				addresses[peer.ip] = 1;
			}, this);
			store.add(newPeers);

			// Remove any peers that shouldn't be left in the store
			store.each(function(record) {
				if (!addresses[record.id]) {
					store.remove(record);
					delete this.peers[record.id];
				}
			}, this);
			store.commitChanges();

			var sortState = store.getSortState();
			if (!sortState) return;
			store.sort(sortState.field, sortState.direction);
		}
	});
})();
/*!
 * Deluge.details.StatusTab.js
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
Ext.ns('Deluge.details');

/**
 * @class Deluge.details.StatusTab
 * @extends Ext.Panel
 */
Deluge.details.StatusTab = Ext.extend(Ext.Panel, {
	title: _('Status'),
	autoScroll: true,
	
	onRender: function(ct, position) {
		Deluge.details.StatusTab.superclass.onRender.call(this, ct, position);
		
		this.progressBar = this.add({
			xtype: 'progress',
			cls: 'x-deluge-status-progressbar'
		});
		
		this.status = this.add({
			cls: 'x-deluge-status',
			id: 'deluge-details-status',
			
			border: false,
			width: 1000,
			listeners: {
				'render': {
					fn: function(panel) {
						panel.load({
							url: deluge.config.base + 'render/tab_status.html',
							text: _('Loading') + '...'
						});
						panel.getUpdater().on('update', this.onPanelUpdate, this);
					},
					scope: this
				}
			}
		});
	},
	
	clear: function() {
		this.progressBar.updateProgress(0, ' ');
		for (var k in this.fields) {
			this.fields[k].innerHTML = '';
		}
	},
	
	update: function(torrentId) {
		if (!this.fields) this.getFields();
		deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Status, {
			success: this.onRequestComplete,
			scope: this
		});
	},
	
	onPanelUpdate: function(el, response) {
		this.fields = {};
		Ext.each(Ext.query('dd', this.status.body.dom), function(field) {
			this.fields[field.className] = field;
		}, this);
	},
	
	onRequestComplete: function(status) {
		seeders = status.total_seeds > -1 ? status.num_seeds + ' (' + status.total_seeds + ')' : status.num_seeds
		peers = status.total_peers > -1 ? status.num_peers + ' (' + status.total_peers + ')' : status.num_peers
		var data = {
			downloaded: fsize(status.total_done, true),
			uploaded: fsize(status.total_uploaded, true),
			share: (status.ratio == -1) ? '&infin;' : status.ratio.toFixed(3),
			announce: ftime(status.next_announce),
			tracker_status: status.tracker_status,
			downspeed: (status.download_payload_rate) ? fspeed(status.download_payload_rate) : '0.0 KiB/s',
			upspeed: (status.upload_payload_rate) ? fspeed(status.upload_payload_rate) : '0.0 KiB/s',
			eta: ftime(status.eta),
			pieces: status.num_pieces + ' (' + fsize(status.piece_length) + ')',
			seeders: seeders,
			peers: peers,
			avail: status.distributed_copies.toFixed(3),
			active_time: ftime(status.active_time),
			seeding_time: ftime(status.seeding_time),
			seed_rank: status.seed_rank,
			time_added: fdate(status.time_added)
		}
		data.auto_managed = _((status.is_auto_managed) ? 'True' : 'False');

		data.downloaded += ' (' + ((status.total_payload_download) ? fsize(status.total_payload_download) : '0.0 KiB') + ')';
		data.uploaded += ' (' + ((status.total_payload_upload) ? fsize(status.total_payload_upload): '0.0 KiB') + ')';
		
		for (var field in this.fields) {
			this.fields[field].innerHTML = data[field];
		}
		var text = status.state + ' ' + status.progress.toFixed(2) + '%';
		this.progressBar.updateProgress(status.progress / 100.0, text);
	}
});
/*!
 * Deluge.add.Window.js
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
 * @class Deluge.add.Window
 * @extends Ext.Window
 * Base class for an add Window
 */
Deluge.add.Window = Ext.extend(Ext.Window, {
    initComponent: function() {
        Deluge.add.Window.superclass.initComponent.call(this);
        this.addEvents(
            'beforeadd',
            'add',
            'addfailed'
        );
    },

	/**
	 * Create an id for the torrent before we have any info about it.
	 */
    createTorrentId: function() {
        return new Date().getTime();
    }
});
/*!
 * Deluge.add.AddWindow.js
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

Deluge.add.AddWindow = Ext.extend(Deluge.add.Window, {

	title: _('Add Torrents'),
	layout: 'border',
	width: 470,
	height: 450,
	bodyStyle: 'padding: 10px 5px;',
	buttonAlign: 'right',
	closeAction: 'hide',
	closable: true,
	plain: true,
	iconCls: 'x-deluge-add-window-icon',

	initComponent: function() {
		Deluge.add.AddWindow.superclass.initComponent.call(this);

		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Add'), this.onAddClick, this);

		function torrentRenderer(value, p, r) {
			if (r.data['info_hash']) {
				return String.format('<div class="x-deluge-add-torrent-name">{0}</div>', value);
			} else {
				return String.format('<div class="x-deluge-add-torrent-name-loading">{0}</div>', value);
			}
		}

		this.list = new Ext.list.ListView({
			store: new Ext.data.SimpleStore({
				fields: [
					{name: 'info_hash', mapping: 1},
					{name: 'text', mapping: 2}
				],
				id: 0
			}),
			columns: [{
				id: 'torrent',
				width: 150,
				sortable: true,
				renderer: torrentRenderer,
				dataIndex: 'text'
			}],
			stripeRows: true,
			singleSelect: true,
			listeners: {
				'selectionchange': {
					fn: this.onSelect,
					scope: this
				}
			},
			hideHeaders: true,
			autoExpandColumn: 'torrent',
			height: '100%',
			autoScroll: true
		});

		this.add({
			region: 'center',
			items: [this.list],
			margins: '5 5 5 5',
			bbar: new Ext.Toolbar({
				items: [{
					iconCls: 'x-deluge-add-file',
					text: _('File'),
					handler: this.onFile,
					scope: this
				}, {
					text: _('Url'),
					iconCls: 'icon-add-url',
					handler: this.onUrl,
					scope: this
				}, {
					text: _('Infohash'),
					iconCls: 'icon-add-magnet',
					hidden: true,
					disabled: true
				}, '->', {
					text: _('Remove'),
					iconCls: 'icon-remove',
					handler: this.onRemove,
					scope: this
				}]
			})
		});

		this.optionsPanel = this.add(new Deluge.add.OptionsPanel());
		this.on('hide', this.onHide, this);
		this.on('show', this.onShow, this);
	},

	clear: function() {
		this.list.getStore().removeAll();
		this.optionsPanel.clear();
	},

	onAddClick: function() {
		var torrents = [];
		if (!this.list) return;
		this.list.getStore().each(function(r) {
			var id = r.get('info_hash');
			torrents.push({
				path: this.optionsPanel.getFilename(id),
				options: this.optionsPanel.getOptions(id)
			});
		}, this);

		deluge.client.web.add_torrents(torrents, {
			success: function(result) {
			}
		})
		this.clear();
		this.hide();
	},

	onCancelClick: function() {
		this.clear();
		this.hide();
	},

	onFile: function() {
		if (!this.file) this.file = new Deluge.add.FileWindow();
		this.file.show();
	},

	onHide: function() {
		this.optionsPanel.setActiveTab(0);
		this.optionsPanel.files.setDisabled(true);
		this.optionsPanel.form.setDisabled(true);
	},

	onRemove: function() {
		if (!this.list.getSelectionCount()) return;
		var torrent = this.list.getSelectedRecords()[0];
		this.list.getStore().remove(torrent);
		this.optionsPanel.clear();

		if (this.torrents && this.torrents[torrent.id]) delete this.torrents[torrent.id];
	},

	onSelect: function(list, selections) {
		if (selections.length) {
			var record = this.list.getRecord(selections[0]);
			this.optionsPanel.setTorrent(record.get('info_hash'));
		} else {
			this.optionsPanel.files.setDisabled(true);
			this.optionsPanel.form.setDisabled(true);
		}
	},

	onShow: function() {
		if (!this.url) {
			this.url = new Deluge.add.UrlWindow();
			this.url.on('beforeadd', this.onTorrentBeforeAdd, this);
			this.url.on('add', this.onTorrentAdd, this);
			this.url.on('addfailed', this.onTorrentAddFailed, this);
		}

		if (!this.file) {
			this.file = new Deluge.add.FileWindow();
			this.file.on('beforeadd', this.onTorrentBeforeAdd, this);
			this.file.on('add', this.onTorrentAdd, this);
			this.file.on('addfailed', this.onTorrentAddFailed, this);
		}

		this.optionsPanel.form.getDefaults();
	},

	onTorrentBeforeAdd: function(torrentId, text) {
		var store = this.list.getStore();
		store.loadData([[torrentId, null, text]], true);
	},

	onTorrentAdd: function(torrentId, info) {
		var r = this.list.getStore().getById(torrentId);
		if (!info) {
			Ext.MessageBox.show({
				title: _('Error'),
				msg: _('Not a valid torrent'),
				buttons: Ext.MessageBox.OK,
				modal: false,
				icon: Ext.MessageBox.ERROR,
				iconCls: 'x-deluge-icon-error'
			});
			this.list.getStore().remove(r);
		} else {
			r.set('info_hash', info['info_hash']);
			r.set('text', info['name']);
			this.list.getStore().commitChanges();
			this.optionsPanel.addTorrent(info);
			this.list.select(r);
		}
	},

	onTorrentAddFailed: function(torrentId) {
		var store = this.list.getStore();
		var torrentRecord = store.getById(torrentId);
		if (torrentRecord) {
			store.remove(torrentRecord);
		}
	},

	onUrl: function(button, event) {
		this.url.show();
	}
});
/*!
 * Deluge.add.File.js
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
 * @class Deluge.add.FileWindow
 * @extends Deluge.add.Window
 */
Deluge.add.FileWindow = Ext.extend(Deluge.add.Window, {

	title: _('Add from File'),
	layout: 'fit',
	width: 350,
	height: 115,
	modal: true,
	plain: true,
	buttonAlign: 'center',
	closeAction: 'hide',
	bodyStyle: 'padding: 10px 5px;',
	iconCls: 'x-deluge-add-file',

	initComponent: function() {
		Deluge.add.FileWindow.superclass.initComponent.call(this);
		this.addButton(_('Add'), this.onAddClick, this);

		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			labelWidth: 35,
			autoHeight: true,
			fileUpload: true,
			items: [{
				xtype: 'fileuploadfield',
				id: 'torrentFile',
				width: 280,
				height: 24,
				emptyText: _('Select a torrent'),
				fieldLabel: _('File'),
				name: 'file',
				buttonCfg: {
					text: _('Browse') + '...'
				}
			}]
		});
	},

	// private
	onAddClick: function(field, e) {
		if (this.form.getForm().isValid()) {
			this.torrentId = this.createTorrentId();
			this.form.getForm().submit({
				url: deluge.config.base + 'upload',
				waitMsg: _('Uploading your torrent...'),
				failure: this.onUploadFailure,
				success: this.onUploadSuccess,
				scope: this
			});
			var name = this.form.getForm().findField('torrentFile').value;
			name = name.split('\\').slice(-1)[0];
			this.fireEvent('beforeadd', this.torrentId, name);
		}
	},

	// private
	onGotInfo: function(info, obj, response, request) {
		info['filename'] = request.options.filename;
		this.fireEvent('add', this.torrentId, info);
	},

	// private
	onUploadFailure: function(form, action) {
		this.hide();
		Ext.MessageBox.show({
			title: _('Error'),
			msg: _('Failed to upload torrent'),
			buttons: Ext.MessageBox.OK,
			modal: false,
			icon: Ext.MessageBox.ERROR,
			iconCls: 'x-deluge-icon-error'
		});
		this.fireEvent('addfailed', this.torrentId);
	},

	// private
	onUploadSuccess: function(fp, upload) {
		this.hide();
		if (upload.result.success) {
			var filename = upload.result.files[0];
			this.form.getForm().findField('torrentFile').setValue('');
			deluge.client.web.get_torrent_info(filename, {
				success: this.onGotInfo,
				scope: this,
				filename: filename
			});
		}
	}
});
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

	autoScroll:  false,
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
				return '<div rel="chkbox" class="x-grid3-check-col'+(v?'-on':'')+'"> </div>';
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
		var el = new Ext.Element(e.target);
		if (el.getAttribute('rel') == 'chkbox') {
			this.setDownload(node, !node.attributes.download);
		}
	}
});
/*!
 * Deluge.add.Infohash.js
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
Ext.namespace('Ext.deluge.add');
/*!
 * Deluge.add.OptionsPanel.js
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

Deluge.add.OptionsPanel = Ext.extend(Ext.TabPanel, {

	torrents: {},

	// layout options
	region: 'south',
	margins: '5 5 5 5',
	activeTab: 0,
	height: 265,

	initComponent: function() {
		Deluge.add.OptionsPanel.superclass.initComponent.call(this);
		this.files = this.add(new Deluge.add.FilesTab());
		this.form = this.add(new Deluge.add.OptionsTab());

		this.files.on('fileschecked', this.onFilesChecked, this);
	},

	addTorrent: function(torrent) {
		this.torrents[torrent['info_hash']] = torrent;
		var fileIndexes = {};
		this.walkFileTree(torrent['files_tree'], function(filename, type, entry, parent) {
			if (type != 'file') return;
			fileIndexes[entry.index] = entry.download;
		}, this);

		var priorities = [];
		Ext.each(Ext.keys(fileIndexes), function(index) {
			priorities[index] = fileIndexes[index];
		});

		var oldId = this.form.optionsManager.changeId(torrent['info_hash'], true);
		this.form.optionsManager.setDefault('file_priorities', priorities);
		this.form.optionsManager.changeId(oldId, true);
	},

	clear: function() {
		this.files.clearFiles();
		this.form.optionsManager.resetAll();
	},

	getFilename: function(torrentId) {
		return this.torrents[torrentId]['filename'];
	},

	getOptions: function(torrentId) {
		var oldId = this.form.optionsManager.changeId(torrentId, true);
		var options = this.form.optionsManager.get();
		this.form.optionsManager.changeId(oldId, true);
		Ext.each(options['file_priorities'], function(priority, index) {
			options['file_priorities'][index] = (priority) ? 1 : 0;
		});
		return options;
	},

	setTorrent: function(torrentId) {
		if (!torrentId) return;

		this.torrentId = torrentId;
		this.form.optionsManager.changeId(torrentId);

		this.files.clearFiles();
		var root = this.files.getRootNode();
		var priorities = this.form.optionsManager.get('file_priorities');

		this.form.setDisabled(false);

		if (this.torrents[torrentId]['files_tree']) {
			this.walkFileTree(this.torrents[torrentId]['files_tree'], function(filename, type, entry, parentNode) {
				var node = new Ext.tree.TreeNode({
					download:  (entry.index) ? priorities[entry.index] : true,
					filename:  filename,
					fileindex: entry.index,
					leaf:      type != 'dir',
					size:      entry.length
				});
				parentNode.appendChild(node);
				if (type == 'dir') return node;
			}, this, root);
			root.firstChild.expand();
			this.files.setDisabled(false);
			this.files.show();
		} else {
			// Files tab is empty so show options tab
			this.form.show();
			this.files.setDisabled(true);
		}

	},

	walkFileTree: function(files, callback, scope, parentNode) {
		for (var filename in files.contents) {
			var entry = files.contents[filename];
			var type = entry.type;

			if (scope) {
				var ret = callback.apply(scope, [filename, type, entry, parentNode]);
			} else {
				var ret = callback(filename, type, entry, parentNode);
			}

			if (type == 'dir') this.walkFileTree(entry, callback, scope, ret);
		}
	},

	onFilesChecked: function(nodes, newValue, oldValue) {
		if (this.form.optionsManager.get('compact_allocation')) {
			Ext.Msg.show({
				title: _('Unable to set file priority!'),
				msg:   _('File prioritization is unavailable when using Compact allocation. Would you like to switch to Full allocation?'),
				buttons: Ext.Msg.YESNO,
				fn: function(result) {
					if (result == 'yes') {
						this.form.optionsManager.update('compact_allocation', false);
						Ext.each(nodes, function(node) {
							if (node.attributes.fileindex < 0) return;
							var priorities = this.form.optionsManager.get('file_priorities');
							priorities[node.attributes.fileindex] = newValue;
							this.form.optionsManager.update('file_priorities', priorities);
						}, this);
					} else {
						this.files.setDownload(nodes[0], oldValue, true);
					}
				},
				scope: this,
				icon: Ext.MessageBox.QUESTION
			});
		} else {
			Ext.each(nodes, function(node) {
				if (node.attributes.fileindex < 0) return;
				var priorities = this.form.optionsManager.get('file_priorities');
				priorities[node.attributes.fileindex] = newValue;
				this.form.optionsManager.update('file_priorities', priorities);
			}, this);
		}
	}
});
/*!
 * Deluge.add.OptionsPanel.js
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
 * @class Deluge.add.OptionsTab
 * @extends Ext.form.FormPanel
 */
Deluge.add.OptionsTab = Ext.extend(Ext.form.FormPanel, {

	title:  _('Options'),
	height: 170,

	border:     false,
	bodyStyle:  'padding: 5px',
	disabled:   true,
	labelWidth: 1,

	initComponent: function() {
		Deluge.add.OptionsTab.superclass.initComponent.call(this);

		this.optionsManager = new Deluge.MultiOptionsManager();

		var fieldset = this.add({
			xtype: 'fieldset',
			title: _('Download Location'),
			border: false,
			autoHeight: true,
			defaultType: 'textfield',
			labelWidth: 1,
			fieldLabel: '',
			style: 'padding-bottom: 5px; margin-bottom: 0px;'
		});
        this.optionsManager.bind('download_location', fieldset.add({
            fieldLabel: '',
            name: 'download_location',
            width: 400,
            labelSeparator: ''
        }));

        var fieldset = this.add({
            xtype: 'fieldset',
            title: _('Move Completed Location'),
            border: false,
            autoHeight: true,
            defaultType: 'togglefield',
            labelWidth: 1,
            fieldLabel: '',
            style: 'padding-bottom: 5px; margin-bottom: 0px;'
        });
        var field = fieldset.add({
            fieldLabel: '',
            name: 'move_completed_path',
            width: 425
        });
        this.optionsManager.bind('move_completed', field.toggle)
        this.optionsManager.bind('move_completed_path', field.input)

		var panel = this.add({
			border: false,
			layout: 'column',
			defaultType: 'fieldset'
		});
		fieldset = panel.add({
			title: _('Allocation'),
			border: false,
			autoHeight: true,
			defaultType: 'radio'
		});

		this.optionsManager.bind('compact_allocation', fieldset.add({
			xtype: 'radiogroup',
			columns: 1,
			vertical: true,
			labelSeparator: '',
			width: 80,
			items: [{
				name: 'compact_allocation',
				value: false,
				inputValue: false,
				boxLabel: _('Full'),
				fieldLabel: '',
				labelSeparator: ''
			}, {
				name: 'compact_allocation',
				value: true,
				inputValue: true,
				boxLabel: _('Compact'),
				fieldLabel: '',
				labelSeparator: ''
			}]
		}));

		fieldset = panel.add({
			title: _('Bandwidth'),
			border: false,
			autoHeight: true,
			bodyStyle: 'margin-left: 7px',
			labelWidth: 105,
			width: 200,
			defaultType: 'spinnerfield'
		});
		this.optionsManager.bind('max_download_speed', fieldset.add({
			fieldLabel: _('Max Down Speed'),
			name: 'max_download_speed',
			width: 60
		}));
		this.optionsManager.bind('max_upload_speed', fieldset.add({
			fieldLabel: _('Max Up Speed'),
			name: 'max_upload_speed',
			width: 60
		}));
		this.optionsManager.bind('max_connections', fieldset.add({
			fieldLabel: _('Max Connections'),
			name: 'max_connections',
			width: 60
		}));
		this.optionsManager.bind('max_upload_slots', fieldset.add({
			fieldLabel: _('Max Upload Slots'),
			name: 'max_upload_slots',
			width: 60
		}));

		fieldset = panel.add({
			title: _('General'),
			border: false,
			autoHeight: true,
			defaultType: 'checkbox'
		});
		this.optionsManager.bind('add_paused', fieldset.add({
			name: 'add_paused',
			boxLabel: _('Add In Paused State'),
			fieldLabel: '',
			labelSeparator: ''
		}));
		this.optionsManager.bind('prioritize_first_last_pieces', fieldset.add({
			name: 'prioritize_first_last_pieces',
			boxLabel: _('Prioritize First/Last Pieces'),
			fieldLabel: '',
			labelSeparator: ''
		}));
	},

	getDefaults: function() {
		var keys = ['add_paused','compact_allocation','download_location',
		'max_connections_per_torrent','max_download_speed_per_torrent',
        'move_completed', 'move_completed_path',
		'max_upload_slots_per_torrent','max_upload_speed_per_torrent',
		'prioritize_first_last_pieces'];

		deluge.client.core.get_config_values(keys, {
			success: function(config) {
				var options = {
					'file_priorities': [],
					'add_paused': config.add_paused,
					'compact_allocation': config.compact_allocation,
					'download_location': config.download_location,
                    'move_completed': config.move_completed,
                    'move_completed_path': config.move_completed_path,
					'max_connections': config.max_connections_per_torrent,
					'max_download_speed': config.max_download_speed_per_torrent,
					'max_upload_slots': config.max_upload_slots_per_torrent,
					'max_upload_speed': config.max_upload_speed_per_torrent,
					'prioritize_first_last_pieces': config.prioritize_first_last_pieces
				}
				this.optionsManager.options = options;
				this.optionsManager.resetAll();
			},
			scope: this
		});
	}
});
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

        if (url.indexOf('magnet:?') == 0 && url.indexOf('xt=urn:btih') > -1) {
            deluge.client.web.get_magnet_info(url, {
                success: this.onGotInfo,
                scope: this,
                filename: url,
                torrentId: torrentId
            });
        } else {
            deluge.client.web.download_torrent_from_url(url, cookies, {
                success: this.onDownload,
                failure: this.onDownloadFailed,
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

    onDownloadFailed: function(obj, resp, req) {
        Ext.MessageBox.show({
            title: _('Error'),
            msg: _('Failed to download torrent'),
            buttons: Ext.MessageBox.OK,
            modal: false,
            icon: Ext.MessageBox.ERROR,
            iconCls: 'x-deluge-icon-error'
        });
        this.fireEvent('addfailed', req.options.torrentId);
    },

    onGotInfo: function(info, obj, response, request) {
        info['filename'] = request.options.filename;
        this.fireEvent('add', request.options.torrentId, info);
    }
});
/*!
 * Deluge.preferences.BandwidthPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Bandwidth
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Bandwidth = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Bandwidth'),
			layout: 'form',
			labelWidth: 10
		}, config);
		Deluge.preferences.Bandwidth.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Deluge.preferences.Bandwidth.superclass.initComponent.call(this);
		
		var om = deluge.preferences.getOptionsManager();
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Global Bandwidth Usage'),
			labelWidth: 200,
			defaultType: 'spinnerfield',
			defaults: {
				minValue: -1,
				maxValue: 99999
			},
			style: 'margin-bottom: 0px; padding-bottom: 0px;',
			autoHeight: true
		});
		om.bind('max_connections_global', fieldset.add({
			name: 'max_connections_global',
			fieldLabel: _('Maximum Connections'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_upload_slots_global', fieldset.add({
			name: 'max_upload_slots_global',
			fieldLabel: _('Maximum Upload Slots'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_download_speed', fieldset.add({
			name: 'max_download_speed',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 80,
			value: -1.0,
			decimalPrecision: 1
		}));
		om.bind('max_upload_speed', fieldset.add({
			name: 'max_upload_speed',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 80,
			value: -1.0,
			decimalPrecision: 1
		}));
		om.bind('max_half_open_connections', fieldset.add({
			name: 'max_half_open_connections',
			fieldLabel: _('Maximum Half-Open Connections'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_connections_per_second', fieldset.add({
			name: 'max_connections_per_second',
			fieldLabel: _('Maximum Connection Attempts per Second'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: '',
			defaultType: 'checkbox',
			style: 'padding-top: 0px; padding-bottom: 5px; margin-top: 0px; margin-bottom: 0px;',
			autoHeight: true
		});
		om.bind('ignore_limits_on_local_network', fieldset.add({
			name: 'ignore_limits_on_local_network',
			height: 22,
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Ignore limits on local network')
		}));
		om.bind('rate_limit_ip_overhead', fieldset.add({
			name: 'rate_limit_ip_overhead',
			height: 22,
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Rate limit IP overhead')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Per Torrent Bandwidth Usage'),
			style: 'margin-bottom: 0px; padding-bottom: 0px;',
			defaultType: 'spinnerfield',
			labelWidth: 200,
			defaults: {
				minValue: -1,
				maxValue: 99999
			},
			autoHeight: true
		});
		om.bind('max_connections_per_torrent', fieldset.add({
			name: 'max_connections_per_torrent',
			fieldLabel: _('Maximum Connections'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_upload_slots_per_torrent', fieldset.add({
			name: 'max_upload_slots_per_torrent',
			fieldLabel: _('Maximum Upload Slots'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_download_speed_per_torrent', fieldset.add({
			name: 'max_download_speed_per_torrent',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_upload_speed_per_torrent', fieldset.add({
			name: 'max_upload_speed_per_torrent',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
	}
});
/*!
 * Deluge.preferences.CachePage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Cache
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Cache = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Cache'),
	layout: 'form',
	
	initComponent: function() {
		Deluge.preferences.Cache.superclass.initComponent.call(this);

		var om = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Settings'),
			autoHeight: true,
			labelWidth: 180,
			defaultType: 'spinnerfield',
			defaults: {
				decimalPrecision: 0,
				minValue: -1,
				maxValue: 999999
			}
		});
		om.bind('cache_size', fieldset.add({
			fieldLabel: _('Cache Size (16 KiB Blocks)'),
			name: 'cache_size',
			width: 60,
			value: 512
		}));
		om.bind('cache_expiry', fieldset.add({
			fieldLabel: _('Cache Expiry (seconds)'),
			name: 'cache_expiry',
			width: 60,
			value: 60
		}));
	}
});
/*!
 * Deluge.preferences.DaemonPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Daemon
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Daemon = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Daemon'),
	layout: 'form',
	
	initComponent: function() {
		Deluge.preferences.Daemon.superclass.initComponent.call(this);

		var om = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Port'),
			autoHeight: true,
			defaultType: 'spinnerfield'
		});
		om.bind('daemon_port', fieldset.add({
			fieldLabel: _('Daemon port'),
			name: 'daemon_port',
			value: 58846,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Connections'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		om.bind('allow_remote', fieldset.add({
			fieldLabel: '',
			height: 22,
			labelSeparator: '',
			boxLabel: _('Allow Remote Connections'),
			name: 'allow_remote'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Other'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		om.bind('new_release_check', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 40,
			boxLabel: _('Periodically check the website for new releases'),
			id: 'new_release_check'
		}));
	}
});
/*!
 * Deluge.preferences.DownloadsPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Downloads
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Downloads = Ext.extend(Ext.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Downloads'),
			layout: 'form',
			autoHeight: true,
			width: 320
		}, config);
		Deluge.preferences.Downloads.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Deluge.preferences.Downloads.superclass.initComponent.call(this);

		var optMan = deluge.preferences.getOptionsManager();
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Folders'),
			labelWidth: 150,
			defaultType: 'togglefield',
			autoHeight: true,
			labelAlign: 'top',
			width: 300,
			style: 'margin-bottom: 5px; padding-bottom: 5px;'
		});

		optMan.bind('download_location', fieldset.add({
			xtype: 'textfield',
			name: 'download_location',
			fieldLabel: _('Download to'),
			width: 280
		}));

		var field = fieldset.add({
			name: 'move_completed_path',
			fieldLabel: _('Move completed to'),
			width: 280
		});
		optMan.bind('move_completed', field.toggle);
		optMan.bind('move_completed_path', field.input);

		field = fieldset.add({
			name: 'torrentfiles_location',
			fieldLabel: _('Copy of .torrent files to'),
			width: 280
		});
		optMan.bind('copy_torrent_file', field.toggle);
		optMan.bind('torrentfiles_location', field.input);

		field = fieldset.add({
			name: 'autoadd_location',
			fieldLabel: _('Autoadd .torrent files from'),
			width: 280
		});
		optMan.bind('autoadd_enable', field.toggle);
		optMan.bind('autoadd_location', field.input);
	
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Allocation'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'radiogroup',
			style: 'margin-bottom: 5px; margin-top: 0; padding-bottom: 5px; padding-top: 0;',
			width: 240
		});
		optMan.bind('compact_allocation', fieldset.add({
			name: 'compact_allocation',
			width: 200,
			labelSeparator: '',
			//disabled: true,
			defaults: {
				width: 80,
				height: 22,
				name: 'compact_allocation'
			},
			items: [{
				boxLabel: _('Use Full'),
				inputValue: false
			}, {
				boxLabel: _('Use Compact'),
				inputValue: true
			}]
		}));
	
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Options'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox',
			style: 'margin-bottom: 0; padding-bottom: 0;',
			width: 280
		});
		optMan.bind('prioritize_first_last_pieces', fieldset.add({
			name: 'prioritize_first_last_pieces',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Prioritize first and last pieces of torrent')
		}));
		optMan.bind('add_paused', fieldset.add({
			name: 'add_paused',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Add torrents in Paused state')
		}));
	}
});
/*!
 * Deluge.preferences.EncryptionPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Encryption
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Encryption = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Encryption'),
	
	initComponent: function() {
		Deluge.preferences.Encryption.superclass.initComponent.call(this);

		var optMan = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Settings'),
			autoHeight: true,
			defaultType: 'combo',
			width: 300
		});
		optMan.bind('enc_in_policy', fieldset.add({
			fieldLabel: _('Inbound'),
			mode: 'local',
			width: 150,
			store: new Ext.data.ArrayStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Forced')],
					[1, _('Enabled')],
					[2, _('Disabled')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_out_policy', fieldset.add({
			fieldLabel: _('Outbound'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Forced')],
					[1, _('Enabled')],
					[2, _('Disabled')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_level', fieldset.add({
			fieldLabel: _('Level'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Handshake')],
					[1, _('Full Stream')],
					[2, _('Either')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_prefer_rc4', fieldset.add({
			xtype: 'checkbox',
			name: 'enc_prefer_rc4',
			height: 40,
			hideLabel: true,
			boxLabel: _('Encrypt entire stream')
		}));
	}
});
/*!
 * Deluge.preferences.InstallPluginWindow.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.InstallPluginWindow
 * @extends Ext.Window
 */
Deluge.preferences.InstallPluginWindow = Ext.extend(Ext.Window, {

	title: _('Install Plugin'),
	layout: 'fit',
	height: 115,
	width: 350,
	
	bodyStyle: 'padding: 10px 5px;',
	buttonAlign: 'center',
	closeAction: 'hide',
	iconCls: 'x-deluge-install-plugin',
	modal: true,
	plain: true,

	initComponent: function() {
		Deluge.add.FileWindow.superclass.initComponent.call(this);
		this.addButton(_('Install'), this.onInstall, this);
		
		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			labelWidth: 70,
			autoHeight: true,
			fileUpload: true,
			items: [{
				xtype: 'fileuploadfield',
				width: 240,
				emptyText: _('Select an egg'),
				fieldLabel: _('Plugin Egg'),
				name: 'file',
				buttonCfg: {
					text: _('Browse') + '...'
				}
			}]
		});
	},

	onInstall: function(field, e) {
		this.form.getForm().submit({
			url: deluge.config.base + 'upload',
			waitMsg: _('Uploading your plugin...'),
			success: this.onUploadSuccess,
			scope: this
		}); 
	},

	onUploadPlugin: function(info, obj, response, request) {
		this.fireEvent('pluginadded');
	},

	onUploadSuccess: function(fp, upload) {
		this.hide();
		if (upload.result.success) {
			var filename = this.form.getForm().getFieldValues().file;
			filename = filename.split('\\').slice(-1)[0]
			var path = upload.result.files[0];
			this.form.getForm().setValues({file: ''});
			deluge.client.web.upload_plugin(filename, path, {
				success: this.onUploadPlugin,
				scope: this,
				filename: filename
			});
		}
	}
});
/*!
 * Deluge.preferences.InterfacePage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Interface
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Interface = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Interface'),
	layout: 'form',
	
	initComponent: function() {
		Deluge.preferences.Interface.superclass.initComponent.call(this);
		
		var om = this.optionsManager = new Deluge.OptionsManager();
		this.on('show', this.onPageShow, this);
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Interface'),
			style: 'margin-bottom: 0px; padding-bottom: 5px; padding-top: 5px',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		om.bind('show_session_speed', fieldset.add({
			name: 'show_session_speed',
			height: 22,
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Show session speed in titlebar')
		}));
		om.bind('sidebar_show_zero', fieldset.add({
			name: 'sidebar_show_zero',
			height: 22,
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Show filters with zero torrents')
		}));
		om.bind('sidebar_multiple_filters', fieldset.add({
			name: 'sidebar_multiple_filters',
			height: 22,
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Allow the use of multiple filters at once')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Password'),
			style: 'margin-bottom: 0px; padding-bottom: 0px; padding-top: 5px',
			autoHeight: true,
			labelWidth: 110,
			defaultType: 'textfield',
			defaults: {
				width: 180,
				inputType: 'password'
			}
		});
		
		this.oldPassword = fieldset.add({
			name: 'old_password',
			fieldLabel: _('Old Password')
		});
		this.newPassword = fieldset.add({
			name: 'new_password',
			fieldLabel: _('New Password')
		});
		this.confirmPassword = fieldset.add({
			name: 'confirm_password',
			fieldLabel: _('Confirm Password')
		});
		
		var panel = fieldset.add({
			xtype: 'panel',
			autoHeight: true,
			border: false,
			width: 320,
			bodyStyle: 'padding-left: 230px'
		})
		panel.add({
			xtype: 'button',
			text: _('Change'),
			listeners: {
				'click': {
					fn: this.onPasswordChange,
					scope: this
				}
			}
		});
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Server'),
			style: 'margin-top: 0px; padding-top: 0px; margin-bottom: 0px; padding-bottom: 0px',
			autoHeight: true,
			labelWidth: 110,
			defaultType: 'spinnerfield',
			defaults: {
				width: 80
			}
		});
		om.bind('session_timeout', fieldset.add({
			name: 'session_timeout',
			fieldLabel: _('Session Timeout'),
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		om.bind('port', fieldset.add({
			name: 'port',
			fieldLabel: _('Port'),
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		this.httpsField = om.bind('https', fieldset.add({
			xtype: 'checkbox',
			name: 'https',
			hideLabel: true,
			width: 280,
			height: 22,
			boxLabel: _('Use SSL (paths relative to Deluge config folder)')
		}));
		this.httpsField.on('check', this.onSSLCheck, this);
		this.pkeyField = om.bind('pkey', fieldset.add({
			xtype: 'textfield',
			disabled: true,
			name: 'pkey',
			width: 180,
			fieldLabel: _('Private Key')
		}));
		this.certField = om.bind('cert', fieldset.add({
			xtype: 'textfield',
			disabled: true,
			name: 'cert',
			width: 180,
			fieldLabel: _('Certificate')
		}));
	},
	
	onApply: function() {
		var changed = this.optionsManager.getDirty();
		if (!Ext.isObjectEmpty(changed)) {
			deluge.client.web.set_config(changed, {
				success: this.onSetConfig,
				scope: this
			});

			for (var key in deluge.config) {
				deluge.config[key] = this.optionsManager.get(key);
			}
		}
	},
	
	onGotConfig: function(config) {
		this.optionsManager.set(config);
	},
	
	onPasswordChange: function() {
		var newPassword = this.newPassword.getValue();
		if (newPassword != this.confirmPassword.getValue()) {
			Ext.MessageBox.show({
				title: _('Invalid Password'),
				msg: _('Your passwords don\'t match!'),
				buttons: Ext.MessageBox.OK,
				modal: false,
				icon: Ext.MessageBox.ERROR,
				iconCls: 'x-deluge-icon-error'
			});
			return;
		}
		
		var oldPassword = this.oldPassword.getValue();
		deluge.client.auth.change_password(oldPassword, newPassword, {
			success: function(result) {
				if (!result) {
					Ext.MessageBox.show({
						title: _('Password'),
						msg: _('Your old password was incorrect!'),
						buttons: Ext.MessageBox.OK,
						modal: false,
						icon: Ext.MessageBox.ERROR,
						iconCls: 'x-deluge-icon-error'
					});
					this.oldPassword.setValue('');
				} else {
					Ext.MessageBox.show({
						title: _('Change Successful'),
						msg: _('Your password was successfully changed!'),
						buttons: Ext.MessageBox.OK,
						modal: false,
						icon: Ext.MessageBox.INFO,
						iconCls: 'x-deluge-icon-info'
					});
					this.oldPassword.setValue('');
					this.newPassword.setValue('');
					this.confirmPassword.setValue('');
				}
			},
			scope: this
		});
	},
	
	onSetConfig: function() {
		this.optionsManager.commit();
	},
	
	onPageShow: function() {
		deluge.client.web.get_config({
			success: this.onGotConfig,
			scope: this
		})
	},
	
	onSSLCheck: function(e, checked) {
		this.pkeyField.setDisabled(!checked);
		this.certField.setDisabled(!checked);
	}
});
/*!
 * Deluge.preferences.NetworkPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Network
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Network = Ext.extend(Ext.form.FormPanel, {
	
	border: false,
	layout: 'form',
	title:  _('Network'),

	initComponent: function() {
		Deluge.preferences.Network.superclass.initComponent.call(this);
		var optMan = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Incoming Ports'),
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('random_port', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Use Random Ports'),
			name: 'random_port',
			height: 22,
			listeners: {
				'check': {
					fn: function(e, checked) {
						this.listenPorts.setDisabled(checked);
					},
					scope: this
				}
			}
		}));
		this.listenPorts = fieldset.add({
			xtype: 'spinnergroup',
			name: 'listen_ports',
			fieldLabel: '',
			labelSeparator: '',
			colCfg: {
				labelWidth: 40,
				style: 'margin-right: 10px;'
			},
			items: [{
				fieldLabel: 'From',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				}
			}, {
				fieldLabel: 'To',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				}
			}]
		});
		optMan.bind('listen_ports', this.listenPorts);
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Outgoing Ports'),
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('random_outgoing_ports', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Use Random Ports'),
			name: 'random_outgoing_ports',
			height: 22,
			listeners: {
				'check': {
					fn: function(e, checked) {
						this.outgoingPorts.setDisabled(checked);
					},
					scope: this
				}
			}
		}));
		this.outgoingPorts = fieldset.add({
			xtype: 'spinnergroup',
			name: 'outgoing_ports',
			fieldLabel: '',
			labelSeparator: '',
			colCfg: {
				labelWidth: 40,
				style: 'margin-right: 10px;'
			},
			items: [{
				fieldLabel: 'From',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				}
			}, {
				fieldLabel: 'To',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				}
			}]
		});
		optMan.bind('outgoing_ports', this.outgoingPorts);
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Network Interface'),
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'textfield'
		});
		optMan.bind('listen_interface', fieldset.add({
			name: 'listen_interface',
			fieldLabel: '',
			labelSeparator: '',
			width: 200
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('TOS'),
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
			bodyStyle: 'margin: 0px; padding: 0px',
			autoHeight: true,
			defaultType: 'textfield'
		});
		optMan.bind('peer_tos', fieldset.add({
			name: 'peer_tos',
			fieldLabel: _('Peer TOS Byte'),
			width: 80
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Network Extras'),
			autoHeight: true,
			layout: 'table',
			layoutConfig: {
				columns: 3
			},			
			defaultType: 'checkbox'
		});
		optMan.bind('upnp', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('UPnP'),
			name: 'upnp'
		}));
		optMan.bind('natpmp', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('NAT-PMP'),
			ctCls: 'x-deluge-indent-checkbox',
			name: 'natpmp'
		}));
		optMan.bind('utpex', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Peer Exchange'),
			ctCls: 'x-deluge-indent-checkbox',
			name: 'utpex'
		}));
		optMan.bind('lsd', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('LSD'),
			name: 'lsd'
		}));
		optMan.bind('dht', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('DHT'),
			ctCls: 'x-deluge-indent-checkbox',
			name: 'dht'
		}));
	}
});
/*!
 * Deluge.preferences.OtherPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Other
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Other = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Other'),
			layout: 'form'
		}, config);
		Deluge.preferences.Other.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Deluge.preferences.Other.superclass.initComponent.call(this);
		
		var optMan = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Updates'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('new_release_check', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 22,
			name: 'new_release_check',
			boxLabel: _('Be alerted about new releases')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('System Information'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		fieldset.add({
			xtype: 'panel',
			border: false,
			bodyCfg: {
				html: _('Help us improve Deluge by sending us your '
				    + 'Python version, PyGTK version, OS and processor '
				    + 'types. Absolutely no other information is sent.')
			}
		});
		optMan.bind('send_info', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Yes, please send anonymous statistics'),
			name: 'send_info'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('GeoIP Database'),
			autoHeight: true,
			labelWidth: 80,
			defaultType: 'textfield'
		});
		optMan.bind('geoip_db_location', fieldset.add({
			name: 'geoip_db_location',
			fieldLabel: _('Location'),
			width: 200
		}));
	}
});
/*!
 * Deluge.preferences.PluginsPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Plugins
 * @extends Ext.Panel
 */
Deluge.preferences.Plugins = Ext.extend(Ext.Panel, {

	layout: 'border',
	title: _('Plugins'),
	border: false,
	height: 400,
	cls: 'x-deluge-plugins',

	pluginTemplate: new Ext.Template(
		'<dl class="singleline">' +
			'<dt>Author:</dt><dd>{author}</dd>' +
			'<dt>Version:</dt><dd>{version}</dd>' +
			'<dt>Author Email:</dt><dd>{email}</dd>' +
			'<dt>Homepage:</dt><dd>{homepage}</dd>' +
			'<dt>Details:</dt><dd>{details}</dd>' +
		'</dl>'
	),

	initComponent: function() {
		Deluge.preferences.Plugins.superclass.initComponent.call(this);
		this.defaultValues = {
			'version': '',
			'email': '',
			'homepage': '',
			'details': ''
		};
		this.pluginTemplate.compile();

		var checkboxRenderer = function(v, p, record){
			p.css += ' x-grid3-check-col-td';
			return '<div class="x-grid3-check-col'+(v?'-on':'')+'"> </div>';
		}

		this.list = this.add({
			xtype: 'listview',
			store: new Ext.data.ArrayStore({
				fields: [
					{name: 'enabled', mapping: 0},
					{name: 'plugin', mapping: 1}
				]
			}),
			columns: [{
				id: 'enabled',
				header: _('Enabled'),
				width: .2,
				sortable: true,
				tpl: new Ext.XTemplate('{enabled:this.getCheckbox}', {
					getCheckbox: function(v) {
						return '<div class="x-grid3-check-col'+(v?'-on':'')+'" rel="chkbox"> </div>';
					}
				}),
				dataIndex: 'enabled'
			}, {
				id: 'plugin',
				header: _('Plugin'),
				width: .8,
				sortable: true,
				dataIndex: 'plugin'
			}],
			singleSelect: true,
			autoExpandColumn: 'plugin',
			listeners: {
				selectionchange: {fn: this.onPluginSelect, scope: this}
			}
		});

		this.panel = this.add({
			region: 'center',
			autoScroll: true,
			margins: '5 5 5 5',
			items: [this.list],
			bbar: new Ext.Toolbar({
				items: [{
					cls: 'x-btn-text-icon',
					iconCls: 'x-deluge-install-plugin',
					text: _('Install'),
					handler: this.onInstallPluginWindow,
					scope: this
				}, '->', {
					cls: 'x-btn-text-icon',
					text: _('Find More'),
					iconCls: 'x-deluge-find-more',
					handler: this.onFindMorePlugins,
					scope: this
				}]
			})
		});

		var pp = this.pluginInfo = this.add({
			xtype:     'panel',
			border:     true,
			height:     160,
			region:    'south',
			margins:   '0 5 5 5'
		});
		var fieldset = pp.add({
			xtype:     'fieldset',
			title:   _('Info'),
			border:     false,
			autoHeight: true,
			labelWidth: 1,
			style:     'margin-top: 5px;'
		});
		this.pluginInfo = fieldset.add({
			xtype: 'panel',
			border: false,
			bodyCfg: {
				style: 'margin-left: 10px'
			}
		});

		this.pluginInfo.on('render', this.onPluginInfoRender, this);
		this.list.on('click', this.onNodeClick, this);
		deluge.preferences.on('show', this.onPreferencesShow, this);
		deluge.events.on('PluginDisabledEvent', this.onPluginDisabled, this);
		deluge.events.on('PluginEnabledEvent', this.onPluginEnabled, this);
	},

	disablePlugin: function(plugin) {
		deluge.client.core.disable_plugin(plugin);
	},

	enablePlugin: function(plugin) {
		deluge.client.core.enable_plugin(plugin);
	},

	setInfo: function(plugin) {
		if (!this.pluginInfo.rendered) return;
		var values = plugin || this.defaultValues;
		this.pluginInfo.body.dom.innerHTML = this.pluginTemplate.apply(values);
	},

	updatePlugins: function() {
		deluge.client.web.get_plugins({
			success: this.onGotPlugins,
			scope: this
		});
	},

	updatePluginsGrid: function() {
		var plugins = [];
		Ext.each(this.availablePlugins, function(plugin) {
			if (this.enabledPlugins.indexOf(plugin) > -1) {
				plugins.push([true, plugin]);
			} else {
				plugins.push([false, plugin]);
			}
		}, this);
		this.list.getStore().loadData(plugins);
	},

	onNodeClick: function(dv, index, node, e) {
		var el = new Ext.Element(e.target);
		if (el.getAttribute('rel') != 'chkbox') return;

		var r = dv.getStore().getAt(index);
		r.set('enabled', !r.get('enabled'));
		r.commit();
		if (r.get('enabled')) {
			this.enablePlugin(r.get('plugin'));
		} else {
			this.disablePlugin(r.get('plugin'));
		}
	},

	onFindMorePlugins: function() {
		window.open('http://dev.deluge-torrent.org/wiki/Plugins');
	},

	onGotPlugins: function(plugins) {
		this.enabledPlugins = plugins.enabled_plugins;
		this.availablePlugins = plugins.available_plugins;
		this.setInfo();
		this.updatePluginsGrid();
	},

	onGotPluginInfo: function(info) {
		var values = {
			author: info['Author'],
			version: info['Version'],
			email: info['Author-email'],
			homepage: info['Home-page'],
			details: info['Description']
		}
		this.setInfo(values);
		delete info;
	},

	onInstallPluginWindow: function() {
		if (!this.installWindow) {
			this.installWindow = new Deluge.preferences.InstallPluginWindow();
			this.installWindow.on('pluginadded', this.onPluginInstall, this);
		}
		this.installWindow.show();
	},

	onPluginEnabled: function(pluginName) {
		var index = this.list.getStore().find('plugin', pluginName);
		if (index == -1) return;
		var plugin = this.list.getStore().getAt(index);
		plugin.set('enabled', true);
		plugin.commit();
	},

	onPluginDisabled: function(pluginName) {
		var index = this.list.getStore().find('plugin', pluginName);
		if (index == -1) return;
		var plugin = this.list.getStore().getAt(index);
		plugin.set('enabled', false);
		plugin.commit();
	},

	onPluginInstall: function() {
		this.updatePlugins();
	},

	onPluginSelect: function(dv, selections) {
        if (selections.length == 0) return;
		var r = dv.getRecords(selections)[0];
		deluge.client.web.get_plugin_info(r.get('plugin'), {
			success: this.onGotPluginInfo,
			scope: this
		});
	},

	onPreferencesShow: function() {
		this.updatePlugins();
	},

	onPluginInfoRender: function(ct, position) {
		this.setInfo();
	}
});
/*!
 * Deluge.preferences.PreferencesWindow.js
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
Ext.namespace('Deluge.preferences');

PreferencesRecord = Ext.data.Record.create([{name:'name', type:'string'}]);

/**
 * @class Deluge.preferences.PreferencesWindow
 * @extends Ext.Window
 */
Deluge.preferences.PreferencesWindow = Ext.extend(Ext.Window, {

	/**
	 * @property {String} currentPage The currently selected page.
	 */
	currentPage: null,

	title: _('Preferences'),
	layout: 'border',
	width: 485,
	height: 500,

	buttonAlign: 'right',
	closeAction: 'hide',
	closable: true,
	iconCls: 'x-deluge-preferences',
	plain: true,
	resizable: false,

	pages: {},

	initComponent: function() {
		Deluge.preferences.PreferencesWindow.superclass.initComponent.call(this);

		this.list = new Ext.list.ListView({
			store: new Ext.data.Store(),
			columns: [{
				id: 'name',
				renderer: fplain,
				dataIndex: 'name'
			}],
			singleSelect: true,
			listeners: {
				'selectionchange': {
					fn: this.onPageSelect, scope: this
				}
			},
			hideHeaders: true,
			autoExpandColumn: 'name',
			deferredRender: false,
			autoScroll: true,
			collapsible: true
		});
		this.add({
			region: 'west',
			title: _('Categories'),
			items: [this.list],
			width: 120,
			margins: '5 0 5 5',
			cmargins: '5 0 5 5'
		});

		this.configPanel = this.add({
			type: 'container',
			autoDestroy: false,
			region: 'center',
			layout: 'card',
			layoutConfig: {
				deferredRender: true
			},
			autoScroll: true,
			width: 300,
			margins: '5 5 5 5',
			cmargins: '5 5 5 5'
		});

		this.addButton(_('Close'), this.onClose, this);
		this.addButton(_('Apply'), this.onApply, this);
		this.addButton(_('Ok'), this.onOk, this);

		this.optionsManager = new Deluge.OptionsManager();
		this.on('afterrender', this.onAfterRender, this);
		this.on('show', this.onShow, this);

		this.initPages();
	},

	initPages: function() {
		deluge.preferences = this;
		this.addPage(new Deluge.preferences.Downloads());
		this.addPage(new Deluge.preferences.Network());
		this.addPage(new Deluge.preferences.Encryption());
		this.addPage(new Deluge.preferences.Bandwidth());
		this.addPage(new Deluge.preferences.Interface());
		this.addPage(new Deluge.preferences.Other());
		this.addPage(new Deluge.preferences.Daemon());
		this.addPage(new Deluge.preferences.Queue());
		this.addPage(new Deluge.preferences.Proxy());
		this.addPage(new Deluge.preferences.Cache());
		this.addPage(new Deluge.preferences.Plugins());
	},

	onApply: function(e) {
		var changed = this.optionsManager.getDirty();
		if (!Ext.isObjectEmpty(changed)) {
			deluge.client.core.set_config(changed, {
				success: this.onSetConfig,
				scope: this
			});
		}

		for (var page in this.pages) {
			if (this.pages[page].onApply) this.pages[page].onApply();
		}
	},


	/**
	 * Return the options manager for the preferences window.
	 * @returns {Deluge.OptionsManager} the options manager
	 */
	getOptionsManager: function() {
		return this.optionsManager;
	},

	/**
	 * Adds a page to the preferences window.
	 * @param {Mixed} page
	 */
	addPage: function(page) {
		var store = this.list.getStore();
		var name = page.title;
		store.add([new PreferencesRecord({name: name})]);
		page['bodyStyle'] = 'padding: 5px';
		page.preferences = this;
		this.pages[name] = this.configPanel.add(page);
		this.pages[name].index = -1;
		return this.pages[name];
	},

	/**
	 * Removes a preferences page from the window.
	 * @param {mixed} name
	 */
	removePage: function(page) {
	    var name = page.title;
	    var store = this.list.getStore();
	    store.removeAt(store.find('name', name));
	    this.configPanel.remove(page);
	    delete this.pages[page.title];
	},

	/**
	 * Select which preferences page is displayed.
	 * @param {String} page The page name to change to
	 */
	selectPage: function(page) {
		if (this.pages[page].index < 0) {
			this.pages[page].index = this.configPanel.items.indexOf(this.pages[page]);
		}
		this.list.select(this.pages[page].index);
	},

	// private
	doSelectPage: function(page) {
		if (this.pages[page].index < 0) {
			this.pages[page].index = this.configPanel.items.indexOf(this.pages[page]);
		}
		this.configPanel.getLayout().setActiveItem(this.pages[page].index);
		this.currentPage = page;
	},

	// private
	onGotConfig: function(config) {
		this.getOptionsManager().set(config);
	},

	// private
	onPageSelect: function(list, selections) {
		var r = list.getRecord(selections[0]);
		this.doSelectPage(r.get('name'));
	},

	// private
	onSetConfig: function() {
		this.getOptionsManager().commit();
	},

	// private
	onAfterRender: function() {
		if (!this.list.getSelectionCount()) {
			this.list.select(0);
		}
		this.configPanel.getLayout().setActiveItem(0);
	},

	// private
	onShow: function() {
		if (!deluge.client.core) return;
		deluge.client.core.get_config({
			success: this.onGotConfig,
			scope: this
		})
	},

	// private
	onClose: function() {
		this.hide();
	},

	// private
	onOk: function() {
		var changed = this.optionsManager.getDirty();
		if (!Ext.isObjectEmpty(changed)) {
			deluge.client.core.set_config(changed, {
				success: this.onSetConfig,
				scope: this
			});
		}

		for (var page in this.pages) {
			if (this.pages[page].onOk) this.pages[page].onOk();
		}

		this.hide();
	}
});
/*!
 * Deluge.preferences.ProxyField.js
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
 *	 The Free Software Foundation, Inc.,
 *	 51 Franklin Street, Fifth Floor
 *	 Boston, MA  02110-1301, USA.
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
Ext.ns('Deluge.preferences');

/**
 * @class Deluge.preferences.ProxyField
 * @extends Ext.form.FieldSet
 */
Deluge.preferences.ProxyField = Ext.extend(Ext.form.FieldSet, {

	border: false,
	autoHeight: true,
	labelWidth: 70,

	initComponent: function() {
		Deluge.preferences.ProxyField.superclass.initComponent.call(this);
		this.proxyType = this.add({
			xtype: 'combo',
			fieldLabel: _('Type'),
			name: 'proxytype',
			mode: 'local',
			width: 150,
			store: new Ext.data.ArrayStore({
				fields: ['id', 'text'],
				data: [
					[0, _('None')],
					[1, _('Socksv4')],
					[2, _('Socksv5')],
					[3, _('Socksv5 with Auth')],
					[4, _('HTTP')],
					[5, _('HTTP with Auth')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		});
		this.proxyType.on('change', this.onFieldChange, this);
		this.proxyType.on('select', this.onTypeSelect, this);

		this.hostname = this.add({
			xtype: 'textfield',
			name: 'hostname',
			fieldLabel: _('Host'),
			width: 220
		});
		this.hostname.on('change', this.onFieldChange, this);

		this.port = this.add({
			xtype: 'spinnerfield',
			name: 'port',
			fieldLabel: _('Port'),
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		});
		this.port.on('change', this.onFieldChange, this);

	   this.username = this.add({
			xtype: 'textfield',
			name: 'username',
			fieldLabel: _('Username'),
			width: 220
		});
		this.username.on('change', this.onFieldChange, this);

		this.password = this.add({
			xtype: 'textfield',
			name: 'password',
			fieldLabel: _('Password'),
			inputType: 'password',
			width: 220
		});
		this.password.on('change', this.onFieldChange, this);

		this.setting = false;
	},

	getName: function() {
		return this.initialConfig.name;
	},

	getValue: function() {
		return {
			'type': this.proxyType.getValue(),
			'hostname': this.hostname.getValue(),
			'port': Number(this.port.getValue()),
			'username': this.username.getValue(),
			'password': this.password.getValue()
		}
	},

	// Set the values of the proxies
	setValue: function(value) {
		this.setting = true;
		this.proxyType.setValue(value['type']);
		var index = this.proxyType.getStore().find('id', value['type']);
		var record = this.proxyType.getStore().getAt(index);

		this.hostname.setValue(value['hostname']);
		this.port.setValue(value['port']);
		this.username.setValue(value['username']);
		this.password.setValue(value['password']);
		this.onTypeSelect(this.type, record, index);
		this.setting = false;
	},

	onFieldChange: function(field, newValue, oldValue) {
		if (this.setting) return;
		var newValues = this.getValue();
		var oldValues = Ext.apply({}, newValues);
		oldValues[field.getName()] = oldValue;

		this.fireEvent('change', this, newValues, oldValues);
	},

	onTypeSelect: function(combo, record, index) {
		var typeId = record.get('id');
		if (typeId > 0) {
			this.hostname.show();
			this.port.show();
		} else {
			this.hostname.hide();
			this.port.hide();
		}

		if (typeId == 3 || typeId == 5) {
			this.username.show();
			this.password.show();
		} else {
			this.username.hide();
			this.password.hide();
		}
	}
});
/*!
 * Deluge.preferences.ProxyPage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Proxy
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Proxy = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Proxy'),
			layout: 'form',
			autoScroll: true
		}, config);
		Deluge.preferences.Proxy.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Deluge.preferences.Proxy.superclass.initComponent.call(this);
		this.peer = this.add(new Deluge.preferences.ProxyField({
			title: _('Peer'),
			name: 'peer'
		}));
		this.peer.on('change', this.onProxyChange, this);

		this.web_seed = this.add(new Deluge.preferences.ProxyField({
			title: _('Web Seed'),
			name: 'web_seed'
		}));
		this.web_seed.on('change', this.onProxyChange, this);

		this.tracker = this.add(new Deluge.preferences.ProxyField({
			title: _('Tracker'),
			name: 'tracker'
		}));
		this.tracker.on('change', this.onProxyChange, this);

		this.dht = this.add(new Deluge.preferences.ProxyField({
			title: _('DHT'),
			name: 'dht'
		}));
		this.dht.on('change', this.onProxyChange, this);

		deluge.preferences.getOptionsManager().bind('proxies', this);
	},

	getValue: function() {
		return {
			'dht': this.dht.getValue(),
			'peer': this.peer.getValue(),
			'tracker': this.tracker.getValue(),
			'web_seed': this.web_seed.getValue()
		}
	},

	setValue: function(value) {
		for (var proxy in value) {
			this[proxy].setValue(value[proxy]);
		}
	},

	onProxyChange: function(field, newValue, oldValue) {
		var newValues = this.getValue();
		var oldValues = Ext.apply({}, newValues);
		oldValues[field.getName()] = oldValue;

		this.fireEvent('change', this, newValues, oldValues);
	}
});
/*!
 * Deluge.preferences.QueuePage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Queue
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Queue = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Queue'),
	layout: 'form',
	
	initComponent: function() {
		Deluge.preferences.Queue.superclass.initComponent.call(this);
		
		var om = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('General'),
			style: 'padding-top: 5px;',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		om.bind('queue_new_to_top', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Queue new torrents to top'),
			name: 'queue_new_to_top'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Active Torrents'),
			autoHeight: true,
			labelWidth: 150,
			defaultType: 'spinnerfield',
			style: 'margin-bottom: 0px; padding-bottom: 0px;'
		});
		om.bind('max_active_limit', fieldset.add({
			fieldLabel: _('Total Active'),
			name: 'max_active_limit',
			value: 8,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		om.bind('max_active_downloading', fieldset.add({
			fieldLabel: _('Total Active Downloading'),
			name: 'max_active_downloading',
			value: 3,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		om.bind('max_active_seeding', fieldset.add({
			fieldLabel: _('Total Active Seeding'),
			name: 'max_active_seeding',
			value: 5,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		om.bind('dont_count_slow_torrents', fieldset.add({
			xtype: 'checkbox',
			name: 'dont_count_slow_torrents',
			height: 40,
			hideLabel: true,
			boxLabel: _('Do not count slow torrents')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Seeding'),
			autoHeight: true,
			labelWidth: 150,
			defaultType: 'spinnerfield',
			style: 'margin-bottom: 0px; padding-bottom: 0px; margin-top: 0; padding-top: 0;'
		});
		om.bind('share_ratio_limit', fieldset.add({
			fieldLabel: _('Share Ratio Limit'),
			name: 'share_ratio_limit',
			value: 8,
			width: 80,
			incrementValue: 0.1,
			minValue: -1,
			maxValue: 99999,
			alternateIncrementValue: 1,
			decimalPrecision: 2
		}));
		om.bind('seed_time_ratio_limit', fieldset.add({
			fieldLabel: _('Share Time Ratio'),
			name: 'seed_time_ratio_limit',
			value: 3,
			width: 80,
			incrementValue: 0.1,
			minValue: -1,
			maxValue: 99999,
			alternateIncrementValue: 1,
			decimalPrecision: 2
		}));
		om.bind('seed_time_limit', fieldset.add({
			fieldLabel: _('Seed Time (m)'),
			name: 'seed_time_limit',
			value: 5,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			autoHeight: true,
			
			layout: 'table',
			layoutConfig: {columns: 2},
			labelWidth: 0,
			defaultType: 'checkbox',
			
			defaults: {
				fieldLabel: '',
				labelSeparator: ''
			}
		});
		this.stopAtRatio = fieldset.add({
			name: 'stop_seed_at_ratio',
			boxLabel: _('Stop seeding when share ratio reaches:')
		});
		this.stopAtRatio.on('check', this.onStopRatioCheck, this);
		om.bind('stop_seed_at_ratio', this.stopAtRatio);
		
		this.stopRatio = fieldset.add({
			xtype: 'spinnerfield',
			name: 'stop_seed_ratio',
			ctCls: 'x-deluge-indent-checkbox',
			disabled: true,
			value: '2.0',
			width: 60,
			incrementValue: 0.1,
			minValue: -1,
			maxValue: 99999,
			alternateIncrementValue: 1,
			decimalPrecision: 2
		});
		om.bind('stop_seed_ratio', this.stopRatio);
		
		this.removeAtRatio = fieldset.add({
			name: 'remove_seed_at_ratio',
			ctCls: 'x-deluge-indent-checkbox',
			boxLabel: _('Remove torrent when share ratio is reached'),
			disabled: true,
			colspan: 2
		});
		om.bind('remove_seed_at_ratio', this.removeAtRatio);
	},
	
	onStopRatioCheck: function(e, checked) {
		this.stopRatio.setDisabled(!checked);
		this.removeAtRatio.setDisabled(!checked);
	}
});
/*!
 * Deluge.StatusbarMenu.js
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
Ext.ns('Deluge');

/**
 * Menu that handles setting the statusbar limits correctly.
 * @class Deluge.StatusbarMenu
 * @extends Ext.menu.Menu
 */
Deluge.StatusbarMenu = Ext.extend(Ext.menu.Menu, {
	
	initComponent: function() {
		Deluge.StatusbarMenu.superclass.initComponent.call(this);
		this.otherWin = new Deluge.OtherLimitWindow(this.initialConfig.otherWin || {});

		this.items.each(function(item) {
			if (item.getXType() != 'menucheckitem') return;
			if (item.value == 'other') {
				item.on('click', this.onOtherClicked, this);
			} else {
				item.on('checkchange', this.onLimitChanged, this);
			}
		}, this);
	},
    
    setValue: function(value) {
        var beenSet = false;
        // set the new value
        this.value = value = (value == 0) ? -1 : value;

        var other = null;
        // uncheck all items
        this.items.each(function(item) {
            if (item.setChecked) {
                item.suspendEvents();
                if (item.value == value) {
                    item.setChecked(true);
                    beenSet = true;
                } else {
                    item.setChecked(false);
                }   
                item.resumeEvents();
            }   

            if (item.value == 'other') other = item;
        }); 

        if (beenSet) return;

        other.suspendEvents();
        other.setChecked(true);
        other.resumeEvents();
    },

	onLimitChanged: function(item, checked) {
		if (!checked || item.value == 'other') return; // we don't care about unchecks or other
		var config = {}
		config[item.group] = item.value
		deluge.client.core.set_config(config, {
			success: function() {
				deluge.ui.update();
			}
		});
	},

	onOtherClicked: function(item, e) {
		this.otherWin.group = item.group;
		this.otherWin.setValue(this.value);
		this.otherWin.show();
	}
});
/*!
 * Deluge.OptionsManager.js
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
Ext.namespace('Deluge');

/**
 * @class Deluge.OptionsManager
 * @extends Ext.util.Observable
 * A class that can be used to manage options throughout the ui.
 * @constructor
 * Creates a new OptionsManager
 * @param {Object} config Configuration options
 */
Deluge.OptionsManager = Ext.extend(Ext.util.Observable, {
	
	constructor: function(config) {
		config = config || {};
		this.binds = {};
		this.changed = {};
		this.options = (config && config['options']) || {};
		this.focused = null;

		this.addEvents({
			/**
			 * @event add
			 * Fires when an option is added
			 */
			'add': true,

			/**
			 * @event changed
			 * Fires when an option is changed
			 * @param {String} option The changed option
			 * @param {Mixed} value The options new value
			 * @param {Mixed} oldValue The options old value
			 */
			'changed': true,

			/**
			 * @event reset
			 * Fires when the options are reset
			 */
			'reset': true
		});
		this.on('changed', this.onChange, this);

		Deluge.OptionsManager.superclass.constructor.call(this);
	},

	/**
	 * Add a set of default options and values to the options manager
	 * @param {Object} options The default options.
	 */
	addOptions: function(options) {
		this.options = Ext.applyIf(this.options, options);
	},
	
	/**
	 * Binds a form field to the specified option.
	 * @param {String} option
	 * @param {Ext.form.Field} field
	 */
	bind: function(option, field) {
		this.binds[option] = this.binds[option] || [];
		this.binds[option].push(field);
		field._doption = option;

		field.on('focus', this.onFieldFocus, this);
		field.on('blur', this.onFieldBlur, this);
		field.on('change', this.onFieldChange, this);
		field.on('check', this.onFieldChange, this);
		field.on('spin', this.onFieldChange, this);
		return field;
	},

	/**
	 * Changes all the changed values to be the default values
	 */
	commit: function() {
		this.options = Ext.apply(this.options, this.changed);
		this.reset();
	},

	/**
	 * Converts the value so it matches the originals type
	 * @param {Mixed} oldValue The original value
	 * @param {Mixed} value The new value to convert
	 */
	convertValueType: function(oldValue, value) {
		if (Ext.type(oldValue) != Ext.type(value)) {
			switch (Ext.type(oldValue)) {
				case 'string':
					value = String(value);
					break;
				case 'number':
					value = Number(value);
					break;
				case 'boolean':
					if (Ext.type(value) == 'string') {
						value = value.toLowerCase();
						value = (value == 'true' || value == '1' || value == 'on') ? true : false;
					} else {
						value = Boolean(value);
					}
					break;
			}
		}
		return value;
	},

	/**
	 * Get the value for an option or options.
	 * @param {String} [option] A single option or an array of options to return.
	 * @returns {Object} the options value.
	 */
	get: function() {
		if (arguments.length == 1) {
			var option = arguments[0];
			return (this.isDirty(option)) ? this.changed[option] : this.options[option];
		} else {
			var options = {};
			Ext.each(arguments, function(option) {
				if (!this.has(option)) return;
				options[option] = (this.isDirty(option)) ? this.changed[option] : this.options[option];
			}, this);
			return options;
		}
	},

	/**
	 * Get the default value for an option or options.
	 * @param {String|Array} [option] A single option or an array of options to return.
	 * @returns {Object} the value of the option
	 */
	getDefault: function(option) {
		return this.options[option];
	},

	/**
	 * Returns the dirty (changed) values.
	 * @returns {Object} the changed options
	 */
	getDirty: function() {
		return this.changed;
	},

	/**
	 * @param {String} [option] The option to check
	 * @returns {Boolean} true if the option has been changed from the default.
	 */
	isDirty: function(option) {
		return !Ext.isEmpty(this.changed[option]);
	},

	/**
	 * Check to see if an option exists in the options manager
	 * @param {String} option
	 * @returns {Boolean} true if the option exists, else false.
	 */
	has: function(option) {
		return (this.options[option]);
	},

	/**
	 * Reset the options back to the default values.
	 */
	reset: function() {
		this.changed = {};
	},

	/**
	 * Sets the value of specified option(s) for the passed in id.
	 * @param {String} option
	 * @param {Object} value The value for the option
	 */
	set: function(option, value) {
		if (option === undefined) {
			return;
		} else if (typeof option == 'object') {
			var options = option;
			this.options = Ext.apply(this.options, options);
			for (var option in options) {
				this.onChange(option, options[option]);
			}
		} else {
			this.options[option] = value;
			this.onChange(option, value)
		}
	},

	/**
	 * Update the value for the specified option and id.
	 * @param {String/Object} option or options to update
	 * @param {Object} [value];
	 */
	update: function(option, value) {
		if (option === undefined) {
			return;
		} else if (value === undefined) {
			for (var key in option) {
				this.update(key, option[key]);
			}
		} else {
			var defaultValue = this.getDefault(option);
			value = this.convertValueType(defaultValue, value);

			var oldValue = this.get(option);
			if (oldValue == value) return;

			if (defaultValue == value) {
				if (this.isDirty(option)) delete this.changed[option];
				this.fireEvent('changed', option, value, oldValue);
				return;
			}

			this.changed[option] = value;
			this.fireEvent('changed', option, value, oldValue);
		}
	},

	/**
	 * Lets the option manager know when a field is blurred so if a value
	 * so value changing operations can continue on that field.
	 */
	onFieldBlur: function(field, event) {
		if (this.focused == field) {
			this.focused = null;
		}
	},

	/**
	 * Stops a form fields value from being blocked by the change functions
	 * @param {Ext.form.Field} field
	 * @private
	 */
	onFieldChange: function(field, event) {
		if (field.field) field = field.field // fix for spinners
		this.update(field._doption, field.getValue());
	},

	/**
	 * Lets the option manager know when a field is focused so if a value
	 * changing operation is performed it won't change the value of the
	 * field.
	 */
	onFieldFocus: function(field, event) {
		this.focused = field;
	},

	onChange: function(option, newValue, oldValue) {
		// If we don't have a bind there's nothing to do.
		if (Ext.isEmpty(this.binds[option])) return;
		Ext.each(this.binds[option], function(bind) {
			// The field is currently focused so we don't want to 
			// change it.
			if (bind == this.focused) return;
			// Set the form field to the new value.
			bind.setValue(newValue);
		}, this);
	}
});
/*!
 * Deluge.AddConnectionWindow.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.AddConnectionWindow
 * @extends Ext.Window
 */
Deluge.AddConnectionWindow = Ext.extend(Ext.Window, {

	title: _('Add Connection'),
	iconCls: 'x-deluge-add-window-icon',

	layout: 'fit',
	width:  300,
	height: 195,

	bodyStyle: 'padding: 10px 5px;',
	closeAction: 'hide',

	initComponent: function() {
		Deluge.AddConnectionWindow.superclass.initComponent.call(this);

		this.addEvents('hostadded');
	
		this.addButton(_('Close'), this.hide, this);
		this.addButton(_('Add'), this.onAddClick, this);
	
		this.on('hide', this.onHide, this);
	
		this.form = this.add({
			xtype: 'form',
			defaultType: 'textfield',
			baseCls: 'x-plain',
			labelWidth: 60,
			items: [{
				fieldLabel: _('Host'),
				name: 'host',
				anchor: '75%',
				value: ''
			}, {
				xtype: 'spinnerfield',
				fieldLabel: _('Port'),
				name: 'port',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 65535
				},
				value: '58846',
				anchor: '40%'
			}, {
				fieldLabel: _('Username'),
				name: 'username',
				anchor: '75%',
				value: ''
			}, {
				fieldLabel: _('Password'),
				anchor: '75%',
				name: 'password',
				inputType: 'password',
				value: ''
			}]
		});
	},

	onAddClick: function() {
		var values = this.form.getForm().getValues();
		deluge.client.web.add_host(values.host, values.port, values.username, values.password, {
			success: function(result) {
				if (!result[0]) {
					Ext.MessageBox.show({
						title: _('Error'),
						msg: "Unable to add host: " + result[1],
						buttons: Ext.MessageBox.OK,
						modal: false,
						icon: Ext.MessageBox.ERROR,
						iconCls: 'x-deluge-icon-error'
					});
				} else {
					this.fireEvent('hostadded');
				}
				this.hide();
			},
			scope: this
		});
	},

	onHide: function() {
		this.form.getForm().reset();
	}
});
/*!
 * Deluge.AddTrackerWindow.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.AddTrackerWindow
 * @extends Ext.Window
 */
Deluge.AddTrackerWindow = Ext.extend(Ext.Window, {
	
	title: _('Add Tracker'),
	layout: 'fit',
	width: 375,
	height: 150,
	plain: true,
	closable: true,
	resizable: false,

	bodyStyle: 'padding: 5px',
	buttonAlign: 'right',
	closeAction: 'hide',
	iconCls: 'x-deluge-edit-trackers',

	initComponent: function() {
		Deluge.AddTrackerWindow.superclass.initComponent.call(this);
	
		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Add'), this.onAddClick, this);
		this.addEvents('add');
	
		this.form = this.add({
			xtype: 'form',
			defaultType: 'textarea',
			baseCls: 'x-plain',
			labelWidth: 55,
			items: [{
				fieldLabel: _('Trackers'),
				name: 'trackers',
				anchor: '100%'
			}]
		})
	},

	onAddClick: function() {
		var trackers = this.form.getForm().findField('trackers').getValue();
		trackers = trackers.split('\n');
	
		var cleaned = [];
		Ext.each(trackers, function(tracker) {
			if (Ext.form.VTypes.url(tracker)) {
				cleaned.push(tracker);
			}
		}, this);
		this.fireEvent('add', cleaned);
		this.hide();
		this.form.getForm().findField('trackers').setValue('');
	},

	onCancelClick: function() {
		this.form.getForm().findField('trackers').setValue('');
		this.hide();
	}
});
/*!
 * Deluge.Client.js
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
Ext.namespace('Ext.ux.util');

/**
 * A class that connects to a json-rpc resource and adds the available
 * methods as functions to the class instance.
 * @class Ext.ux.util.RpcClient
 * @namespace Ext.ux.util
 */
Ext.ux.util.RpcClient = Ext.extend(Ext.util.Observable, {

	_components: [],
	
	_methods: [],
	
	_requests: {},
	
	_url: null,
	
	_optionKeys: ['scope', 'success', 'failure'],
	
	constructor: function(config) {
		Ext.ux.util.RpcClient.superclass.constructor.call(this, config);
		this._url = config.url || null;
		this._id = 0;
		
		this.addEvents(
			// raw events
			/**
			 * @event connected
			 * Fires when the client has retrieved the list of methods from the server.
			 * @param {Ext.ux.util.RpcClient} this
			 */
			 'connected',
			 
			 'error'
		);
		this.reloadMethods();
	},
	
	reloadMethods: function() {
		this._execute('system.listMethods', {
			success: this._setMethods,
			scope: this
		});
	},

	_execute: function(method, options) {
		options = options || {};
		options.params = options.params || [];
		options.id = this._id;
		
		var request = Ext.encode({
			method: method,
			params: options.params,
			id: options.id
		});
		this._id++;
		
		return Ext.Ajax.request({
			url: this._url,
			method: 'POST',
			success: this._onSuccess,
			failure: this._onFailure,
			scope: this,
			jsonData: request,
			options: options
		});
	},
	
	_onFailure: function(response, requestOptions) {
		var options = requestOptions.options;
		errorObj = {
			id: options.id,
			result: null,
			error: {
				msg: 'HTTP: ' + response.status + ' ' + response.statusText,
				code: 255
			}
		}
		
		this.fireEvent('error', errorObj, response, requestOptions)
		
		if (Ext.type(options.failure) != 'function') return;
		if (options.scope) {
			options.failure.call(options.scope, errorObj, response, requestOptions);
		} else {
			options.failure(errorObj, response, requestOptions);
		}            
	},
	
	_onSuccess: function(response, requestOptions) {
		var responseObj = Ext.decode(response.responseText);
		var options = requestOptions.options;
		if (responseObj.error) {
			this.fireEvent('error', responseObj, response, requestOptions);
			
			if (Ext.type(options.failure) != 'function') return;
			if (options.scope) {
				options.failure.call(options.scope, responseObj, response, requestOptions);
			} else {
				options.failure(responseObj, response, requestOptions);
			}
		} else {
			if (Ext.type(options.success) != 'function') return;
			if (options.scope) {
				options.success.call(options.scope, responseObj.result, responseObj, response, requestOptions);
			} else {
				options.success(responseObj.result, responseObj, response, requestOptions);
			}
		}
	},
	
	_parseArgs: function(args) {
		var params = [];
		Ext.each(args, function(arg) {
			params.push(arg);
		});
		
		var options = params[params.length - 1];
		if (Ext.type(options) == 'object') {
			var keys = Ext.keys(options), isOption = false;
			
			Ext.each(this._optionKeys, function(key) {
				if (keys.indexOf(key) > -1) isOption = true;
			});
			
			if (isOption) {
				params.remove(options)
			} else {
				options = {}
			}
		} else {
			options = {}
		}
		options.params = params;
		return options;
	},

	_setMethods: function(methods) {
		var components = {}, self = this;
		
		Ext.each(methods, function(method) {
			var parts = method.split('.');
			var component = components[parts[0]] || {};
			
			var fn = function() {
				var options = self._parseArgs(arguments);
				return self._execute(method, options);
			};
			component[parts[1]] = fn;
			components[parts[0]] = component;
		});
		
		for (var name in components) {
			self[name] = components[name];
		}
        Ext.each(this._components, function(component) {
            if (!component in components) {
                delete this[component];
            }
        }, this);
		this._components = Ext.keys(components);
		this.fireEvent('connected', this);
	}
});
/*!
 * Deluge.ConnectionManager.js
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

Deluge.ConnectionManager = Ext.extend(Ext.Window, {

	layout: 'fit',
	width: 300,
	height: 220,
	bodyStyle: 'padding: 10px 5px;',
	buttonAlign: 'right',
	closeAction: 'hide',
	closable: true,
	plain: true,
	title: _('Connection Manager'),
	iconCls: 'x-deluge-connect-window-icon',

	initComponent: function() {
		Deluge.ConnectionManager.superclass.initComponent.call(this);
		this.on('hide',  this.onHide, this);
		this.on('show', this.onShow, this);

		deluge.events.on('login', this.onLogin, this);
		deluge.events.on('logout', this.onLogout, this);

		this.addButton(_('Close'), this.onClose, this);
		this.addButton(_('Connect'), this.onConnect, this);

		this.list = new Ext.list.ListView({
			store: new Ext.data.ArrayStore({
				fields: [
					{name: 'status', mapping: 3},
					{name: 'host', mapping: 1},
					{name: 'port', mapping: 2},
					{name: 'version', mapping: 4}
				],
				id: 0
			}),
			columns: [{
				header: _('Status'),
				width: .24,
				sortable: true,
				dataIndex: 'status'
			}, {
				id:'host',
				header: _('Host'),
				width: .51,
				sortable: true,
				tpl: '{host}:{port}',
				dataIndex: 'host'
			}, {
				header: _('Version'),
				width: .25,
				sortable: true,
				tpl: '<tpl if="version">{version}</tpl>',
				dataIndex: 'version'
			}],
			singleSelect: true,
			listeners: {
				'selectionchange': {fn: this.onSelectionChanged, scope: this}
			}
		});

		this.panel = this.add({
			autoScroll: true,
			items: [this.list],
			bbar: new Ext.Toolbar({
				buttons: [
					{
						id: 'cm-add',
						cls: 'x-btn-text-icon',
						text: _('Add'),
						iconCls: 'icon-add',
						handler: this.onAddClick,
						scope: this
					}, {
						id: 'cm-remove',
						cls: 'x-btn-text-icon',
						text: _('Remove'),
						iconCls: 'icon-remove',
						handler: this.onRemoveClick,
						disabled: true,
						scope: this
					}, '->', {
						id: 'cm-stop',
						cls: 'x-btn-text-icon',
						text: _('Stop Daemon'),
						iconCls: 'icon-error',
						handler: this.onStopClick,
						disabled: true,
						scope: this
					}
				]
			})
		});
		this.update = this.update.createDelegate(this);
	},

	/**
	 * Check to see if the the web interface is currently connected
	 * to a Deluge Daemon and show the Connection Manager if not.
	 */
	checkConnected: function() {
		deluge.client.web.connected({
			success: function(connected) {
				if (connected) {
					deluge.events.fire('connect');
				} else {
					this.show();
				}
			},
			scope: this
		});
	},

	disconnect: function(show) {
		deluge.events.fire('disconnect');
		if (show) {
			if (this.isVisible()) return;
			this.show();
		}
	},

	loadHosts: function() {
		deluge.client.web.get_hosts({
			success: this.onGetHosts,
			scope: this
		});
	},

	update: function() {
		this.list.getStore().each(function(r) {
			deluge.client.web.get_host_status(r.id, {
				success: this.onGetHostStatus,
				scope: this
			});
		}, this);
	},

	/**
	 * Updates the buttons in the Connection Manager UI according to the
	 * passed in records host state.
	 * @param {Ext.data.Record} record The hosts record to update the UI for
	 */
	updateButtons: function(record) {
		var button = this.buttons[1], status = record.get('status');

		// Update the Connect/Disconnect button
		if (status == _('Connected')) {
			button.enable();
			button.setText(_('Disconnect'));
		} else if (status == _('Offline')) {
			button.disable();
		} else {
			button.enable();
			button.setText(_('Connect'));
		}

		// Update the Stop/Start Daemon button
		if (status == _('Offline')) {
			if (record.get('host') == '127.0.0.1' || record.get('host') == 'localhost') {
				this.stopHostButton.enable();
				this.stopHostButton.setText(_('Start Daemon'));
			} else {
				this.stopHostButton.disable();
			}
		} else {
			this.stopHostButton.enable();
			this.stopHostButton.setText(_('Stop Daemon'));
		}
	},

	// private
	onAddClick: function(button, e) {
		if (!this.addWindow) {
			this.addWindow = new Deluge.AddConnectionWindow();
			this.addWindow.on('hostadded', this.onHostAdded, this);
		}
		this.addWindow.show();
	},

	// private
	onHostAdded: function() {
		this.loadHosts();
	},

	// private
	onClose: function(e) {
		this.hide();
	},

	// private
	onConnect: function(e) {
		var selected = this.list.getSelectedRecords()[0];
		if (!selected) return;

		if (selected.get('status') == _('Connected')) {
			deluge.client.web.disconnect({
				success: function(result) {
					this.update(this);
					deluge.events.fire('disconnect');
				},
				scope: this
			});
		} else {
			var id = selected.id;
			deluge.client.web.connect(id, {
				success: function(methods) {
					deluge.client.reloadMethods();
					deluge.client.on('connected', function(e) {
						deluge.events.fire('connect');
					}, this, {single: true});
				}
			});
			this.hide();
		}
	},

	// private
	onGetHosts: function(hosts) {
		this.list.getStore().loadData(hosts);
		Ext.each(hosts, function(host) {
			deluge.client.web.get_host_status(host[0], {
				success: this.onGetHostStatus,
				scope: this
			});
		}, this);
	},

	// private
	onGetHostStatus: function(host) {
		var record = this.list.getStore().getById(host[0]);
		record.set('status', host[3])
		record.set('version', host[4])
		record.commit();
		if (this.list.getSelectedRecords()[0] == record) this.updateButtons(record);
	},

	// private
	onHide: function() {
		if (this.running) window.clearInterval(this.running);
	},

	// private
	onLogin: function() {
		if (deluge.config.first_login) {
			Ext.MessageBox.confirm('Change password',
				'As this is your first login, we recommend that you ' +
				'change your password. Would you like to ' +
				'do this now?', function(res) {
					this.checkConnected();
					if (res == 'yes') {
						deluge.preferences.show();
						deluge.preferences.selectPage('Interface');
					}
					deluge.client.web.set_config({first_login: false});
				}, this);
		} else {
			this.checkConnected();
		}
	},

	// private
	onLogout: function() {
		this.disconnect();
		if (!this.hidden && this.rendered) {
			this.hide();
		}
	},

	// private
	onRemoveClick: function(button) {
		var connection = this.list.getSelectedRecords()[0];
		if (!connection) return;

		deluge.client.web.remove_host(connection.id, {
			success: function(result) {
				if (!result) {
					Ext.MessageBox.show({
						title: _('Error'),
						msg: result[1],
						buttons: Ext.MessageBox.OK,
						modal: false,
						icon: Ext.MessageBox.ERROR,
						iconCls: 'x-deluge-icon-error'
					});
				} else {
					this.list.getStore().remove(connection);
				}
			},
			scope: this
		});
	},

	// private
	onSelectionChanged: function(list, selections) {
		if (selections[0]) {
			this.removeHostButton.enable();
			this.stopHostButton.enable();
			this.stopHostButton.setText(_('Stop Daemon'));
			this.updateButtons(this.list.getRecord(selections[0]));
		} else {
			this.removeHostButton.disable();
			this.stopHostButton.disable();
		}
	},

    // FIXME: Find out why this is being fired twice
	// private
	onShow: function() {
		if (!this.addHostButton) {
			var bbar = this.panel.getBottomToolbar();
			this.addHostButton = bbar.items.get('cm-add');
			this.removeHostButton = bbar.items.get('cm-remove');
			this.stopHostButton = bbar.items.get('cm-stop');
		}
		this.loadHosts();
        if (this.running) return;
		this.running = window.setInterval(this.update, 2000, this);
	},

	// private
	onStopClick: function(button, e) {
		var connection = this.list.getSelectedRecords()[0];
		if (!connection) return;

		if (connection.get('status') == 'Offline') {
			// This means we need to start the daemon
			deluge.client.web.start_daemon(connection.get('port'));
		} else {
			// This means we need to stop the daemon
			deluge.client.web.stop_daemon(connection.id, {
				success: function(result) {
					if (!result[0]) {
						Ext.MessageBox.show({
							title: _('Error'),
							msg: result[1],
							buttons: Ext.MessageBox.OK,
							modal: false,
							icon: Ext.MessageBox.ERROR,
							iconCls: 'x-deluge-icon-error'
						});
					}
				}
			});
		}
	}
});
/*!
 * Deluge.js
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

// Setup the state manager
Ext.state.Manager.setProvider(new Ext.state.CookieProvider());

// Add some additional functions to ext and setup some of the
// configurable parameters
Ext.apply(Ext, {
	escapeHTML: function(text) {
		text = String(text).replace('<', '&lt;').replace('>', '&gt;');
		return text.replace('&', '&amp;');
	},

	isObjectEmpty: function(obj) {
		for(var i in obj) { return false; }
		return true;
	},

	areObjectsEqual: function(obj1, obj2) {
		var equal = true;
		if (!obj1 || !obj2) return false;
		for (var i in obj1) {
			if (obj1[i] != obj2[i]) {
				equal = false;
			}
		}
		return equal;
	},
	
	keys: function(obj) {
		var keys = [];
		for (var i in obj) if (obj.hasOwnProperty(i))
		{
			keys.push(i);
		}
		return keys;
	},

	values: function(obj) {
		var values = [];
		for (var i in obj) {
			if (obj.hasOwnProperty(i)) {
				values.push(obj[i]);
			}
		}
		return values;
	},
		
	splat: function(obj) {
		var type = Ext.type(obj);
		return (type) ? ((type != 'array') ? [obj] : obj) : [];
	}
});
Ext.getKeys = Ext.keys;
Ext.BLANK_IMAGE_URL = deluge.config.base + 'images/s.gif';
Ext.USE_NATIVE_JSON = true;

// Create the Deluge namespace
Ext.apply(Deluge, {

	// private
	pluginStore: {},
	
	// private
	progressTpl:	'<div class="x-progress-wrap x-progress-renderered">' +
						'<div class="x-progress-inner">' +
							'<div style="width: {2}px" class="x-progress-bar">' +
								'<div style="z-index: 99; width: {3}px" class="x-progress-text">' +
									'<div style="width: {1}px;">{0}</div>' +
								'</div>' +
							'</div>' +
							'<div class="x-progress-text x-progress-text-back">' +
								'<div style="width: {1}px;">{0}</div>' +
							'</div>' +
						'</div>' +
					'</div>',

	
	/**
	 * A method to create a progress bar that can be used by renderers
	 * to display a bar within a grid or tree.
	 * @param {Number} progress The bars progress
	 * @param {Number} width The width of the bar
	 * @param {String} text The text to display on the bar
	 * @param {Number} modified Amount to subtract from the width allowing for fixes
	 */
	progressBar: function(progress, width, text, modifier) {
		modifier = Ext.value(modifier, 10);
		var progressWidth = ((width / 100.0) * progress).toFixed(0);
		var barWidth = progressWidth - 1;
		var textWidth = ((progressWidth - modifier) > 0 ? progressWidth - modifier : 0);
		return String.format(Deluge.progressTpl, text, width, barWidth, textWidth);
	},

	/**
	 * Constructs a new instance of the specified plugin.
	 * @param {String} name The plugin name to create
	 */
	createPlugin: function(name) {
		return new Deluge.pluginStore[name]();
	},

	/**
	 * Check to see if a plugin has been registered.
	 * @param {String} name The plugin name to check
	 */
	hasPlugin: function(name) {
		return (Deluge.pluginStore[name]) ? true : false;
	},

	/**
	 * Register a plugin with the Deluge interface.
	 * @param {String} name The plugin name to register
	 * @param {Plugin} plugin The plugin to register
	 */
	registerPlugin: function(name, plugin) {
		Deluge.pluginStore[name] = plugin;
	}
	
});

// Setup a space for plugins to insert themselves
deluge.plugins = {};

// Hinting for gettext_gen.py
// _('Do Not Download')
// _('Normal Priority')
// _('High Priority')
// _('Highest Priority')
FILE_PRIORITY = {
	9: 'Mixed',
    0: 'Do Not Download',
    1: 'Normal Priority',
    2: 'High Priority',
    5: 'High Priority',
    7: 'Highest Priority',
	'Mixed': 9,
    'Do Not Download': 0,
    'Normal Priority': 1,
    'High Priority': 5,
    'Highest Priority': 7
}

FILE_PRIORITY_CSS = {
	9: 'x-mixed-download',
	0: 'x-no-download',
	1: 'x-normal-download',
	2: 'x-high-download',
	5: 'x-high-download',
	7: 'x-highest-download'
}
/*!
 * Deluge.EditTrackerWindow.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.EditTrackerWindow
 * @extends Ext.Window
 */
Deluge.EditTrackerWindow = Ext.extend(Ext.Window, {

	title: _('Edit Tracker'),
	layout: 'fit',
	width: 375,
	height: 110,
	plain: true,
	closable: true,
	resizable: false,

	bodyStyle: 'padding: 5px',
	buttonAlign: 'right',
	closeAction: 'hide',
	iconCls: 'x-deluge-edit-trackers',
	
	initComponent: function() {
		Deluge.EditTrackerWindow.superclass.initComponent.call(this);
		
		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Save'), this.onSaveClick, this);
		this.on('hide', this.onHide, this);
		
		this.form = this.add({
			xtype: 'form',
			defaultType: 'textfield',
			baseCls: 'x-plain',
			labelWidth: 55,
			items: [{
				fieldLabel: _('Tracker'),
				name: 'tracker',
				anchor: '100%'
			}]
		});
	},
	
	show: function(record) {
		Deluge.EditTrackerWindow.superclass.show.call(this);
		
		this.record = record;
		this.form.getForm().findField('tracker').setValue(record.data['url']);
	},
	
	onCancelClick: function() {
		this.hide();
	},
	
	onHide: function() {
		this.form.getForm().findField('tracker').setValue('');
	},
	
	onSaveClick: function() {
		var url = this.form.getForm().findField('tracker').getValue();
		this.record.set('url', url);
		this.record.commit();
		this.hide();
	}
});
/*!
 * Deluge.EditTrackers.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.EditTrackerWindow
 * @extends Ext.Window
 */
Deluge.EditTrackersWindow = Ext.extend(Ext.Window, {

	title: _('Edit Trackers'),
	layout: 'fit',
	width: 350,
	height: 220,
	plain: true,
	closable: true,
	resizable: true,

	bodyStyle: 'padding: 5px',
	buttonAlign: 'right',
	closeAction: 'hide',
	iconCls: 'x-deluge-edit-trackers',

	initComponent: function() {
		Deluge.EditTrackersWindow.superclass.initComponent.call(this);

		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Ok'), this.onOkClick, this);
		this.addEvents('save');

		this.on('show', this.onShow, this);
		this.on('save', this.onSave, this);

		this.addWindow = new Deluge.AddTrackerWindow();
		this.addWindow.on('add', this.onAddTrackers, this);
		this.editWindow = new Deluge.EditTrackerWindow();

		this.list = new Ext.list.ListView({
			store: new Ext.data.JsonStore({
				root: 'trackers',
				fields: [
					'tier',
					'url'
				]
			}),
			columns: [{
				header: _('Tier'),
				width: .1,
				dataIndex: 'tier'
			}, {
				header: _('Tracker'),
				width: .9,
				dataIndex: 'url'
			}],
			columnSort: {
				sortClasses: ['', '']
			},
			stripeRows: true,
			singleSelect: true,
			listeners: {
				'dblclick': {fn: this.onListNodeDblClicked, scope: this},
				'selectionchange': {fn: this.onSelect, scope: this}
			}
		});

		this.panel = this.add({
			margins: '0 0 0 0',
			items: [this.list],
			autoScroll: true,
			bbar: new Ext.Toolbar({
				items: [
					{
						text: _('Up'),
						iconCls: 'icon-up',
						handler: this.onUpClick,
						scope: this
					}, {
						text: _('Down'),
						iconCls: 'icon-down',
						handler: this.onDownClick,
						scope: this
					}, '->', {
						text: _('Add'),
						iconCls: 'icon-add',
						handler: this.onAddClick,
						scope: this
					}, {
						text: _('Edit'),
						iconCls: 'icon-edit-trackers',
						handler: this.onEditClick,
						scope: this
					}, {
						text: _('Remove'),
						iconCls: 'icon-remove',
						handler: this.onRemoveClick,
						scope: this
					}
				]
			})
		});
	},

	onAddClick: function() {
		this.addWindow.show();
	},

	onAddTrackers: function(trackers) {
		var store = this.list.getStore();
		Ext.each(trackers, function(tracker) {
			var duplicate = false, heightestTier = -1;
			store.each(function(record) {
				if (record.get('tier') > heightestTier) {
					heightestTier = record.get('tier');
				}
				if (tracker == record.get('tracker')) {
					duplicate = true;
					return false;
				}
			}, this);
			if (duplicate) return;
			store.add(new store.recordType({'tier': heightestTier + 1, 'url': tracker}));
		}, this);
	},

	onCancelClick: function() {
		this.hide();
	},

	onEditClick: function() {
		this.editWindow.show(this.list.getSelectedRecords()[0]);
	},

	onHide: function() {
		this.list.getStore().removeAll();
	},

	onListNodeDblClicked: function(list, index, node, e) {
		this.editWindow.show(this.list.getRecord(node));
	},

	onOkClick: function() {
		var trackers = [];
		this.list.getStore().each(function(record) {
			trackers.push({
				'tier': record.get('tier'),
				'url': record.get('url')
			})
		}, this);

		deluge.client.core.set_torrent_trackers(this.torrentId, trackers, {
			failure: this.onSaveFail,
			scope: this
		});

		this.hide();
	},

	onRemoveClick: function() {
		// Remove from the grid
		this.list.getStore().remove(this.list.getSelectedRecords()[0]);
	},

	onRequestComplete: function(status) {
		this.list.getStore().loadData(status);
		this.list.getStore().sort('tier', 'ASC');
	},

	onSaveFail: function() {

	},

	onSelect: function(list) {
		if (list.getSelectionCount()) {
			this.panel.getBottomToolbar().items.get(4).enable();
		}
	},

	onShow: function() {
		this.panel.getBottomToolbar().items.get(4).disable();
		var r = deluge.torrents.getSelected();
		this.torrentId = r.id;
		deluge.client.core.get_torrent_status(r.id, ['trackers'], {
			success: this.onRequestComplete,
			scope: this
		});
	},

	onDownClick: function() {
		var r = this.list.getSelectedRecords()[0];
        if (!r) return;

		r.set('tier', r.get('tier') + 1);
		r.store.sort('tier', 'ASC');
        r.store.commitChanges();

        this.list.select(r.store.indexOf(r));
	},

	onUpClick: function() {
		var r = this.list.getSelectedRecords()[0];
        if (!r) return;

		if (r.get('tier') == 0) return;
		r.set('tier', r.get('tier') - 1);
		r.store.sort('tier', 'ASC');
        r.store.commitChanges();

        this.list.select(r.store.indexOf(r));
	}
});
/*!
 * Deluge.EventsManager.js
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

/**
 * @class Deluge.EventsManager
 * @extends Ext.util.Observable
 * <p>Deluge.EventsManager is instantated as <tt>deluge.events</tt> and can be used by components of the UI to fire global events</p>
 * Class for holding global events that occur within the UI.
 */
Deluge.EventsManager = Ext.extend(Ext.util.Observable, {
	constructor: function() {
		this.toRegister = [];
		this.on('login', this.onLogin, this);
		Deluge.EventsManager.superclass.constructor.call(this);
	},
	
	/**
	 * Append an event handler to this object.
	 */
	addListener: function(eventName, fn, scope, o) {
		this.addEvents(eventName);
		if (/[A-Z]/.test(eventName.substring(0, 1))) {
			if (!deluge.client) {
				this.toRegister.push(eventName);
			} else {
				deluge.client.web.register_event_listener(eventName);
			}
		}
		Deluge.EventsManager.superclass.addListener.call(this, eventName, fn, scope, o);
	},

	getEvents: function() {
		deluge.client.web.get_events({
			success: this.onGetEventsSuccess,
			failure: this.onGetEventsFailure,
			scope: this
		});
	},

	/**
	 * Starts the EventsManagerManager checking for events.
	 */
	start: function() {
		Ext.each(this.toRegister, function(eventName) {
			deluge.client.web.register_event_listener(eventName);
		});
		this.running = true;
		this.errorCount = 0;
		this.getEvents();
	},

	/**
	 * Stops the EventsManagerManager checking for events.
	 */
	stop: function() {
		this.running = false;
	},

	// private
	onLogin: function() {
		this.start();
	},

	onGetEventsSuccess: function(events) {
        if (!this.running) return;
		if (events) {
            Ext.each(events, function(event) {
                var name = event[0], args = event[1];
                args.splice(0, 0, name);
                this.fireEvent.apply(this, args);
            }, this);
        }
		this.getEvents();
	},

	// private
	onGetEventsFailure: function(result, error) {
		// the request timed out or we had a communication failure
		if (!this.running) return;
		if (!error.isTimeout && this.errorCount++ >= 3) {
			this.stop();
			return;
		}
		this.getEvents();
	}
});

/**
 * Appends an event handler to this object (shorthand for {@link #addListener})
 * @method 
 */
Deluge.EventsManager.prototype.on = Deluge.EventsManager.prototype.addListener

/**
 * Fires the specified event with the passed parameters (minus the
 * event name).
 * @method 
 */
Deluge.EventsManager.prototype.fire = Deluge.EventsManager.prototype.fireEvent
deluge.events = new Deluge.EventsManager();
/*!
 * Deluge.FileBrowser.js
 * 
 * Copyright (c) Damien Churchill 2010 <damoxc@gmail.com>
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

Ext.namespace('Deluge');
Deluge.FileBrowser = Ext.extend(Ext.Window, {

	title: _('File Browser'),

	width:  500,
	height: 400,

	initComponent: function() {
		Deluge.FileBrowser.superclass.initComponent.call(this);

		this.add({
			xtype: 'toolbar',
			items: [{
				text: _('Back'),
				iconCls: 'icon-back'
			}, {
				text: _('Forward'),
				iconCls: 'icon-forward'
			}, {
				text: _('Up'),
				iconCls: 'icon-up'
			}, {
				text: _('Home'),
				iconCls: 'icon-home'
			}]
		});
	}

});
/*!
 * Deluge.FilterPanel.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.FilterPanel
 * @extends Ext.list.ListView
 */
Deluge.FilterPanel = Ext.extend(Ext.Panel, {

    autoScroll: true,

	border: false,

	show_zero: null,

	initComponent: function() {
		Deluge.FilterPanel.superclass.initComponent.call(this);
		this.filterType = this.initialConfig.filter;

		var title = this.filterType.replace('_', ' '),
			parts = title.split(' '),
			title = '';
		Ext.each(parts, function(p) {
			fl = p.substring(0, 1).toUpperCase();
			title += fl + p.substring(1) + ' ';
		});
		this.setTitle(_(title));

		if (Deluge.FilterPanel.templates[this.filterType]) {
			var tpl = Deluge.FilterPanel.templates[this.filterType];
		} else {
			var tpl = '<div class="x-deluge-filter x-deluge-{filter:lowercase}">{filter} ({count})</div>';
		}

		this.list = this.add({
			xtype: 'listview',
			singleSelect: true,
			hideHeaders: true,
			reserveScrollOffset: true,
			store: new Ext.data.ArrayStore({
				idIndex: 0,
				fields: ['filter', 'count']
			}),
			columns: [{
				id: 'filter',
				sortable: false,
				tpl: tpl,
				dataIndex: 'filter'
			}]
		});
		this.relayEvents(this.list, ['selectionchange']);
	},

	/**
	 * Return the currently selected filter state
	 * @returns {String} the current filter state
	 */
	getState: function() {
		if (!this.list.getSelectionCount()) return;

		var state = this.list.getSelectedRecords()[0];
		if (state.id == 'All') return;
		return state.id;
	},

	/**
	 * Return the current states in the filter
	 */
	getStates: function() {
		return this.states;
	},

	/**
	 * Return the Store for the ListView of the FilterPanel
	 * @returns {Ext.data.Store} the ListView store
	 */
	getStore: function() {
		return this.list.getStore();
	},

	/**
	 * Update the states in the FilterPanel
	 */
	updateStates: function(states) {
		this.states = {};
		Ext.each(states, function(state) {
			this.states[state[0]] = state[1];
		}, this);

		var show_zero = (this.show_zero == null) ? deluge.config.sidebar_show_zero : this.show_zero;
		if (!show_zero) {
			var newStates = [];
			Ext.each(states, function(state) {
				if (state[1] > 0 || state[0] == _('All')) {
					newStates.push(state);
				}
			});
			states = newStates;
		}

		var store = this.getStore();
		var filters = {};
		Ext.each(states, function(s, i) {
			var record = store.getById(s[0]);
			if (!record) {
				record = new store.recordType({
					filter: s[0],
					count: s[1]
				});
				record.id = s[0];
				store.insert(i, record);
			}
			record.beginEdit();
			record.set('filter', s[0]);
			record.set('count', s[1]);
			record.endEdit();
			filters[s[0]] = true;
		}, this);

		store.each(function(record) {
			if (filters[record.id]) return;
			var r = this.list.getSelectedRecords()[0];
			store.remove(record);
			if (r.id == record.id) {
				this.list.select(0);
			}
		}, this);

		store.commitChanges();

		if (!this.list.getSelectionCount()) {
			this.list.select(0);
		}
	}

});

Deluge.FilterPanel.templates = {
	'tracker_host':  '<div class="x-deluge-filter" style="background-image: url(' + deluge.config.base + 'tracker/{filter});">{filter} ({count})</div>'
}
/*!
 * Deluge.Formatters.js
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

/**
 * A collection of functions for string formatting values.
 * @class Deluge.Formatters
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 * @singleton
 */
Deluge.Formatters = {
	/**
	 * Formats a date string in the locale's date representation based on the
	 * systems timezone.
	 *
	 * @param {Number} timestamp time in seconds since the Epoch
	 * @return {String} a string in the locale's date representation or ""
	 * if seconds < 0
	 */
	date: function(timestamp) {
		function zeroPad(num, count) {
			var numZeropad = num + '';
			while (numZeropad.length < count) {
				numZeropad = '0' + numZeropad;
			}
			return numZeropad;
		}
		timestamp = timestamp * 1000;
		var date = new Date(timestamp);
		return String.format('{0}/{1}/{2} {3}:{4}:{5}',
			zeroPad(date.getDate(), 2), zeroPad(date.getMonth() + 1, 2), date.getFullYear(),
			zeroPad(date.getHours(), 2), zeroPad(date.getMinutes(), 2), zeroPad(date.getSeconds(), 2));
	},
	
	/**
	 * Formats the bytes value into a string with KiB, MiB or GiB units.
	 *
	 * @param {Number} bytes the filesize in bytes
	 * @param {Boolean} showZero pass in true to displays 0 values
	 * @return {String} formatted string with KiB, MiB or GiB units.
	 */
	size: function(bytes, showZero) {
		if (!bytes && !showZero) return '';
		bytes = bytes / 1024.0;
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' KiB'; }
		else { bytes = bytes / 1024; }
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' MiB'; }
		else { bytes = bytes / 1024; }
	
		return bytes.toFixed(1) + ' GiB'
	},

	/**
	 * Formats the bytes value into a string with K, M or G units.
	 *
	 * @param {Number} bytes the filesize in bytes
	 * @param {Boolean} showZero pass in true to displays 0 values
	 * @return {String} formatted string with K, M or G units.
	 */
	sizeShort: function(bytes, showZero) {
		if (!bytes && !showZero) return '';
		bytes = bytes / 1024.0;
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' K'; }
		else { bytes = bytes / 1024; }
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' M'; }
		else { bytes = bytes / 1024; }
	
		return bytes.toFixed(1) + ' G'
	},

	/**
	 * Formats a string to display a transfer speed utilizing {@link #size}
	 *
	 * @param {Number} bytes the number of bytes per second
	 * @param {Boolean} showZero pass in true to displays 0 values
	 * @return {String} formatted string with KiB, MiB or GiB units.
	 */
	speed: function(bytes, showZero) {
		return (!bytes && !showZero) ? '' : fsize(bytes, showZero) + '/s';
	},
	
	/**
	 * Formats a string to show time in a human readable form.
	 *
	 * @param {Number} time the number of seconds
	 * @return {String} a formatted time string. will return '' if seconds == 0
	 */
	timeRemaining: function(time) {
		if (time == 0) { return '&infin;' }
        time = time.toFixed(0);
		if (time < 60) { return time + 's'; }
		else { time = time / 60; }
	
		if (time < 60) {
			var minutes = Math.floor(time)
			var seconds = Math.round(60 * (time - minutes))
			if (seconds > 0) {
				return minutes + 'm ' + seconds + 's';
			} else {
				return minutes + 'm'; }
			}
		else { time = time / 60; }
	
		if (time < 24) { 
			var hours = Math.floor(time)
			var minutes = Math.round(60 * (time - hours))
			if (minutes > 0) {
				return hours + 'h ' + minutes + 'm';
			} else {
				return hours + 'h';
			}			
		}
		else { time = time / 24; }
	
		var days = Math.floor(time)
		var hours = Math.round(24 * (time - days))
		if (hours > 0) {
			return days + 'd ' + hours + 'h';
		} else {
			return days + 'd';
		}
	},
	
	/**
	 * Simply returns the value untouched, for when no formatting is required.
	 *
	 * @param {Mixed} value the value to be displayed
	 * @return the untouched value.
	 */
	plain: function(value) {
		return value;
	},

	cssClassEscape: function(value) {
		return value.toLowerCase().replace('.', '_');
	}
}
var fsize = Deluge.Formatters.size;
var fsize_short = Deluge.Formatters.sizeShort;
var fspeed = Deluge.Formatters.speed;
var ftime = Deluge.Formatters.timeRemaining;
var fdate = Deluge.Formatters.date;
var fplain = Deluge.Formatters.plain;
Ext.util.Format.cssClassEscape = Deluge.Formatters.cssClassEscape;
/*!
 * Deluge.Keys.js
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

/**
 * @description The torrent status keys that are commonly used around the UI.
 * @class Deluge.Keys
 * @singleton
 */
Deluge.Keys = {

	/**
	 * Keys that are used within the torrent grid.
	 * <pre>['queue', 'name', 'total_wanted', 'state', 'progress', 'num_seeds',
	 * 'total_seeds', 'num_peers', 'total_peers', 'download_payload_rate',
	 * 'upload_payload_rate', 'eta', 'ratio', 'distributed_copies',
	 * 'is_auto_managed', 'time_added', 'tracker_host', 'save_path',
	 * 'total_done', 'total_uploaded', 'max_download_speed', 'max_upload_speed',
	 * 'seeds_peers_ratio']</pre>
	 */
    Grid: [
        'queue', 'name', 'total_wanted', 'state', 'progress', 'num_seeds',
        'total_seeds', 'num_peers', 'total_peers', 'download_payload_rate',
        'upload_payload_rate', 'eta', 'ratio', 'distributed_copies',
        'is_auto_managed', 'time_added', 'tracker_host', 'save_path',
        'total_done', 'total_uploaded', 'max_download_speed', 'max_upload_speed',
        'seeds_peers_ratio'
    ],

    /**
     * Keys used in the status tab of the statistics panel.
     * These get updated to include the keys in {@link #Grid}.
	 * <pre>['total_done', 'total_payload_download', 'total_uploaded',
	 * 'total_payload_upload', 'next_announce', 'tracker_status', 'num_pieces',
	 * 'piece_length', 'is_auto_managed', 'active_time', 'seeding_time',
	 * 'seed_rank']</pre>
	 */
    Status: [
        'total_done', 'total_payload_download', 'total_uploaded',
        'total_payload_upload', 'next_announce', 'tracker_status', 'num_pieces',
        'piece_length', 'is_auto_managed', 'active_time', 'seeding_time',
        'seed_rank'
    ],

    /**
     * Keys used in the files tab of the statistics panel.
     * <pre>['files', 'file_progress', 'file_priorities']</pre>
	 */
    Files: [
        'files', 'file_progress', 'file_priorities'
    ],

    /**
     * Keys used in the peers tab of the statistics panel.
     * <pre>['peers']</pre>
	 */
    Peers: [
        'peers'
    ],

    /**
     * Keys used in the details tab of the statistics panel.
	 */
    Details: [
        'name', 'save_path', 'total_size', 'num_files', 'message',
        'tracker', 'comment'
    ],

    /**
	 * Keys used in the options tab of the statistics panel.
	 * <pre>['max_download_speed', 'max_upload_speed', 'max_connections', 'max_upload_slots',
	 *  'is_auto_managed', 'stop_at_ratio', 'stop_ratio', 'remove_at_ratio', 'private',
	 *  'prioritize_first_last']</pre>
	 */
    Options: [
        'max_download_speed', 'max_upload_speed', 'max_connections',
        'max_upload_slots','is_auto_managed', 'stop_at_ratio', 'stop_ratio',
        'remove_at_ratio', 'private', 'prioritize_first_last',
        'move_completed', 'move_completed_path'
    ]
};

// Merge the grid and status keys together as the status keys contain all the
// grid ones.
Ext.each(Deluge.Keys.Grid, function(key) {
    Deluge.Keys.Status.push(key);
});
/*!
 * Deluge.LoginWindow.js
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

Deluge.LoginWindow = Ext.extend(Ext.Window, {

	firstShow:   true,
	bodyStyle:   'padding: 10px 5px;',
	buttonAlign: 'center',
	closable:    false,
	closeAction: 'hide',
	iconCls:     'x-deluge-login-window-icon',
	layout:      'fit',
	modal:       true,
	plain:       true,
	resizable:   false,
	title:       _('Login'),
	width:       300,
	height:      120,

	initComponent: function() {
		Deluge.LoginWindow.superclass.initComponent.call(this);
		this.on('show', this.onShow, this);

		this.addButton({
			text: _('Login'),
			handler: this.onLogin,
			scope: this
		});

		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			labelWidth: 120,
			labelAlign: 'right',
			defaults: {width: 110},
			defaultType: 'textfield'
		});

		this.passwordField = this.form.add({
			xtype: 'textfield',
			fieldLabel: _('Password'),
			grow: true,
			growMin: '110',
			growMax: '145',
			id: '_password',
			name: 'password',
			inputType: 'password'
		});
		this.passwordField.on('specialkey', this.onSpecialKey, this);
	},

	logout: function() {
		deluge.events.fire('logout');
		deluge.client.auth.delete_session({
			success: function(result) {
				this.show(true);
			},
			scope: this
		});
	},

	show: function(skipCheck) {
		if (this.firstShow) {
			deluge.client.on('error', this.onClientError, this);
			this.firstShow = false;
		}

		if (skipCheck) {
			return Deluge.LoginWindow.superclass.show.call(this);
		}

		deluge.client.auth.check_session({
			success: function(result) {
				if (result) {
					deluge.events.fire('login');
				} else {
					this.show(true);
				}
			},
			failure: function(result) {
				this.show(true);
			},
			scope: this
		});
	},

	onSpecialKey: function(field, e) {
		if (e.getKey() == 13) this.onLogin();
	},

	onLogin: function() {
		var passwordField = this.passwordField;
		deluge.client.auth.login(passwordField.getValue(), {
			success: function(result) {
				if (result) {
					deluge.events.fire('login');
					this.hide();
					passwordField.setRawValue('');
				} else {
					Ext.MessageBox.show({
						title: _('Login Failed'),
						msg: _('You entered an incorrect password'),
						buttons: Ext.MessageBox.OK,
						modal: false,
						fn: function() {
							passwordField.focus(true, 10);
						},
						icon: Ext.MessageBox.WARNING,
						iconCls: 'x-deluge-icon-warning'
					});
				}
			},
			scope: this
		});
	},

	onClientError: function(errorObj, response, requestOptions) {
		if (errorObj.error.code == 1) {
			deluge.events.fire('logout');
			this.show(true);
		}
	},

	onShow: function() {
		this.passwordField.focus(true, 300);
	}
});
/*!
 * Deluge.Menus.js
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

deluge.menus = {
	onTorrentAction: function(item, e) {
		var ids = deluge.torrents.getSelectedIds();
		var action = item.initialConfig.torrentAction;

		switch (action) {
			case 'pause':
			case 'resume':
				deluge.client.core[action + '_torrent'](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'top':
			case 'up':
			case 'down':
			case 'bottom':
				deluge.client.core['queue_' + action](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'edit_trackers':
				deluge.editTrackers.show();
				break;
			case 'update':
				deluge.client.core.force_reannounce(ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'remove':
				deluge.removeWindow.show(ids);
				break;
			case 'recheck':
				deluge.client.core.force_recheck(ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'move':
				deluge.moveStorage.show(ids);
				break;
		}
	}
}

deluge.menus.torrent = new Ext.menu.Menu({
	id: 'torrentMenu',
	items: [{
		torrentAction: 'pause',
		text: _('Pause'),
		iconCls: 'icon-pause',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, {
		torrentAction: 'resume',
		text: _('Resume'),
		iconCls: 'icon-resume',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, '-', {
		text: _('Options'),
		iconCls: 'icon-options',
		hideOnClick: false,
		menu: new Ext.menu.Menu({
			items: [{
				text: _('D/L Speed Limit'),
				iconCls: 'x-deluge-downloading',
				hideOnClick: false,
				menu: new Ext.menu.Menu({
					items: [{
						text: _('5 KiB/s')
					}, {
						text: _('10 KiB/s')
					}, {
						text: _('30 KiB/s')
					}, {
						text: _('80 KiB/s')
					}, {
						text: _('300 KiB/s')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('U/L Speed Limit'),
				iconCls: 'x-deluge-seeding',
				hideOnClick: false,
				menu: new Ext.menu.Menu({
					items: [{
						text: _('5 KiB/s')
					}, {
						text: _('10 KiB/s')
					}, {
						text: _('30 KiB/s')
					}, {
						text: _('80 KiB/s')
					}, {
						text: _('300 KiB/s')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('Connection Limit'),
				iconCls: 'x-deluge-connections',
				hideOnClick: false,
				menu: new Ext.menu.Menu({
					items: [{
						text: _('50')
					}, {
						text: _('100')
					}, {
						text: _('200')
					}, {
						text: _('300')
					}, {
						text: _('500')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				text: _('Upload Slot Limit'),
				iconCls: 'icon-upload-slots',
				hideOnClick: false,
				menu: new Ext.menu.Menu({
					items: [{
						text: _('0')
					}, {
						text: _('1')
					}, {
						text: _('2')
					}, {
						text: _('3')
					}, {
						text: _('5')
					},{
						text: _('Unlimited')
					}]
				})
			}, {
				id: 'auto_managed',
				text: _('Auto Managed'),
				checked: false
			}]
		})
	}, '-', {
		text: _('Queue'),
		iconCls: 'icon-queue',
		hideOnClick: false,
		menu: new Ext.menu.Menu({
			items: [{
				torrentAction: 'top',
				text: _('Top'),
				iconCls: 'icon-top',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			},{
				torrentAction: 'up',
				text: _('Up'),
				iconCls: 'icon-up',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			},{
				torrentAction: 'down',
				text: _('Down'),
				iconCls: 'icon-down',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			},{
				torrentAction: 'bottom',
				text: _('Bottom'),
				iconCls: 'icon-bottom',
				handler: deluge.menus.onTorrentAction,
				scope: deluge.menus
			}]
		})
	}, '-', {
		torrentAction: 'update',
		text: _('Update Tracker'),
		iconCls: 'icon-update-tracker',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, {
		torrentAction: 'edit_trackers',
		text: _('Edit Trackers'),
		iconCls: 'icon-edit-trackers',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, '-', {
		torrentAction: 'remove',
		text: _('Remove Torrent'),
		iconCls: 'icon-remove',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, '-', {
		torrentAction: 'recheck',
		text: _('Force Recheck'),
		iconCls: 'icon-recheck',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}, {
		torrentAction: 'move',
		text: _('Move Storage'),
		iconCls: 'icon-move',
		handler: deluge.menus.onTorrentAction,
		scope: deluge.menus
	}]
});

deluge.menus.filePriorities = new Ext.menu.Menu({
	id: 'filePrioritiesMenu',
	items: [{
		id: 'expandAll',
		text: _('Expand All'),
		iconCls: 'icon-expand-all'
	}, '-', {
		id: 'no_download',
		text: _('Do Not Download'),
		iconCls: 'icon-do-not-download',
		filePriority: FILE_PRIORITY['Do Not Download']
	}, {
		id: 'normal',
		text: _('Normal Priority'),
		iconCls: 'icon-normal',
		filePriority: FILE_PRIORITY['Normal Priority']
	}, {
		id: 'high',
		text: _('High Priority'),
		iconCls: 'icon-high',
		filePriority: FILE_PRIORITY['High Priority']
	}, {
		id: 'highest',
		text: _('Highest Priority'),
		iconCls: 'icon-highest',
		filePriority: FILE_PRIORITY['Highest Priority']
	}]
});
/*!
 * Deluge.MoveStorage.js
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

Ext.namespace('Deluge');
Deluge.MoveStorage = Ext.extend(Ext.Window, {
	
	constructor: function(config) {
		config = Ext.apply({
			title: _('Move Storage'),
			width: 375,
			height: 110,
			layout: 'fit',
			buttonAlign: 'right',
			closeAction: 'hide',
			closable: true,
			iconCls: 'x-deluge-move-storage',
			plain: true,
			resizable: false
		}, config);
		Deluge.MoveStorage.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Deluge.MoveStorage.superclass.initComponent.call(this);

		this.addButton(_('Cancel'), this.onCancel, this);
		this.addButton(_('Move'), this.onMove, this);

		this.form = this.add({
			xtype: 'form',
			border: false,
			defaultType: 'textfield',
			width: 300,
			bodyStyle: 'padding: 5px'
		});

		this.moveLocation = this.form.add({
			fieldLabel: _('Location'),
			name: 'location',
			width: 240
		});
		//this.form.add({
		//	xtype: 'button',
		//	text: _('Browse'),
		//	handler: function() {
		//		if (!this.fileBrowser) {
		//			this.fileBrowser = new Deluge.FileBrowser();
		//		}
		//		this.fileBrowser.show();
		//	},
		//	scope: this
		//});
	},

	hide: function() {
		Deluge.MoveStorage.superclass.hide.call(this);
		this.torrentIds = null;
	},

	show: function(torrentIds) {
		Deluge.MoveStorage.superclass.show.call(this);
		this.torrentIds = torrentIds;
	},

	onCancel: function() {
		this.hide();
	},

	onMove: function() {
		var dest = this.moveLocation.getValue();
		deluge.client.core.move_storage(this.torrentIds, dest);
		this.hide();
	}
});
deluge.moveStorage = new Deluge.MoveStorage();
/*!
 * Deluge.MultiOptionsManager.js
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

/**
 * @description A class that can be used to manage options throughout the ui.
 * @namespace Deluge
 * @class Deluge.MultiOptionsManager
 * @extends Deluge.OptionsManager
 */
Deluge.MultiOptionsManager = Ext.extend(Deluge.OptionsManager, {

	constructor: function(config) {
		this.currentId = null;
		this.stored = {};
		Deluge.MultiOptionsManager.superclass.constructor.call(this, config);
	},
	
	/**
	 * Changes bound fields to use the specified id.
	 * @param {String} id
	 */
	changeId: function(id, dontUpdateBinds) {
		var oldId = this.currentId;
		this.currentId = id;
		if (!dontUpdateBinds) {
			for (var option in this.options) {
				if (!this.binds[option]) continue;
				Ext.each(this.binds[option], function(bind) {
					bind.setValue(this.get(option));
				}, this);
			}
		}
		return oldId;
	},

	/**
	 * Changes all the changed values to be the default values
	 * @param {String} id
	 */
	commit: function() {
		this.stored[this.currentId] = Ext.apply(this.stored[this.currentId], this.changed[this.currentId]);
		this.reset();
	},
	
	/**
	 * Get the value for an option
	 * @param {String/Array} option A single option or an array of options to return.
	 * @returns {Object} the options value.
	 */
	get: function() {
		if (arguments.length == 1) {
			var option = arguments[0];
			return (this.isDirty(option)) ? this.changed[this.currentId][option] : this.getDefault(option);
		} else if (arguments.length == 0) {
			var options = {};
			for (var option in this.options) {
			    options[option] = (this.isDirty(option)) ? this.changed[this.currentId][option] : this.getDefault(option);
			}
			return options;
		} else {
			var options = {};
			Ext.each(arguments, function(option) {
				options[option] = (this.isDirty(option)) ? this.changed[this.currentId][option] : this.getDefault(option);
			}, this);
			return options;
		}
	},

	/**
	 * Get the default value for an option.
	 * @param {String} option A single option.
	 * @returns {Object} the value of the option
	 */
	getDefault: function(option) {
		return (this.has(option)) ? this.stored[this.currentId][option] : this.options[option];
	},

	/**
	 * Returns the dirty (changed) values.
	 * @returns {Object} the changed options
	 */
	getDirty: function() {
		return (this.changed[this.currentId]) ? this.changed[this.currentId] : {};
	},

	/**
	 * Check to see if the option has been changed.
	 * @param {String} option
	 * @returns {Boolean} true if the option has been changed, else false.
	 */
	isDirty: function(option) {
		return (this.changed[this.currentId] && !Ext.isEmpty(this.changed[this.currentId][option]));
	},

	/**
	 * Check to see if an id has had an option set to something other than the
	 * default value.
	 * @param {String} option
	 * @returns {Boolean} true if the id has an option, else false.
	 */
	has: function(option) {
		return (this.stored[this.currentId] && !Ext.isEmpty(this.stored[this.currentId][option]));
	},

	/**
	 * Reset the options back to the default values for the specified id.
	 */
	reset: function() {
		if (this.changed[this.currentId]) delete this.changed[this.currentId];
		if (this.stored[this.currentId]) delete this.stored[this.currentId];
	},

	/**
	 * Reset the options back to their defaults for all ids.
	 */
	resetAll: function() {
		this.changed = {};
		this.stored = {};
		this.changeId(null);
	},

	/**
	 * Sets the value of specified option for the passed in id.
	 * @param {String} id
	 * @param {String} option
	 * @param {Object} value The value for the option
	 */
	setDefault: function(option, value) {
		if (option === undefined) {
			return;
		} else if (value === undefined) {
			for (var key in option) {
				this.setDefault(key, option[key]);
			}
		} else {
			var oldValue = this.getDefault(option);
			value = this.convertValueType(oldValue, value);
			
			// If the value is the same as the old value there is 
			// no point in setting it again.
			if (oldValue == value) return;
			
			// Store the new default
			if (!this.stored[this.currentId]) this.stored[this.currentId] = {};
			this.stored[this.currentId][option] = value;
			
			if (!this.isDirty(option)) {
				this.fireEvent('changed', option, value, oldValue);
			}
		}
	},

	/**
	 * Update the value for the specified option and id.
	 * @param {String} id
	 * @param {String/Object} option or options to update
	 * @param {Object} [value];
	 */
	update: function(option, value) {
		if (option === undefined) {
			return;
		} else if (value === undefined) {
			for (var key in option) {
				this.update(key, option[key]);
			}
		} else {
			if (!this.changed[this.currentId]) this.changed[this.currentId] = {};

			var defaultValue = this.getDefault(option);
			value = this.convertValueType(defaultValue, value);
			
			var oldValue = this.get(option);
			if (oldValue == value) return;

			if (defaultValue == value) {
				if (this.isDirty(option)) delete this.changed[this.currentId][option];
				this.fireEvent('changed', option, value, oldValue);
				return;
			} else {
				this.changed[this.currentId][option] = value;
				this.fireEvent('changed', option, value, oldValue);
			}
		}
	}
});
/*!
 * Deluge.OtherLimitWindow.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.OtherLimitWindow
 * @extends Ext.Window
 */
Deluge.OtherLimitWindow = Ext.extend(Ext.Window, {
	
	layout: 'fit',
	width: 210,
	height: 100,

	closeAction: 'hide',

	initComponent: function() {
		Deluge.OtherLimitWindow.superclass.initComponent.call(this);
		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			bodyStyle: 'padding: 5px',
			layout: 'hbox',
			layoutConfig: {
				pack: 'start'
			},
			items: [{
				xtype: 'spinnerfield',
				name: 'limit'
			}]
		});
		if (this.initialConfig.unit) {
			this.form.add({
				border: false,
				baseCls: 'x-plain',
				bodyStyle: 'padding: 5px',
				html: this.initialConfig.unit
			});
		} else {
			this.setSize(180, 100);
		}

		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Ok'), this.onOkClick, this);
		this.afterMethod('show', this.doFocusField, this);
	},

	setValue: function(value) {
		this.form.getForm().setValues({limit: value});
	},

	onCancelClick: function() {
		this.form.getForm().reset();
		this.hide();
	},

	onOkClick: function() {
		var config = {};
		config[this.group] = this.form.getForm().getValues().limit;
		deluge.client.core.set_config(config, {
			success: function() {
				deluge.ui.update();
			}
		});
		this.hide();
	},

	doFocusField: function() {
		this.form.getForm().findField('limit').focus(true, 10);
	}
});
/*!
 * Deluge.Plugin.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.Plugin
 * @extends Ext.util.Observable
 */
Deluge.Plugin = Ext.extend(Ext.util.Observable, {

	/**
	 * The plugins name
	 * @property name
	 * @type {String}
	 */
	name: null,

	constructor: function(config) {
		this.isDelugePlugin = true;
		this.addEvents({
			/**
			 * @event enabled
			 * @param {Plugin} plugin the plugin instance
			 */
			"enabled": true,

			/**
			 * @event disabled
			 * @param {Plugin} plugin the plugin instance
			 */
			"disabled": true
		});
		Deluge.Plugin.superclass.constructor.call(this, config);
	},
	
	/**
	 * Disables the plugin, firing the "{@link #disabled}" event and
	 * then executing the plugins clean up method onDisabled.
	 */
	disable: function() {
		this.fireEvent("disabled", this);
		if (this.onDisable) this.onDisable();
	},
	
	/**
	 * Enables the plugin, firing the "{@link #enabled}" event and
	 * then executes the plugins setup method, onEnabled.
	 */
	enable: function() {
        deluge.client.reloadMethods();
		this.fireEvent("enable", this);
		if (this.onEnable) this.onEnable();
	},

	registerTorrentStatus: function(key, header, options) {
		options = options || {};
		var cc = options.colCfg || {}, sc = options.storeCfg || {};
		sc = Ext.apply(sc, {name: key});
		deluge.torrents.meta.fields.push(sc);
		deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);

		cc = Ext.apply(cc, {
			header: header,
			dataIndex: key
		});
		var cols = deluge.torrents.columns.slice(0);
		cols.push(cc);
		deluge.torrents.colModel.setConfig(cols);
		deluge.torrents.columns = cols;

		Deluge.Keys.Grid.push(key);
		deluge.torrents.getView().refresh(true);
	},

	deregisterTorrentStatus: function(key) {
		var fields = [];
		Ext.each(deluge.torrents.meta.fields, function(field) {
			if (field.name != key) fields.push(field);
		});
		deluge.torrents.meta.fields = fields;
		deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);

		var cols = [];
		Ext.each(deluge.torrents.columns, function(col) {
			if (col.dataIndex != key) cols.push(col);
		});
		deluge.torrents.colModel.setConfig(cols);
		deluge.torrents.columns = cols;

		var keys = [];
		Ext.each(Deluge.Keys.Grid, function(k) {
			if (k == key) keys.push(k);
		});
		Deluge.Keys.Grid = keys;
		deluge.torrents.getView().refresh(true);
	}
});

Ext.ns('Deluge.plugins');
/*!
 * Deluge.RemoveWindow.js
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

/**
 * @class Deluge.RemoveWindow
 * @extends Ext.Window
 */
Deluge.RemoveWindow = Ext.extend(Ext.Window, {
    
    title:  _('Remove Torrent'),
    layout: 'fit',
    width:  350,
	height: 100,
    
    buttonAlign: 'right',
    closeAction: 'hide',
    closable:    true,
    iconCls:     'x-deluge-remove-window-icon',
    plain:       true,
    
    bodyStyle: 'padding: 5px; padding-left: 10px;',
    html: 'Are you sure you wish to remove the torrent (s)?',
	
	initComponent: function() {
		Deluge.RemoveWindow.superclass.initComponent.call(this);
		this.addButton(_('Cancel'), this.onCancel, this);
		this.addButton(_('Remove With Data'), this.onRemoveData, this);
		this.addButton(_('Remove Torrent'), this.onRemove, this);
	},
	
	remove: function(removeData) {
		Ext.each(this.torrentIds, function(torrentId) {
			deluge.client.core.remove_torrent(torrentId, removeData, {
				success: function() {
					this.onRemoved(torrentId);
				},
				scope: this,
				torrentId: torrentId
			});
		}, this);
		
	},
	
	show: function(ids) {
		Deluge.RemoveWindow.superclass.show.call(this);
		this.torrentIds = ids;
	},
	
	onCancel: function() {
		this.hide();
		this.torrentIds = null;
	},
	
	onRemove: function() {
		this.remove(false);
	},
	
	onRemoveData: function() {
		this.remove(true);
	},
	
	onRemoved: function(torrentId) {
		deluge.events.fire('torrentRemoved', torrentId);
		this.hide();
		deluge.ui.update();
	}
});

deluge.removeWindow = new Deluge.RemoveWindow();
/*!
 * Deluge.Sidebar.js
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

// These are just so gen_gettext.py will pick up the strings
// _('State')
// _('Tracker Host')

/**
 * @class Deluge.Sidebar
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 */
Deluge.Sidebar = Ext.extend(Ext.Panel, {

	// private
	panels: {},

	// private
	selected: null,

	constructor: function(config) {
		config = Ext.apply({
			id: 'sidebar',
			region: 'west',
			cls: 'deluge-sidebar',
			title: _('Filters'),
			layout: 'accordion',
			split: true,
			width: 200,
			minSize: 100,
			collapsible: true,
			margins: '5 0 0 5',
			cmargins: '5 0 0 5'
		}, config);
		Deluge.Sidebar.superclass.constructor.call(this, config);
	},

	// private
	initComponent: function() {
		Deluge.Sidebar.superclass.initComponent.call(this);
		deluge.events.on("disconnect", this.onDisconnect, this);
	},

	createFilter: function(filter, states) {
		var panel = new Deluge.FilterPanel({
			filter: filter
		});
		panel.on('selectionchange', function(view, nodes) {
			deluge.ui.update();
		});
		this.add(panel);
	
		this.doLayout();
		this.panels[filter] = panel;

		panel.header.on('click', function(header) {
			if (!deluge.config.sidebar_multiple_filters) {
				deluge.ui.update();
			}
			if (!panel.list.getSelectionCount()) {
				panel.list.select(0);	
			}
		});
		this.fireEvent('filtercreate', this, panel);

		panel.updateStates(states);
		this.fireEvent('afterfiltercreate', this, panel);
	},

	getFilter: function(filter) {
		return this.panels[filter];
	},

	getFilterStates: function() {
		var states = {}

		if (deluge.config.sidebar_multiple_filters) {
			// Grab the filters from each of the filter panels
			this.items.each(function(panel) {
				var state = panel.getState();
				if (state == null) return;
				states[panel.filterType] = state;
			}, this);
		} else {
			var panel = this.getLayout().activeItem;
			if (panel) {
				var state = panel.getState();
				if (!state == null) return;
				states[panel.filterType] = state;
			}
		}

		return states;
	},

	hasFilter: function(filter) {
		return (this.panels[filter]) ? true : false;
	},

	// private
	onDisconnect: function() {
		for (var filter in this.panels) {
			this.remove(this.panels[filter]);
		}
		this.panels = {};
		this.selected = null;
	},

	onFilterSelect: function(selModel, rowIndex, record) {
		deluge.ui.update();
	},

	update: function(filters) {
		for (var filter in filters) {
			var states = filters[filter];
			if (Ext.getKeys(this.panels).indexOf(filter) > -1) {
				this.panels[filter].updateStates(states);
			} else {
				this.createFilter(filter, states);
			}
		}

		// Perform a cleanup of fitlers that aren't enabled any more
		Ext.each(Ext.keys(this.panels), function(filter) {
			if (Ext.keys(filters).indexOf(filter) == -1) {
				// We need to remove the panel
				this.remove(this.panels[filter]);
				this.doLayout();
				delete this.panels[filter];
			}
		}, this);
	}
});
/*!
 * Deluge.Statusbar.js
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
Ext.namespace('Deluge');

Deluge.Statusbar = Ext.extend(Ext.ux.StatusBar, {
	constructor: function(config) {
		config = Ext.apply({
			id: 'deluge-statusbar',
			defaultIconCls: 'x-deluge-statusbar x-not-connected',
			defaultText: _('Not Connected')
		}, config);
		Deluge.Statusbar.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Deluge.Statusbar.superclass.initComponent.call(this);

		deluge.events.on('connect', this.onConnect, this);
		deluge.events.on('disconnect', this.onDisconnect, this);
	},

	createButtons: function() {
		this.buttons = this.add({
			id: 'statusbar-connections',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-connections',
			tooltip: _('Connections'),
			menu: new Deluge.StatusbarMenu({
				items: [{
					text: '50',
					value: '50',
					group: 'max_connections_global',
					checked: false
				},{
					text: '100',
					value: '100',
					group: 'max_connections_global',
					checked: false
				},{
					text: '200',
					value: '200',
					group: 'max_connections_global',
					checked: false
				},{
					text: '300',
					value: '300',
					group: 'max_connections_global',
					checked: false
				},{
					text: '500',
					value: '500',
					group: 'max_connections_global',
					checked: false
				},{
					text: _('Unlimited'),
					value: '-1',
					group: 'max_connections_global',
					checked: false
				},'-',{
					text: _('Other'),
					value: 'other',
					group: 'max_connections_global',
					checked: false
				}],
				otherWin: {
					title: _('Set Maximum Connections')
				}
			})
		}, '-', {
			id: 'statusbar-downspeed',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-downloading',
			tooltip: _('Download Speed'),
			menu: new Deluge.StatusbarMenu({
				items: [{
					value: '5',
					text: '5 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '10',
					text: '10 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '30',
					text: '30 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '80',
					text: '80 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '300',
					text: '300 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '-1',
					text: _('Unlimited'),
					group: 'max_download_speed',
					checked: false
				},'-',{
					value: 'other',
					text: _('Other'),
					group: 'max_download_speed',
					checked: false
				}],
				otherWin: {
					title: _('Set Maximum Download Speed'),
					unit: _('Kib/s')
				}
			})
		}, '-', {
			id: 'statusbar-upspeed',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-seeding',
			tooltip: _('Upload Speed'),
			menu: new Deluge.StatusbarMenu({
				items: [{
					value: '5',
					text: '5 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '10',
					text: '10 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '30',
					text: '30 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '80',
					text: '80 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '300',
					text: '300 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '-1',
					text: _('Unlimited'),
					group: 'max_upload_speed',
					checked: false
				},'-',{
					value: 'other',
					text: _('Other'),
					group: 'max_upload_speed',
					checked: false
				}],
				otherWin: {
					title: _('Set Maximum Upload Speed'),
					unit: _('Kib/s')
				}
			})
		}, '-', {
			id: 'statusbar-traffic',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-traffic',
			tooltip: _('Protocol Traffic Download/Upload'),
			handler: function() {
				deluge.preferences.show();
				deluge.preferences.selectPage('Network');
			}
		}, '-', {
			id: 'statusbar-dht',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-dht',
			tooltip: _('DHT Nodes')
		}, '-', {
			id: 'statusbar-freespace',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-freespace',
			tooltip: _('Freespace in download location'),
			handler: function() {
				deluge.preferences.show();
				deluge.preferences.selectPage('Downloads');
			}
		});
		this.created = true;
	},

	onConnect: function() {
		this.setStatus({
			iconCls: 'x-connected',
			text: ''
		});
		if (!this.created) {
			this.createButtons();
		} else {
			Ext.each(this.buttons, function(item) {
				item.show();
				item.enable();
			});
		}
		this.doLayout();
	},

	onDisconnect: function() {
		this.clearStatus({useDefaults:true});
		Ext.each(this.buttons, function(item) {
			item.hide();
			item.disable();
		});
		this.doLayout();
	},

	update: function(stats) {
		if (!stats) return;

		function addSpeed(val) {return val + ' KiB/s'}

		var updateStat = function(name, config) {
			var item = this.items.get('statusbar-' + name);
			if (config.limit.value > 0) {
				var value = (config.value.formatter) ? config.value.formatter(config.value.value, true) : config.value.value;
				var limit = (config.limit.formatter) ? config.limit.formatter(config.limit.value, true) : config.limit.value;
				var str = String.format(config.format, value, limit);
			} else {
				var str = (config.value.formatter) ? config.value.formatter(config.value.value, true) : config.value.value;
			}
			item.setText(str);

			if (!item.menu) return;
			item.menu.setValue(config.limit.value);
		}.createDelegate(this);

		updateStat('connections', {
			value: {value: stats.num_connections},
			limit: {value: stats.max_num_connections},
			format: '{0} ({1})'
		});

		updateStat('downspeed', {
			value: {
				value: stats.download_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_download,
				formatter: addSpeed
			},
			format: '{0} ({1})'
		});

		updateStat('upspeed', {
			value: {
				value: stats.upload_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_upload,
				formatter: addSpeed
			},
			format: '{0} ({1})'
		});

		updateStat('traffic', {
			value: {
				value: stats.download_protocol_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.upload_protocol_rate,
				formatter: Deluge.Formatters.speed
			},
			format: '{0}/{1}'
		});

		this.items.get('statusbar-dht').setText(stats.dht_nodes);
		this.items.get('statusbar-freespace').setText(fsize(stats.free_space));
	}
});
/*!
 * Deluge.Toolbar.js
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

/**
 * An extension of the <tt>Ext.Toolbar</tt> class that provides an extensible toolbar for Deluge.
 * @class Deluge.Toolbar
 * @extends Ext.Toolbar
 */
Deluge.Toolbar = Ext.extend(Ext.Toolbar, {
	constructor: function(config) {
		config = Ext.apply({
			items: [
				{
					id: 'tbar-deluge-text',
					disabled: true,
					text: _('Deluge'),
					iconCls: 'x-deluge-main-panel',
				}, new Ext.Toolbar.Separator(),
				{
					id: 'create',
					disabled: true,
					hidden: true,
					text: _('Create'),
					iconCls: 'icon-create',
					handler: this.onTorrentAction
				},{
					id: 'add',
					disabled: true,
					text: _('Add'),
					iconCls: 'icon-add',
					handler: this.onTorrentAdd
				},{
					id: 'remove',
					disabled: true,
					text: _('Remove'),
					iconCls: 'icon-remove',
					handler: this.onTorrentAction
				}, new Ext.Toolbar.Separator(),{
					id: 'pause',
					disabled: true,
					text: _('Pause'),
					iconCls: 'icon-pause',
					handler: this.onTorrentAction
				},{
					id: 'resume',
					disabled: true,
					text: _('Resume'),
					iconCls: 'icon-resume',
					handler: this.onTorrentAction
				}, new Ext.Toolbar.Separator(),{
					id: 'up',
					cls: 'x-btn-text-icon',
					disabled: true,
					text: _('Up'),
					iconCls: 'icon-up',
					handler: this.onTorrentAction
				},{
					id: 'down',
					disabled: true,
					text: _('Down'),
					iconCls: 'icon-down',
					handler: this.onTorrentAction
				}, new Ext.Toolbar.Separator(),{
					id: 'preferences',
					text: _('Preferences'),
					iconCls: 'x-deluge-preferences',
					handler: this.onPreferencesClick,
					scope: this
				},{
					id: 'connectionman',
					text: _('Connection Manager'),
					iconCls: 'x-deluge-connection-manager',
					handler: this.onConnectionManagerClick,
					scope: this
				},'->',{
					id: 'help',
					iconCls: 'icon-help',
					text: _('Help'),
					handler: this.onHelpClick,
					scope: this
				},{
					id: 'logout',
					iconCls: 'icon-logout',
					disabled: true,
					text: _('Logout'),
					handler: this.onLogout,
					scope: this
				}
			]
		}, config);
		Deluge.Toolbar.superclass.constructor.call(this, config);
	},

	connectedButtons: [
		'add', 'remove', 'pause', 'resume', 'up', 'down'
	],
	
	initComponent: function() {
		Deluge.Toolbar.superclass.initComponent.call(this);
		deluge.events.on('connect', this.onConnect, this);
		deluge.events.on('login', this.onLogin, this);
	},
	
	onConnect: function() {
		Ext.each(this.connectedButtons, function(buttonId) {
			this.items.get(buttonId).enable();
		}, this);
	},
	
	onDisconnect: function() {
		Ext.each(this.connectedButtons, function(buttonId) {
			this.items.get(buttonId).disable();
		}, this);
	},
	
	onLogin: function() {
		this.items.get('logout').enable();
	},
	
	onLogout: function() {
		this.items.get('logout').disable();
		deluge.login.logout();
	},
	
	onConnectionManagerClick: function() {
		deluge.connectionManager.show();
	},
	
	onHelpClick: function() {
		window.open('http://dev.deluge-torrent.org/wiki/UserGuide');
	},
	
	onPreferencesClick: function() {
		deluge.preferences.show();
	},
	
	onTorrentAction: function(item) {
		var selection = deluge.torrents.getSelections();
		var ids = [];
		Ext.each(selection, function(record) {
			ids.push(record.id);
		});
		
		switch (item.id) {
			case 'remove':
				deluge.removeWindow.show(ids);
				break;
			case 'pause':
			case 'resume':
				deluge.client.core[item.id + '_torrent'](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
			case 'up':
			case 'down':
				deluge.client.core['queue_' + item.id](ids, {
					success: function() {
						deluge.ui.update();
					}
				});
				break;
		}
	},
	
	onTorrentAdd: function() {
		deluge.add.show();
	}
});
/*!
 * Deluge.TorrentGrid.js
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

(function() {

	/* Renderers for the Torrent Grid */
	function queueRenderer(value) {
		return (value == -1) ? '' : value + 1;
	}
	function torrentNameRenderer(value, p, r) {
		return String.format('<div class="torrent-name x-deluge-{0}">{1}</div>', r.data['state'].toLowerCase(), value);
	}
	function torrentSpeedRenderer(value) {
		if (!value) return;
		return fspeed(value);
	}
	function torrentLimitRenderer(value) {
		if (value == -1) return '';
		return fspeed(value * 1024.0);
	}
	function torrentProgressRenderer(value, p, r) {
		value = new Number(value);
		var progress = value;
		var text = r.data['state'] + ' ' + value.toFixed(2) + '%';
		if ( this.style ) {
			var style = this.style
		} else {
			var style = p.style
		}
		var width = new Number(style.match(/\w+:\s*(\d+)\w+/)[1]);
		return Deluge.progressBar(value, width - 8, text);
	}
	function seedsRenderer(value, p, r) {
		if (r.data['total_seeds'] > -1) {
			return String.format('{0} ({1})', value, r.data['total_seeds']);
		} else {
			return value;
		}
	}
	function peersRenderer(value, p, r) {
		if (r.data['total_peers'] > -1) {
			return String.format('{0} ({1})', value, r.data['total_peers']);
		} else {
			return value;
		}
	}
	function availRenderer(value, p, r)	{
		return (value < 0) ? '&infin;' : parseFloat(new Number(value).toFixed(3));
	}
	function trackerRenderer(value, p, r) {
		return String.format('<div style="background: url(' + deluge.config.base + 'tracker/{0}) no-repeat; padding-left: 20px;">{0}</div>', value);
	}

	function etaSorter(eta) {
		return eta * -1;
	}

	/**
	 * Deluge.TorrentGrid Class
	 *
	 * @author Damien Churchill <damoxc@gmail.com>
	 * @version 1.3
	 *
	 * @class Deluge.TorrentGrid
	 * @extends Ext.grid.GridPanel
	 * @constructor
	 * @param {Object} config Configuration options
	 */
	Deluge.TorrentGrid = Ext.extend(Ext.grid.GridPanel, {

		// object to store contained torrent ids
		torrents: {},

		columns: [{
			id:'queue',
			header: _('#'),
			width: 30,
			sortable: true,
			renderer: queueRenderer,
			dataIndex: 'queue'
		}, {
			id:'name',
			header: _('Name'),
			width: 150,
			sortable: true,
			renderer: torrentNameRenderer,
			dataIndex: 'name'
		}, {
			header: _('Size'),
			width: 75,
			sortable: true,
			renderer: fsize,
			dataIndex: 'total_wanted'
		}, {
			header: _('Progress'),
			width: 150,
			sortable: true,
			renderer: torrentProgressRenderer,
			dataIndex: 'progress'
		}, {
			header: _('Down Speed'),
			width: 80,
			sortable: true,
			renderer: torrentSpeedRenderer,
			dataIndex: 'download_payload_rate'
		}, {
			header: _('Up Speed'),
			width: 80,
			sortable: true,
			renderer: torrentSpeedRenderer,
			dataIndex: 'upload_payload_rate'
		}, {
			header: _('ETA'),
			width: 60,
			sortable: true,
			renderer: ftime,
			dataIndex: 'eta'
		}, {
			header: _('Seeders'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: seedsRenderer,
			dataIndex: 'num_seeds'
		}, {
			header: _('Peers'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: peersRenderer,
			dataIndex: 'num_peers'
		}, {
			header: _('Ratio'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: availRenderer,
			dataIndex: 'ratio'
		}, {
			header: _('Avail'),
			hidden: true,
			width: 60,
			sortable: true,
			renderer: availRenderer,
			dataIndex: 'distributed_copies'
		}, {
			header: _('Added'),
			hidden: true,
			width: 80,
			sortable: true,
			renderer: fdate,
			dataIndex: 'time_added'
		}, {
			header: _('Tracker'),
			hidden: true,
			width: 120,
			sortable: true,
			renderer: trackerRenderer,
			dataIndex: 'tracker_host'
		}, {
			header: _('Save Path'),
			hidden: true,
			width: 120,
			sortable: true,
			renderer: fplain,
			dataIndex: 'save_path'
		}, {
			header: _('Downloaded'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: fsize,
			dataIndex: 'total_done'
		}, {
			header: _('Uploaded'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: fsize,
			dataIndex: 'total_uploaded'
		}, {
			header: _('Down Limit'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: torrentLimitRenderer,
			dataIndex: 'max_download_speed'
		}, {
			header: _('Up Limit'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: torrentLimitRenderer,
			dataIndex: 'max_upload_speed'
		}, {
			header: _('Seeders') + '/' + _('Peers'),
			hidden: true,
			width: 75,
			sortable: true,
			renderer: availRenderer,
			dataIndex: 'seeds_peers_ratio'
		}],

		meta: {
			root: 'torrents',
			idProperty: 'id',
			fields: [
				{name: 'queue', sortType: Deluge.data.SortTypes.asQueuePosition},
				{name: 'name', sortType: Deluge.data.SortTypes.asName},
				{name: 'total_wanted', type: 'int'},
				{name: 'state'},
				{name: 'progress', type: 'float'},
				{name: 'num_seeds', type: 'int'},
				{name: 'total_seeds', type: 'int'},
				{name: 'num_peers', type: 'int'},
				{name: 'total_peers', type: 'int'},
				{name: 'download_payload_rate', type: 'int'},
				{name: 'upload_payload_rate', type: 'int'},
				{name: 'eta', type: 'int', sortType: etaSorter},
				{name: 'ratio', type: 'float'},
				{name: 'distributed_copies', type: 'float'},
				{name: 'time_added', type: 'int'},
				{name: 'tracker_host'},
				{name: 'save_path'},
				{name: 'total_done', type: 'int'},
				{name: 'total_uploaded', type: 'int'},
				{name: 'max_download_speed', type: 'int'},
				{name: 'max_upload_speed', type: 'int'},
				{name: 'seeds_peers_ratio', type: 'float'}
			]
		},

		keys: [{
			key: 'a',
			ctrl: true,
			stopEvent: true,
			handler: function() {
				deluge.torrents.getSelectionModel().selectAll();
			}
		}, {
			key: [46],
			stopEvent: true,
			handler: function() {
				ids = deluge.torrents.getSelectedIds();
				deluge.removeWindow.show(ids);
			}
		}],

		constructor: function(config) {
			config = Ext.apply({
				id: 'torrentGrid',
				store: new Ext.data.JsonStore(this.meta),
				columns: this.columns,
				keys: this.keys,
				region: 'center',
				cls: 'deluge-torrents',
				stripeRows: true,
				autoExpandColumn: 'name',
				autoExpandMin: 150,
				deferredRender:false,
				autoScroll:true,
				margins: '5 5 0 0',
				stateful: true,
				view: new Ext.ux.grid.BufferView({
					rowHeight: 26,
					scrollDelay: false
				})
			}, config);
			Deluge.TorrentGrid.superclass.constructor.call(this, config);
		},

	initComponent: function() {
		Deluge.TorrentGrid.superclass.initComponent.call(this);
		deluge.events.on('torrentRemoved', this.onTorrentRemoved, this);
		deluge.events.on('disconnect', this.onDisconnect, this);

		this.on('rowcontextmenu', function(grid, rowIndex, e) {
			e.stopEvent();
			var selection = grid.getSelectionModel();
			if (!selection.isSelected(rowIndex)) {
				selection.selectRow(rowIndex);
			}
			deluge.menus.torrent.showAt(e.getPoint());
		});
	},

	/**
	 * Returns the record representing the torrent at the specified index.
	 *
	 * @param index {int} The row index of the torrent you wish to retrieve.
	 * @return {Ext.data.Record} The record representing the torrent.
	 */
	getTorrent: function(index) {
		return this.getStore().getAt(index);
	},

	/**
	 * Returns the currently selected record.
	 * @ return {Array/Ext.data.Record} The record(s) representing the rows
	 */
	getSelected: function() {
		return this.getSelectionModel().getSelected();
	},

	/**
	 * Returns the currently selected records.
	 */
	getSelections: function() {
		return this.getSelectionModel().getSelections();
	},

	/**
	 * Return the currently selected torrent id.
	 * @return {String} The currently selected id.
	 */
	getSelectedId: function() {
		return this.getSelectionModel().getSelected().id
	},

	/**
	 * Return the currently selected torrent ids.
	 * @return {Array} The currently selected ids.
	 */
	getSelectedIds: function() {
		var ids = [];
		Ext.each(this.getSelectionModel().getSelections(), function(r) {
			ids.push(r.id);
		});
		return ids;
	},

	update: function(torrents, wipe) {
		var store = this.getStore();

		// Need to perform a complete reload of the torrent grid.
		if (wipe) {
			store.removeAll();
			this.torrents = {};
		}

		var newTorrents = [];

		// Update and add any new torrents.
		for (var t in torrents) {
			var torrent = torrents[t];

			if (this.torrents[t]) {
				var record = store.getById(t);
				record.beginEdit();
				for (var k in torrent) {
					if (record.get(k) != torrent[k]) {
						record.set(k, torrent[k]);
					}
				}
				record.endEdit();
			} else {
				var record = new Deluge.data.Torrent(torrent);
				record.id = t;
				this.torrents[t] = 1;
				newTorrents.push(record);
			}
		}
		store.add(newTorrents);

		// Remove any torrents that should not be in the store.
		store.each(function(record) {
			if (!torrents[record.id]) {
				store.remove(record);
				delete this.torrents[record.id];
			}
		}, this);
		store.commitChanges();

		var sortState = store.getSortState()
		if (!sortState) return;
		store.sort(sortState.field, sortState.direction);
	},

	// private
	onDisconnect: function() {
		this.getStore().removeAll();
		this.torrents = {};
	},

	// private
	onTorrentRemoved: function(torrentIds) {
		var selModel = this.getSelectionModel();
		Ext.each(torrentIds, function(torrentId) {
			var record = this.getStore().getById(torrentId);
			if (selModel.isSelected(record)) {
				selModel.deselectRow(this.getStore().indexOf(record));
			}
			this.getStore().remove(record);
			delete this.torrents[torrentId];
		}, this);
	}
});
deluge.torrents = new Deluge.TorrentGrid();
})();
/*!
 * Deluge.UI.js
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

/**
 * @static
 * @class Deluge.UI
 * The controller for the whole interface, that ties all the components
 * together and handles the 2 second poll.
 */
deluge.ui = {

	errorCount: 0,

	filters: null,

	/**
	 * @description Create all the interface components, the json-rpc client
	 * and set up various events that the UI will utilise.
	 */
	initialize: function() {
		deluge.add = new Deluge.add.AddWindow();
		deluge.details = new Deluge.details.DetailsPanel();
		deluge.connectionManager = new Deluge.ConnectionManager();
		deluge.editTrackers = new Deluge.EditTrackersWindow();
		deluge.login = new Deluge.LoginWindow();
		deluge.preferences = new Deluge.preferences.PreferencesWindow();
		deluge.sidebar = new Deluge.Sidebar();
		deluge.statusbar = new Deluge.Statusbar();
		deluge.toolbar = new Deluge.Toolbar();

		this.detailsPanel = new Ext.Panel({
			id: 'detailsPanel',
			cls: 'detailsPanel',
			region: 'south',
			split: true,
			height: 215,
			minSize: 100,
			collapsible: true,
			margins: '0 5 5 5',
			cmargins: '0 5 5 5',
			layout: 'fit',
			items: [
				deluge.details
			],
		});

		this.MainPanel = new Ext.Panel({
			id: 'mainPanel',
			iconCls: 'x-deluge-main-panel',
			layout: 'border',
			border: false,
			tbar: deluge.toolbar,
			items: [
				deluge.sidebar,
				this.detailsPanel,
				deluge.torrents
			],
			bbar: deluge.statusbar
		});

		this.Viewport = new Ext.Viewport({
			layout: 'fit',
			items: [this.MainPanel]
		});

		deluge.events.on("connect", this.onConnect, this);
		deluge.events.on("disconnect", this.onDisconnect, this);
		deluge.events.on('PluginDisabledEvent', this.onPluginDisabled, this);
		deluge.events.on('PluginEnabledEvent', this.onPluginEnabled, this);
		deluge.client = new Ext.ux.util.RpcClient({
			url: deluge.config.base + 'json'
		});

		// enable all the already active plugins
		for (var plugin in Deluge.pluginStore) {
			plugin = Deluge.createPlugin(plugin);
			plugin.enable();
			deluge.plugins[plugin.name] = plugin;
		}

		// Initialize quicktips so all the tooltip configs start working.
		Ext.QuickTips.init();

		deluge.client.on('connected', function(e) {
			deluge.login.show();
		}, this, {single: true});

		this.update = this.update.createDelegate(this);
		this.checkConnection = this.checkConnection.createDelegate(this);

		this.originalTitle = document.title;
	},

	checkConnection: function() {
		deluge.client.web.connected({
			success: this.onConnectionSuccess,
			failure: this.onConnectionError,
			scope: this
		});
	},

	update: function() {
		var filters = deluge.sidebar.getFilterStates();
		this.oldFilters = this.filters;
		this.filters = filters;

		deluge.client.web.update_ui(Deluge.Keys.Grid, filters, {
			success: this.onUpdate,
			failure: this.onUpdateError,
			scope: this
		});
		deluge.details.update();
	},

	onConnectionError: function(error) {

	},

	onConnectionSuccess: function(result) {
		deluge.statusbar.setStatus({
			iconCls: 'x-deluge-statusbar icon-ok',
			text: _('Connection restored')
		});
		clearInterval(this.checking);
		if (!result) {
			deluge.connectionManager.show();
		}
	},

	onUpdateError: function(error) {
		if (this.errorCount == 2) {
			Ext.MessageBox.show({
				title: 'Lost Connection',
				msg: 'The connection to the webserver has been lost!',
				buttons: Ext.MessageBox.OK,
				icon: Ext.MessageBox.ERROR
			});
			deluge.events.fire('disconnect');
			deluge.statusbar.setStatus({
				text: 'Lost connection to webserver'}
			);
			this.checking = setInterval(this.checkConnection, 2000);
		}
		this.errorCount++;
	},

	/**
	 * @static
	 * @private
	 * Updates the various components in the interface.
	 */
	onUpdate: function(data) {
		if (!data['connected']) {
			deluge.connectionManager.disconnect(true);
			return;
		}

		if (deluge.config.show_session_speed) {
			document.title = 'D: ' + fsize_short(data['stats'].download_rate, true) +
				' U: ' + fsize_short(data['stats'].upload_rate, true) + ' - ' +
				this.originalTitle;
		}
		if (Ext.areObjectsEqual(this.filters, this.oldFilters)) {
			deluge.torrents.update(data['torrents']);
		} else {
			deluge.torrents.update(data['torrents'], true);
		}
		deluge.statusbar.update(data['stats']);
		deluge.sidebar.update(data['filters']);
		this.errorCount = 0;
	},

	/**
	 * @static
	 * @private
	 * Start the Deluge UI polling the server and update the interface.
	 */
	onConnect: function() {
		if (!this.running) {
			this.running = setInterval(this.update, 2000);
			this.update();
		}
		deluge.client.web.get_plugins({
			success: this.onGotPlugins,
			scope: this
		});
	},

	/**
	 * @static
	 * @private
	 */
	onDisconnect: function() {
		this.stop();
	},

	onGotPlugins: function(plugins) {
		Ext.each(plugins.enabled_plugins, function(plugin) {
			if (deluge.plugins[plugin]) return;
			deluge.client.web.get_plugin_resources(plugin, {
				success: this.onGotPluginResources,
				scope: this
			});
		}, this);
	},

	onPluginEnabled: function(pluginName) {
		if (deluge.plugins[pluginName]) {
			deluge.plugins[pluginName].enable();
		} else {
			deluge.client.web.get_plugin_resources(pluginName, {
				success: this.onGotPluginResources,
				scope: this
			});
		}
	},

	onGotPluginResources: function(resources) {
		var scripts = (Deluge.debug) ? resources.debug_scripts : resources.scripts;
		Ext.each(scripts, function(script) {
			Ext.ux.JSLoader({
				url: deluge.config.base + script,
				onLoad: this.onPluginLoaded,
				pluginName: resources.name
			});
		}, this);
	},

	onPluginDisabled: function(pluginName) {
		if (deluge.plugins[pluginName]) deluge.plugins[pluginName].disable();
	},

	onPluginLoaded: function(options) {
		// This could happen if the plugin has multiple scripts
		if (!Deluge.hasPlugin(options.pluginName)) return;

		// Enable the plugin
		plugin = Deluge.createPlugin(options.pluginName);
		plugin.enable();
		deluge.plugins[plugin.name] = plugin;
	},

	/**
	 * @static
	 * Stop the Deluge UI polling the server and clear the interface.
	 */
	stop: function() {
		if (this.running) {
			clearInterval(this.running);
			this.running = false;
			deluge.torrents.getStore().removeAll();
		}
	}
}

Ext.onReady(function(e) {
	deluge.ui.initialize();
});
