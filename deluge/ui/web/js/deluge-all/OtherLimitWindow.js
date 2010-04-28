/*!
 * Deluge.OtherLimitWindow.js
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
 * @class Deluge.OtherLimitWindow
 * @extends Ext.Window
 */
Deluge.OtherLimitWindow = Ext.extend(Ext.Window, {
	
	layout: 'fit',
	width: 210,
	height: 100,

	closeAction: 'hide',

	initComponent: function() {
		Deluge.OtherLimitWindow.superclass.initComponent.call(this);
		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			bodyStyle: 'padding: 5px',
			layout: 'hbox',
			layoutConfig: {
				pack: 'start'
			},
			items: [{
				xtype: 'spinnerfield',
				name: 'limit'
			}]
		});
		if (this.initialConfig.unit) {
			this.form.add({
				border: false,
				baseCls: 'x-plain',
				bodyStyle: 'padding: 5px',
				html: this.initialConfig.unit
			});
		} else {
			this.setSize(180, 100);
		}

		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Ok'), this.onOkClick, this);
		this.afterMethod('show', this.doFocusField, this);
	},

	setValue: function(value) {
		this.form.getForm().setValues({limit: value});
	},

	onCancelClick: function() {
		this.form.getForm().reset();
		this.hide();
	},

	onOkClick: function() {
		var config = {};
		config[this.group] = this.form.getForm().getValues().limit;
		deluge.client.core.set_config(config, {
			success: function() {
				deluge.ui.update();
			}
		});
		this.hide();
	},

	doFocusField: function() {
		this.form.getForm().findField('limit').focus(true, 10);
	}
});
