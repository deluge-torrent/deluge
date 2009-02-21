/*
Script: deluge-connections.js
    Contains all objects and functions related to the connection manager.

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

Deluge.Connections = {
	disconnect: function() {
		Deluge.Events.fire('disconnect');
	},
	
    onClose: function(e) {
		$clear(Deluge.Connections.running);
		Deluge.Connections.Window.hide();
    },
    
    onConnect: function(e) {
		$clear(Deluge.Connections.running);
		Deluge.Connections.Window.hide();
		var selected = Deluge.Connections.Grid.getSelectionModel().getSelected();
		if (!selected) return;
		var id = selected.id;
		Deluge.Client.web.connect(id, {
			onSuccess: function(methods) {
				Deluge.Client = new JSON.RPC('/json', {
					methods: methods
				});
				Deluge.Events.fire('connect');
			}
		});
    },
	
	onGetHosts: function(hosts) {
		Deluge.Connections.Store.loadData(hosts);
		var selection = Deluge.Connections.Grid.getSelectionModel();
		selection.selectRow(Deluge.Connections.selectedRow);
	},
	
	onRender: function() {
		Deluge.Events.on('logout', function(e) {
			Deluge.Connections.disconnect();
			Deluge.Connections.Window.hide();
		});
	},
	
	onSelect: function(selModel, rowIndex, record) {
		Deluge.Connections.selectedRow = rowIndex;
	},
	
	onShow: function(window) {
		Deluge.Connections.running = Deluge.Connections.runCheck.periodical(2000);
		Deluge.Connections.runCheck();
	},
	
	runCheck: function() {
		Deluge.Client.web.get_hosts({
			onSuccess: Deluge.Connections.onGetHosts
		});
	}
}

Deluge.Connections.Store = new Ext.data.SimpleStore({
	fields: [
		{name: 'status', mapping: 3},
		{name: 'host', mapping: 1},
		{name: 'port', mapping: 2},
		{name: 'version', mapping: 4}
	],
	id: 0
});

var renderHost = function(value, p, r) {
	return value + ':' + r.data['port']
}

Deluge.Connections.Grid = new Ext.grid.GridPanel({
	store: Deluge.Connections.Store,
	cls: 'deluge-torrents',
	columns: [
		{header: 'Status', width: 55, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'status'},
		{id:'host', header: 'Host', width: 150, sortable: true, renderer: renderHost, dataIndex: 'host'},
		{header: 'Version', width: 75, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'version'}
	],	
	stripeRows: true,
	selModel: new Ext.grid.RowSelectionModel({
		singleSelect: true,
		listeners: {'rowselect': Deluge.Connections.onSelect}
	}),
	autoExpandColumn: 'host',
	deferredRender:false,
	autoScroll:true,
	margins: '0 0 0 0',
	bbar: new Ext.Toolbar({
		items: [
			{
				id: 'add',
				cls: 'x-btn-text-icon',
				text: _('Add'),
				icon: '/icons/16/add.png'
			}, {
				id: 'remove',
				cls: 'x-btn-text-icon',
				text: _('Remove'),
				icon: '/icons/16/remove.png'
			}, '->', {
				id: 'stop',
				cls: 'x-btn-text-icon',
				text: _('Stop Daemon'),
				icon: '/icons/16/error.png'
			}
		]
	})
});

Deluge.Connections.Window = new Ext.Window({
    layout: 'fit',
    width: 300,
    height: 200,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    title: _('Connection Manager'),
    items: [Deluge.Connections.Grid],
    buttons: [{
        text: _('Close'),
        handler: Deluge.Connections.onClose
    },{
        text: _('Connect'),
        handler: Deluge.Connections.onConnect
    }],
	listeners: {
		'hide': Deluge.Connections.onClose,
		'show': Deluge.Connections.onShow,
		'render': Deluge.Connections.onRender
	}
});