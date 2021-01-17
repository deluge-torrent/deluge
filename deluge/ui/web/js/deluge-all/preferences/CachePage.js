/**
 * Deluge.preferences.CachePage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Cache
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Cache = Ext.extend(Ext.form.FormPanel, {
    border: false,
    title: _('Cache'),
    header: false,
    layout: 'form',

    initComponent: function () {
        Deluge.preferences.Cache.superclass.initComponent.call(this);

        var om = deluge.preferences.getOptionsManager();

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Settings'),
            autoHeight: true,
            labelWidth: 180,
            defaultType: 'spinnerfield',
            defaults: {
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 999999,
            },
        });
        om.bind(
            'cache_size',
            fieldset.add({
                fieldLabel: _('Cache Size (16 KiB Blocks):'),
                labelSeparator: '',
                name: 'cache_size',
                width: 60,
                value: 512,
            })
        );
        om.bind(
            'cache_expiry',
            fieldset.add({
                fieldLabel: _('Cache Expiry (seconds):'),
                labelSeparator: '',
                name: 'cache_expiry',
                width: 60,
                value: 60,
            })
        );
    },
});
