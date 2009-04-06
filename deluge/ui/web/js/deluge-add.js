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

Deluge.Add = {
	torrents: new Hash(),
	
	clear: function() {
		this.clearFiles();
		this.Store.loadData([]);
		this.torrents.empty();
	},
	
	clearFiles: function() {
		var root = this.Files.getRootNode();
		if (!root.hasChildNodes()) return;
		root.cascade(function(node) {
			if (!node.parentNode || !node.getOwnerTree()) return;
			node.remove();
		});
	},
	
	onAdd: function() {
		torrents = new Array();
		this.torrents.each(function(info, hash) {
			torrents.include({
				path: info['filename'],
				options: {}
			});
		});
		Deluge.Client.web.add_torrents(torrents, {
			onSuccess: function(result) {
			}
		})
		this.clear();
		this.Window.hide();
	},
	
	onFile: function() {
		this.File.Window.show();
	},
	
	onOptionsRender: function(panel) {
		panel.layout = new Ext.layout.FormLayout();
		panel.layout.setContainer(panel);
		panel.doLayout();
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

Deluge.Add.Files = new Ext.tree.ColumnTree({
	id: 'files',
	layout: 'fit',
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
})

Deluge.Add.Store = new Ext.data.SimpleStore({
	fields: [
		{name: 'torrent', mapping: 1}
	],
	id: 0
});

Deluge.Add.Grid = new Ext.grid.GridPanel({
	store: Deluge.Add.Store,
	region: 'center',
	columns: [
		{id: 'torrent', width: 150, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'torrent'}
	],	
	stripeRows: true,
	selModel: new Ext.grid.RowSelectionModel({
		singleSelect: true,
		listeners: {'rowselect': {fn: Deluge.Add.onSelect, scope: Deluge.Add}}
	}),
	hideHeaders: true,
	autoExpandColumn: 'torrent',
	deferredRender: false,
	autoScroll: true,
	margins: '5 5 5 5',
	bbar: new Ext.Toolbar({
		items: [
			{
				id: 'file',
				cls: 'x-btn-text-icon',
				iconCls: 'x-deluge-add-file',
				text: _('File'),
				handler: Deluge.Add.onFile,
				scope: Deluge.Add
			}, {
				id: 'url',
				cls: 'x-btn-text-icon',
				text: _('Url'),
				icon: '/icons/add_url.png',
				handler: Deluge.Add.onUrl,
				scope: Deluge.Add
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
				handler: Deluge.Add.onRemove,
				scope: Deluge.Add
			}
		]
	})
});

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
					defaultType: 'radio',
					autoHeight: true,
					border: false,
					labelWidth: 1,
					width: 100,
					items: [{
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Full'),
						inputValue: 'false',
						name: 'compact_allocation',
						width: 50
					},{
						fieldLabel: '',
						labelSeparator: '',
						boxLabel: _('Compact'),
						inputValue: 'true',
						name: 'compact_allocation',
						width: 75
					}]
				}, {
					xtype: 'fieldset',
					title: _('Bandwidth'),
					layout: 'form',
					autoHeight: true,
					defaultType: 'uxspinner',
					labelWidth: 100,
					items: [{
						id: 'add_max_download_speed',
						fieldLabel: _('Max Down Speed'),
						width: 60,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						id: 'add_max_upload_speed',
						fieldLabel: _('Max Up Speed'),
						width: 60,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						id: 'add_max_connections',
						fieldLabel: _('Max Connections'),
						width: 60,
						value: -1,
						strategy: new Ext.ux.form.Spinner.NumberStrategy({
							minValue: -1,
							maxValue: 99999,
							incrementValue: 1
						})
					}, {
						id: 'add_max_upload_slots',
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
						id: 'prioritize_first_last'
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
			}]
		})],
		listeners: {
			'render': {
				fn: Deluge.Add.onOptionsRender,
				scope: Deluge.Add
			}
		}
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

Deluge.Add.Url.form = new Ext.form.FormPanel({
    defaultType: 'textfield',
    id: 'urlAddForm',
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
                fn: Deluge.Add.Url.onAdd,
                scope: Deluge.Add.Url
            }
        }
    }]
});

Deluge.Add.Url.Window = new Ext.Window({
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
    items: Deluge.Add.Url.form,
    buttons: [{
        text: _('Add'),
        handler: Deluge.Add.Url.onAdd,
		scope: Deluge.Add.Url
    }]
});

Deluge.Add.Window = new Ext.Window({
	layout: 'border',
    width: 470,
    height: 450,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    title: _('Add Torrents'),
    iconCls: 'x-deluge-add-window-icon',
    items: [Deluge.Add.Grid, Deluge.Add.Options],
    buttons: [{
        text: _('Cancel'),
		handler: function() {
			Deluge.Add.clear();
			Deluge.Add.Window.hide();
		}
    }, {
		text: _('Add'),
		handler: Deluge.Add.onAdd,
		scope: Deluge.Add
	}],
    listeners: {
		'render': {
			fn: Deluge.Add.onRender,
			scope: Deluge.Add
		}
	}
});