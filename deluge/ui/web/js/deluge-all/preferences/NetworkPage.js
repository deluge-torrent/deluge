/*!
 * Deluge.preferences.NetworkPage.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Network
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Network = Ext.extend(Ext.form.FormPanel, {
	
	border: false,
	layout: 'form',
	title:  _('Network'),

	initComponent: function() {
		Deluge.preferences.Network.superclass.initComponent.call(this);
		var optMan = deluge.preferences.getOptionsManager();
		
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
			height: 22,
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
			xtype: 'spinnergroup',
			name: 'listen_ports',
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
				}
			}, {
				fieldLabel: 'To',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				}
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
			height: 22,
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
			xtype: 'spinnergroup',
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
				}
			}, {
				fieldLabel: 'To',
				strategy: {
					xtype: 'number',
					decimalPrecision: 0,
					minValue: -1,
					maxValue: 99999
				}
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
	}
});
