(function() {
	DownloadPanel = Ext.extend(Ext.FormPanel, {
		constructor: function(config) {
			config = Ext.apply({
				border: false,
				title: _('Downloads'),
				layout: 'form'
			}, config);
			DownloadPanel.superclass.constructor.call(this, config);
		},
		
		initComponent: function() {
			DownloadPanel.superclass.initComponent.call(this);
			
			this.fieldsets = {}
			this.fields = {};
			
			var optMan = Deluge.Preferences.getOptionsManager();			
			optMan.addOptions({
				'download_location': ''
			});
			
			var fieldset = this.add({
				xtype: 'fieldset',
				border: false,
				title: _('Folders'),
				labelWidth: 140,
				defaultType: 'textfield',
				defaults: {
					enableKeyEvents: true
				},
				autoHeight: true
			});
			optMan.bind('download_location', fieldset.add({
				name: 'download_location',
				fieldLabel: _('Download to'),
				width: 125
			}));
			optMan.bind('move_completed_path', fieldset.add({
				name: 'move_completed_path',
				fieldLabel: _('Move completed to'),
				width: 125
			}));
			optMan.bind('torrentfiles_location', fieldset.add({
				name: 'torrentfiles_location',
				fieldLabel: _('Copy of .torrent files to'),
				width: 125
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
					{boxLabel: _('Compact') + '&nbsp;', value: 'true'},
					{boxLabel: _('Full'), value: 'false'}
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
		},
		
		onShow: function() {
			DownloadPanel.superclass.onShow.call(this);
		}
	});
	Deluge.Preferences.addPage(new DownloadPanel());
})();