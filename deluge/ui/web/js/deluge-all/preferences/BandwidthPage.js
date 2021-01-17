/**
 * Deluge.preferences.BandwidthPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Bandwidth
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Bandwidth = Ext.extend(Ext.form.FormPanel, {
    constructor: function (config) {
        config = Ext.apply(
            {
                border: false,
                title: _('Bandwidth'),
                header: false,
                layout: 'form',
                labelWidth: 10,
            },
            config
        );
        Deluge.preferences.Bandwidth.superclass.constructor.call(this, config);
    },

    initComponent: function () {
        Deluge.preferences.Bandwidth.superclass.initComponent.call(this);

        var om = deluge.preferences.getOptionsManager();
        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Global Bandwidth Usage'),
            labelWidth: 200,
            defaultType: 'spinnerfield',
            defaults: {
                minValue: -1,
                maxValue: 99999,
            },
            style: 'margin-bottom: 0px; padding-bottom: 0px;',
            autoHeight: true,
        });
        om.bind(
            'max_connections_global',
            fieldset.add({
                name: 'max_connections_global',
                fieldLabel: _('Maximum Connections:'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );
        om.bind(
            'max_upload_slots_global',
            fieldset.add({
                name: 'max_upload_slots_global',
                fieldLabel: _('Maximum Upload Slots'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );
        om.bind(
            'max_download_speed',
            fieldset.add({
                name: 'max_download_speed',
                fieldLabel: _('Maximum Download Speed (KiB/s):'),
                labelSeparator: '',
                width: 80,
                value: -1.0,
                decimalPrecision: 1,
            })
        );
        om.bind(
            'max_upload_speed',
            fieldset.add({
                name: 'max_upload_speed',
                fieldLabel: _('Maximum Upload Speed (KiB/s):'),
                labelSeparator: '',
                width: 80,
                value: -1.0,
                decimalPrecision: 1,
            })
        );
        om.bind(
            'max_half_open_connections',
            fieldset.add({
                name: 'max_half_open_connections',
                fieldLabel: _('Maximum Half-Open Connections:'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );
        om.bind(
            'max_connections_per_second',
            fieldset.add({
                name: 'max_connections_per_second',
                fieldLabel: _('Maximum Connection Attempts per Second:'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: '',
            defaultType: 'checkbox',
            style:
                'padding-top: 0px; padding-bottom: 5px; margin-top: 0px; margin-bottom: 0px;',
            autoHeight: true,
        });
        om.bind(
            'ignore_limits_on_local_network',
            fieldset.add({
                name: 'ignore_limits_on_local_network',
                height: 22,
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('Ignore limits on local network'),
            })
        );
        om.bind(
            'rate_limit_ip_overhead',
            fieldset.add({
                name: 'rate_limit_ip_overhead',
                height: 22,
                fieldLabel: '',
                labelSeparator: '',
                boxLabel: _('Rate limit IP overhead'),
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Per Torrent Bandwidth Usage'),
            style: 'margin-bottom: 0px; padding-bottom: 0px;',
            defaultType: 'spinnerfield',
            labelWidth: 200,
            defaults: {
                minValue: -1,
                maxValue: 99999,
            },
            autoHeight: true,
        });
        om.bind(
            'max_connections_per_torrent',
            fieldset.add({
                name: 'max_connections_per_torrent',
                fieldLabel: _('Maximum Connections:'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );
        om.bind(
            'max_upload_slots_per_torrent',
            fieldset.add({
                name: 'max_upload_slots_per_torrent',
                fieldLabel: _('Maximum Upload Slots:'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );
        om.bind(
            'max_download_speed_per_torrent',
            fieldset.add({
                name: 'max_download_speed_per_torrent',
                fieldLabel: _('Maximum Download Speed (KiB/s):'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );
        om.bind(
            'max_upload_speed_per_torrent',
            fieldset.add({
                name: 'max_upload_speed_per_torrent',
                fieldLabel: _('Maximum Upload Speed (KiB/s):'),
                labelSeparator: '',
                width: 80,
                value: -1,
                decimalPrecision: 0,
            })
        );
    },
});
