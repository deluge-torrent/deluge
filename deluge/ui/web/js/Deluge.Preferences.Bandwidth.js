Ext.namespace('Ext.deluge.preferences');
Ext.deluge.preferences.Bandwidth = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Bandwidth'),
			layout: 'form',
			labelWidth: 10
		}, config);
		Ext.deluge.preferences.Bandwidth.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.preferences.Bandwidth.superclass.initComponent.call(this);
		
		var optMan = Deluge.Preferences.getOptionsManager();
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Global Bandwidth Usage'),
			labelWidth: 200,
			defaultType: 'uxspinner',
			style: 'margin-bottom: 0px; padding-bottom: 0px;',
			autoHeight: true
		});
		optMan.bind('max_connections', fieldset.add({
			name: 'max_connections',
			fieldLabel: _('Maximum Connections'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_upload_slots', fieldset.add({
			name: 'max_upload_slots',
			fieldLabel: _('Maximum Upload Slots'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_download_speed', fieldset.add({
			name: 'max_download_speed',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_upload_speed', fieldset.add({
			name: 'max_upload_speed',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_half_open_connections', fieldset.add({
			name: 'max_half_open_connections',
			fieldLabel: _('Maximum Half-Open Connections'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_connections_per_second', fieldset.add({
			name: 'max_half_open_connections',
			fieldLabel: _('Maximum Connection Attempts per Second'),
			width: 60,
			value: -1
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: '',
			defaultType: 'checkbox',
			style: 'padding-top: 0px; margin-top: 0px; margin-bottom: 0px;',
			autoHeight: true
		});
		optMan.bind('ignore_local', fieldset.add({
			name: 'ignore_local',
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Ignore limits on local network'),
		}));
		optMan.bind('limit_ip_overhead', fieldset.add({
			name: 'limit_ip_overhead',
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Rate limit IP overhead'),
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Per Torrent Bandwidth Usage'),
			defaultType: 'uxspinner',
			labelWidth: 200,
			autoHeight: true
		});
		optMan.bind('max_connections_per_torrent', fieldset.add({
			name: 'max_connections_per_torrent',
			fieldLabel: _('Maximum Connections'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_upload_slots_per_torrent', fieldset.add({
			name: 'max_upload_slots_per_torrent',
			fieldLabel: _('Maximum Upload Slots'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_download_speed_per_torrent', fieldset.add({
			name: 'max_download_speed_per_torrent',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 60,
			value: -1
		}));
		optMan.bind('max_upload_speed_per_torrent', fieldset.add({
			name: 'max_upload_speed_per_torrent',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 60,
			value: -1
		}));
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Bandwidth());