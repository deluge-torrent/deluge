/**
 * Deluge.preferences.QueuePage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Queue
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Queue = Ext.extend(Ext.form.FormPanel, {
    border: false,
    title: _('Queue'),
    header: false,
    layout: 'form',

    initComponent: function () {
        Deluge.preferences.Queue.superclass.initComponent.call(this);

        var om = deluge.preferences.getOptionsManager();

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('New Torrents'),
            style: 'padding-top: 5px; margin-bottom: 0px;',
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        om.bind(
            'queue_new_to_top',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                height: 22,
                boxLabel: _('Queue to top'),
                name: 'queue_new_to_top',
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Active Torrents'),
            autoHeight: true,
            labelWidth: 150,
            defaultType: 'spinnerfield',
            style: 'padding-top: 5px; margin-bottom: 0px',
        });
        om.bind(
            'max_active_limit',
            fieldset.add({
                fieldLabel: _('Total:'),
                labelSeparator: '',
                name: 'max_active_limit',
                value: 8,
                width: 80,
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            })
        );
        om.bind(
            'max_active_downloading',
            fieldset.add({
                fieldLabel: _('Downloading:'),
                labelSeparator: '',
                name: 'max_active_downloading',
                value: 3,
                width: 80,
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            })
        );
        om.bind(
            'max_active_seeding',
            fieldset.add({
                fieldLabel: _('Seeding:'),
                labelSeparator: '',
                name: 'max_active_seeding',
                value: 5,
                width: 80,
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            })
        );
        om.bind(
            'dont_count_slow_torrents',
            fieldset.add({
                xtype: 'checkbox',
                name: 'dont_count_slow_torrents',
                height: 22,
                hideLabel: true,
                boxLabel: _('Ignore slow torrents'),
            })
        );
        om.bind(
            'auto_manage_prefer_seeds',
            fieldset.add({
                xtype: 'checkbox',
                name: 'auto_manage_prefer_seeds',
                hideLabel: true,
                boxLabel: _('Prefer seeding torrents'),
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Seeding Rotation'),
            autoHeight: true,
            labelWidth: 150,
            defaultType: 'spinnerfield',
            style: 'padding-top: 5px; margin-bottom: 0px',
        });
        om.bind(
            'share_ratio_limit',
            fieldset.add({
                fieldLabel: _('Share Ratio:'),
                labelSeparator: '',
                name: 'share_ratio_limit',
                value: 8,
                width: 80,
                incrementValue: 0.1,
                minValue: -1,
                maxValue: 99999,
                alternateIncrementValue: 1,
                decimalPrecision: 2,
            })
        );
        om.bind(
            'seed_time_ratio_limit',
            fieldset.add({
                fieldLabel: _('Time Ratio:'),
                labelSeparator: '',
                name: 'seed_time_ratio_limit',
                value: 3,
                width: 80,
                incrementValue: 0.1,
                minValue: -1,
                maxValue: 99999,
                alternateIncrementValue: 1,
                decimalPrecision: 2,
            })
        );
        om.bind(
            'seed_time_limit',
            fieldset.add({
                fieldLabel: _('Time (m):'),
                labelSeparator: '',
                name: 'seed_time_limit',
                value: 5,
                width: 80,
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            autoHeight: true,
            style: 'padding-top: 5px; margin-bottom: 0px',
            title: _('Share Ratio Reached'),

            layout: 'table',
            layoutConfig: { columns: 2 },
            labelWidth: 0,
            defaultType: 'checkbox',

            defaults: {
                fieldLabel: '',
                labelSeparator: '',
            },
        });
        this.stopAtRatio = fieldset.add({
            name: 'stop_seed_at_ratio',
            boxLabel: _('Share Ratio:'),
        });
        this.stopAtRatio.on('check', this.onStopRatioCheck, this);
        om.bind('stop_seed_at_ratio', this.stopAtRatio);

        this.stopRatio = fieldset.add({
            xtype: 'spinnerfield',
            name: 'stop_seed_ratio',
            ctCls: 'x-deluge-indent-checkbox',
            disabled: true,
            value: '2.0',
            width: 60,
            incrementValue: 0.1,
            minValue: -1,
            maxValue: 99999,
            alternateIncrementValue: 1,
            decimalPrecision: 2,
        });
        om.bind('stop_seed_ratio', this.stopRatio);

        this.removeAtRatio = fieldset.add({
            xtype: 'radiogroup',
            columns: 1,
            colspan: 2,
            disabled: true,
            style: 'margin-left: 10px',
            items: [
                {
                    boxLabel: _('Pause torrent'),
                    name: 'at_ratio',
                    inputValue: false,
                    checked: true,
                },
                {
                    boxLabel: _('Remove torrent'),
                    name: 'at_ratio',
                    inputValue: true,
                },
            ],
        });
        om.bind('remove_seed_at_ratio', this.removeAtRatio);
    },

    onStopRatioCheck: function (e, checked) {
        this.stopRatio.setDisabled(!checked);
        this.removeAtRatio.setDisabled(!checked);
    },
});
