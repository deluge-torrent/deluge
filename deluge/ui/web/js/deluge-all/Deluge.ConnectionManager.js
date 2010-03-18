/*
Script: Deluge.ConnectionManager.js
	Contains all objects and functions related to the connection manager.

Copyright:
	(C) Damien Churchill 2009-2010 <damoxc@gmail.com>
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

(function() {
	var hostRenderer = function(value, p, r) {
		return value + ':' + r.data['port']
	}

	Deluge.AddConnectionWindow = Ext.extend(Ext.Window, {

		constructor: function(config) {
			config = Ext.apply({
				layout: 'fit',
				width: 300,
				height: 195,
				bodyStyle: 'padding: 10px 5px;',
				buttonAlign: 'right',
				closeAction: 'hide',
				closable: true,
				plain: true,
				title: _('Add Connection'),
				iconCls: 'x-deluge-add-window-icon'
			}, config);
			Deluge.AddConnectionWindow.superclass.constructor.call(this, config);
		},
	
		initComponent: function() {
			Deluge.AddConnectionWindow.superclass.initComponent.call(this);
	
			this.addEvents('hostadded');
		
			this.addButton(_('Close'), this.hide, this);
			this.addButton(_('Add'), this.onAddClick, this);
		
			this.on('hide', this.onHide, this);
		
			this.form = this.add({
				xtype: 'form',
				defaultType: 'textfield',
				id: 'connectionAddForm',
				baseCls: 'x-plain',
				labelWidth: 55
			});
		
			this.hostField = this.form.add({
				fieldLabel: _('Host'),
				id: 'host',
				name: 'host',
				anchor: '100%',
				value: ''
			});
		
			this.portField = this.form.add({
				fieldLabel: _('Port'),
				id: 'port',
				xtype: 'spinnerfield',
				name: 'port',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 65535
				},
				value: '58846',
				anchor: '50%'
			});
		
			this.usernameField = this.form.add({
				fieldLabel: _('Username'),
				id: 'username',
				name: 'username',
				anchor: '100%',
				value: ''
			});
		
			this.passwordField = this.form.add({
				fieldLabel: _('Password'),
				anchor: '100%',
				id: '_password',
				name: '_password',
				inputType: 'password',
				value: ''
			});
		},
	
		onAddClick: function() {
			var host = this.hostField.getValue();
			var port = this.portField.getValue();
			var username = this.usernameField.getValue();
			var password = this.passwordField.getValue();
	
			deluge.client.web.add_host(host, port, username, password, {
				success: function(result) {
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
						this.fireEvent('hostadded');
					}
					this.hide();
				},
				scope: this
			});
		},
	
		onHide: function() {
			this.form.getForm().reset();
		}
	});

	Deluge.ConnectionManager = Ext.extend(Ext.Window, {

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
	
		initComponent: function() {
			Deluge.ConnectionManager.superclass.initComponent.call(this);
			this.on('hide',  this.onHide, this);
			this.on('show', this.onShow, this);

			deluge.events.on('disconnect', this.onDisconnect, this);
			deluge.events.on('login', this.onLogin, this);
			deluge.events.on('logout', this.onLogout, this);
	
			this.addButton(_('Close'), this.onClose, this);
			this.addButton(_('Connect'), this.onConnect, this);
		
			this.grid = this.add({
				xtype: 'grid',
				store: new Ext.data.SimpleStore({
					fields: [
						{name: 'status', mapping: 3},
						{name: 'host', mapping: 1},
						{name: 'port', mapping: 2},
						{name: 'version', mapping: 4}
					],
					id: 0
				}),
				columns: [{
					header: _('Status'),
					width: 65,
					sortable: true,
					renderer: fplain,
					dataIndex: 'status'
				}, {
					id:'host',
					header: _('Host'),
					width: 150,
					sortable: true,
					renderer: hostRenderer,
					dataIndex: 'host'
				}, {
					header: _('Version'),
					width: 75,
					sortable: true,
					renderer: fplain,
					dataIndex: 'version'
				}],
				stripeRows: true,
				selModel: new Ext.grid.RowSelectionModel({
					singleSelect: true,
					listeners: {
						'rowselect': {fn: this.onSelect, scope: this},
						'selectionchange': {fn: this.onSelectionChanged, scope: this}
					}
				}),
				autoExpandColumn: 'host',
				deferredRender:false,
				autoScroll:true,
				margins: '0 0 0 0',
				bbar: new Ext.Toolbar({
					buttons: [
						{
							id: 'cm-add',
							cls: 'x-btn-text-icon',
							text: _('Add'),
							icon: '/icons/add.png',
							handler: this.onAddClick,
							scope: this
						}, {
							id: 'cm-remove',
							cls: 'x-btn-text-icon',
							text: _('Remove'),
							icon: '/icons/remove.png',
							handler: this.onRemove,
							disabled: true,
							scope: this
						}, '->', {
							id: 'cm-stop',
							cls: 'x-btn-text-icon',
							text: _('Stop Daemon'),
							icon: '/icons/error.png',
							handler: this.onStop,
							disabled: true,
							scope: this
						}
					]
				})
			});

			this.update = this.update.createDelegate(this);
		},

		/**
		 * Check to see if the the web interface is currently connected
		 * to a Deluge Daemon and show the Connection Manager if not.
		 */
		checkConnected: function() {
			deluge.client.web.connected({
				success: function(connected) {
					if (connected) {
						deluge.events.fire('connect');
					} else {
						this.show();
					}
				},
				scope: this
			});
		},

		disconnect: function() {
			deluge.events.fire('disconnect');
		},
	
		loadHosts: function() {
			deluge.client.web.get_hosts({
				success: this.onGetHosts,
				scope: this
			});
		},
	
		update: function() {
			this.grid.getStore().each(function(r) {
				deluge.client.web.get_host_status(r.id, {
					success: this.onGetHostStatus,
					scope: this
				});
			}, this);
		},
	
		/**
		 * Updates the buttons in the Connection Manager UI according to the
		 * passed in records host state.
		 * @param {Ext.data.Record} record The hosts record to update the UI for
		 */
		updateButtons: function(record) {
			var button = this.buttons[1], status = record.get('status');
		
			// Update the Connect/Disconnect button
			if (status == _('Connected')) {
				button.enable();
				button.setText(_('Disconnect'));
			} else if (status == _('Offline')) {
				button.disable();
			} else {
				button.enable();
				button.setText(_('Connect'));
			}
			
			// Update the Stop/Start Daemon button
			if (status == _('Offline')) {
				if (record.get('host') == '127.0.0.1' || record.get('host') == 'localhost') {
					this.stopHostButton.enable();
					this.stopHostButton.setText(_('Start Daemon'));
				} else {
					this.stopHostButton.disable();
				}
			} else {
				this.stopHostButton.enable();
				this.stopHostButton.setText(_('Stop Daemon'));
			}
		},
	
		onAddClick: function(button, e) {
			if (!this.addWindow) {
				this.addWindow = new Deluge.AddConnectionWindow();
				this.addWindow.on('hostadded', this.onHostAdded, this);
			}
			this.addWindow.show();
		},
	
		onHostAdded: function() {
			this.loadHosts();
		},
	
		// private
		onClose: function(e) {
			if (this.running) window.clearInterval(this.running);
			this.hide();
		},
	
		// private
		onConnect: function(e) {
			var selected = this.grid.getSelectionModel().getSelected();
			if (!selected) return;
	
			if (selected.get('status') == _('Connected')) {
				deluge.client.web.disconnect({
					success: function(result) {
						this.update(this);
						Deluge.Events.fire('disconnect');
					},
					scope: this
				});
			} else {
				var id = selected.id;
				deluge.client.web.connect(id, {
					success: function(methods) {
						deluge.client.reloadMethods();
						deluge.client.on('connected', function(e) {
							deluge.events.fire('connect');
						}, this, {single: true});
					}
				});
				this.hide();
			}
		},

		onDisconnect: function() {
			if (this.isVisible()) return;
			this.show();
		},

		// private
		onGetHosts: function(hosts) {
			this.grid.getStore().loadData(hosts);
			Ext.each(hosts, function(host) {
				deluge.client.web.get_host_status(host[0], {
					success: this.onGetHostStatus,
					scope: this
				});
			}, this);
		},
	
		// private
		onGetHostStatus: function(host) {
			var record = this.grid.getStore().getById(host[0]);
			record.set('status', host[3])
			record.set('version', host[4])
			record.commit();
			if (this.grid.getSelectionModel().getSelected() == record) this.updateButtons(record);
		},

		// private
		onHide: function() {
			if (this.running) window.clearInterval(this.running);	
		},

		// private
		onLogin: function() {
			if (deluge.config.first_login) {
				Ext.MessageBox.confirm('Change password',
					'As this is your first login, we recommend that you ' +
					'change your password. Would you like to ' +
					'do this now?', function(res) {
						this.checkConnected();
						if (res == 'yes') {
							deluge.preferences.show();
							deluge.preferences.selectPage('Interface');
						}
						deluge.client.web.set_config({first_login: false});
					}, this);
			} else {
				this.checkConnected();
			}
		},

		// private
		onLogout: function() {
			this.disconnect();
			if (!this.hidden && this.rendered) {
				this.hide();
			}
		},
	
		// private
		onRemove: function(button) {
			var connection = this.grid.getSelectionModel().getSelected();
			if (!connection) return;
	
			deluge.client.web.remove_host(connection.id, {
				success: function(result) {
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
						this.grid.getStore().remove(connection);
					}
				},
				scope: this
			});
		},

		// private
		onSelect: function(selModel, rowIndex, record) {
			this.selectedRow = rowIndex;
		},

		// private
		onSelectionChanged: function(selModel) {
			var record = selModel.getSelected();
			if (selModel.hasSelection()) {
				this.removeHostButton.enable();
				this.stopHostButton.enable();
				this.stopHostButton.setText(_('Stop Daemon'));
			} else {
				this.removeHostButton.disable();
				this.stopHostButton.disable();
			}
			this.updateButtons(record);
		},

		// private
		onShow: function() {
			if (!this.addHostButton) {
				var bbar = this.grid.getBottomToolbar();
				this.addHostButton = bbar.items.get('cm-add');
				this.removeHostButton = bbar.items.get('cm-remove');
				this.stopHostButton = bbar.items.get('cm-stop');
			}
			this.loadHosts();
			this.running = window.setInterval(this.update, 2000, this);
		},
		
		// private
		onStop: function(button, e) {
			var connection = this.grid.getSelectionModel().getSelected();
			if (!connection) return;
	
			if (connection.get('status') == 'Offline') {
				// This means we need to start the daemon
				deluge.client.web.start_daemon(connection.get('port'));
			} else {
				// This means we need to stop the daemon
				deluge.client.web.stop_daemon(connection.id, {
					success: function(result) {
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
			}
		}
	});
	deluge.connectionManager = new Deluge.ConnectionManager();
})();
