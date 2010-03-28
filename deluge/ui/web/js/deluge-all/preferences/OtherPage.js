/*!
 * Deluge.preferences.OtherPage.js
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
 * @class Deluge.preferences.Other
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Other = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Other'),
			layout: 'form'
		}, config);
		Deluge.preferences.Other.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Deluge.preferences.Other.superclass.initComponent.call(this);
		
		var optMan = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Updates'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('new_release_check', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 22,
			name: 'new_release_check',
			boxLabel: _('Be alerted about new releases')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('System Information'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		fieldset.add({
			xtype: 'panel',
			border: false,
			bodyCfg: {
				html: _('Help us improve Deluge by sending us your '
				    + 'Python version, PyGTK version, OS and processor '
				    + 'types. Absolutely no other information is sent.')
			}
		});
		optMan.bind('send_info', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Yes, please send anonymous statistics'),
			name: 'send_info'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('GeoIP Database'),
			autoHeight: true,
			labelWidth: 80,
			defaultType: 'textfield'
		});
		optMan.bind('geoip_db_location', fieldset.add({
			name: 'geoip_db_location',
			fieldLabel: _('Location'),
			width: 200
		}));
	}
});
