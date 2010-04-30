/*!
 * Deluge.preferences.DaemonPage.js
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
 * @class Deluge.preferences.Daemon
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Daemon = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Daemon'),
	layout: 'form',
	
	initComponent: function() {
		Deluge.preferences.Daemon.superclass.initComponent.call(this);

		var om = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Port'),
			autoHeight: true,
			defaultType: 'spinnerfield'
		});
		om.bind('daemon_port', fieldset.add({
			fieldLabel: _('Daemon port'),
			name: 'daemon_port',
			value: 58846,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Connections'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		om.bind('allow_remote', fieldset.add({
			fieldLabel: '',
			height: 22,
			labelSeparator: '',
			boxLabel: _('Allow Remote Connections'),
			name: 'allow_remote'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Other'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		om.bind('new_release_check', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 40,
			boxLabel: _('Periodically check the website for new releases'),
			id: 'new_release_check'
		}));
	}
});
