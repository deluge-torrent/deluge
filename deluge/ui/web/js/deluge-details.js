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

Deluge.Details = {
	clear: function() {
		this.Panel.items.each(function(item) {
			if (item.clear) item.clear();
		});
	},
	
	update: function(tab) {	
		var torrent = Deluge.Torrents.getSelected();
		if (!torrent) return;
		
		tab = tab || this.Panel.getActiveTab();
		if (tab.update) {
			tab.update(torrent.id);
		}
	},

	onRender: function(panel) {
		Deluge.Torrents.Grid.on('rowclick', this.onTorrentsClick.bindWithEvent(this));
		
		var selModel = Deluge.Torrents.Grid.getSelectionModel();
		selModel.on('selectionchange', function(selModel) {
			if (!selModel.hasSelection()) {
				this.clear.delay(10, this);
			}
		}.bindWithEvent(this));
		Deluge.Events.on('disconnect', this.clear.bind(this));
	},
	
	onTabChange: function(panel, tab) {
		this.update(tab);
	},
	
	onTorrentsClick: function(grid, rowIndex, e) {
		this.update();
	}
}

Deluge.Details.Status = {
	onRender: function(panel) {
		this.panel = panel;
		this.progressBar = new Deluge.ProgressBar({
			id: 'pbar-status',
			cls: 'deluge-status-progressbar'
		});
		this.panel.add(this.progressBar);
		this.panel.add({
			id: 'status-details',
			cls: 'deluge-status',
			border: false,
			listeners: {'render': Deluge.Details.Status.onStatusRender}
		});
		this.panel.update = this.update.bind(this);
		this.panel.clear = this.clear.bind(this);
	},
	
	onStatusRender: function(panel) {
		this.status = panel;
		this.status.load({
			url: '/render/tab_status.html',
			text: _('Loading') + '...'
		});
	},
	
	onRequestComplete: function(status) {
		seeders = status.total_seeds > -1 ? status.num_seeds + ' (' + status.total_seeds + ')' : status.num_seeds
		peers = status.total_peers > -1 ? status.num_peers + ' (' + status.total_peers + ')' : status.num_peers
		var data = {
			downloaded: fsize(status.total_done) + ' (' + fsize(status.total_payload_download) + ')',
            uploaded: fsize(status.total_uploaded) + ' (' + fsize(status.total_payload_upload) + ')',
            share: status.ratio.toFixed(3),
            announce: ftime(status.next_announce),
            tracker_status: status.tracker_status,
            downspeed: fspeed(status.download_payload_rate),
            upspeed: fspeed(status.upload_payload_rate),
            eta: ftime(status.eta),
            pieces: status.num_pieces + ' (' + fsize(status.piece_length) + ')',
            seeders: seeders,
            peers: peers,
            avail: status.distributed_copies.toFixed(3),
            active_time: ftime(status.active_time),
            seeding_time: ftime(status.seeding_time),
            seed_rank: status.seed_rank,
			auto_managed: 'False'
		}
		if (status.is_auto_managed) {data.auto_managed = 'True'}
		this.fields.each(function(value, key) {
			value.set('text', data[key]);
		}, this);
		var text = status.state + ' ' + status.progress.toFixed(2) + '%';
		this.progressBar.updateProgress(status.progress, text);
	},
	
	getFields: function() {
		var panel = this.panel.items.get('status-details');
		this.fields = new Hash();
		panel.body.dom.getElements('dd').each(function(item) {
			this.fields[item.getProperty('class')] = item;
		}, this);
	},
	
	update: function(torrentId) {
		if (!this.fields) this.getFields();
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Status, {
			onSuccess: this.onRequestComplete.bind(this)
		});
	},
	
	clear: function() {
		if (!this.fields) return;
		this.progressBar.updateProgress(0, ' ');
		this.fields.each(function(value, key) {
			value.set('text', '');
		}, this);
	}
}

Deluge.Details.Details = {
	onRender: function(panel) {
		this.panel = panel.load({
			url: '/render/tab_details.html',
			text: _('Loading') + '...',
			callback: this.onLoaded.bindWithEvent(this)
		});
		this.doUpdate = false;
		this.panel.update = this.update.bind(this);
		this.panel.clear = this.clear.bind(this);
	},
	
	onLoaded: function() {
		this.getFields();
		this.doUpdate = true;
		if (Deluge.Details.Panel.getActiveTab() == this.panel) {
			Deluge.Details.update(this.panel);
		}
	},
	
	onRequestComplete: function(torrent, torrentId) {
		var data = {
            torrent_name: torrent.name,
            hash: torrentId,
            path: torrent.save_path,
            size: fsize(torrent.total_size),
            files: torrent.num_files,
            status: torrent.tracker_status,
            tracker: torrent.tracker,
			comment: torrent.comment
        };
		this.fields.each(function(value, key) {
			value.set('text', data[key]);
		}, this);
	},
	
	getFields: function() {
		this.fields = new Hash();
		this.panel.body.dom.getElements('dd').each(function(item) {
			this.fields[item.getProperty('class')] = item;
		}, this);
	},
	
	update: function(torrentId) {
		if (!this.doUpdate) return;
		if (!this.fields) this.getFields();
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Details, {
			onSuccess: this.onRequestComplete.bindWithEvent(this, torrentId)
		});
	},
	
	clear: function() {
		if (!this.fields) return;
		this.fields.each(function(value, key) {
			value.set('text', '');
		}, this);
	}
}

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

function flag(value) {
	return String.format('<img src="/flag/{0}" />', value);
}

function peer_address(value, p, record) {
	var seed = (record.data['seed'] == 1024) ? 'x-deluge-seed' : 'x-deluge-peer'
	return String.format('<div class="{0}">{1}</div>', seed, value);
}

function progress_renderer(value) {
	var progress = (value * 100).toInt();
	return String.format(tpl, progress, '', progress);
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
	region: 'south',
	split: true,
	height: 220,
	minSize: 100,
	collapsible: true,
	margins: '0 5 5 5',
	activeTab: 0,
	items: [{
		id: 'status',
		title: _('Status'),
		listeners: {'render': {fn: Deluge.Details.Status.onRender, scope: Deluge.Details.Status}}
	},{
		id: 'details',
		title: _('Details'),
		cls: 'deluge-status',
		listeners: {'render': {fn: Deluge.Details.Details.onRender, scope: Deluge.Details.Details}}
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
		},{
			header: _('Size'),
			width: 150,
			dataIndex: 'size',
			renderer: fsize
		},{
			header: _('Progress'),
			width: 150,
			dataIndex: 'progress',
			renderer: progress_renderer
		},{
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
			{header: 'Progress', width: 150, sortable: true, renderer: progress_renderer, dataIndex: 'progress'},
			{header: 'Down Speed', width: 100, sortable: true, renderer: fspeed, dataIndex: 'downspeed'},
			{header: 'Up Speed', width: 100, sortable: true, renderer: fspeed, dataIndex: 'upspeed'}
		],	
		stripeRows: true,
		deferredRender:false,
		autoScroll:true,
		margins: '0 0 0 0',
		listeners: {'render': {fn: Deluge.Details.Peers.onRender, scope: Deluge.Details.Peers}}
	}), new Ext.form.FormPanel({
		id: 'options',
		title: _('Options'),
		frame: true,
		items: [{
			layout: 'column',
			border: false,
			defaults: {
				columnWidth: '.33',
				border: false
			},
			
			items: [{
				bodyStyle: 'padding-right:5px;',
				items: [{
					xtype: 'fieldset',
					title: _('Bandwidth'),
					autoHeight: true,
					defaultType: 'uxspinner',
					items: [{
						fieldLabel: _('Max Download Speed'),
						name: 'max_download_speed'
					}, {
						fieldLabel: _('Max Upload Speed'),
						name: 'max_upload_speed'
					}, {
						fieldLabel: _('Max Connections'),
						name: 'max_connections'
					}, {
						fieldLabel: _('Max Upload Slots'),
						name: 'max_upload_slots'
					}]
				}]
			}, {
				bodyStyle: 'padding-left: 5px; padding-right:5px;',
				items: [{
					xtype: 'fieldset',
					title: _('Queue'),
					autoHeight: true,
					defaultType: 'checkbox',
					items: [{
						fieldLabel: '',
						boxLabel: _('Auto Managed'),
						name: 'auto_managed'
					}, {
						fieldLabel: '',
						boxLabel: _('Stop seed at ratio'),
						name: 'stop_ratio'
					}, {
						fieldLabel: '',
						boxLabel: _('Remove at ratio'),
						name: 'remove_ratio'
					}, {
						fieldLabel: '',
						boxLabel: _('Move Completed'),
						name: 'move_completed'
					}]
				}]
			}, {
				bodyStyle: 'padding-left:5px;',
				items: [{
					xtype: 'fieldset',
					title: _('General'),
					autoHeight: true,
					defaultType: 'checkbox',
					items: [{
						fieldLabel: '',
						boxLabel: _('Private'),
						name: 'private'
					}, {
						fieldLabel: '',
						boxLabel: _('Prioritize First/Last'),
						name: 'prioritize_first'
					}]
				}]
			}],
		}]
	})],
	listeners: {
		'render': {fn: Deluge.Details.onRender, scope: Deluge.Details},
		'tabchange': {fn: Deluge.Details.onTabChange, scope: Deluge.Details}
	}
});