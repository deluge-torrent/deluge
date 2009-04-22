/*
Script: deluge-details.js
    Contains all objects and functions related to the lower details panel and
	it's containing tabs.

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

(function() {
	Ext.namespace('Ext.deluge.details');
	Ext.deluge.details.TabPanel = Ext.extend(Ext.TabPanel, {
		
		constructor: function(config) {
			config = Ext.apply({
				region: 'south',
				split: true,
				height: 220,
				minSize: 100,
				collapsible: true,
				margins: '0 5 5 5',
				activeTab: 0
			}, config);
			Ext.deluge.details.TabPanel.superclass.constructor.call(this, config);
		},
		
		clear: function() {
			this.items.each(function(panel) {
				if (panel.clear) panel.clear();
			});
		},
		
		update: function(tab) {
			var torrent = Deluge.Torrents.getSelected();
			if (!torrent) return;
			
			tab = tab || this.getActiveTab();
			if (tab.update) tab.update(torrent.id);
		},
		
		/* Event Handlers */
		
		// We need to add the events in onRender since Deluge.Torrents hasn't
		// been created yet.
		onRender: function(ct, position) {
			Ext.deluge.details.TabPanel.superclass.onRender.call(this, ct, position);
			Deluge.Events.on('disconnect', this.clear, this);
			Deluge.Torrents.on('rowclick', this.onTorrentsClick, this);
			this.on('tabchange', this.onTabChange, this);
			
			Deluge.Torrents.getSelectionModel().on('selectionchange', function(selModel) {
				if (!selModel.hasSelection()) this.clear();
			}, this);
		},
		
		onTabChange: function(panel, tab) {
			this.update(tab);
		},
		
		onTorrentsClick: function(grid, rowIndex, e) {
			this.update();
		}
	});
	Deluge.Details = new Ext.deluge.details.TabPanel();
})();

/*
Deluge.Details.Options = {
	onRender: function(panel) {
		panel.layout = new Ext.layout.FormLayout();
		panel.layout.setContainer(panel);
		panel.doLayout();
		this.form = panel.getForm();
	},
	
	onRequestComplete: function(torrent) {
		
	},
	
	clear: function() {
		this.form.findField('max_download_speed').setValue(0);
		this.form.findField('max_upload_speed').setValue(0);
		this.form.findField('max_connections').setValue(0);
		this.form.findField('max_upload_slots').setValue(0);
		this.form.findField('stop_ratio').setValue(0);
		this.form.findField('is_auto_managed').setValue(false);
		this.form.findField('stop_at_ratio').setValue(false);
		this.form.findField('remove_at_ratio').setValue(false);
		this.form.findField('private').setValue(false);
		this.form.findField('prioritize_first_last').setValue(false);
	},
	
	update: function(torrentId) {
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Options, {
			onSuccess: this.onRequestComplete.bindWithEvent(this, torrentId)
		});
	},
	
	reset: function() {
		if (this.torrentId) {
			delete this.changed[this.torrentId];
		}
	}
}

Deluge.Details.Panel = new Ext.TabPanel({
	,
	items: [new Ext.form.FormPanel({
		id: 'options',
		title: _('Options'),
		frame: true,
		autoScroll:true,
		deferredRender:false,
		
		items: [{
			layout: 'column',
			defaults: {
				//columnWidth: '.33',
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
					items: [{
						items: [{
							id: 'edit_trackers',
							xtype: 'button',
							text: _('Edit Trackers'),
							cls: 'x-btn-text-icon',
							iconCls: 'x-deluge-edit-trackers',
							width: 100
						}]
					}, {
						items: [{
							id: 'apply',
							xtype: 'button',
							text: _('Apply'),
							style: 'margin-left: 10px',
							width: 100
						}]
					}]
				}]
			}]
		}],
		listeners: {
			'render': {
				fn: Deluge.Details.Options.onRender,
				scope: Deluge.Details.Options
			}
		}
	})],
	listeners: {
		'render': {fn: Deluge.Details.onRender, scope: Deluge.Details},
		'tabchange': {fn: Deluge.Details.onTabChange, scope: Deluge.Details}
	}
});*/