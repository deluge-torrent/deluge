/**
 * Script: main_tab.js
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
 * @class Deluge.ux.AutoAdd.AutoAddMainPanel
 * @extends Ext.Panel
 */
Deluge.ux.AutoAdd.AutoAddMainPanel = Ext.extend(Ext.Panel, {
    id: 'main_tab_panel',
    title: _('Main'),

    initComponent: function () {
        Deluge.ux.AutoAdd.AutoAddMainPanel.superclass.initComponent.call(this);
        this.watchFolderFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Watch Folder'),
            defaultType: 'textfield',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            width: '85%',
            labelWidth: 1,
            items: [
                {
                    xtype: 'textfield',
                    id: 'path',
                    hideLabel: true,
                    width: 304,
                },
                {
                    hideLabel: true,
                    id: 'enabled',
                    xtype: 'checkbox',
                    boxLabel: _('Enable this watch folder'),
                    checked: true,
                },
            ],
        });

        this.torrentActionFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Torrent File Action'),
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            width: '85%',
            labelWidth: 1,
            defaults: {
                style: 'margin-bottom: 2px',
            },
            items: [
                {
                    xtype: 'radiogroup',
                    columns: 1,
                    items: [
                        {
                            xtype: 'radio',
                            name: 'torrent_action',
                            id: 'isnt_append_extension',
                            boxLabel: _('Delete .torrent after adding'),
                            checked: true,
                            hideLabel: true,
                            listeners: {
                                check: function (cb, newValue) {
                                    if (newValue) {
                                        Ext.getCmp(
                                            'append_extension'
                                        ).setDisabled(newValue);
                                        Ext.getCmp('copy_torrent').setDisabled(
                                            newValue
                                        );
                                        Ext.getCmp(
                                            'delete_copy_torrent_toggle'
                                        ).setDisabled(newValue);
                                    }
                                },
                            },
                        },
                        {
                            xtype: 'container',
                            layout: 'hbox',
                            hideLabel: true,
                            items: [
                                {
                                    xtype: 'radio',
                                    name: 'torrent_action',
                                    id: 'append_extension_toggle',
                                    boxLabel: _(
                                        'Append extension after adding:'
                                    ),
                                    hideLabel: true,
                                    listeners: {
                                        check: function (cb, newValue) {
                                            if (newValue) {
                                                Ext.getCmp(
                                                    'append_extension'
                                                ).setDisabled(!newValue);
                                                Ext.getCmp(
                                                    'copy_torrent'
                                                ).setDisabled(newValue);
                                                Ext.getCmp(
                                                    'delete_copy_torrent_toggle'
                                                ).setDisabled(newValue);
                                            }
                                        },
                                    },
                                },
                                {
                                    xtype: 'textfield',
                                    id: 'append_extension',
                                    hideLabel: true,
                                    disabled: true,
                                    style: 'margin-left: 2px',
                                    width: 112,
                                },
                            ],
                        },
                        {
                            xtype: 'container',
                            hideLabel: true,
                            items: [
                                {
                                    xtype: 'container',
                                    layout: 'hbox',
                                    hideLabel: true,
                                    items: [
                                        {
                                            xtype: 'radio',
                                            name: 'torrent_action',
                                            id: 'copy_torrent_toggle',
                                            boxLabel: _(
                                                'Copy of .torrent files to:'
                                            ),
                                            hideLabel: true,
                                            listeners: {
                                                check: function (cb, newValue) {
                                                    if (newValue) {
                                                        Ext.getCmp(
                                                            'append_extension'
                                                        ).setDisabled(newValue);
                                                        Ext.getCmp(
                                                            'copy_torrent'
                                                        ).setDisabled(
                                                            !newValue
                                                        );
                                                        Ext.getCmp(
                                                            'delete_copy_torrent_toggle'
                                                        ).setDisabled(
                                                            !newValue
                                                        );
                                                    }
                                                },
                                            },
                                        },
                                        {
                                            xtype: 'textfield',
                                            id: 'copy_torrent',
                                            hideLabel: true,
                                            disabled: true,
                                            style: 'margin-left: 2px',
                                            width: 152,
                                        },
                                    ],
                                },
                                {
                                    xtype: 'checkbox',
                                    id: 'delete_copy_torrent_toggle',
                                    boxLabel: _(
                                        'Delete copy of torrent file on remove'
                                    ),
                                    style: 'margin-left: 10px',
                                    disabled: true,
                                },
                            ],
                        },
                    ],
                },
            ],
        });

        this.downloadFolderFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Download Folder'),
            defaultType: 'textfield',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            width: '85%',
            labelWidth: 1,
            items: [
                {
                    hideLabel: true,
                    id: 'download_location_toggle',
                    xtype: 'checkbox',
                    boxLabel: _('Set download folder'),
                    listeners: {
                        check: function (cb, checked) {
                            Ext.getCmp('download_location').setDisabled(
                                !checked
                            );
                        },
                    },
                },
                {
                    xtype: 'textfield',
                    id: 'download_location',
                    hideLabel: true,
                    width: 304,
                    disabled: true,
                },
            ],
        });

        this.moveCompletedFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Move Completed'),
            defaultType: 'textfield',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            width: '85%',
            labelWidth: 1,
            items: [
                {
                    hideLabel: true,
                    id: 'move_completed_toggle',
                    xtype: 'checkbox',
                    boxLabel: _('Set move completed folder'),
                    listeners: {
                        check: function (cb, checked) {
                            Ext.getCmp('move_completed_path').setDisabled(
                                !checked
                            );
                        },
                    },
                },
                {
                    xtype: 'textfield',
                    id: 'move_completed_path',
                    hideLabel: true,
                    width: 304,
                    disabled: true,
                },
            ],
        });

        this.LabelFset = new Ext.form.FieldSet({
            xtype: 'fieldset',
            border: false,
            title: _('Label'),
            defaultType: 'textfield',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 3px;',
            //width: '85%',
            labelWidth: 1,
            //hidden: true,
            items: [
                {
                    xtype: 'container',
                    layout: 'hbox',
                    hideLabel: true,
                    items: [
                        {
                            hashLabel: false,
                            id: 'label_toggle',
                            xtype: 'checkbox',
                            boxLabel: _('Label:'),
                            listeners: {
                                check: function (cb, checked) {
                                    Ext.getCmp('label').setDisabled(!checked);
                                },
                            },
                        },
                        {
                            xtype: 'combo',
                            id: 'label',
                            hideLabel: true,
                            //width: 220,
                            width: 254,
                            disabled: true,
                            style: 'margin-left: 2px',
                            mode: 'local',
                            valueField: 'displayText',
                            displayField: 'displayText',
                        },
                    ],
                },
            ],
        });

        this.add([
            this.watchFolderFset,
            this.torrentActionFset,
            this.downloadFolderFset,
            this.moveCompletedFset,
            this.LabelFset,
        ]);
    },
});
