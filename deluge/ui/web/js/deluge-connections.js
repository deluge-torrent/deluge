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
	
	loginShow: function() {
		Deluge.Events.on('logout', function(e) {
			Deluge.Connections.disconnect();
			Deluge.Connections.Window.hide();
		});

		Deluge.Client.web.connected({
			onSuccess: function(connected) {
				if (connected) {
					Deluge.Events.fire('connect');
				} else {
					Deluge.Connections.Window.show();
				}
			}
		});
	},
	
	onAdd: function(button, e) {
		Deluge.Connections.Add.show();
	},
	
	onAddHost: function() {
		var form = Deluge.Connections.Add.items.first();
		var host = form.items.get('host').getValue();
		var port = form.items.get('port').getValue();
		var username = form.items.get('username').getValue();
		var password = form.items.get('_password').getValue();
		
		Deluge.Client.web.add_host(host, port, username, password, {
			onSuccess: function(result) {
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
					Deluge.Connections.runCheck();
				}
				Deluge.Connections.Add.hide();
			}
		});
	},
	
	onAddWindowHide: function() {
		// Tidy up the form to ensure all the values are default.
		var form = Deluge.Connections.Add.items.first();
		form.items.get('host').reset();
		form.items.get('port').reset();
		form.items.get('username').reset();
		form.items.get('_password').reset();
	},
	
    onClose: function(e) {
		$clear(Deluge.Connections.running);
		Deluge.Connections.Window.hide();
    },
    
    onConnect: function(e) {
		
		var selected = Deluge.Connections.Grid.getSelectionModel().getSelected();
		if (!selected) return;
		
		if (selected.get('status') == _('Connected')) {
			Deluge.Client.web.disconnect({
				onSuccess: function(result) {
					Deluge.Connections.runCheck();
					Deluge.Events.fire('disconnect');
				}
			});
		} else {
			var id = selected.id;
			Deluge.Client.web.connect(id, {
				onSuccess: function(methods) {
					Deluge.Client = new JSON.RPC('/json', {
						methods: methods
					});
					Deluge.Events.fire('connect');
				}
			});
			$clear(Deluge.Connections.running);
			Deluge.Connections.Window.hide();
		}
    },
	
	onGetHosts: function(hosts) {
		Deluge.Connections.Store.loadData(hosts);
		var selection = Deluge.Connections.Grid.getSelectionModel();
		selection.selectRow(Deluge.Connections.selectedRow);
	},
	
	onRemove: function(button) {
		var connection = Deluge.Connections.Grid.getSelectionModel().getSelected();
		Deluge.Client.web.remove_host(connection.id, {
			onSuccess: function(result) {
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
					Deluge.Connections.Grid.store.remove(connection);
				}
			}
		});
	},
	
	onSelect: function(selModel, rowIndex, record) {
		Deluge.Connections.selectedRow = rowIndex;
		var button = Deluge.Connections.Window.buttons[1];
		if (record.get('status') == _('Connected')) {
			button.setText(_('Disconnect'));
		} else {
			button.setText(_('Connect'));
		}
	},
	
	onShow: function(window) {
		Deluge.Connections.running = Deluge.Connections.runCheck.periodical(2000);
		Deluge.Connections.runCheck();
	},
	
	onStop: function(button, e) {
		var connection = Deluge.Connections.Grid.getSelectionModel().getSelected();
		Deluge.Client.web.stop_daemon(connection.id, {
			onSuccess: function(result) {
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
	},
	
	runCheck: function(callback) {
		callback = $pick(callback, Deluge.Connections.onGetHosts);
		Deluge.Client.web.get_hosts({
			onSuccess: callback
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
	columns: [
		{header: 'Status', width: 65, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'status'},
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
				icon: '/icons/add.png',
				handler: Deluge.Connections.onAdd
			}, {
				id: 'remove',
				cls: 'x-btn-text-icon',
				text: _('Remove'),
				icon: '/icons/remove.png',
				handler: Deluge.Connections.onRemove
			}, '->', {
				id: 'stop',
				cls: 'x-btn-text-icon',
				text: _('Stop Daemon'),
				icon: '/icons/error.png',
				handler: Deluge.Connections.onStop
			}
		]
	})
});

Deluge.Connections.Add = new Ext.Window({
	layout: 'fit',
    width: 300,
    height: 195,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    title: _('Add Connection'),
    iconCls: 'x-deluge-add-window-icon',
    items: [new Ext.form.FormPanel({
		defaultType: 'textfield',
		id: 'connectionAddForm',
		baseCls: 'x-plain',
		labelWidth: 55,
		items: [{
			fieldLabel: _('Host'),
			id: 'host',
			name: 'host',
			anchor: '100%',
			listeners: {}
		},{
			fieldLabel: _('Port'),
			id: 'port',
			xtype: 'uxspinner',
			ctCls: 'x-form-uxspinner',
			name: 'port',
			strategy: Ext.ux.form.Spinner.NumberStrategy(),
			value: '58846',
			anchor: '50%',
			listeners: {}
		}, {
			fieldLabel: _('Username'),
			id: 'username',
			name: 'username',
			anchor: '100%',
			listeners: {}
		},{
			fieldLabel: _('Password'),
			anchor: '100%',
			id: '_password',
			name: '_password',
			inputType: 'password'
		}]
	})],
    buttons: [{
        text: _('Close'),
		handler: function() {
			Deluge.Connections.Add.hide();
		}
    },{
        text: _('Add'),
		handler: Deluge.Connections.onAddHost
    }],
	listeners: {
		'hide': Deluge.Connections.onAddWindowHide
	}
});

Deluge.Connections.Window = new Ext.Window({
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
		'show': Deluge.Connections.onShow
	}
});