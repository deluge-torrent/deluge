/*!
 * Deluge.preferences.QueuePage.js
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
 * @class Deluge.preferences.Queue
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Queue = Ext.extend(Ext.form.FormPanel, {

	border: false,
	title: _('Queue'),
	layout: 'form',
	
	initComponent: function() {
		Deluge.preferences.Queue.superclass.initComponent.call(this);
		
		var om = deluge.preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('General'),
			style: 'padding-top: 5px;',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		om.bind('queue_new_to_top', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Queue new torrents to top'),
			name: 'queue_new_to_top'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Active Torrents'),
			autoHeight: true,
			labelWidth: 150,
			defaultType: 'spinnerfield',
			style: 'margin-bottom: 0px; padding-bottom: 0px;'
		});
		om.bind('max_active_limit', fieldset.add({
			fieldLabel: _('Total Active'),
			name: 'max_active_limit',
			value: 8,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		om.bind('max_active_downloading', fieldset.add({
			fieldLabel: _('Total Active Downloading'),
			name: 'max_active_downloading',
			value: 3,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		om.bind('max_active_seeding', fieldset.add({
			fieldLabel: _('Total Active Seeding'),
			name: 'max_active_seeding',
			value: 5,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		om.bind('dont_count_slow_torrents', fieldset.add({
			xtype: 'checkbox',
			name: 'dont_count_slow_torrents',
			height: 40,
			hideLabel: true,
			boxLabel: _('Do not count slow torrents')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Seeding'),
			autoHeight: true,
			labelWidth: 150,
			defaultType: 'spinnerfield',
			style: 'margin-bottom: 0px; padding-bottom: 0px; margin-top: 0; padding-top: 0;'
		});
		om.bind('share_ratio_limit', fieldset.add({
			fieldLabel: _('Share Ratio Limit'),
			name: 'share_ratio_limit',
			value: 8,
			width: 80,
			incrementValue: 0.1,
			minValue: -1,
			maxValue: 99999,
			alternateIncrementValue: 1,
			decimalPrecision: 2
		}));
		om.bind('seed_time_ratio_limit', fieldset.add({
			fieldLabel: _('Share Time Ratio'),
			name: 'seed_time_ratio_limit',
			value: 3,
			width: 80,
			incrementValue: 0.1,
			minValue: -1,
			maxValue: 99999,
			alternateIncrementValue: 1,
			decimalPrecision: 2
		}));
		om.bind('seed_time_limit', fieldset.add({
			fieldLabel: _('Seed Time (m)'),
			name: 'seed_time_limit',
			value: 5,
			width: 80,
			decimalPrecision: 0,
			minValue: -1,
			maxValue: 99999
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			autoHeight: true,
			
			layout: 'table',
			layoutConfig: {columns: 2},
			labelWidth: 0,
			defaultType: 'checkbox',
			
			defaults: {
				fieldLabel: '',
				labelSeparator: ''
			}
		});
		this.stopAtRatio = fieldset.add({
			name: 'stop_seed_at_ratio',
			boxLabel: _('Stop seeding when share ratio reaches:')
		});
		this.stopAtRatio.on('check', this.onStopRatioCheck, this);
		om.bind('stop_seed_at_ratio', this.stopAtRatio);
		
		this.stopRatio = fieldset.add({
			xtype: 'spinnerfield',
			name: 'stop_seed_ratio',
			ctCls: 'x-deluge-indent-checkbox',
			disabled: true,
			value: '2.0',
			width: 60,
			incrementValue: 0.1,
			minValue: -1,
			maxValue: 99999,
			alternateIncrementValue: 1,
			decimalPrecision: 2
		});
		om.bind('stop_seed_ratio', this.stopRatio);
		
		this.removeAtRatio = fieldset.add({
			name: 'remove_seed_at_ratio',
			ctCls: 'x-deluge-indent-checkbox',
			boxLabel: _('Remove torrent when share ratio is reached'),
			disabled: true,
			colspan: 2
		});
		om.bind('remove_seed_at_ratio', this.removeAtRatio);
	},
	
	onStopRatioCheck: function(e, checked) {
		this.stopRatio.setDisabled(!checked);
		this.removeAtRatio.setDisabled(!checked);
	}
});
