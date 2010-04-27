/*!
 * Deluge.add.OptionsPanel.js
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
Ext.ns('Deluge.add');

/**
 * @class Deluge.add.OptionsTab
 * @extends Ext.form.FormPanel
 */
Deluge.add.OptionsTab = Ext.extend(Ext.form.FormPanel, {

	title:  _('Options'),
	height: 170,

	border:     false,
	bodyStyle:  'padding: 5px',
	disabled:   true,
	labelWidth: 1,

	initComponent: function() {
		Deluge.add.OptionsTab.superclass.initComponent.call(this);

		this.optionsManager = new Deluge.MultiOptionsManager();

		var fieldset = this.add({
			xtype: 'fieldset',
			title: _('Download Location'),
			border: false,
			autoHeight: true,
			defaultType: 'textfield',
			labelWidth: 1,
			fieldLabel: '',
			style: 'padding-bottom: 5px; margin-bottom: 0px;'
		});

		this.optionsManager.bind('download_location', fieldset.add({
			fieldLabel: '',
			name: 'download_location',
			width: 400,
			labelSeparator: ''
		}));
	
		var panel = this.add({
			border: false,
			layout: 'column',
			defaultType: 'fieldset'
		});
		fieldset = panel.add({
			title: _('Allocation'),
			border: false,
			autoHeight: true,
			defaultType: 'radio',
			width: 100
		});

		this.optionsManager.bind('compact_allocation', fieldset.add({
			xtype: 'radiogroup',
			columns: 1,
			vertical: true,
			labelSeparator: '',
			items: [{
				name: 'compact_allocation',
				value: false,
				inputValue: false,
				boxLabel: _('Full'),
				fieldLabel: '',
				labelSeparator: ''
			}, {
				name: 'compact_allocation',
				value: true,
				inputValue: true,
				boxLabel: _('Compact'),
				fieldLabel: '',
				labelSeparator: ''
			}]
		}));

		fieldset = panel.add({
			title: _('Bandwidth'),
			border: false,
			autoHeight: true,
			labelWidth: 100,
			width: 200,
			defaultType: 'spinnerfield'
		});
		this.optionsManager.bind('max_download_speed', fieldset.add({
			fieldLabel: _('Max Down Speed'),
			labelStyle: 'margin-left: 10px',
			name: 'max_download_speed',
			width: 60
		}));
		this.optionsManager.bind('max_upload_speed', fieldset.add({
			fieldLabel: _('Max Up Speed'),
			labelStyle: 'margin-left: 10px',
			name: 'max_upload_speed',
			width: 60
		}));
		this.optionsManager.bind('max_connections', fieldset.add({
			fieldLabel: _('Max Connections'),
			labelStyle: 'margin-left: 10px',
			name: 'max_connections',
			width: 60
		}));
		this.optionsManager.bind('max_upload_slots', fieldset.add({
			fieldLabel: _('Max Upload Slots'),
			labelStyle: 'margin-left: 10px',
			name: 'max_upload_slots',
			width: 60
		}));
	
		fieldset = panel.add({
			title: _('General'),
			border: false,
			autoHeight: true,
			defaultType: 'checkbox'
		});
		this.optionsManager.bind('add_paused', fieldset.add({
			name: 'add_paused',
			boxLabel: _('Add In Paused State'),
			fieldLabel: '',
			labelSeparator: ''
		}));
		this.optionsManager.bind('prioritize_first_last_pieces', fieldset.add({
			name: 'prioritize_first_last_pieces',
			boxLabel: _('Prioritize First/Last Pieces'),
			fieldLabel: '',
			labelSeparator: ''
		}));
	},

	getDefaults: function() {
		var keys = ['add_paused','compact_allocation','download_location',
		'max_connections_per_torrent','max_download_speed_per_torrent',
		'max_upload_slots_per_torrent','max_upload_speed_per_torrent',
		'prioritize_first_last_pieces'];

		deluge.client.core.get_config_values(keys, {
			success: function(config) {
				var options = {
					'file_priorities': [],
					'add_paused': config.add_paused,
					'compact_allocation': config.compact_allocation,
					'download_location': config.download_location,
					'max_connections': config.max_connections_per_torrent,
					'max_download_speed': config.max_download_speed_per_torrent,
					'max_upload_slots': config.max_upload_slots_per_torrent,
					'max_upload_speed': config.max_upload_speed_per_torrent,
					'prioritize_first_last_pieces': config.prioritize_first_last_pieces
				}
				this.optionsManager.options = options;
				this.optionsManager.resetAll();
			},
			scope: this
		});
	}
});
