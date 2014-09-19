/*!
 * Deluge.preferences.ProxyPage.js
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
 * @class Deluge.preferences.Proxy
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Proxy = Ext.extend(Ext.form.FormPanel, {
    constructor: function(config) {
        config = Ext.apply({
            border: false,
            title: _('Proxy'),
            layout: 'form',
            autoScroll: true
        }, config);
        Deluge.preferences.Proxy.superclass.constructor.call(this, config);
    },

    initComponent: function() {
        Deluge.preferences.Proxy.superclass.initComponent.call(this);
        this.proxy = this.add(new Deluge.preferences.ProxyField({
            title: _('Proxy'),
            name: 'proxy'
        }));
        this.proxy.on('change', this.onProxyChange, this);
        deluge.preferences.getOptionsManager().bind('proxy', this.proxy);

        this.i2p_proxy = this.add(new Deluge.preferences.ProxyI2PField({
            title: _('I2P Proxy'),
            name: 'i2p_proxy'
        }));
        deluge.preferences.getOptionsManager().bind('i2p_proxy', this.i2p_proxy);

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Anonymous Mode'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox'
        });
        deluge.preferences.getOptionsManager().bind('anonymous_mode', fieldset.add({
            fieldLabel: '',
            labelSeparator: '',
            height: 20,
            name: 'anonymous_mode',
            boxLabel: _('Hide Client Identity')
        }));

    },

    getValue: function() {
        return {
            'proxy': this.proxy.getValue(),
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
