/*!
 * Deluge.AddTrackerWindow.js
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
 * @class Deluge.AddTrackerWindow
 * @extends Ext.Window
 */
Deluge.AddTrackerWindow = Ext.extend(Ext.Window, {
	
	title: _('Add Tracker'),
	layout: 'fit',
	width: 375,
	height: 150,
	plain: true,
	closable: true,
	resizable: false,

	bodyStyle: 'padding: 5px',
	buttonAlign: 'right',
	closeAction: 'hide',
	iconCls: 'x-deluge-edit-trackers',

	initComponent: function() {
		Deluge.AddTrackerWindow.superclass.initComponent.call(this);
	
		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Add'), this.onAddClick, this);
		this.addEvents('add');
	
		this.form = this.add({
			xtype: 'form',
			defaultType: 'textarea',
			baseCls: 'x-plain',
			labelWidth: 55,
			items: [{
				fieldLabel: _('Trackers'),
				name: 'trackers',
				anchor: '100%'
			}]
		})
	},

	onAddClick: function() {
		var trackers = this.form.getForm().findField('trackers').getValue();
		trackers = trackers.split('\n');
	
		var cleaned = [];
		Ext.each(trackers, function(tracker) {
			if (Ext.form.VTypes.url(tracker)) {
				cleaned.push(tracker);
			}
		}, this);
		this.fireEvent('add', cleaned);
		this.hide();
		this.form.getForm().findField('trackers').setValue('');
	},

	onCancelClick: function() {
		this.form.getForm().findField('trackers').setValue('');
		this.hide();
	}
});
