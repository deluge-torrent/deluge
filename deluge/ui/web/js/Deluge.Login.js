/*
Script: deluge-login.js
    Contains all objects and functions related to the login system.

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

(function(){
	Ext.deluge.LoginWindow = Ext.extend(Ext.Window, {
		
		firstShow: true,
		
		constructor: function(config) {
			config = Ext.apply({
				layout: 'fit',
				width: 300,
				height: 120,
				bodyStyle: 'padding: 10px 5px;',
				buttonAlign: 'center',
				closeAction: 'hide',
				closable: false,
				modal: true,
				plain: true,
				resizable: false,
				title: _('Login'),
				iconCls: 'x-deluge-login-window-icon'
			}, config);
			Ext.deluge.LoginWindow.superclass.constructor.call(this, config);
		},
		
		initComponent: function() {
			Ext.deluge.LoginWindow.superclass.initComponent.call(this);
			Deluge.Events.on('logout', this.onLogout, this);
			this.on('show', this.onShow, this);
			this.on('beforeshow', this.onBeforeShow, this);
			
			this.addButton({
				text: _('Login'),
				handler: this.onLogin,
				scope: this
			});
			
			this.loginForm = this.add({
				xtype: 'form',
				defaultType: 'textfield',
				id: 'loginForm',
				baseCls: 'x-plain',
				labelWidth: 55,
				items: [{
					fieldLabel: _('Password'),
					id: 'password',
					name: 'password',
					inputType: 'password',
					anchor: '100%',
					listeners: {
						'specialkey': {
							fn: this.onKey,
							scope: this
						}
					}
				}]
			})
		},
		
		onKey: function(field, e) {
			if (e.getKey() == 13) this.onLogin();
		},
		
		onLogin: function() {
			var passwordField = this.loginForm.items.get('password');
			Deluge.Client.auth.login(passwordField.getValue(), {
				success: function(result) {
					if (result) {
						Deluge.Events.fire('login');
						this.hide();
						passwordField.setRawValue('');
						Deluge.UI.cookies.set("session", result);
					} else {
						Ext.MessageBox.show({
							title: _('Login Failed'),
							msg: _('You entered an incorrect password'),
							buttons: Ext.MessageBox.OK,
							modal: false,
							fn: function() {
								passwordField.focus();
							},
							icon: Ext.MessageBox.WARNING,
							iconCls: 'x-deluge-icon-warning'
						});
					}
				},
				scope: this
			});
		},
		
		onLogout: function() {
			var session = Deluge.UI.cookies.get("session", false);
			if (session) {
				Deluge.Client.auth.delete_session(session, {
					success: function(result) {
						Deluge.UI.cookies.clear("session");
						this.show();
					},
					scope: this
				});
			}
		},
		
		onBeforeShow: function() {
			var session = Deluge.UI.cookies.get("session", false);
			if (session) {
				Deluge.Client.auth.check_session(session, {
					success: function(result) {
						if (result) {
							Deluge.Events.fire('login');
							this.loginForm.items.get('password').setRawValue('');
							this.hide();
						} else {
							Deluge.UI.cookies.clear("session");
							this.show();
						}
					},
					failure: function(result) {
						Deluge.UI.cookies.clear("session");
						this.show();
					},
					scope: this
				});
				return false;
			}
		},
		
		onShow: function() {
			var passwordField = this.loginForm.items.get('password');
			passwordField.focus(false, 150);
		}
	});
	
	Deluge.Login = new Ext.deluge.LoginWindow();
})();