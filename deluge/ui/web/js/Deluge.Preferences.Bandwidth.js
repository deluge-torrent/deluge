Deluge.Preferences.addPage({
	border: false,
	title: _('Bandwidth'),
	xtype: 'form',
	layout: 'form',
	labelWidth: 10,
	items: [{
		xtype: 'fieldset',
		border: false,
		title: _('Global Bandwidth Usage'),
		autoHeight: true,
		labelWidth: 200,
		style: 'margin-bottom: 0px; padding-bottom: 0px;',
		defaultType: 'uxspinner',
		items: [{
			name: 'max_connections',
			fieldLabel: _('Maximum Connections'),
			width: 60,
			value: -1
		}, {
			name: 'max_upload_slots',
			fieldLabel: _('Maximum Upload Slots'),
			width: 60,
			value: -1
		}, {
			name: 'max_download_speed',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 60,
			value: -1
		}, {
			name: 'max_upload_speed',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 60,
			value: -1
		}, {
			name: 'max_half_open_connections',
			fieldLabel: _('Maximum Half-Open Connections'),
			width: 60,
			value: -1
		}, {
			name: 'max_connections_per_second',
			fieldLabel: _('Maximum Connection Attempts per Second'),
			width: 60,
			value: -1
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: '',
		autoHeight: true,
		style: 'padding-top: 0px; margin-top: 0px; margin-bottom: 0px;',
		items: [{
			xtype: 'checkbox',
			name: 'ignore_local',
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Ignore limits on local network'),
			value: -1
		}, {
			xtype: 'checkbox',
			name: 'limit_ip_overhead',
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Rate limit IP overhead'),
			value: -1
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: _('Per Torrent Bandwidth Usage'),
		autoHeight: true,
		labelWidth: 200,
		defaultType: 'uxspinner',
		items: [{
			name: 'max_connections_per_torrent',
			fieldLabel: _('Maximum Connections'),
			width: 60,
			value: -1
		}, {
			name: 'max_upload_slots_per_torrent',
			fieldLabel: _('Maximum Upload Slots'),
			width: 60,
			value: -1
		}, {
			name: 'max_download_speed_per_torrent',
			fieldLabel: _('Maximum Download Speed (KiB/s)'),
			width: 60,
			value: -1
		}, {
			name: 'max_upload_speed_per_torrent',
			fieldLabel: _('Maximum Upload Speed (KiB/s)'),
			width: 60,
			value: -1
		}]
	}]
});