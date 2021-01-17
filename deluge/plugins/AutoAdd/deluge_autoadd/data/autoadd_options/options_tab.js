/**
 * Script: options_tab.js
 *      The client-side javascript code for the AutoAdd plugin.
 *
 * Copyright (C) 2009 GazpachoKing <chase.sterling@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.ns('Deluge.ux.AutoAdd');

/**
 * @class Deluge.ux.AutoAdd.AutoAddOptionsPanel
 * @extends Ext.Panel
 */
Deluge.ux.AutoAdd.AutoAddOptionsPanel = Ext.extend(Ext.Panel, {
    id: 'options_tab_panel',
    title: _('Options'),

    initComponent: function () {
        Deluge.ux.AutoAdd.AutoAddOptionsPanel.superclass.initComponent.call(
            this
        );
        var maxDownload = {
            idCheckbox: 'max_download_speed_toggle',
            labelCheckbox: 'Max Download Speed (KiB/s):',
            idSpinner: 'max_download_speed',
            decimalPrecision: 1,
        };
        var maxUploadSpeed = {
            idCheckbox: 'max_upload_speed_toggle',
            labelCheckbox: 'Max upload Speed (KiB/s):',
            idSpinner: 'max_upload_speed',
            decimalPrecision: 1,
        };
        var maxConnections = {
            idCheckbox: 'max_connections_toggle',
            labelCheckbox: 'Max Connections::',
            idSpinner: 'max_connections',
            decimalPrecision: 0,
        };
        var maxUploadSlots = {
            idCheckbox: 'max_upload_slots_toggle',
            labelCheckbox: 'Max Upload Slots:',
            idSpinner: 'max_upload_slots',
            decimalPrecision: 0,
        };
        // queue data
        var addPause = {
            idCheckbox: 'add_paused_toggle',
            labelCheckbox: 'Add Pause:',
            nameRadio: 'add_paused',
            labelRadio: {
                yes: 'Yes',
                no: 'No',
            },
        };
        var queueTo = {
            idCheckbox: 'queue_to_top_toggle',
            labelCheckbox: 'Queue To:',
            nameRadio: 'queue_to_top',
            labelRadio: {
                yes: 'Top',
                no: 'Bottom',
            },
        };
        var autoManaged = {
            idCheckbox: 'auto_managed_toggle',
            labelCheckbox: 'Auto Managed:',
            nameRadio: 'auto_managed',
            labelRadio: {
                yes: 'Yes',
                no: 'No',
            },
        };

        this.ownerFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Owner'),
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            //width: '85%',
            labelWidth: 1,
            items: [
                {
                    xtype: 'combo',
                    id: 'owner',
                    hideLabel: true,
                    width: 312,
                    mode: 'local',
                    valueField: 'displayText',
                    displayField: 'displayText',
                },
            ],
        });

        this.bandwidthFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Bandwidth'),
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            //width: '85%',
            labelWidth: 1,
            defaults: {
                style: 'margin-bottom: 5px',
            },
        });
        this.bandwidthFset.add(this._getBandwidthContainer(maxDownload));
        this.bandwidthFset.add(this._getBandwidthContainer(maxUploadSpeed));
        this.bandwidthFset.add(this._getBandwidthContainer(maxConnections));
        this.bandwidthFset.add(this._getBandwidthContainer(maxUploadSlots));

        this.queueFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Queue'),
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            //width: '85%',
            labelWidth: 1,
            defaults: {
                style: 'margin-bottom: 5px',
            },
            items: [
                {
                    xtype: 'container',
                    layout: 'hbox',
                    hideLabel: true,
                },
            ],
        });
        this.queueFset.add(this._getQueueContainer(addPause));
        this.queueFset.add(this._getQueueContainer(queueTo));
        this.queueFset.add(this._getQueueContainer(autoManaged));
        this.queueFset.add({
            xtype: 'container',
            hideLabel: true,
            items: [
                {
                    xtype: 'container',
                    layout: 'hbox',
                    hideLabel: true,
                    items: [
                        {
                            xtype: 'checkbox',
                            id: 'stop_at_ratio_toggle',
                            boxLabel: _('Stop seed at ratio:'),
                            hideLabel: true,
                            width: 175,
                            listeners: {
                                check: function (cb, checked) {
                                    Ext.getCmp('stop_ratio').setDisabled(
                                        !checked
                                    );
                                    Ext.getCmp('remove_at_ratio').setDisabled(
                                        !checked
                                    );
                                },
                            },
                        },
                        {
                            xtype: 'spinnerfield',
                            id: 'stop_ratio',
                            hideLabel: true,
                            disabled: true,
                            value: 0.0,
                            minValue: 0.0,
                            maxValue: 100.0,
                            decimalPrecision: 1,
                            incrementValue: 0.1,
                            style: 'margin-left: 2px',
                            width: 100,
                        },
                    ],
                },
                {
                    xtype: 'container',
                    layout: 'hbox',
                    hideLabel: true,
                    style: 'margin-left: 10px',
                    items: [
                        {
                            xtype: 'checkbox',
                            id: 'remove_at_ratio',
                            boxLabel: _('Remove at ratio'),
                            disabled: true,
                            checked: true,
                        },
                        {
                            xtype: 'checkbox',
                            id: 'remove_at_ratio_toggle',
                            disabled: true,
                            checked: true,
                            hidden: true,
                        },
                        {
                            xtype: 'checkbox',
                            id: 'stop_ratio_toggle',
                            disabled: true,
                            checked: true,
                            hidden: true,
                        },
                        {
                            xtype: 'checkbox',
                            id: 'stop_ratio_toggle',
                            disabled: true,
                            checked: true,
                            hidden: true,
                        },
                    ],
                },
            ],
        });
        this.queueFset.add({
            xtype: 'checkbox',
            id: 'seed_mode',
            boxLabel: _('Skip File Hash Check'),
            hideLabel: true,
            width: 175,
        });

        this.add([this.ownerFset, this.bandwidthFset, this.queueFset]);
    },

    _getBandwidthContainer: function (values) {
        return new Ext.Container({
            xtype: 'container',
            layout: 'hbox',
            hideLabel: true,
            items: [
                {
                    xtype: 'checkbox',
                    hideLabel: true,
                    id: values.idCheckbox,
                    boxLabel: _(values.labelCheckbox),
                    width: 175,
                    listeners: {
                        check: function (cb, checked) {
                            Ext.getCmp(values.idSpinner).setDisabled(!checked);
                        },
                    },
                },
                {
                    xtype: 'spinnerfield',
                    id: values.idSpinner,
                    hideLabel: true,
                    disabled: true,
                    minValue: -1,
                    maxValue: 10000,
                    value: 0.0,
                    decimalPrecision: values.decimalPrecision,
                    style: 'margin-left: 2px',
                    width: 100,
                },
            ],
        });
    },

    _getQueueContainer: function (values) {
        return new Ext.Container({
            xtype: 'container',
            layout: 'hbox',
            hideLabel: true,
            items: [
                {
                    xtype: 'checkbox',
                    hideLabel: true,
                    id: values.idCheckbox,
                    boxLabel: _(values.labelCheckbox),
                    width: 175,
                    listeners: {
                        check: function (cb, checked) {
                            Ext.getCmp(values.nameRadio).setDisabled(!checked);
                            Ext.getCmp('not_' + values.nameRadio).setDisabled(
                                !checked
                            );
                        },
                    },
                },
                {
                    xtype: 'radio',
                    name: values.nameRadio,
                    id: values.nameRadio,
                    boxLabel: _(values.labelRadio.yes),
                    hideLabel: true,
                    checked: true,
                    disabled: true,
                    width: 50,
                },
                {
                    xtype: 'radio',
                    name: values.nameRadio,
                    id: 'not_' + values.nameRadio,
                    boxLabel: _(values.labelRadio.no),
                    hideLabel: true,
                    disabled: true,
                },
            ],
        });
    },
});
