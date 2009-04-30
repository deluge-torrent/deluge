Deluge.Preferences.addPage({
	border: false,
	title: _('Downloads'),
	xtype: 'form',
	layout: 'form',
	items: [{
		xtype: 'fieldset',
		border: false,
		title: _('Folders'),
		labelWidth: 140,
		defaultType: 'textfield',
		autoHeight: true,
		items: [{
			name: 'download_location',
			fieldLabel: _('Download to'),
			width: 125
		}, {
			name: 'move_completed',
			fieldLabel: _('Move completed to'),
			width: 125
		}, {
			name: 'copy_torrent_files',
			fieldLabel: _('Copy of .torrent files to'),
			width: 125
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: _('Allocation'),
		autoHeight: true,
		labelWidth: 1,
		defaultType: 'radio',
		items: [{
			name: 'compact_allocation',
			labelSeparator: '',
			boxLabel: _('Compact')
		}, {
			name: 'compact_allocation',
			labelSeparator: '',
			boxLabel: _('Full')
		}]
	}, {
		xtype: 'fieldset',
		border: false,
		title: _('Options'),
		autoHeight: true,
		labelWidth: 1,
		defaultType: 'checkbox',
		items: [{
			name: 'prioritize_first_last',
			labelSeparator: '',
			boxLabel: _('Prioritize first and last pieces of torrent')
		}, {
			name: 'add_paused',
			labelSeparator: '',
			boxLabel: _('Add torrents in Paused state')
		}]
	}]
});