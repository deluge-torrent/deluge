/**
 * Deluge.preferences.ProxyPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Proxy
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Proxy = Ext.extend(Ext.form.FormPanel, {
    constructor: function (config) {
        config = Ext.apply(
            {
                border: false,
                title: _('Proxy'),
                header: false,
                layout: 'form',
                autoScroll: true,
            },
            config
        );
        Deluge.preferences.Proxy.superclass.constructor.call(this, config);
    },

    initComponent: function () {
        Deluge.preferences.Proxy.superclass.initComponent.call(this);
        this.proxy = this.add(
            new Deluge.preferences.ProxyField({
                title: _('Proxy'),
                name: 'proxy',
            })
        );
        this.proxy.on('change', this.onProxyChange, this);
        deluge.preferences.getOptionsManager().bind('proxy', this.proxy);
    },

    getValue: function () {
        return {
            proxy: this.proxy.getValue(),
        };
    },

    setValue: function (value) {
        for (var proxy in value) {
            this[proxy].setValue(value[proxy]);
        }
    },

    onProxyChange: function (field, newValue, oldValue) {
        var newValues = this.getValue();
        var oldValues = Ext.apply({}, newValues);
        oldValues[field.getName()] = oldValue;

        this.fireEvent('change', this, newValues, oldValues);
    },
});
