/*!
 * Deluge.LoginWindow.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */

Deluge.LoginWindow = Ext.extend(Ext.Window, {
	
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
		Deluge.LoginWindow.superclass.initComponent.call(this);
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
			defaultType: 'textfield'
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
		deluge.events.fire('logout');
		deluge.client.auth.delete_session({
			success: function(result) {
				this.show(true);
			},
			scope: this
		});
	},
	
	show: function(skipCheck) {
		if (this.firstShow) {
			deluge.client.on('error', this.onClientError, this);
			this.firstShow = false;
		}
		
		if (skipCheck) {
			return Deluge.LoginWindow.superclass.show.call(this);
		}
		
		deluge.client.auth.check_session({
			success: function(result) {
				if (result) {
					deluge.events.fire('login');
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
		deluge.client.auth.login(passwordField.getValue(), {
			success: function(result) {
				if (result) {
					deluge.events.fire('login');
					this.hide();
					passwordField.setRawValue('');
				} else {
					Ext.MessageBox.show({
						title: _('Login Failed'),
						msg: _('You entered an incorrect password'),
						buttons: Ext.MessageBox.OK,
						modal: false,
						fn: function() {
							passwordField.focus(true, 10);
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
			deluge.events.fire('logout');
			this.show(true);
		}
	},
	
	onShow: function() {
		this.passwordField.focus(true, 100);
	}
});
