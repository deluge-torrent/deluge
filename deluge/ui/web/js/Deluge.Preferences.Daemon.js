Deluge.Preferences.addPage({
	border: false,
	title: _('Daemon'),
	xtype: 'form',
	layout: 'form',
	items: [{
		xtype: 'fieldset',
		border: false,
		title: _('Port'),
		autoHeight: true,
		defaultType: 'uxspinner',
		items: [{
			fieldLabel: _('Daemon port'),
			id: 'daemon_port'
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: _('Connections'),
		autoHeight: true,
		labelWidth: 1,
		defaultType: 'checkbox',
		items: [{
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Allow Remote Connections'),
			id: 'allow_remote'
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: _('Other'),
		autoHeight: true,
		labelWidth: 1,
		defaultType: 'checkbox',
		items: [{
			fieldLabel: '',
			labelSeparator: '',
			height: 40,
			boxLabel: _('Periodically check the website for new releases'),
			id: 'new_releases'
		}]
	}]
});