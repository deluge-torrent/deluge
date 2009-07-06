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

Ext.namespace('Ext.deluge.add');
Ext.deluge.add.OptionsPanel = Ext.extend(Ext.TabPanel, {
	
	torrents: {},

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
		
		this.optionsManager = new Deluge.OptionsManager({
			defaults: {
				'add_paused': false,
				'compact_allocation': false,
				'download_location': '~',
				'max_connections_per_torrent': -1,
				'max_download_speed_per_torrent': -1,
				'max_upload_slots_per_torrent': -1,
				'max_upload_speed_per_torrent': -1,
				'prioritize_first_last_pieces': false,
				'file_priorities': []
			}
		});
		
		this.form = this.add({
			xtype: 'form',
			labelWidth: 1,
			title: _('Options'),
			bodyStyle: 'padding: 5px;',
			border: false,
			height: 170
		});
		
		var fieldset = this.form.add({
			xtype: 'fieldset',
			title: _('Download Location'),
			border: false,
			autoHeight: true,
			defaultType: 'textfield',
			labelWidth: 1,
			fieldLabel: ''
		});
		this.optionsManager.bind('download_location', fieldset.add({
			fieldLabel: '',
			name: 'download_location',
			width: 400,
			labelSeparator: ''
		}));
		
		var panel = this.form.add({
			border: false,
			layout: 'column',
			defaultType: 'fieldset'
		});
		fieldset = panel.add({
			title: _('Allocation'),
			border: false,
			autoHeight: true,
			defaultType: 'radio',
			width: 100
		});

		this.optionsManager.bind('compact_allocation', fieldset.add({
			xtype: 'radiogroup',
			columns: 1,
			vertical: true,
			labelSeparator: '',
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
				labelSeparator: '',
			}]
		}));
		
		fieldset = panel.add({
			title: _('Bandwidth'),
			border: false,
			autoHeight: true,
			labelWidth: 100,
			width: 200,
			defaultType: 'uxspinner'
		});
		this.optionsManager.bind('max_download_speed_per_torrent', fieldset.add({
			fieldLabel: _('Max Down Speed'),
			/*labelStyle: 'margin-left: 10px',*/
			name: 'max_download_speed_per_torrent',
			width: 60
		}));
		this.optionsManager.bind('max_upload_speed_per_torrent', fieldset.add({
			fieldLabel: _('Max Up Speed'),
			/*labelStyle: 'margin-left: 10px',*/
			name: 'max_upload_speed_per_torrent',
			width: 60
		}));
		this.optionsManager.bind('max_connections_per_torrent', fieldset.add({
			fieldLabel: _('Max Connections'),
			/*labelStyle: 'margin-left: 10px',*/
			name: 'max_connections_per_torrent',
			width: 60
		}));
		this.optionsManager.bind('max_upload_slots_per_torrent', fieldset.add({
			fieldLabel: _('Max Upload Slots'),
			/*labelStyle: 'margin-left: 10px',*/
			name: 'max_upload_slots_per_torrent',
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
			labelSeparator: '',
		}));
		this.optionsManager.bind('prioritize_first_last_pieces', fieldset.add({
			name: 'prioritize_first_last_pieces',
			boxLabel: _('Prioritize First/Last Pieces'),
			fieldLabel: '',
			labelSeparator: '',
		}));
		
		this.form.on('render', this.onFormRender, this);
	},
	
	onFormRender: function(form) {
		form.layout = new Ext.layout.FormLayout();
		form.layout.setContainer(form);
		form.doLayout();
		
		this.optionsManager.changeId(null);
	},
	
	addTorrent: function(torrent) {
		this.torrents[torrent['info_hash']] = torrent;
		this.walkFileTree(torrent['files_tree'], function(filename, type, entry, parent) {
		}, this);
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
	},
	
	getOptions: function(torrentId) {
		
	},
	
	setTorrent: function(torrentId) {
		var self = this;
		this.clearFiles();
		var root = this.files.getRootNode();
		this.walkFileTree(this.torrents[torrentId]['files_tree'], function(filename, type, entry, parent) {
			if (type == 'dir') {
				var folder = new Ext.tree.TreeNode({
					text: filename,
					checked: true
				});
				folder.on('checkchange', this.onFolderCheck, self);
				parent.appendChild(folder);
				return folder;
			} else {
				var node = new Ext.tree.TreeNode({
					filename: filename,
					fileindex: entry[0],
					text: filename, // this needs to be here for sorting reasons
					size: fsize(entry[1]),
					leaf: true,
					checked: entry[2],
					iconCls: 'x-deluge-file',
					uiProvider: Ext.tree.ColumnNodeUI
				});
				node.on('checkchange', this.onNodeCheck, self);
				parent.appendChild(node);
			}
		}, this, root);
		root.firstChild.expand();
	},
	
	walkFileTree: function(files, callback, scope, parent) {
		for (var filename in files) {
			var entry = files[filename];
			var type = (Ext.type(entry) == 'object') ? 'dir' : 'file';
			
			if (scope) {
				var ret = callback.apply(scope, [filename, type, entry, parent]);
			} else {
				var ret = callback(filename, type, entry, parent);
			}
			
			parent = (ret) ? ret : parent;
			if (type == 'dir') this.walkFileTree(entry, callback, scope, parent);
		}
	},
	
	onFolderCheck: function(node, checked) {
		node.cascade(function(child) {
			if (!child.ui.checkbox) return;
			child.ui.checkbox.checked = checked;
		}, this);
	},
	
	onNodeCheck: function(node, checked) {
		
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
			if (r.data['info_hash']) {
				return String.format('<div class="x-deluge-add-torrent-name">{0}</div>', value);
			} else {
				return String.format('<div class="x-deluge-add-torrent-name-loading">{0}</div>', value);
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
		
		this.optionsPanel = this.add(new Ext.deluge.add.OptionsPanel());
		this.on('show', this.onShow, this);
	},
	
	clear: function() {
		this.torrents = {};
		this.grid.getStore().removeAll();
	},
	
	onAdd: function() {
		var priorities = this.optionsPanel.getFilePriorities();
		return;
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
		this.optionsPanel.setTorrent(record.get('info_hash'));
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
		this.optionsPanel.addTorrent(info);
	},
	
	onUrl: function(button, event) {
		this.url.show();
	}
});
Deluge.Add = new Ext.deluge.add.AddWindow();
