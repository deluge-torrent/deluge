Ext.namespace('Ext.deluge.preferences');
//Ext.

Ext.deluge.preferences.Network = Ext.extend(Ext.form.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Network'),
			layout: 'form'
		}, config);
		Ext.deluge.preferences.Network.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.preferences.Network.superclass.initComponent.call(this);
		var optMan = Deluge.Preferences.getOptionsManager();
		
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Incoming Ports'),
			style: 'margin-bottom: 0px; padding-bottom: 0px;',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('random_port', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Use Random Ports'),
			name: 'random_port',
			listeners: {
				'check': {
					fn: function(e, checked) {
						this.listenPorts.setDisabled(checked);
					},
					scope: this
				}
			}
		}));
		this.listenPorts = fieldset.add({
			xtype: 'uxspinnergroup',
			name: 'listen_ports',
			fieldLabel: '',
			labelSeparator: '',
			colCfg: {
				labelWidth: 40,
				style: 'margin-right: 10px;'
			},
			items: [{
				fieldLabel: 'From',
				width: 80,
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				},
			}, {
				fieldLabel: 'To',
				width: 80,
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				},
			}]
		});
		optMan.bind('listen_ports', this.listenPorts);
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Outgoing Ports'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox'
		});
		optMan.bind('random_outgoing_ports', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Use Random Ports'),
			name: 'random_outgoing_ports',
			listeners: {
				'check': {
					fn: function(e, checked) {
						this.outgoingPorts.setDisabled(checked);
					},
					scope: this
				}
			}
		}));
		this.outgoingPorts = fieldset.add({
			xtype: 'uxspinnergroup',
			name: 'outgoing_ports',
			fieldLabel: '',
			labelSeparator: '',
			colCfg: {
				labelWidth: 40,
				style: 'margin-right: 10px;'
			},
			items: [{
				fieldLabel: 'From',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				},
			}, {
				fieldLabel: 'To',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				},
			}]
		});
		optMan.bind('outgoing_ports', this.outgoingPorts);
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Network());