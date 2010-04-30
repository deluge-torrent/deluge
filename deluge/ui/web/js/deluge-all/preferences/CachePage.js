/*!
 * Deluge.preferences.CachePage.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Cache
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Cache = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Cache'),
	layout: 'form',
	
	initComponent: function() {
		Deluge.preferences.Cache.superclass.initComponent.call(this);

		var om = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Settings'),
			autoHeight: true,
			labelWidth: 180,
			defaultType: 'spinnerfield',
			defaults: {
				decimalPrecision: 0,
				minValue: -1,
				maxValue: 99999
			}
		});
		om.bind('cache_size', fieldset.add({
			fieldLabel: _('Cache Size (16 KiB Blocks)'),
			name: 'cache_size',
			width: 60,
			value: 512
		}));
		om.bind('cache_expiry', fieldset.add({
			fieldLabel: _('Cache Expiry (seconds)'),
			name: 'cache_expiry',
			width: 60,
			value: 60
		}));
	}
});
