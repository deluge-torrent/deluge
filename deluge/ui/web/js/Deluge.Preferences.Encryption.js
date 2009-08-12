Ext.namespace('Ext.deluge.preferences');
Ext.deluge.preferences.Encryption = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Encryption'),
			layout: 'form'
		}, config);
		Ext.deluge.preferences.Encryption.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.preferences.Encryption.superclass.initComponent.call(this);

		var optMan = Deluge.Preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Settings'),
			autoHeight: true,
			defaultType: 'combo'
		});
		optMan.bind('enc_in_policy', fieldset.add({
			fieldLabel: _('Inbound'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Forced')],
					[1, _('Enabled')],
					[2, _('Disabled')]
				]
			}),
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_out_policy', fieldset.add({
			fieldLabel: _('Outbound'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Forced')],
					[1, _('Enabled')],
					[2, _('Disabled')]
				]
			}),
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_level', fieldset.add({
			fieldLabel: _('Level'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Handshake')],
					[1, _('Full Stream')],
					[2, _('Either')]
				]
			}),
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		}));
		optMan.bind('enc_prefer_rc4', fieldset.add({
			xtype: 'checkbox',
			name: 'enc_prefer_rc4',
			height: 40,
			hideLabel: true,
			boxLabel: _('Encrypt entire stream')
		}));
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Encryption());