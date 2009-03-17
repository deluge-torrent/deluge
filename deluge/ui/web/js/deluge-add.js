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
	onRender: function(window) {
		
	},
	
	onTorrentAdded: function(info) {
		this.Store.loadData([[info['info_hash'], info['name']]], true);
	},
	
	onUrl: function(button, event) {
		this.Url.Window.show();
	}
}

Deluge.Add.Files = new Ext.tree.ColumnTree({
	id: 'files',
	layout: 'fit',
	rootVisible: false,
	autoScroll: true,
	height: 200,
	border: false,
	
	columns: [{
		width: 40,
		dataIndex: 'enabled'
	},{
		header: _('Filename'),
		width: 250,
		dataIndex: 'filename'
	},{
		header: _('Size'),
		width: 80,
		dataIndex: 'size'
	}],
	
	loader: new Deluge.FilesTreeLoader({
		uiProviders: {
			'col': Ext.tree.ColumnNodeUI
		}
	}),
	
	root: new Ext.tree.AsyncTreeNode({
		text:'Tasks'
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
		listeners: {'rowselect': Deluge.Connections.onSelect}
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
				text: _('File'),
				icon: '/icons/16/add_file.png'
			}, {
				id: 'url',
				cls: 'x-btn-text-icon',
				text: _('Url'),
				icon: '/icons/16/add_url.png',
				handler: Deluge.Add.onUrl,
				scope: Deluge.Add
			}, {
				id: 'infohash',
				cls: 'x-btn-text-icon',
				text: _('Infohash'),
				icon: '/icons/16/add_magnet.png'
			}, '->', {
				id: 'remove',
				cls: 'x-btn-text-icon',
				text: _('Remove'),
				icon: '/icons/16/remove.png'
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

Deluge.Add.Url = {
	onAdd: function(field, e) {
		if (field.id == 'url' && e.getKey() != e.ENTER) return;

		var field = this.Form.items.get('url');
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
		bound(info);
	}
}

Deluge.Add.Url.Form = new Ext.form.FormPanel({
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
    width: 300,
    height: 150,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'center',
    closeAction: 'hide',
    closable: false,
    modal: true,
    plain: true,
    title: _('Add from Url'),
    iconCls: 'x-deluge-add-url-window-icon',
    items: Deluge.Add.Url.Form,
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
        text: _('Cancel')
    }, {
		text: _('Add')
	}],
    listeners: {'render': {fn: Deluge.Add.onRender, scope: Deluge.Add}}
});