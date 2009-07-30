Ext.namespace('Ext.deluge.preferences');
Ext.deluge.preferences.Daemon = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Daemon'),
			layout: 'form'
		}, config);
		Ext.deluge.preferences.Daemon.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.preferences.Daemon.superclass.initComponent.call(this);

		var optMan = Deluge.Preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Port'),
			autoHeight: true,
			defaultType: 'uxspinner'
		});
		optMan.bind('daemon_port', fieldset.add({
			fieldLabel: _('Daemon port'),
			name: 'daemon_port'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Connections'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('allow_remote', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Allow Remote Connections'),
			name: 'allow_remote'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Other'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('new_release_check', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			height: 40,
			boxLabel: _('Periodically check the website for new releases'),
			id: 'new_release_check'
		}));
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Daemon());