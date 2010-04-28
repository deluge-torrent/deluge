/*!
 * Deluge.preferences.EncryptionPage.js
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
 * @class Deluge.preferences.Encryption
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Encryption = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Encryption'),
	
	initComponent: function() {
		Deluge.preferences.Encryption.superclass.initComponent.call(this);

		var optMan = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Settings'),
			autoHeight: true,
			defaultType: 'combo',
			width: 300
		});
		optMan.bind('enc_in_policy', fieldset.add({
			fieldLabel: _('Inbound'),
			mode: 'local',
			width: 150,
			store: new Ext.data.ArrayStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Forced')],
					[1, _('Enabled')],
					[2, _('Disabled')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_out_policy', fieldset.add({
			fieldLabel: _('Outbound'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Forced')],
					[1, _('Enabled')],
					[2, _('Disabled')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_level', fieldset.add({
			fieldLabel: _('Level'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Handshake')],
					[1, _('Full Stream')],
					[2, _('Either')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_prefer_rc4', fieldset.add({
			xtype: 'checkbox',
			name: 'enc_prefer_rc4',
			height: 40,
			hideLabel: true,
			boxLabel: _('Encrypt entire stream')
		}));
	}
});
