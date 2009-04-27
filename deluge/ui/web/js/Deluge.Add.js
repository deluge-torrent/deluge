/*
Script: deluge-add.js
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
            onSuccess: function(config) {
				this.defaults = config;
				$each(config, function(value, key) {
					var field = this.form.findField(key);
					if (!field) return;
					field.setValue(value);
				}, this);
				var field = this.form.findField('compact_allocation');
				if (config['compact_allocation']) {
					field.items.get('compact_allocation_true').setValue(true);
					field.items.get('compact_allocation_false').setValue(false);
				} else {
					field.items.get('compact_allocation_false').setValue(true);
					field.items.get('compact_allocation_true').setValue(false);
				}
			}.bindWithEvent(this)
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
	}
});

Ext.deluge.add.UrlWindow = Ext.extend(Ext.deluge.add.Window, {
	constructor: function(config) {
		config = Ext.apply({
			layout: 'fit',
			width: 350,
			height: 115,
			bodyStyle: 'padding: 10px 5px;',
			buttonAlign: 'center',
			closeAction: 'hide',
			modal: true,
			plain: true,
			title: _('Add from Url'),
			iconCls: 'x-deluge-add-url-window-icon',
			buttons: [{
				text: _('Add'),
				handler: this.onAdd,
				scope: this
			}]
		}, config);
		Ext.deluge.add.UrlWindow.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.add.UrlWindow.superclass.initComponent.call(this);
		this.form = this.add(new Ext.form.FormPanel({
			defaultType: 'textfield',
			baseCls: 'x-plain',
			labelWidth: 55,
			items: [{
				fieldLabel: _('Url'),
				id: 'url',
				name: 'url',
				inputType: 'url',
				anchor: '100%',
				listeners: {
					'specialkey': {
						fn: this.onAdd,
						scope: this
					}
				}
			}]
		}));
	},
	
	onAdd: function(field, e) {
		if (field.id == 'url' && e.getKey() != e.ENTER) return;

		var field = this.form.items.get('url');
		var url = field.getValue();
		
		Deluge.Client.web.download_torrent_from_url(url, {
			success: this.onDownload,
			scope: this
		});
		this.hide();
		this.fireEvent('beforeadd', url);
	},
	
	onDownload: function(filename) {
		this.form.items.get('url').setValue('');
		Deluge.Client.web.get_torrent_info(filename, {
			success: this.onGotInfo,
			scope: this,
			filename: filename
		});
	},
	
	onGotInfo: function(info, obj, response, request) {
		info['filename'] = request.options.filename;
		this.fireEvent('add', info);
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
		
		this.grid = this.add({
			xtype: 'grid',
			region: 'center',
			store: new Ext.data.SimpleStore({
				fields: [{name: 'torrent', mapping: 1}],
				id: 0
			}),
			columns: [{
					id: 'torrent',
					width: 150,
					sortable: true,
					renderer: fplain,
					dataIndex: 'torrent'
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
		
		this.url = new Ext.deluge.add.UrlWindow();
		this.url.on('beforeadd', this.onTorrentBeforeAdd, this);
		this.url.on('add', this.onTorrentAdd, this);
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
		this.clearFiles();
	},
	
	onSelect: function(selModel, rowIndex, record) {
		var torrentInfo = this.torrents[record.id];
		
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
	
	onTorrentBeforeAdd: function(temptext) {
	},
	
	onTorrentAdd: function(info) {
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
		this.grid.getStore().loadData([[info['info_hash'], info['name']]], true);
		this.torrents[info['info_hash']] = info;
	},
	
	onUrl: function(button, event) {
		this.url.show();
	}
});
Deluge.Add = new Ext.deluge.add.AddWindow();

/*Deluge.Add = {
	
	
	
	onFile: function() {
		this.File.Window.show();
	},
	
	onOptionsRender: function(panel) {
		panel.layout = new Ext.layout.FormLayout();
		panel.layout.setContainer(panel);
		panel.doLayout();
		this.form = panel.getForm();
		this.getDefaults();
	},
	
	onRender: function(window) {
		new Ext.tree.TreeSorter(this.Files, {
			folderSort: true
		});
	},
	
	onSelect: function(selModel, rowIndex, record) {
		var torrentInfo = Deluge.Add.torrents[record.id];
		
		function walk(files, parent) {
			$each(files, function(item, file) {
				if ($type(item) == 'object') {
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
			});
		}
		
		this.clearFiles();
		
		var root = this.Files.getRootNode();
		walk(torrentInfo['files_tree'], root);
		root.firstChild.expand();
	},
	
	onTorrentAdded: function(info, filename) {
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
		info['filename'] = filename;
		this.Store.loadData([[info['info_hash'], info['name']]], true);
		this.torrents[info['info_hash']] = info;
	},
	
	onUrl: function(button, event) {
		this.Url.Window.show();
	},
	
	onRemove: function() {
		var selection = this.Grid.getSelectionModel();
		if (!selection.hasSelection()) return;
		var torrent = selection.getSelected();
		
		delete this.torrents[torrent.id];
		this.Store.remove(torrent);
		this.clearFiles();
	}
}

Deluge.Add.Options = new Ext.TabPanel({
	region: 'south',
	margins: '5 5 5 5',
	activeTab: 0,
	height: 220,
	items: [{
		id: 'addFilesTab',
		title: _('Files'),
		items: [Deluge.Add.Files]
	},{
		id: 'addOptionsTab',
		title: _('Options'),
		layout: 'fit',
		items: [new Ext.form.FormPanel({
			id: 'addOptionsForm',
			bodyStyle: 'padding: 5px;',
			border: false,
			items: [{
				xtype: 'fieldset',
				style: 'padding: 0px; padding-top: 5px;',
				title: _('Download Location'),
				border: false,
				autoHeight: true,
				border: false,
				labelWidth: 1,
				items: [{
					layout: 'column',
					border: false,
					items: [{
						xtype: 'textfield',
						id: 'download_location',
						fieldLabel: '',
						labelSeparator: '',
						width: 330
					}, {
						border: false,
						style: 'padding-left: 5px;',
						items: [{
							xtype: 'button',
							text: _('Browse') + '...',
							disabled: true
						}]
					}]
				}]
			}, {
				layout: 'column',
				border: false,
				defaults: {
					border: false
				},
				items: [{
					xtype: 'fieldset',
					bodyStyle: 'margin-left: 5px; margin-right:5px;',
					title: _('Allocation'),
					autoHeight: true,
					border: false,
					labelWidth: 1,
					width: 100,
					items: [new Ext.form.RadioGroup({
						id: 'compact_allocation',
						name: 'compact_allocation',
						columns: 1,
						labelSeparator: '',
						items: [{
							boxLabel: _('Full'),
							inputValue: 'false',
							id: 'compact_allocation_false',
							name: 'compact_allocation',
							checked: true
						},{
							boxLabel: _('Compact'),
							inputValue: 'true',
							id: 'compact_allocation_true',
							name: 'compact_allocation'
						}]
					})]
				}, {
					xtype: 'fieldset',
					title: _('Bandwidth'),
					layout: 'form',
					autoHeight: true,
					defaultType: 'uxspinner',
					labelWidth: 100,
					items: [{
						id: 'max_download_speed_per_torrent',
						fieldLabel: _('Max Down Speed'),
						width: 60,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						id: 'max_upload_speed_per_torrent',
						fieldLabel: _('Max Up Speed'),
						width: 60,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						id: 'max_connections_per_torrent',
						fieldLabel: _('Max Connections'),
						width: 60,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						id: 'max_upload_slots_per_torrent',
						fieldLabel: _('Max Upload Slots'),
						colspan: 2,
						width: 60,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}]
				}, {
					xtype: 'fieldset',
					title: _('General'),
					autoHeight: true,
					border: false,
					labelWidth: 10,
					defaultType: 'checkbox',
					items: [{
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Add In Paused State'),
						id: 'add_paused'
					}, {
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Prioritize First/Last Piece'),
						id: 'prioritize_first_last_pieces'
					}, {
						xtype: 'button',
						text: _('Apply to All'),
						style: 'margin-left: 20px; margin-top: 5px;'
					}, {
						xtype: 'button',
						text: _('Revert to Defaults'),
						style: 'margin-left: 20px; margin-top: 5px;'
					}]
				}]
			}],
			listeners: {
				'render': {
					fn: Deluge.Add.onOptionsRender,
					scope: Deluge.Add
				}
			}
		})]
	}]
});

Deluge.Add.File = {
	onAdd: function() {
		if (this.form.getForm().isValid()) {
			this.form.getForm().submit({
				url: '/upload',
				waitMsg: _('Uploading your torrent...'),
				success: this.onUploadSuccess.bindWithEvent(this)
			});
		}
	},
	
	onUploadSuccess: function(fp, upload) {
		this.Window.hide();
		var filename = upload.result.toString();
		this.form.items.get('torrentFile').setValue('');
		Deluge.Client.web.get_torrent_info(filename, {
			onSuccess: Deluge.Add.onTorrentAdded.bindWithEvent(Deluge.Add, filename)
		});
	}
}

Deluge.Add.File.form = new Ext.form.FormPanel({
	fileUpload: true,
    id: 'fileAddForm',
    baseCls: 'x-plain',
    labelWidth: 55,
	autoHeight: true,
    items: [{
		xtype: 'fileuploadfield',
		id: 'torrentFile',
		emptyText: _('Select a torrent'),
        fieldLabel: _('File'),
        name: 'file',
		buttonCfg: {
			text: _('Browse') + '...'
		}
    }]
});

Deluge.Add.File.Window = new Ext.Window({
	layout: 'fit',
    width: 350,
    height: 115,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'center',
    closeAction: 'hide',
    modal: true,
    plain: true,
    title: _('Add from File'),
    iconCls: 'x-deluge-add-file',
    items: Deluge.Add.File.form,
    buttons: [{
        text: _('Add'),
        handler: Deluge.Add.File.onAdd,
		scope: Deluge.Add.File
    }]
});

Deluge.Add.Url = {
	onAdd: function(field, e) {
		if (field.id == 'url' && e.getKey() != e.ENTER) return;

		var field = this.form.items.get('url');
		var url = field.getValue();
		
		Deluge.Client.web.download_torrent_from_url(url, {
			onSuccess: this.onDownload.bindWithEvent(this)
		});
		this.Window.hide();
	},
	
	onDownload: function(filename) {
		this.form.items.get('url').setValue('');
		Deluge.Client.web.get_torrent_info(filename, {
			onSuccess: Deluge.Add.onTorrentAdded.bindWithEvent(Deluge.Add, filename)
		});
	}
}

Deluge.Add.Url.form = ;
*/