/*
Script: Deluge.Details.Options.js
    The options tab displayed in the details panel.

Copyright:
	(C) Damien Churchill 2009 <damoxc@gmail.com>
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, write to:
		The Free Software Foundation, Inc.,
		51 Franklin Street, Fifth Floor
		Boston, MA  02110-1301, USA.
*/

Ext.deluge.details.OptionsTab = Ext.extend(Ext.form.FormPanel, {

	title: _('Options'),
	cls: 'x-deluge-options',
	
	constructor: function(config) {
		this.initialConfig = {
			autoScroll:true,
			
			deferredRender:false
		}
		config = Ext.apply({
			items: [{
				layout: 'column',
				border: false,
				bodyStyle: 'padding: 5px;',
				defaults: {
					border: false
				},
				
				items: [{
					bodyStyle: 'padding-left: 5px; padding-right:5px;',
					width: 300,
					items: [{
						xtype: 'fieldset',
						title: _('Bandwidth'),
						layout: 'table',
						layoutConfig: {columns: 3},
						autoHeight: true,
						labelWidth: 150,
						defaultType: 'uxspinner',
						items: [{
							xtype: 'label',
							text: _('Max Download Speed'),
							forId: 'max_download_speed',
							cls: 'x-deluge-options-label'
						}, {
							id: 'max_download_speed',
							name: 'max_download_speed',
							width: 100,
							value: -1,
							strategy: new Ext.ux.form.Spinner.NumberStrategy({
								minValue: -1,
								maxValue: 99999,
								incrementValue: 1
							})
						}, {
							xtype: 'label',
							text: 'KiB/s',
							style: 'margin-left: 10px;'
						}, {
							xtype: 'label',
							text: _('Max Upload Speed'),
							forId: 'max_upload_speed',
							cls: 'x-deluge-options-label'
						}, {
							id: 'max_upload_speed',
							width: 100,
							value: -1,
							strategy: new Ext.ux.form.Spinner.NumberStrategy({
								minValue: -1,
								maxValue: 99999,
								incrementValue: 1
							})
						}, {
							xtype: 'label',
							text: 'KiB/s',
							style: 'margin-left: 10px;'
						}, {
							xtype: 'label',
							text: _('Max Connections'),
							forId: 'max_connections',
							cls: 'x-deluge-options-label'
						}, {
							id: 'max_connections',
							colspan: 2,
							width: 100,
							value: -1,
							strategy: new Ext.ux.form.Spinner.NumberStrategy({
								minValue: -1,
								maxValue: 99999,
								incrementValue: 1
							})
						}, {
							xtype: 'label',
							text: _('Max Upload Slots'),
							forId: 'max_upload_slots',
							cls: 'x-deluge-options-label'
						}, {
							id: 'max_upload_slots',
							colspan: 2,
							width: 100,
							value: -1,
							strategy: new Ext.ux.form.Spinner.NumberStrategy({
								minValue: -1,
								maxValue: 99999,
								incrementValue: 1
							})
						}]
					}]
				}, {
					bodyStyle: 'padding-left: 5px; padding-right:5px;',
					width: 200,
					items: [{
						xtype: 'fieldset',
						title: _('Queue'),
						autoHeight: true,
						labelWidth: 1,
						defaultType: 'checkbox',
						items: [{
							fieldLabel: '',
							labelSeparator: '',
							boxLabel: _('Auto Managed'),
							id: 'is_auto_managed'
						}, {
							fieldLabel: '',
							labelSeparator: '',
							boxLabel: _('Stop seed at ratio'),
							id: 'stop_at_ratio'
						}, {
							fieldLabel: '',
							labelSeparator: '',
							boxLabel: _('Remove at ratio'),
							id: 'remove_at_ratio'
						}, {
							fieldLabel: '',
							labelSeparator: '',
							boxLabel: _('Move Completed'),
							id: 'move_completed'
						}]
					}]
				}, {
					bodyStyle: 'padding-left:5px;',
					width: 200,
					items: [{
						xtype: 'fieldset',
						title: _('General'),
						autoHeight: true,
						defaultType: 'checkbox',
						labelWidth: 1,
						items: [{
							fieldLabel: '',
							labelSeparator: '',
							boxLabel: _('Private'),
							id: 'private'
						}, {
							fieldLabel: '',
							labelSeparator: '',
							boxLabel: _('Prioritize First/Last'),
							id: 'prioritize_first_last'
						}]
					}, {
						layout: 'column',
						border: false,
						defaults: {border: false},
						items: [{
							items: [{
								id: 'edit_trackers',
								xtype: 'button',
								text: _('Edit Trackers'),
								cls: 'x-btn-text-icon',
								iconCls: 'x-deluge-edit-trackers',
								border: false,
								width: 100
							}]
						}, {
							items: [{
								id: 'apply',
								xtype: 'button',
								text: _('Apply'),
								style: 'margin-left: 10px',
								border: false,
								width: 100
							}]
						}]
					}]
				}]
			}]
		}, config);
		Ext.deluge.details.OptionsTab.superclass.constructor.call(this, config);
	},
	
	onRender: function(ct, position) {
		Ext.deluge.details.OptionsTab.superclass.onRender.call(this, ct, position);
		this.layout = new Ext.layout.ColumnLayout();
		this.layout.setContainer(this);
		this.doLayout();
	},
	
	clear: function() {
		var form = this.getForm();
		//form.findField('max_download_speed').setValue(0);
		//form.findField('max_upload_speed').setValue(0);
		//form.findField('max_connections').setValue(0);
		//form.findField('max_upload_slots').setValue(0);
		//form.findField('stop_ratio').setValue(0);
		//form.findField('is_auto_managed').setValue(false);
		//form.findField('stop_at_ratio').setValue(false);
		//form.findField('remove_at_ratio').setValue(false);
		//form.findField('private').setValue(false);
		//form.findField('prioritize_first_last').setValue(false);
	},
	
	reset: function() {
		if (this.torrentId) {
			delete this.changed[this.torrentId];
		}
	},
	
	update: function(torrentId) {
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Options, {
			success: this.onRequestComplete,
			scope: this,
			torrentId: torrentId
		});
	},
	
	onRequestComplete: function(torrent, options) {

	}
});
Deluge.Details.add(new Ext.deluge.details.OptionsTab());