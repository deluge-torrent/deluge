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
	var LoginWindow = function(config) {
		Ext.apply(this, {
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
		});
		Ext.apply(this, config);
		LoginWindow.superclass.constructor.call(this);
	};
	
	Ext.extend(LoginWindow, Ext.Window, {
		initComponent: function() {
			LoginWindow.superclass.initComponent.call();
			Deluge.Events.on('logout', this.onLogout);
			this.on('show', this.onShow, this);
			
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
			});
		},
		
		onKey: function(field, e) {
			if (e.getKey() == 13) this.onLogin();
		},
		
		onLogin: function() {
			var passwordField = this.loginForm.items.get('password');
			Deluge.Client.web.login(passwordField.getValue(), {
				onSuccess: function(result) {
					if (result == true) {
						this.hide();
						Deluge.Connections.loginShow();
						passwordField.setRawValue('');
						Deluge.Events.fire('login')
					} else {
						Ext.MessageBox.show({
							title: _('Login Failed'),
							msg: _('You entered an incorrect password'),
							buttons: Ext.MessageBox.OK,
							modal: false,
							icon: Ext.MessageBox.WARNING,
							iconCls: 'x-deluge-icon-warning'
						});
					}
				}.bindWithEvent(this)
			});
		},
		
		onLogout: function() {
			this.show();
		},
		
		onShow: function() {
			var passwordField = this.loginForm.items.get('password');
			passwordField.focus(false, 150);
		}
	});
	
	Deluge.Login = new LoginWindow();
})();