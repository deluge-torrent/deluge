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
		this.Store.loadData([]);
		this.torrents.empty();
		this.Window.hide();
	},
	
	onFile: function() {
		this.File.Window.show();
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
		walk(torrentInfo['files'], root);
		root.firstChild.expand();
	},
	
	onTorrentAdded: function(info) {
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
				icon: '/icons/add_magnet.png'
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
	height: 200,
	items: [{
		id: 'files',
		title: _('Files'),
		items: [Deluge.Add.Files]
	},{
		id: 'options',
		title: _('Options')
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
		Deluge.Client.web.get_torrent_info(filename, {
			onSuccess: this.onGotInfo.bindWithEvent(this)
		});
	},
	
	onGotInfo: function(info) {
		var bound = Deluge.Add.onTorrentAdded.bind(Deluge.Add)
		this.form.items.get('torrentFile').setValue('');
		bound(info);
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
			text: _('Browse...')
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
		Deluge.Client.web.get_torrent_info(filename, {
			onSuccess: this.onGotInfo.bindWithEvent(this)
		});
	},
	
	onGotInfo: function(info) {
		var bound = Deluge.Add.onTorrentAdded.bind(Deluge.Add)
		this.form.items.get('url').setValue('');
		bound(info);
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
    width: 400,
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