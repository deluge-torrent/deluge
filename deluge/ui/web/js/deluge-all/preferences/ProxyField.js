/**
 * Deluge.preferences.ProxyField.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge.preferences');

/**
 * @class Deluge.preferences.ProxyField
 * @extends Ext.form.FieldSet
 */
Deluge.preferences.ProxyField = Ext.extend(Ext.form.FieldSet, {
    border: false,
    autoHeight: true,
    labelWidth: 70,

    initComponent: function () {
        Deluge.preferences.ProxyField.superclass.initComponent.call(this);
        this.proxyType = this.add({
            xtype: 'combo',
            fieldLabel: _('Type:'),
            labelSeparator: '',
            name: 'proxytype',
            mode: 'local',
            width: 150,
            store: new Ext.data.ArrayStore({
                fields: ['id', 'text'],
                data: [
                    [0, _('None')],
                    [1, _('Socks4')],
                    [2, _('Socks5')],
                    [3, _('Socks5 Auth')],
                    [4, _('HTTP')],
                    [5, _('HTTP Auth')],
                    [6, _('I2P')],
                ],
            }),
            editable: false,
            triggerAction: 'all',
            valueField: 'id',
            displayField: 'text',
        });
        this.proxyType.on('change', this.onFieldChange, this);
        this.proxyType.on('select', this.onTypeSelect, this);

        this.hostname = this.add({
            xtype: 'textfield',
            name: 'hostname',
            fieldLabel: _('Host:'),
            labelSeparator: '',
            width: 220,
        });
        this.hostname.on('change', this.onFieldChange, this);

        this.port = this.add({
            xtype: 'spinnerfield',
            name: 'port',
            fieldLabel: _('Port:'),
            labelSeparator: '',
            width: 80,
            decimalPrecision: 0,
            minValue: 0,
            maxValue: 65535,
        });
        this.port.on('change', this.onFieldChange, this);

        this.username = this.add({
            xtype: 'textfield',
            name: 'username',
            fieldLabel: _('Username:'),
            labelSeparator: '',
            width: 220,
        });
        this.username.on('change', this.onFieldChange, this);

        this.password = this.add({
            xtype: 'textfield',
            name: 'password',
            fieldLabel: _('Password:'),
            labelSeparator: '',
            inputType: 'password',
            width: 220,
        });
        this.password.on('change', this.onFieldChange, this);

        this.proxy_host_resolve = this.add({
            xtype: 'checkbox',
            name: 'proxy_host_resolve',
            fieldLabel: '',
            boxLabel: _('Proxy Hostnames'),
            width: 220,
        });
        this.proxy_host_resolve.on('change', this.onFieldChange, this);

        this.proxy_peer_conn = this.add({
            xtype: 'checkbox',
            name: 'proxy_peer_conn',
            fieldLabel: '',
            boxLabel: _('Proxy Peers'),
            width: 220,
        });
        this.proxy_peer_conn.on('change', this.onFieldChange, this);

        this.proxy_tracker_conn = this.add({
            xtype: 'checkbox',
            name: 'proxy_tracker_conn',
            fieldLabel: '',
            boxLabel: _('Proxy Trackers'),
            width: 220,
        });
        this.proxy_tracker_conn.on('change', this.onFieldChange, this);

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Force Proxy'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
            style: 'padding-left: 0px; margin-top: 10px',
        });

        this.force_proxy = fieldset.add({
            fieldLabel: '',
            labelSeparator: '',
            height: 20,
            name: 'force_proxy',
            boxLabel: _('Force Use of Proxy'),
        });
        this.force_proxy.on('change', this.onFieldChange, this);

        this.anonymous_mode = fieldset.add({
            fieldLabel: '',
            labelSeparator: '',
            height: 20,
            name: 'anonymous_mode',
            boxLabel: _('Hide Client Identity'),
        });
        this.anonymous_mode.on('change', this.onFieldChange, this);

        this.setting = false;
    },

    getName: function () {
        return this.initialConfig.name;
    },

    getValue: function () {
        return {
            type: this.proxyType.getValue(),
            hostname: this.hostname.getValue(),
            port: Number(this.port.getValue()),
            username: this.username.getValue(),
            password: this.password.getValue(),
            proxy_hostnames: this.proxy_host_resolve.getValue(),
            proxy_peer_connections: this.proxy_peer_conn.getValue(),
            proxy_tracker_connections: this.proxy_tracker_conn.getValue(),
            force_proxy: this.force_proxy.getValue(),
            anonymous_mode: this.anonymous_mode.getValue(),
        };
    },

    // Set the values of the proxies
    setValue: function (value) {
        this.setting = true;
        this.proxyType.setValue(value['type']);
        var index = this.proxyType.getStore().find('id', value['type']);
        var record = this.proxyType.getStore().getAt(index);

        this.hostname.setValue(value['hostname']);
        this.port.setValue(value['port']);
        this.username.setValue(value['username']);
        this.password.setValue(value['password']);
        this.proxy_host_resolve.setValue(value['proxy_hostnames']);
        this.proxy_peer_conn.setValue(value['proxy_peer_connections']);
        this.proxy_tracker_conn.setValue(value['proxy_tracker_connections']);
        this.force_proxy.setValue(value['force_proxy']);
        this.anonymous_mode.setValue(value['anonymous_mode']);

        this.onTypeSelect(this.type, record, index);
        this.setting = false;
    },

    onFieldChange: function (field, newValue, oldValue) {
        if (this.setting) return;
        var newValues = this.getValue();
        var oldValues = Ext.apply({}, newValues);
        oldValues[field.getName()] = oldValue;

        this.fireEvent('change', this, newValues, oldValues);
    },

    onTypeSelect: function (combo, record, index) {
        var typeId = record.get('id');
        if (typeId > 0) {
            this.hostname.show();
            this.port.show();
            this.proxy_peer_conn.show();
            this.proxy_tracker_conn.show();
            if (typeId > 1 && typeId < 6) {
                this.proxy_host_resolve.show();
            } else {
                this.proxy_host_resolve.hide();
            }
        } else {
            this.hostname.hide();
            this.port.hide();
            this.proxy_host_resolve.hide();
            this.proxy_peer_conn.hide();
            this.proxy_tracker_conn.hide();
        }

        if (typeId == 3 || typeId == 5) {
            this.username.show();
            this.password.show();
        } else {
            this.username.hide();
            this.password.hide();
        }
    },
});
