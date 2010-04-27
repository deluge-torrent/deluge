/*!
 * Deluge.AddConnectionWindow.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.AddConnectionWindow
 * @extends Ext.Window
 */
Deluge.AddConnectionWindow = Ext.extend(Ext.Window, {

	title: _('Add Connection'),
	iconCls: 'x-deluge-add-window-icon',

	layout: 'fit',
	width:  300,
	height: 195,

	bodyStyle: 'padding: 10px 5px;',
	closeAction: 'hide',

	initComponent: function() {
		Deluge.AddConnectionWindow.superclass.initComponent.call(this);

		this.addEvents('hostadded');
	
		this.addButton(_('Close'), this.hide, this);
		this.addButton(_('Add'), this.onAddClick, this);
	
		this.on('hide', this.onHide, this);
	
		this.form = this.add({
			xtype: 'form',
			defaultType: 'textfield',
			baseCls: 'x-plain',
			labelWidth: 60,
			items: [{
				fieldLabel: _('Host'),
				name: 'host',
				anchor: '75%',
				value: ''
			}, {
				xtype: 'spinnerfield',
				fieldLabel: _('Port'),
				name: 'port',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 65535
				},
				value: '58846',
				anchor: '40%'
			}, {
				fieldLabel: _('Username'),
				name: 'username',
				anchor: '75%',
				value: ''
			}, {
				fieldLabel: _('Password'),
				anchor: '75%',
				name: 'password',
				inputType: 'password',
				value: ''
			}]
		});
	},

	onAddClick: function() {
		var values = this.form.getForm().getValues();
		deluge.client.web.add_host(values.host, values.port, values.username, values.password, {
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
