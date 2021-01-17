/**
 * Deluge.preferences.DaemonPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Daemon
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Daemon = Ext.extend(Ext.form.FormPanel, {
    border: false,
    title: _('Daemon'),
    header: false,
    layout: 'form',

    initComponent: function () {
        Deluge.preferences.Daemon.superclass.initComponent.call(this);

        var om = deluge.preferences.getOptionsManager();

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Port'),
            autoHeight: true,
            defaultType: 'spinnerfield',
        });
        om.bind(
            'daemon_port',
            fieldset.add({
                fieldLabel: _('Daemon port:'),
                labelSeparator: '',
                name: 'daemon_port',
                value: 58846,
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Connections'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        om.bind(
            'allow_remote',
            fieldset.add({
                fieldLabel: '',
                height: 22,
                labelSeparator: '',
                boxLabel: _('Allow Remote Connections'),
                name: 'allow_remote',
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Other'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        om.bind(
            'new_release_check',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                height: 40,
                boxLabel: _('Periodically check the website for new releases'),
                id: 'new_release_check',
            })
        );
    },
});
