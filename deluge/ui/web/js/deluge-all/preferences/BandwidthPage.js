/*!
 * Deluge.preferences.BandwidthPage.js
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
 * @class Deluge.preferences.Bandwidth
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Bandwidth = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Bandwidth'),
			layout: 'form',
			labelWidth: 10
		}, config);
		Deluge.preferences.Bandwidth.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Deluge.preferences.Bandwidth.superclass.initComponent.call(this);
		
		var om = deluge.preferences.getOptionsManager();
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Global Bandwidth Usage'),
			labelWidth: 200,
			defaultType: 'spinnerfield',
			defaults: {
				minValue: -1,
				maxValue: 99999
			},
			style: 'margin-bottom: 0px; padding-bottom: 0px;',
			autoHeight: true
		});
		om.bind('max_connections_global', fieldset.add({
			name: 'max_connections_global',
			fieldLabel: _('Maximum Connections'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_upload_slots_global', fieldset.add({
			name: 'max_upload_slots_global',
			fieldLabel: _('Maximum Upload Slots'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_download_speed', fieldset.add({
			name: 'max_download_speed',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 80,
			value: -1.0,
			decimalPrecision: 1
		}));
		om.bind('max_upload_speed', fieldset.add({
			name: 'max_upload_speed',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 80,
			value: -1.0,
			decimalPrecision: 1
		}));
		om.bind('max_half_open_connections', fieldset.add({
			name: 'max_half_open_connections',
			fieldLabel: _('Maximum Half-Open Connections'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_connections_per_second', fieldset.add({
			name: 'max_connections_per_second',
			fieldLabel: _('Maximum Connection Attempts per Second'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: '',
			defaultType: 'checkbox',
			style: 'padding-top: 0px; padding-bottom: 5px; margin-top: 0px; margin-bottom: 0px;',
			autoHeight: true
		});
		om.bind('ignore_limits_on_local_network', fieldset.add({
			name: 'ignore_limits_on_local_network',
			height: 22,
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Ignore limits on local network')
		}));
		om.bind('rate_limit_ip_overhead', fieldset.add({
			name: 'rate_limit_ip_overhead',
			height: 22,
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Rate limit IP overhead')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Per Torrent Bandwidth Usage'),
			style: 'margin-bottom: 0px; padding-bottom: 0px;',
			defaultType: 'spinnerfield',
			labelWidth: 200,
			defaults: {
				minValue: -1,
				maxValue: 99999
			},
			autoHeight: true
		});
		om.bind('max_connections_per_torrent', fieldset.add({
			name: 'max_connections_per_torrent',
			fieldLabel: _('Maximum Connections'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_upload_slots_per_torrent', fieldset.add({
			name: 'max_upload_slots_per_torrent',
			fieldLabel: _('Maximum Upload Slots'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_download_speed_per_torrent', fieldset.add({
			name: 'max_download_speed_per_torrent',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
		om.bind('max_upload_speed_per_torrent', fieldset.add({
			name: 'max_upload_speed_per_torrent',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 80,
			value: -1,
			decimalPrecision: 0
		}));
	}
});
