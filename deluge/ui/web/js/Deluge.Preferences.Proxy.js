Ext.namespace('Ext.deluge.preferences');
Ext.deluge.preferences.ProxyField = Ext.extend(Ext.form.FieldSet, {

	constructor: function(config) {
		config = Ext.apply({
			border: false,
			autoHeight: true,
			labelWidth: 70
		}, config);
		Ext.deluge.preferences.ProxyField.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Ext.deluge.preferences.ProxyField.superclass.initComponent.call(this);
		this.type = this.add({
			xtype: 'combo',
			fieldLabel: _('Type'),
			mode: 'local',
			width: 150,
			store: new Ext.data.SimpleStore({
				fields: ['id', 'text'],
				data: [
					[0, _('None')],
					[1, _('Socksv4')],
					[2, _('Socksv5')],
					[3, _('Socksv5 with Auth')],
					[4, _('HTTP')],
					[5, _('HTTP with Auth')],
				]
			}),
			value: 0,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		})
		this.host = this.add({
			xtype: 'textfield',
			fieldLabel: _('Host'),
			disabled: true,
			width: 220
		});
		this.port = this.add({
			xtype: 'uxspinner',
			fieldLabel: _('Port'),
			width: 80,
			strategy: {
				xtype: 'number',
				decimalPrecision: 0,
				minValue: -1,
				maxValue: 99999
			},
			disabled: true
		});
		this.username = this.add({
			xtype: 'textfield',
			fieldLabel: _('Username'),
			disabled: true,
			width: 220
		});
		this.password = this.add({
			xtype: 'textfield',
			fieldLabel: _('Password'),
			inputType: 'password',
			disabled: true,
			width: 220
		});
		this.type.on('select', this.onTypeSelect, this);
	},
	
	onTypeSelect: function(combo, record, index) {
		var typeId = record.get('id');
		if (typeId > 0) {
			this.host.setDisabled(false);
			this.port.setDisabled(false);
		} else {
			this.host.setDisabled(true);
			this.port.setDisabled(true);
		}
		
		if (typeId == 3 || typeId == 5) {
			this.username.setDisabled(false);
			this.password.setDisabled(false);
		} else {
			this.username.setDisabled(true);
			this.password.setDisabled(true);
		}
	}
});


Ext.deluge.preferences.Proxy = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Proxy'),
			layout: 'form'
		}, config);
		Ext.deluge.preferences.Proxy.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.preferences.Proxy.superclass.initComponent.call(this);
		
		var optMan = Deluge.Preferences.getOptionsManager();
		
		this.add(new Ext.deluge.preferences.ProxyField({
			title: _('Peer')
		}));
		this.add(new Ext.deluge.preferences.ProxyField({
			title: _('Web Seed')
		}));
		this.add(new Ext.deluge.preferences.ProxyField({
			title: _('Tracker')
		}));
		this.add(new Ext.deluge.preferences.ProxyField({
			title: _('DHT')
		}));
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Proxy());