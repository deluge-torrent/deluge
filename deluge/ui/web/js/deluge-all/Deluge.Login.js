/*
Script: Deluge.Login.js
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

Ext.deluge.LoginWindow = Ext.extend(Ext.Window, {
	
	firstShow:   true,
	bodyStyle:   'padding: 10px 5px;',
	buttonAlign: 'center',
	closable:    false,
	closeAction: 'hide',
	iconCls:     'x-deluge-login-window-icon',
	layout:      'fit',
	modal:       true,
	plain:       true,
	resizable:   false,
	title:       _('Login'),
	width:       300,
	height:      120,
	
	initComponent: function() {
		Ext.deluge.LoginWindow.superclass.initComponent.call(this);
		this.on('show', this.onShow, this);
		
		this.addButton({
			text: _('Login'),
			handler: this.onLogin,
			scope: this
		});
		
		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			labelWidth: 55,
			width: 300,
			defaults: {width: 200},
			defaultType: 'textfield',
		});

		this.passwordField = this.form.add({
			xtype: 'textfield',
			fieldLabel: _('Password'),
			id: '_password',
			name: 'password',
			inputType: 'password'
		});
		this.passwordField.on('specialkey', this.onSpecialKey, this);
	},
	
	logout: function() {
		Deluge.Events.fire('logout');
		Deluge.Client.auth.delete_session({
			success: function(result) {
				this.show(true);
			},
			scope: this
		});
	},
	
	show: function(skipCheck) {
		if (this.firstShow) {
			Deluge.Client.on('error', this.onClientError, this);
			this.firstShow = false;
		}
		
		if (skipCheck) {
			return Ext.deluge.LoginWindow.superclass.show.call(this);
		}
		
		Deluge.Client.auth.check_session({
			success: function(result) {
				if (result) {
					Deluge.Events.fire('login');
				} else {
					this.show(true);
				}
			},
			failure: function(result) {
				this.show(true);
			},
			scope: this
		});
	},
	
	onSpecialKey: function(field, e) {
		if (e.getKey() == 13) this.onLogin();
	},
	
	onLogin: function() {
		var passwordField = this.passwordField;
		Deluge.Client.auth.login(passwordField.getValue(), {
			success: function(result) {
				if (result) {
					Deluge.Events.fire('login');
					this.hide();
					passwordField.setRawValue('');
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
	
	onClientError: function(errorObj, response, requestOptions) {
		if (errorObj.error.code == 1) {
			Deluge.Events.fire('logout');
			this.show(true);
		}
	},
	
	onShow: function() {
		this.passwordField.focus(false, 150);
		this.passwordField.setRawValue('');
	}
});

Deluge.Login = new Ext.deluge.LoginWindow();
