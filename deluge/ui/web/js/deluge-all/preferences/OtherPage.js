/**
 * Deluge.preferences.OtherPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Other
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Other = Ext.extend(Ext.form.FormPanel, {
    constructor: function (config) {
        config = Ext.apply(
            {
                border: false,
                title: _('Other'),
                header: false,
                layout: 'form',
            },
            config
        );
        Deluge.preferences.Other.superclass.constructor.call(this, config);
    },

    initComponent: function () {
        Deluge.preferences.Other.superclass.initComponent.call(this);

        var optMan = deluge.preferences.getOptionsManager();

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Updates'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        optMan.bind(
            'new_release_check',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                height: 22,
                name: 'new_release_check',
                boxLabel: _('Be alerted about new releases'),
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('System Information'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        fieldset.add({
            xtype: 'panel',
            border: false,
            bodyCfg: {
                html: _(
                    'Help us improve Deluge by sending us your Python version, PyGTK version, OS and processor types. Absolutely no other information is sent.'
                ),
            },
        });
        optMan.bind(
            'send_info',
            fieldset.add({
                fieldLabel: '',
                labelSeparator: '',
                height: 22,
                boxLabel: _('Yes, please send anonymous statistics'),
                name: 'send_info',
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('GeoIP Database'),
            autoHeight: true,
            labelWidth: 80,
            defaultType: 'textfield',
        });
        optMan.bind(
            'geoip_db_location',
            fieldset.add({
                name: 'geoip_db_location',
                fieldLabel: _('Path:'),
                labelSeparator: '',
                width: 200,
            })
        );
    },
});
