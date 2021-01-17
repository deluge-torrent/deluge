/**
 * Deluge.LoginWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Deluge.LoginWindow = Ext.extend(Ext.Window, {
    firstShow: true,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'center',
    closable: false,
    closeAction: 'hide',
    iconCls: 'x-deluge-login-window-icon',
    layout: 'fit',
    modal: true,
    plain: true,
    resizable: false,
    title: _('Login'),
    width: 300,
    height: 120,

    initComponent: function () {
        Deluge.LoginWindow.superclass.initComponent.call(this);
        this.on('show', this.onShow, this);

        this.addButton({
            text: _('Login'),
            handler: this.onLogin,
            scope: this,
        });

        this.form = this.add({
            xtype: 'form',
            baseCls: 'x-plain',
            labelWidth: 120,
            labelAlign: 'right',
            defaults: { width: 110 },
            defaultType: 'textfield',
        });

        this.passwordField = this.form.add({
            xtype: 'textfield',
            fieldLabel: _('Password:'),
            labelSeparator: '',
            grow: true,
            growMin: '110',
            growMax: '145',
            id: '_password',
            name: 'password',
            inputType: 'password',
        });
        this.passwordField.on('specialkey', this.onSpecialKey, this);
    },

    logout: function () {
        deluge.events.fire('logout');
        deluge.client.auth.delete_session({
            success: function (result) {
                this.show(true);
            },
            scope: this,
        });
    },

    show: function (skipCheck) {
        if (this.firstShow) {
            deluge.client.on('error', this.onClientError, this);
            this.firstShow = false;
        }

        if (skipCheck) {
            return Deluge.LoginWindow.superclass.show.call(this);
        }

        deluge.client.auth.check_session({
            success: function (result) {
                if (result) {
                    deluge.events.fire('login');
                } else {
                    this.show(true);
                }
            },
            failure: function (result) {
                this.show(true);
            },
            scope: this,
        });
    },

    onSpecialKey: function (field, e) {
        if (e.getKey() == 13) this.onLogin();
    },

    onLogin: function () {
        var passwordField = this.passwordField;
        deluge.client.auth.login(passwordField.getValue(), {
            success: function (result) {
                if (result) {
                    deluge.events.fire('login');
                    this.hide();
                    passwordField.setRawValue('');
                } else {
                    Ext.MessageBox.show({
                        title: _('Login Failed'),
                        msg: _('You entered an incorrect password'),
                        buttons: Ext.MessageBox.OK,
                        modal: false,
                        fn: function () {
                            passwordField.focus(true, 10);
                        },
                        icon: Ext.MessageBox.WARNING,
                        iconCls: 'x-deluge-icon-warning',
                    });
                }
            },
            scope: this,
        });
    },

    onClientError: function (errorObj, response, requestOptions) {
        if (errorObj.error.code == 1) {
            deluge.events.fire('logout');
            this.show(true);
        }
    },

    onShow: function () {
        this.passwordField.focus(true, 300);
    },
});
