Ext.namespace('Ext.deluge.preferences');
Ext.deluge.preferences.Other = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Other'),
			layout: 'form'
		}, config);
		Ext.deluge.preferences.Other.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.preferences.Other.superclass.initComponent.call(this);
		
		var optMan = Deluge.Preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Updates'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('new_release_check', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			name: 'new_release_check',
			boxLabel: _('Be alerted about new releases')
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('System Information'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		fieldset.add({
			xtype: 'panel',
			border: false,
			bodyCfg: {
				html: _('Help us improve Deluge by sending us your '
				    + 'Python version, PyGTK version, OS and processor '
				    + 'types. Absolutely no other information is sent.')
			}
		});
		optMan.bind('send_info', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Yes, please send anonymous statistics'),
			name: 'send_info'
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('GeoIP Database'),
			autoHeight: true,
			labelWidth: 80,
			defaultType: 'textfield'
		});
		optMan.bind('geoip_db_location', fieldset.add({
			name: 'geoip_db_location',
			fieldLabel: _('Location'),
			width: 200
		}));
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Other());