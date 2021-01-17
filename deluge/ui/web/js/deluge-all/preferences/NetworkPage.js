/**
 * Deluge.preferences.NetworkPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

// custom Vtype for vtype:'IPAddress'
Ext.apply(Ext.form.VTypes, {
    IPAddress: function (v) {
        return /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(v);
    },
    IPAddressText: 'Must be a numeric IP address',
    IPAddressMask: /[\d\.]/i,
});

/**
 * @class Deluge.preferences.Network
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Network = Ext.extend(Ext.form.FormPanel, {
    border: false,
    layout: 'form',
    title: _('Network'),
    header: false,

    initComponent: function () {
        Deluge.preferences.Network.superclass.initComponent.call(this);
        var optMan = deluge.preferences.getOptionsManager();

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Incoming Address'),
            style: 'margin-bottom: 5px; padding-bottom: 0px;',
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'textfield',
        });
        optMan.bind(
            'listen_interface',
            fieldset.add({
                name: 'listen_interface',
                fieldLabel: '',
                labelSeparator: '',
                width: 200,
                vtype: 'IPAddress',
            })
        );

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Incoming Port'),
            style: 'margin-bottom: 5px; padding-bottom: 0px;',
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        optMan.bind(
            'random_port',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('Use Random Port'),
                name: 'random_port',
                height: 22,
                listeners: {
                    check: {
                        fn: function (e, checked) {
                            this.listenPort.setDisabled(checked);
                        },
                        scope: this,
                    },
                },
            })
        );

        this.listenPort = fieldset.add({
            xtype: 'spinnerfield',
            name: 'listen_port',
            fieldLabel: '',
            labelSeparator: '',
            width: 75,
            strategy: {
                xtype: 'number',
                decimalPrecision: 0,
                minValue: 0,
                maxValue: 65535,
            },
        });
        optMan.bind('listen_ports', this.listenPort);

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Outgoing Interface'),
            style: 'margin-bottom: 5px; padding-bottom: 0px;',
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'textfield',
        });
        optMan.bind(
            'outgoing_interface',
            fieldset.add({
                name: 'outgoing_interface',
                fieldLabel: '',
                labelSeparator: '',
                width: 40,
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Outgoing Ports'),
            style: 'margin-bottom: 5px; padding-bottom: 0px;',
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        optMan.bind(
            'random_outgoing_ports',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('Use Random Ports'),
                name: 'random_outgoing_ports',
                height: 22,
                listeners: {
                    check: {
                        fn: function (e, checked) {
                            this.outgoingPorts.setDisabled(checked);
                        },
                        scope: this,
                    },
                },
            })
        );
        this.outgoingPorts = fieldset.add({
            xtype: 'spinnergroup',
            name: 'outgoing_ports',
            fieldLabel: '',
            labelSeparator: '',
            colCfg: {
                labelWidth: 40,
                style: 'margin-right: 10px;',
            },
            items: [
                {
                    fieldLabel: _('From:'),
                    labelSeparator: '',
                    strategy: {
                        xtype: 'number',
                        decimalPrecision: 0,
                        minValue: 0,
                        maxValue: 65535,
                    },
                },
                {
                    fieldLabel: _('To:'),
                    labelSeparator: '',
                    strategy: {
                        xtype: 'number',
                        decimalPrecision: 0,
                        minValue: 0,
                        maxValue: 65535,
                    },
                },
            ],
        });
        optMan.bind('outgoing_ports', this.outgoingPorts);

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Network Extras'),
            autoHeight: true,
            layout: 'table',
            layoutConfig: {
                columns: 3,
            },
            defaultType: 'checkbox',
        });
        optMan.bind(
            'upnp',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('UPnP'),
                name: 'upnp',
            })
        );
        optMan.bind(
            'natpmp',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('NAT-PMP'),
                ctCls: 'x-deluge-indent-checkbox',
                name: 'natpmp',
            })
        );
        optMan.bind(
            'utpex',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('Peer Exchange'),
                ctCls: 'x-deluge-indent-checkbox',
                name: 'utpex',
            })
        );
        optMan.bind(
            'lsd',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('LSD'),
                name: 'lsd',
            })
        );
        optMan.bind(
            'dht',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('DHT'),
                ctCls: 'x-deluge-indent-checkbox',
                name: 'dht',
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Type Of Service'),
            style: 'margin-bottom: 5px; padding-bottom: 0px;',
            bodyStyle: 'margin: 0px; padding: 0px',
            autoHeight: true,
            defaultType: 'textfield',
        });
        optMan.bind(
            'peer_tos',
            fieldset.add({
                name: 'peer_tos',
                fieldLabel: _('Peer TOS Byte:'),
                labelSeparator: '',
                width: 40,
            })
        );
    },
});
