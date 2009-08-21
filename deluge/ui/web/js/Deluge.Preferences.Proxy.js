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
			name: 'type',
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
		this.hostname = this.add({
			xtype: 'textfield',
			name: 'hostname',
			fieldLabel: _('Host'),
			width: 220
		});
		
		this.port = this.add({
			xtype: 'uxspinner',
			name: 'port',
			fieldLabel: _('Port'),
			width: 80,
			strategy: {
				xtype: 'number',
				decimalPrecision: 0,
				minValue: -1,
				maxValue: 99999
			}
		});
		
		this.username = this.add({
			xtype: 'textfield',
			name: 'username',
			fieldLabel: _('Username'),
			width: 220
		});
		
		this.password = this.add({
			xtype: 'textfield',
			name: 'password',
			fieldLabel: _('Password'),
			inputType: 'password',
			width: 220
		});
		
		this.type.on('change', this.onFieldChange, this);
		this.type.on('select', this.onTypeSelect, this);
		this.setting = false;
	},
	
	getName: function() {
		return this.initialConfig.name;
	},
	
	getValue: function() {
		return {
			'type': this.type.getValue(),
			'hostname': this.hostname.getValue(),
			'port': this.port.getValue(),
			'username': this.username.getValue(),
			'password': this.password.getValue()
		}
	},

	/**
	 * Set the values of the proxies
	 */
	setValue: function(value) {
		this.setting = true;
		this.type.setValue(value['type']);
		var index = this.type.getStore().find('id', value['type']);
		var record = this.type.getStore().getAt(index);
		
		this.hostname.setValue(value['hostname']);
		this.port.setValue(value['port']);
		this.username.setValue(value['username']);
		this.password.setValue(value['password']);
		this.onTypeSelect(this.type, record, index);
		this.setting = false;
	},
	
	onFieldChange: function(field, newValue, oldValue) {
		if (this.setting) return;
		var newValues = this.getValue();
		var oldValues = Ext.apply({}, newValues);
		oldValues[field.getName()] = oldValue;
		
		this.fireEvent('change', this, newValues, oldValues);
	},
	
	onTypeSelect: function(combo, record, index) {
		var typeId = record.get('id');
		if (typeId > 0) {
			this.hostname.show();
			this.port.show();
		} else {
			this.hostname.hide();
			this.port.hide();
		}
		
		if (typeId == 3 || typeId == 5) {
			this.username.show();
			this.password.show();
		} else {
			this.username.hide();
			this.password.hide();
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
		this.peer = this.add(new Ext.deluge.preferences.ProxyField({
			title: _('Peer'),
			name: 'peer'
		}));
		this.peer.on('change', this.onProxyChange, this);
		
		this.web_seed = this.add(new Ext.deluge.preferences.ProxyField({
			title: _('Web Seed'),
			name: 'web_seed'
		}));
		this.web_seed.on('change', this.onProxyChange, this);
		
		this.tracker = this.add(new Ext.deluge.preferences.ProxyField({
			title: _('Tracker'),
			name: 'tracker'
		}));
		this.tracker.on('change', this.onProxyChange, this);
		
		this.dht = this.add(new Ext.deluge.preferences.ProxyField({
			title: _('DHT'),
			name: 'dht'
		}));
		this.dht.on('change', this.onProxyChange, this);
		
		Deluge.Preferences.getOptionsManager().bind('proxies', this);
	},
	
	getValue: function() {
		return {
			'dht': this.dht.getValue(),
			'peer': this.peer.getValue(),
			'tracker': this.tracker.getValue(),
			'web_seed': this.web_seed.getValue()
		}
	},
	
	setValue: function(value) {
		for (var proxy in value) {
			this[proxy].setValue(value[proxy]);
		}
	},
	
	onProxyChange: function(field, newValue, oldValue) {
		var newValues = this.getValue();
		var oldValues = Ext.apply({}, newValues);
		oldValues[field.getName()] = oldValue;
		
		this.fireEvent('change', this, newValues, oldValues);
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Proxy());