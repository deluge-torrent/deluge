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
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
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
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
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
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Network Interface'),
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'textfield'
		});
		optMan.bind('listen_interface', fieldset.add({
			name: 'listen_interface',
			fieldLabel: '',
			labelSeparator: '',
			width: 200
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('TOS'),
			style: 'margin-bottom: 5px; padding-bottom: 0px;',
			bodyStyle: 'margin: 0px; padding: 0px',
			autoHeight: true,
			defaultType: 'textfield'
		});
		optMan.bind('peer_tos', fieldset.add({
			name: 'peer_tos',
			fieldLabel: _('Peer TOS Byte'),
			width: 80
		}));
		
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Network Extras'),
			autoHeight: true,
			layout: 'table',
			layoutConfig: {
				columns: 3
			},			
			defaultType: 'checkbox'
		});
		optMan.bind('upnp', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('UPnP'),
			name: 'upnp'
		}));
		optMan.bind('natpmp', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('NAT-PMP'),
			ctCls: 'x-deluge-indent-checkbox',
			name: 'natpmp'
		}));
		optMan.bind('utpex', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('Peer Exchange'),
			ctCls: 'x-deluge-indent-checkbox',
			name: 'utpex'
		}));
		optMan.bind('lsd', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('LSD'),
			name: 'lsd'
		}));
		optMan.bind('dht', fieldset.add({
			fieldLabel: '',
			labelSeparator: '',
			boxLabel: _('DHT'),
			ctCls: 'x-deluge-indent-checkbox',
			name: 'dht'
		}));
		
		/*fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Encryption'),
			autoHeight: true,
			layout: 'column',	
			defaultType: 'panel',
			defaults: {
				border: false,
				layout: 'form',
				defaultType: 'combo'
			}
		});
		
		var column = fieldset.add({
			
		});
		optMan.bind('enc_in_policy', column.add({
			fieldLabel: _('Inbound'),
			mode: 'local',
			store: [
				[0, _('Forced')],
				[1, _('Enabled')],
				[2, _('Disabled')]
			],
			//new Ext.data.SimpleStore({
			//	fields: ['id', 'text'],
			//	data: 
			//}),
			width: 100,
			//forceSelection: true,
			//valueField: 'id',
			//displayField: 'text'
		}));*/
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Network());