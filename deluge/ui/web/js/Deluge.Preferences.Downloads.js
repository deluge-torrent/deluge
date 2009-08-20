Ext.namespace('Ext.deluge.preferences');
Ext.deluge.preferences.Downloads = Ext.extend(Ext.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Downloads'),
			layout: 'form',
			autoHeight: true
		}, config);
		Ext.deluge.preferences.Downloads.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.preferences.Downloads.superclass.initComponent.call(this);
		
		var optMan = Deluge.Preferences.getOptionsManager();
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Folders'),
			labelWidth: 150,
			defaultType: 'textfield',
			autoHeight: true
		});
		optMan.bind('download_location', fieldset.add({
			name: 'download_location',
			fieldLabel: _('Download to'),
			width: 140
		}));
		optMan.bind('move_completed_path', fieldset.add({
			name: 'move_completed_path',
			fieldLabel: _('Move completed to'),
			width: 140,
			disabled: true
		}));
		optMan.bind('torrentfiles_location', fieldset.add({
			name: 'torrentfiles_location',
			fieldLabel: _('Copy of .torrent files to'),
			width: 140,
			disabled: true
		}));
		optMan.bind('autoadd_location', fieldset.add({
			name: 'autoadd_location',
			fieldLabel: _('Autoadd .torrent files from'),
			width: 140,
			disabled: true
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Allocation'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'radiogroup'
		});
		optMan.bind('compact_allocation', fieldset.add({
			name: 'compact_allocation',
			labelSeparator: '',
			items: [
				{boxLabel: _('Compact') + '&nbsp;', inputValue: true},
				{boxLabel: _('Full'), inputValue: false}
			]
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Options'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('prioritize_first_last_pieces', fieldset.add({
			name: 'prioritize_first_last_pieces',
			labelSeparator: '',
			boxLabel: _('Prioritize first and last pieces of torrent')
		}));
		optMan.bind('add_paused', fieldset.add({
			name: 'add_paused',
			labelSeparator: '',
			boxLabel: _('Add torrents in Paused state')
		}));
		
		this.on('show', this.onShow, this);
	},
	
	onShow: function() {
		Ext.deluge.preferences.Downloads.superclass.onShow.call(this);
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Downloads());