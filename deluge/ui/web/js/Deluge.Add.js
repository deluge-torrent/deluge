/*
Script: Deluge.Add.js
    Contains the Add Torrent window.

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

Ext.namespace('Ext.deluge.add');
Ext.deluge.add.OptionsPanel = Ext.extend(Ext.TabPanel, {

	constructor: function(config) {
		config = Ext.apply({
			region: 'south',
			margins: '5 5 5 5',
			activeTab: 0,
			height: 220
		}, config);
		Ext.deluge.add.OptionsPanel.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.add.OptionsPanel.superclass.initComponent.call(this);
		this.files = this.add(new Ext.tree.ColumnTree({
			layout: 'fit',
			title: _('Files'),
			rootVisible: false,
			autoScroll: true,
			height: 170,
			border: false,
			animate: false,
			
			columns: [{
				header: _('Filename'),
				width: 275,
				dataIndex: 'filename'
			},{
				header: _('Size'),
				width: 80,
				dataIndex: 'size'
			}],
			
			root: new Ext.tree.AsyncTreeNode({
				text: 'Files'
			})
		}));
		new Ext.tree.TreeSorter(this.files, {
			folderSort: true
		});
		
		this.form = this.add({
			xtype: 'form',
			labelWidth: 1,
			frame: false,
			title: _('Options'),
			bodyStyle: 'padding: 5px;',
			border: false,
			
			
			items: [{
				xtype: 'fieldset',
				title: _('Download Location'),
				border: false,
				defaultType: 'textfield',
				labelWidth: 1,
				items: [{
					fieldLabel: '',
					labelSeperator: '',
					name: 'download_location',
					width: 330
				}]
			}]
		});
	},
	
	clear: function() {
		this.clearFiles();
	},
	
	clearFiles: function() {
		var root = this.files.getRootNode();
		if (!root.hasChildNodes()) return;
		root.cascade(function(node) {
			if (!node.parentNode || !node.getOwnerTree()) return;
			node.remove();
		});
	},
	
	getDefaults: function() {
		var keys = [
            'add_paused',
            'compact_allocation',
            'download_location',
            'max_connections_per_torrent',
            'max_download_speed_per_torrent',
            'max_upload_slots_per_torrent',
            'max_upload_speed_per_torrent',
            'prioritize_first_last_pieces'
        ]
        Deluge.Client.core.get_config_values(keys, {
            success: function(config) {
				this.defaults = config;
				for (var key in config) {
					var field = this.form.findField(key);
					if (!field) return;
					field.setValue(config[key]);
				}
				var field = this.form.findField('compact_allocation');
				if (config['compact_allocation']) {
					field.items.get('compact_allocation_true').setValue(true);
					field.items.get('compact_allocation_false').setValue(false);
				} else {
					field.items.get('compact_allocation_false').setValue(true);
					field.items.get('compact_allocation_true').setValue(false);
				}
			},
			scope: this
        });
	}
});

Ext.deluge.add.Window = Ext.extend(Ext.Window, {
	initComponent: function() {
		Ext.deluge.add.Window.superclass.initComponent.call(this);
		this.addEvents(
			'beforeadd',
			'add'
		);
	},
	
	createTorrentId: function() {
		return new Date().getTime();
	}
});

Ext.deluge.add.AddWindow = Ext.extend(Ext.deluge.add.Window, {
	
	torrents: {},
	
	constructor: function(config) {
		config = Ext.apply({
			title: _('Add Torrents'),
			layout: 'border',
			width: 470,
			height: 450,
			bodyStyle: 'padding: 10px 5px;',
			buttonAlign: 'right',
			closeAction: 'hide',
			closable: true,
			plain: true,
			iconCls: 'x-deluge-add-window-icon'
		}, config);
		Ext.deluge.add.AddWindow.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.add.AddWindow.superclass.initComponent.call(this);
		
		this.addButton(_('Cancel'), this.onCancel, this);
		this.addButton(_('Add'), this.onAdd, this);
		
		function torrentRenderer(value, p, r) {
			if (r.data['infohash']) {
				return String.format('<div class="x-add-torrent-name">{0}</div>', value);
			} else {
				return String.format('<div class="x-add-torrent-name-loading">{0}</div>', value);
			}
		}
		
		this.grid = this.add({
			xtype: 'grid',
			region: 'center',
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
			selModel: new Ext.grid.RowSelectionModel({
				singleSelect: true,
				listeners: {
					'rowselect': {
						fn: this.onSelect,
						scope: this
					}
				}
			}),
			hideHeaders: true,
			autoExpandColumn: 'torrent',
			deferredRender: false,
			autoScroll: true,
			margins: '5 5 5 5',
			bbar: new Ext.Toolbar({
				items: [{
					id: 'file',
					cls: 'x-btn-text-icon',
					iconCls: 'x-deluge-add-file',
					text: _('File'),
					handler: this.onFile,
					scope: this
				}, {
					id: 'url',
					cls: 'x-btn-text-icon',
					text: _('Url'),
					icon: '/icons/add_url.png',
					handler: this.onUrl,
					scope: this
				}, {
					id: 'infohash',
					cls: 'x-btn-text-icon',
					text: _('Infohash'),
					icon: '/icons/add_magnet.png',
					disabled: true
				}, '->', {
					id: 'remove',
					cls: 'x-btn-text-icon',
					text: _('Remove'),
					icon: '/icons/remove.png',
					handler: this.onRemove,
					scope: this
				}]
			})
		});
		
		this.options = this.add(new Ext.deluge.add.OptionsPanel());
		this.on('show', this.onShow, this);
	},
	
	clear: function() {
		this.torrents = {};
		this.grid.getStore().removeAll();
		this.options.clear();
	},
	
	onAdd: function() {
		torrents = [];
		for (var id in this.torrents) {
			var info = this.torrents[id];
			torrents.push({
				path: info['filename'],
				options: {}
			});
		}
		Deluge.Client.web.add_torrents(torrents, {
			success: function(result) {
			}
		})
		this.clear();
		this.hide();
	},
	
	onCancel: function() {
		this.clear();
		this.hide();
	},
	
	onFile: function() {
		this.file.show();
	},
	
	onRemove: function() {
		var selection = this.grid.getSelectionModel();
		if (!selection.hasSelection()) return;
		var torrent = selection.getSelected();
		
		delete this.torrents[torrent.id];
		this.grid.getStore().remove(torrent);
		this.options.clear();
	},
	
	onSelect: function(selModel, rowIndex, record) {
		var torrentInfo = this.torrents[record.get('info_hash')];
		
		function walk(files, parent) {
			for (var file in files) {
				var item = files[file];
				
				if (Ext.type(item) == 'object') {
					var child = new Ext.tree.TreeNode({
						text: file
					});
					walk(item, child);
					parent.appendChild(child);
				} else {
					parent.appendChild(new Ext.tree.TreeNode({
						filename: file,
						text: file, // this needs to be here for sorting reasons
						size: fsize(item[0]),
						leaf: true,
						checked: item[1],
						iconCls: 'x-deluge-file',
						uiProvider: Ext.tree.ColumnNodeUI
					}));	
				}
			}
		}
		
		this.options.clearFiles();		
		var root = this.options.files.getRootNode();
		walk(torrentInfo['files_tree'], root);
		root.firstChild.expand();
	},
	
	onShow: function() {
		if (!this.url) {
			this.url = new Ext.deluge.add.UrlWindow();
			this.url.on('beforeadd', this.onTorrentBeforeAdd, this);
			this.url.on('add', this.onTorrentAdd, this);
		}
		
		if (!this.file) {
			this.file = new Ext.deluge.add.FileWindow();
			this.file.on('beforeadd', this.onTorrentBeforeAdd, this);
			this.file.on('add', this.onTorrentAdd, this);
		}
	},
	
	onTorrentBeforeAdd: function(torrentId, text) {
		var store = this.grid.getStore();
		store.loadData([[torrentId, null, text]], true);
	},
	
	onTorrentAdd: function(torrentId, info) {
		if (!info) {
			Ext.MessageBox.show({
				title: _('Error'),
				msg: _('Not a valid torrent'),
				buttons: Ext.MessageBox.OK,
				modal: false,
				icon: Ext.MessageBox.ERROR,
				iconCls: 'x-deluge-icon-error'
			});
			return;
		}
		
		var r = this.grid.getStore().getById(torrentId);
		r.set('info_hash', info['info_hash']);
		r.set('text', info['name']);
		this.grid.getStore().commitChanges();
		this.torrents[info['info_hash']] = info;
	},
	
	onUrl: function(button, event) {
		this.url.show();
	}
});
Deluge.Add = new Ext.deluge.add.AddWindow();