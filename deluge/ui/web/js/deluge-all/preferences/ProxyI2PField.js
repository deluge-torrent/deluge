/*!
 * Deluge.preferences.ProxyI2PField.js
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
