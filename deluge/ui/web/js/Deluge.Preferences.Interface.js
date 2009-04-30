Deluge.Preferences.addPage({
	border: false,
	title: _('Interface'),
	xtype: 'form',
	layout: 'form',
	items: [{
		xtype: 'fieldset',
		border: false,
		title: _('Window'),
		autoHeight: true,
		labelWidth: 1,
		items: [{
			xtype: 'checkbox',
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Show session speed in titlebar'),
			id: 'show_session_speed'
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: _('Sidebar'),
		autoHeight: true,
		labelWidth: 1,
		items: [{
			xtype: 'checkbox',
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Hide filters with zero torrents'),
			id: 'hide_sidebar_zero'
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: _('Password'),
		autoHeight: true,
		defaultType: 'textfield',
		items: [{
			fieldLabel: 'New Password',
			inputType: 'password',
			id: 'new_password'
		}, {
			inputType: 'password',
			fieldLabel: 'Confirm Password',
			id: 'confirm_password'
		}]
	}]
});