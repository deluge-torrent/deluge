/**
 * Deluge.preferences.EncryptionPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Encryption
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Encryption = Ext.extend(Ext.form.FormPanel, {
    border: false,
    title: _('Encryption'),
    header: false,

    initComponent: function () {
        Deluge.preferences.Encryption.superclass.initComponent.call(this);

        var optMan = deluge.preferences.getOptionsManager();

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Settings'),
            header: false,
            autoHeight: true,
            defaultType: 'combo',
            width: 300,
        });
        optMan.bind(
            'enc_in_policy',
            fieldset.add({
                fieldLabel: _('Incoming:'),
                labelSeparator: '',
                mode: 'local',
                width: 150,
                store: new Ext.data.ArrayStore({
                    fields: ['id', 'text'],
                    data: [
                        [0, _('Forced')],
                        [1, _('Enabled')],
                        [2, _('Disabled')],
                    ],
                }),
                editable: false,
                triggerAction: 'all',
                valueField: 'id',
                displayField: 'text',
            })
        );
        optMan.bind(
            'enc_out_policy',
            fieldset.add({
                fieldLabel: _('Outgoing:'),
                labelSeparator: '',
                mode: 'local',
                width: 150,
                store: new Ext.data.SimpleStore({
                    fields: ['id', 'text'],
                    data: [
                        [0, _('Forced')],
                        [1, _('Enabled')],
                        [2, _('Disabled')],
                    ],
                }),
                editable: false,
                triggerAction: 'all',
                valueField: 'id',
                displayField: 'text',
            })
        );
        optMan.bind(
            'enc_level',
            fieldset.add({
                fieldLabel: _('Level:'),
                labelSeparator: '',
                mode: 'local',
                width: 150,
                store: new Ext.data.SimpleStore({
                    fields: ['id', 'text'],
                    data: [
                        [0, _('Handshake')],
                        [1, _('Full Stream')],
                        [2, _('Either')],
                    ],
                }),
                editable: false,
                triggerAction: 'all',
                valueField: 'id',
                displayField: 'text',
            })
        );
    },
});
