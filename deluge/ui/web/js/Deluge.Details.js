/*
Script: deluge-details.js
    Contains all objects and functions related to the lower details panel and
	it's containing tabs.

Copyright:
	(C) Damien Churchill 2009 <damoxc@gmail.com>
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
*/

(function() {
	Ext.namespace('Ext.deluge.details');
	Ext.deluge.details.TabPanel = Ext.extend(Ext.TabPanel, {
		
		constructor: function(config) {
			config = Ext.apply({
				region: 'south',
				split: true,
				height: 220,
				minSize: 100,
				collapsible: true,
				margins: '0 5 5 5',
				activeTab: 0
			}, config);
			Ext.deluge.details.TabPanel.superclass.constructor.call(this, config);
		},
		
		clear: function() {
			this.items.each(function(panel) {
				if (panel.clear) panel.clear();
			});
		},
		
		update: function(tab) {
			var torrent = Deluge.Torrents.getSelected();
			if (!torrent) return;
			
			tab = tab || this.getActiveTab();
			if (tab.update) tab.update(torrent.id);
		},
		
		/* Event Handlers */
		
		// We need to add the events in onRender since Deluge.Torrents hasn't
		// been created yet.
		onRender: function(ct, position) {
			Ext.deluge.details.TabPanel.superclass.onRender.call(this, ct, position);
			Deluge.Events.on('disconnect', this.clear, this);
			Deluge.Torrents.on('rowclick', this.onTorrentsClick, this);
			
			Deluge.Torrents.getSelectionModel().on('selectionchange', function(selModel) {
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
	Deluge.Details = new Ext.deluge.details.TabPanel();
})();

/*
Deluge.Details.Files = {
	onRender: function(panel) {
		this.panel = panel;
		this.panel.clear = this.clear.bind(this);
		this.panel.update = this.update.bind(this);
		
		new Ext.tree.TreeSorter(this.panel, {
			folderSort: true
		});
		Deluge.Menus.FilePriorities.on('itemclick', this.onItemClick.bindWithEvent(this));
	},
	
	onContextMenu: function(node, e) {
		e.stopEvent();
		var selModel = this.panel.getSelectionModel();
		if (selModel.getSelectedNodes().length < 2) {
			selModel.clearSelections();
			node.select();
		}
		Deluge.Menus.FilePriorities.showAt(e.getPoint());
	},
	
	onItemClick: function(baseItem, e) {
		switch (baseItem.id) {
			case 'expandAll':
				this.panel.expandAll();
				break;
			default:
				var indexes = new Hash();
				function walk(node) {
					if (!$defined(node.attributes.fileIndex)) return;
					indexes[node.attributes.fileIndex] = node.attributes.priority;
				}
				this.panel.getRootNode().cascade(walk);
				
				var nodes = this.panel.getSelectionModel().getSelectedNodes();
				$each(nodes, function(node) {
					if (!$defined(node.attributes.fileIndex)) return;
					indexes[node.attributes.fileIndex] = baseItem.filePriority;
				});
				
				priorities = new Array(indexes.getLength());
				indexes.each(function(priority, index) {
					priorities[index] = priority;
				});
				
				Deluge.Client.core.set_torrent_file_priorities(this.torrentId, priorities, {
					onSuccess: function() {
						$each(nodes, function(node) {
							node.setColumnValue(3, baseItem.filePriority);
						});
					}.bind(this)
				});
				break;
		}
	},
	
	onRequestComplete: function(files, torrentId) {
		if (this.torrentId != torrentId) {
			this.clear();
			this.torrentId = torrentId;
		}
		function walk(files, parent) {
			$each(files, function(item, file) {
				var child = parent.findChild('id', file);
				if ($type(item) == 'object') {
					if (!child) {
						child = new Ext.tree.TreeNode({
							id: file,
							text: file
						});
						parent.appendChild(child);
					}
					walk(item, child);
				} else {
					if (!child) {
						child = new Ext.tree.ColumnTreeNode({
							id: file,
							filename: file,
							text: file, // this needs to be here for sorting
							fileIndex: item[0],
							size: item[1],
							progress: item[2],
							priority: item[3],
							leaf: true,
							iconCls: 'x-deluge-file',
							uiProvider: Ext.tree.ColumnNodeUI
						});
						parent.appendChild(child);
					}
					child.setColumnValue(1, item[1]);
					child.setColumnValue(2, item[2]);
					child.setColumnValue(3, item[3]);
				}
			});
		}
		var root = this.panel.getRootNode();
		walk(files, root);
		root.firstChild.expand();
	},
	
	clear: function() {
		var root = this.panel.getRootNode();
		if (!root.hasChildNodes()) return;
		root.cascade(function(node) {
			var parent = node.parentNode;
			if (!parent) return;
			if (!parent.ownerTree) return;
			parent.removeChild(node);
		});
	},
	
	update: function(torrentId) {
		Deluge.Client.web.get_torrent_files(torrentId, {
			onSuccess: this.onRequestComplete.bindWithEvent(this, torrentId)
		});
	}
}

Deluge.Details.Peers = {
	onRender: function(panel) {
		this.panel = panel;
		this.panel.update = this.update.bind(this);
		this.panel.clear = this.clear.bind(this);
	},
	
	onRequestComplete: function(torrent) {
		var peers = new Array();
		torrent.peers.each(function(peer) {
			peers.include([peer.country, peer.ip, peer.client, peer.progress, peer.down_speed, peer.up_speed, peer.seed]);
		}, this);
		this.Store.loadData(peers);
	},
	
	clear: function() {
		this.Store.loadData([]);
	},
	
	update: function(torrentId) {
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Peers, {
			onSuccess: this.onRequestComplete.bindWithEvent(this, torrentId)
		});
	}
}

Deluge.Details.Options = {
	onRender: function(panel) {
		panel.layout = new Ext.layout.FormLayout();
		panel.layout.setContainer(panel);
		panel.doLayout();
		this.form = panel.getForm();
	},
	
	onRequestComplete: function(torrent) {
		
	},
	
	clear: function() {
		this.form.findField('max_download_speed').setValue(0);
		this.form.findField('max_upload_speed').setValue(0);
		this.form.findField('max_connections').setValue(0);
		this.form.findField('max_upload_slots').setValue(0);
		this.form.findField('stop_ratio').setValue(0);
		this.form.findField('is_auto_managed').setValue(false);
		this.form.findField('stop_at_ratio').setValue(false);
		this.form.findField('remove_at_ratio').setValue(false);
		this.form.findField('private').setValue(false);
		this.form.findField('prioritize_first_last').setValue(false);
	},
	
	update: function(torrentId) {
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Options, {
			onSuccess: this.onRequestComplete.bindWithEvent(this, torrentId)
		});
	},
	
	reset: function() {
		if (this.torrentId) {
			delete this.changed[this.torrentId];
		}
	}
}

function flag(value) {
	return String.format('<img src="/flag/{0}" />', value);
}

function peer_address(value, p, record) {
	var seed = (record.data['seed'] == 1024) ? 'x-deluge-seed' : 'x-deluge-peer'
	return String.format('<div class="{0}">{1}</div>', seed, value);
}

function file_progress(value) {
	var progress = value * 100;
	return progressBar(progress, this.width - 50, progress.toFixed(2) + '%');
}

function peer_progress(value) {
	var progress = (value * 100).toInt();
	var width = this.style.match(/\w+:\s*(\d+)\w+/)[1].toInt() - 8;
	return progressBar(progress, width, progress + '%');
}

FILE_PRIORITY_CSS = {
	0: 'x-no-download',
	1: 'x-normal-download',
	2: 'x-high-download',
	5: 'x-highest-download'
}

function priority_renderer(value) {
	return String.format('<div class="{0}">{1}</div>', FILE_PRIORITY_CSS[value], _(FILE_PRIORITY[value]));
}

function sort_address(value) {
	var m = value.match(/(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\:(\d+)/);
	var address = 0;
	var parts = [m[1], m[2], m[3], m[4]];
	$each(parts, function(part, index) {
		part = parseInt(part);
		address = address | part << ((3 - index) * 8);
		alert("Total: " + address + "\nPart: " + part + "\nIndex: " + index + "\nCalc: " + (part << ((3 - index) * 8)));
	});
	return address;
}

Deluge.Details.Peers.Store = new Ext.data.SimpleStore({
	fields: [
		{name: 'country'},
		{name: 'address', sortType: sort_address},
		{name: 'client'},
		{name: 'progress', type: 'float'},
		{name: 'downspeed', type: 'int'},
		{name: 'upspeed', type: 'int'},
		{name: 'seed', type: 'int'}
	],
	id: 0
});

Deluge.Details.Panel = new Ext.TabPanel({
	,
	items: [{
		id: 'details',
		title: _('Details'),
		cls: 'deluge-status',
		listeners: {
			'render': {
				fn: Deluge.Details.Details.onRender,
				scope: Deluge.Details.Details
			}
		}
	}, new Ext.tree.ColumnTree({
		id: 'files',
		title: _('Files'),
		rootVisible: false,
		autoScroll: true,
		selModel: new Ext.tree.MultiSelectionModel(),
		
		columns: [{
			header: _('Filename'),
			width: 330,
			dataIndex: 'filename'
		}, {
			header: _('Size'),
			width: 150,
			dataIndex: 'size',
			renderer: fsize
		}, {
			header: _('Progress'),
			width: 150,
			dataIndex: 'progress',
			renderer: file_progress
		}, {
			header: _('Priority'),
			width: 150,
			dataIndex: 'priority',
			renderer: priority_renderer
		}],
		
		root: new Ext.tree.TreeNode({
            text: 'Files'
        }),
		listeners: {
			'render': {
				fn: Deluge.Details.Files.onRender,
				scope: Deluge.Details.Files
			},
			'contextmenu': {
				fn: Deluge.Details.Files.onContextMenu,
				scope: Deluge.Details.Files
			}
		}
	}), new Ext.grid.GridPanel({
		id: 'peers',
		title: _('Peers'),
		cls: 'x-deluge-peers',
		store: Deluge.Details.Peers.Store,
		columns: [
			{header: '&nbsp;', width: 30, sortable: true, renderer: flag, dataIndex: 'country'},
			{header: 'Address', width: 125, sortable: true, renderer: peer_address, dataIndex: 'address'},
			{header: 'Client', width: 125, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'client'},
			{header: 'Progress', width: 150, sortable: true, renderer: peer_progress, dataIndex: 'progress'},
			{header: 'Down Speed', width: 100, sortable: true, renderer: fspeed, dataIndex: 'downspeed'},
			{header: 'Up Speed', width: 100, sortable: true, renderer: fspeed, dataIndex: 'upspeed'}
		],	
		stripeRows: true,
		deferredRender:false,
		autoScroll:true,
		margins: '0 0 0 0',
		listeners: {
			'render': {
				fn: Deluge.Details.Peers.onRender,
				scope: Deluge.Details.Peers
			}
		}
	}), new Ext.form.FormPanel({
		id: 'options',
		title: _('Options'),
		frame: true,
		autoScroll:true,
		deferredRender:false,
		
		items: [{
			layout: 'column',
			defaults: {
				//columnWidth: '.33',
				border: false
			},
			
			items: [{
				bodyStyle: 'padding-left: 5px; padding-right:5px;',
				width: 300,
				items: [{
					xtype: 'fieldset',
					title: _('Bandwidth'),
					layout: 'table',
					layoutConfig: {columns: 3},
					autoHeight: true,
					labelWidth: 150,
					defaultType: 'uxspinner',
					items: [{
						xtype: 'label',
						text: _('Max Download Speed'),
						forId: 'max_download_speed',
						cls: 'x-deluge-options-label'
					}, {
						id: 'max_download_speed',
						width: 100,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						xtype: 'label',
						text: 'KiB/s',
						style: 'margin-left: 10px;'
					}, {
						xtype: 'label',
						text: _('Max Upload Speed'),
						forId: 'max_upload_speed',
						cls: 'x-deluge-options-label'
					}, {
						id: 'max_upload_speed',
						width: 100,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						xtype: 'label',
						text: 'KiB/s',
						style: 'margin-left: 10px;'
					}, {
						xtype: 'label',
						text: _('Max Connections'),
						forId: 'max_connections',
						cls: 'x-deluge-options-label'
					}, {
						id: 'max_connections',
						colspan: 2,
						width: 100,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						xtype: 'label',
						text: _('Max Upload Slots'),
						forId: 'max_upload_slots',
						cls: 'x-deluge-options-label'
					}, {
						id: 'max_upload_slots',
						colspan: 2,
						width: 100,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}]
				}]
			}, {
				bodyStyle: 'padding-left: 5px; padding-right:5px;',
				width: 200,
				items: [{
					xtype: 'fieldset',
					title: _('Queue'),
					autoHeight: true,
					labelWidth: 1,
					defaultType: 'checkbox',
					items: [{
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Auto Managed'),
						id: 'is_auto_managed'
					}, {
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Stop seed at ratio'),
						id: 'stop_at_ratio'
					}, {
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Remove at ratio'),
						id: 'remove_at_ratio'
					}, {
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Move Completed'),
						id: 'move_completed'
					}]
				}]
			}, {
				bodyStyle: 'padding-left:5px;',
				width: 200,
				items: [{
					xtype: 'fieldset',
					title: _('General'),
					autoHeight: true,
					defaultType: 'checkbox',
					labelWidth: 1,
					items: [{
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Private'),
						id: 'private'
					}, {
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Prioritize First/Last'),
						id: 'prioritize_first_last'
					}]
				}, {
					layout: 'column',
					items: [{
						items: [{
							id: 'edit_trackers',
							xtype: 'button',
							text: _('Edit Trackers'),
							cls: 'x-btn-text-icon',
							iconCls: 'x-deluge-edit-trackers',
							width: 100
						}]
					}, {
						items: [{
							id: 'apply',
							xtype: 'button',
							text: _('Apply'),
							style: 'margin-left: 10px',
							width: 100
						}]
					}]
				}]
			}]
		}],
		listeners: {
			'render': {
				fn: Deluge.Details.Options.onRender,
				scope: Deluge.Details.Options
			}
		}
	})],
	listeners: {
		'render': {fn: Deluge.Details.onRender, scope: Deluge.Details},
		'tabchange': {fn: Deluge.Details.onTabChange, scope: Deluge.Details}
	}
});*/