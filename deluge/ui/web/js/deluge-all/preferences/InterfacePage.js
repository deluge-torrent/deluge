/**
 * Deluge.preferences.InterfacePage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Interface
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Interface = Ext.extend(Ext.form.FormPanel, {
    border: false,
    title: _('Interface'),
    header: false,
    layout: 'form',

    initComponent: function () {
        Deluge.preferences.Interface.superclass.initComponent.call(this);

        var om = (this.optionsManager = new Deluge.OptionsManager());
        this.on('show', this.onPageShow, this);

        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Interface'),
            style: 'margin-bottom: 0px; padding-bottom: 5px; padding-top: 5px',
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
            defaults: {
                height: 17,
                fieldLabel: '',
                labelSeparator: '',
            },
        });
        om.bind(
            'show_session_speed',
            fieldset.add({
                name: 'show_session_speed',
                boxLabel: _('Show session speed in titlebar'),
            })
        );
        om.bind(
            'sidebar_show_zero',
            fieldset.add({
                name: 'sidebar_show_zero',
                boxLabel: _('Show filters with zero torrents'),
            })
        );
        om.bind(
            'sidebar_multiple_filters',
            fieldset.add({
                name: 'sidebar_multiple_filters',
                boxLabel: _('Allow the use of multiple filters at once'),
            })
        );

        var languagePanel = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Language'),
            style: 'margin-bottom: 0px; padding-bottom: 5px; padding-top: 5px',
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
        });
        this.language = om.bind(
            'language',
            languagePanel.add({
                xtype: 'combo',
                labelSeparator: '',
                name: 'language',
                mode: 'local',
                width: 200,
                store: new Ext.data.ArrayStore({
                    fields: ['id', 'text'],
                }),
                editable: false,
                triggerAction: 'all',
                valueField: 'id',
                displayField: 'text',
            })
        );

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('WebUI Password'),
            style: 'margin-bottom: 0px; padding-bottom: 5px; padding-top: 5px',
            autoHeight: true,
            labelWidth: 100,
            defaultType: 'textfield',
            defaults: {
                width: 100,
                inputType: 'password',
                labelStyle: 'padding-left: 5px',
                height: 20,
                labelSeparator: '',
            },
        });

        this.oldPassword = fieldset.add({
            name: 'old_password',
            fieldLabel: _('Old:'),
        });
        this.newPassword = fieldset.add({
            name: 'new_password',
            fieldLabel: _('New:'),
        });
        this.confirmPassword = fieldset.add({
            name: 'confirm_password',
            fieldLabel: _('Confirm:'),
        });

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Server'),
            style: 'padding-top: 5px; margin-bottom: 0px; padding-bottom: 5px',
            autoHeight: true,
            labelWidth: 100,
            defaultType: 'spinnerfield',
            defaults: {
                labelSeparator: '',
                labelStyle: 'padding-left: 5px',
                height: 20,
                width: 80,
            },
        });
        om.bind(
            'session_timeout',
            fieldset.add({
                name: 'session_timeout',
                fieldLabel: _('Session Timeout:'),
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            })
        );
        om.bind(
            'port',
            fieldset.add({
                name: 'port',
                fieldLabel: _('Port:'),
                decimalPrecision: 0,
                minValue: 1,
                maxValue: 65535,
            })
        );
        this.httpsField = om.bind(
            'https',
            fieldset.add({
                xtype: 'checkbox',
                name: 'https',
                hideLabel: true,
                width: 300,
                style: 'margin-left: 5px',
                boxLabel: _(
                    'Enable SSL (paths relative to Deluge config folder)'
                ),
            })
        );
        this.httpsField.on('check', this.onSSLCheck, this);
        this.pkeyField = om.bind(
            'pkey',
            fieldset.add({
                xtype: 'textfield',
                disabled: true,
                name: 'pkey',
                width: 180,
                fieldLabel: _('Private Key:'),
            })
        );
        this.certField = om.bind(
            'cert',
            fieldset.add({
                xtype: 'textfield',
                disabled: true,
                name: 'cert',
                width: 180,
                fieldLabel: _('Certificate:'),
            })
        );
    },

    onApply: function () {
        var changed = this.optionsManager.getDirty();
        if (!Ext.isObjectEmpty(changed)) {
            deluge.client.web.set_config(changed, {
                success: this.onSetConfig,
                scope: this,
            });

            for (var key in deluge.config) {
                deluge.config[key] = this.optionsManager.get(key);
            }
            if ('language' in changed) {
                Ext.Msg.show({
                    title: _('WebUI Language Changed'),
                    msg: _(
                        'Do you want to refresh the page now to use the new language?'
                    ),
                    buttons: {
                        yes: _('Refresh'),
                        no: _('Close'),
                    },
                    multiline: false,
                    fn: function (btnText) {
                        if (btnText === 'yes') location.reload();
                    },
                    icon: Ext.MessageBox.QUESTION,
                });
            }
        }
        if (this.oldPassword.getValue() || this.newPassword.getValue()) {
            this.onPasswordChange();
        }
    },

    onOk: function () {
        this.onApply();
    },

    onGotConfig: function (config) {
        this.optionsManager.set(config);
    },

    onGotLanguages: function (info, obj, response, request) {
        info.unshift(['', _('System Default')]);
        this.language.store.loadData(info);
        this.language.setValue(this.optionsManager.get('language'));
    },

    onPasswordChange: function () {
        var newPassword = this.newPassword.getValue();
        if (newPassword != this.confirmPassword.getValue()) {
            Ext.MessageBox.show({
                title: _('Invalid Password'),
                msg: _("Your passwords don't match!"),
                buttons: Ext.MessageBox.OK,
                modal: false,
                icon: Ext.MessageBox.ERROR,
                iconCls: 'x-deluge-icon-error',
            });
            return;
        }

        var oldPassword = this.oldPassword.getValue();
        deluge.client.auth.change_password(oldPassword, newPassword, {
            success: function (result) {
                if (!result) {
                    Ext.MessageBox.show({
                        title: _('Password'),
                        msg: _('Your old password was incorrect!'),
                        buttons: Ext.MessageBox.OK,
                        modal: false,
                        icon: Ext.MessageBox.ERROR,
                        iconCls: 'x-deluge-icon-error',
                    });
                    this.oldPassword.setValue('');
                } else {
                    Ext.MessageBox.show({
                        title: _('Change Successful'),
                        msg: _('Your password was successfully changed!'),
                        buttons: Ext.MessageBox.OK,
                        modal: false,
                        icon: Ext.MessageBox.INFO,
                        iconCls: 'x-deluge-icon-info',
                    });
                    this.oldPassword.setValue('');
                    this.newPassword.setValue('');
                    this.confirmPassword.setValue('');
                }
            },
            scope: this,
        });
    },

    onSetConfig: function () {
        this.optionsManager.commit();
    },

    onPageShow: function () {
        deluge.client.web.get_config({
            success: this.onGotConfig,
            scope: this,
        });
        deluge.client.webutils.get_languages({
            success: this.onGotLanguages,
            scope: this,
        });
    },

    onSSLCheck: function (e, checked) {
        this.pkeyField.setDisabled(!checked);
        this.certField.setDisabled(!checked);
    },
});
