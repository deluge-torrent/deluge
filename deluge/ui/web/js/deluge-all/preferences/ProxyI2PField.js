/*!
 * Deluge.preferences.ProxyI2PField.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge.preferences');

/**
 * @class Deluge.preferences.ProxyI2PField
 * @extends Ext.form.FieldSet
 */
Deluge.preferences.ProxyI2PField = Ext.extend(Ext.form.FieldSet, {

    border: false,
    autoHeight: true,
    labelWidth: 70,

    initComponent: function() {
        Deluge.preferences.ProxyI2PField.superclass.initComponent.call(this);
        this.hostname = this.add({
            xtype: 'textfield',
            name: 'hostname',
            fieldLabel: _('Host:'),
            labelSeparator: '',
            width: 220
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
            maxValue: 65535
        });
        this.port.on('change', this.onFieldChange, this);

        this.setting = false;
    },

    getName: function() {
        return this.initialConfig.name;
    },

    getValue: function() {
        return {
            'hostname': this.hostname.getValue(),
            'port': Number(this.port.getValue())
        }
    },

    // Set the values of the proxies
    setValue: function(value) {
        this.setting = true;
        this.hostname.setValue(value['hostname']);
        this.port.setValue(value['port']);
        this.setting = false;
    },

    onFieldChange: function(field, newValue, oldValue) {
        if (this.setting) return;
        var newValues = this.getValue();
        var oldValues = Ext.apply({}, newValues);
        oldValues[field.getName()] = oldValue;

        this.fireEvent('change', this, newValues, oldValues);
    }
});
