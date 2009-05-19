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

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
*/


Ext.deluge.details.OptionsTab = Ext.extend(Ext.form.FormPanel, {

	constructor: function(config) {
		config = Ext.apply({
			autoScroll: true,
			bodyStyle: 'padding: 5px;',
			border: false,
			cls: 'x-deluge-options',
			defaults: {
				autoHeight: true,
				labelWidth: 1,
				defaultType: 'checkbox'
			},
			deferredRender: false,
			layout: 'column',
			title: _('Options')
		}, config);
		Ext.deluge.details.OptionsTab.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.details.OptionsTab.superclass.initComponent.call(this);
		
		this.fieldsets = {}, this.fields = {};
		
		/*
		 * Bandwidth Options
		 */
		this.fieldsets.bandwidth = this.add({
			xtype: 'fieldset',
			defaultType: 'uxspinner',
			bodyStyle: 'padding: 5px',
			
			layout: 'table',
			layoutConfig: {columns: 3},
			labelWidth: 150,
			
			style: 'margin-left: 10px; margin-right: 5px; padding: 5px',
			title: _('Bandwidth'),
			width: 300
		});
		
		/*
		 * Max Download Speed
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Download Speed'),
			forId: 'max_download_speed',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_download_speed = this.fieldsets.bandwidth.add({
			id: 'max_download_speed',
			name: 'max_download_speed',
			width: 100,
			value: -1,
			stragegy: new Ext.ux.form.Spinner.NumberStrategy({
				minValue: -1,
				maxValue: 99999,
				incrementValue: 1
			})
		});
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('KiB/s'),
			style: 'margin-left: 10px'
		});
		
		/*
		 * Max Upload Speed
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Upload Speed'),
			forId: 'max_upload_speed',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_upload_speed = this.fieldsets.bandwidth.add({
			id: 'max_upload_speed',
			name: 'max_upload_speed',
			width: 100,
			value: -1,
			stragegy: new Ext.ux.form.Spinner.NumberStrategy({
				minValue: -1,
				maxValue: 99999,
				incrementValue: 1
			})
		});
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('KiB/s'),
			style: 'margin-left: 10px'
		});
		
		/*
		 * Max Connections
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Connections'),
			forId: 'max_connections',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_connections = this.fieldsets.bandwidth.add({
			id: 'max_connections',
			name: 'max_connections',
			width: 100,
			value: -1,
			stragegy: new Ext.ux.form.Spinner.NumberStrategy({
				minValue: -1,
				maxValue: 99999,
				incrementValue: 1
			})
		});
		this.fieldsets.bandwidth.add({xtype: 'label'});
		
		/*
		 * Max Upload Slots
		 */
		this.fieldsets.bandwidth.add({
			xtype: 'label',
			text: _('Max Upload Slots'),
			forId: 'max_upload_slots',
			cls: 'x-deluge-options-label'
		});
		this.fields.max_upload_slots = this.fieldsets.bandwidth.add({
			id: 'max_upload_slots',
			name: 'max_upload_slots',
			width: 100,
			value: -1,
			stragegy: new Ext.ux.form.Spinner.NumberStrategy({
				minValue: -1,
				maxValue: 99999,
				incrementValue: 1
			})
		});

		/*
		 * Queue Options
		 */
		this.fieldsets.queue = this.add({
			xtype: 'fieldset',
			title: _('Queue'),
			style: 'margin-left: 5px; margin-right: 5px; padding: 5px',
			width: 200,
			defaults: {
				fieldLabel: '',
				labelSeparator: ''
			}
		});
		
		this.fields.is_auto_managed = this.fieldsets.queue.add({
			fieldLabel: '',
			labelSeparator: '',
			id: 'is_auto_managed',
			boxLabel: _('Auto Managed')
		});
		
		this.fields.stop_at_ratio = this.fieldsets.queue.add({
			fieldLabel: '',
			labelSeparator: '',
			id: 'stop_at_ratio',
			boxLabel: _('Stop seed at ratio')
		});
		
		this.fields.remove_at_ratio = this.fieldsets.queue.add({
			fieldLabel: '',
			labelSeparator: '',
			id: 'remove_at_ratio',
			style: 'margin-left: 10px',
			boxLabel: _('Remove at ratio')
		});
		
		this.fields.move_completed = this.fieldsets.queue.add({
			fieldLabel: '',
			labelSeparator: '',
			id: 'move_completed',
			boxLabel: _('Move Completed')
		});
		
		
		/*
		 * General Options
		 */
		this.rightColumn =  this.add({
			border: false,
			autoHeight: true,
			style: 'margin-left: 5px',
			width: 200
		});
		
		this.fieldsets.general = this.rightColumn.add({
			xtype: 'fieldset',
			autoHeight: true,
			defaultType: 'checkbox',
			title: _('General'),
			layout: 'form'
		});
		
		this.fields['private'] = this.fieldsets.general.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Private'),
			id: 'private'
		});
		
		this.fields.prioritize_first_last = this.fieldsets.general.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Prioritize First/Last'),
			id: 'prioritize_first_last'
		});
		
		/*
		 * Buttons
		 */
		this.buttonPanel = this.rightColumn.add({
			layout: 'column',
			xtype: 'panel',
			border: false
		});
		
		// The buttons below are required to be added to a panel
		// first as simply adding them to the column layout throws an
		// error c.getSize() does not exist. This could be intentional
		// or it may possible be a bug in ext-js. Take care when upgrading
		// to ext-js 3.0.
		
		/*
		 * Edit Trackers button
		 */
		this.buttonPanel.add({
			xtype: 'panel',
			border: false
		}).add({
			id: 'edit_trackers',
			xtype: 'button',
			text: _('Edit Trackers'),
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-edit-trackers',
			border: false,
			width: 100,
			handler: this.onEditTrackers,
			scope: this
		});
		
		/*
		 * Apply button
		 */
		this.buttonPanel.add({
			xtype: 'panel',
			border: false
		}).add({
			id: 'apply',
			xtype: 'button',
			text: _('Apply'),
			style: 'margin-left: 10px;',
			border: false,
			width: 100,
		});
	},
	
	onRender: function(ct, position) {
		Ext.deluge.details.OptionsTab.superclass.onRender.call(this, ct, position);
		
		// This is another hack I think, so keep an eye out here when upgrading.
		this.layout = new Ext.layout.ColumnLayout();
		this.layout.setContainer(this);
		this.doLayout();
	},
	
	clear: function() {
		this.fields.max_download_speed.setValue(0);
		this.fields.max_upload_speed.setValue(0);
		this.fields.max_connections.setValue(0);
		this.fields.max_upload_slots.setValue(0);
		this.fields.is_auto_managed.setValue(false);
		this.fields.stop_at_ratio.setValue(false);
		this.fields.remove_at_ratio.setValue(false);
		this.fields['private'].setValue(false);
		this.fields.prioritize_first_last.setValue(false);
	},
	
	reset: function() {
		if (this.torrentId) {
			delete this.changed[this.torrentId];
		}
	},
	
	update: function(torrentId) {
		this.torrentId = torrentId;
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Options, {
			success: this.onRequestComplete,
			scope: this
		});
	},
	
	onEditTrackers: function() {
		Deluge.EditTrackers.show();
	},
	
	onRequestComplete: function(torrent, options) {
		for (var key in torrent) {
			if (this.fields[key]) {
				this.fields[key].setValue(torrent[key])
			} else {
				//alert(key);
			}
		}
	}
});
Deluge.Details.add(new Ext.deluge.details.OptionsTab());
