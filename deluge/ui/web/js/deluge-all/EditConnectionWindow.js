/**
 * Deluge.EditConnectionWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * @class Deluge.EditConnectionWindow
 * @extends Ext.Window
 */
Deluge.EditConnectionWindow = Ext.extend(Ext.Window, {
    title: _('Edit Connection'),
    iconCls: 'x-deluge-add-window-icon',

    layout: 'fit',
    width: 300,
    height: 195,
    constrainHeader: true,
    bodyStyle: 'padding: 10px 5px;',
    closeAction: 'hide',

    initComponent: function () {
        Deluge.EditConnectionWindow.superclass.initComponent.call(this);

        this.addEvents('hostedited');

        this.addButton(_('Close'), this.hide, this);
        this.addButton(_('Edit'), this.onEditClick, this);

        this.on('hide', this.onHide, this);

        this.form = this.add({
            xtype: 'form',
            defaultType: 'textfield',
            baseCls: 'x-plain',
            labelWidth: 60,
            items: [
                {
                    fieldLabel: _('Host:'),
                    labelSeparator: '',
                    name: 'host',
                    anchor: '75%',
                    value: '',
                },
                {
                    xtype: 'spinnerfield',
                    fieldLabel: _('Port:'),
                    labelSeparator: '',
                    name: 'port',
                    strategy: {
                        xtype: 'number',
                        decimalPrecision: 0,
                        minValue: 0,
                        maxValue: 65535,
                    },
                    anchor: '40%',
                    value: 58846,
                },
                {
                    fieldLabel: _('Username:'),
                    labelSeparator: '',
                    name: 'username',
                    anchor: '75%',
                    value: '',
                },
                {
                    fieldLabel: _('Password:'),
                    labelSeparator: '',
                    anchor: '75%',
                    name: 'password',
                    inputType: 'password',
                    value: '',
                },
            ],
        });
    },

    show: function (connection) {
        Deluge.EditConnectionWindow.superclass.show.call(this);

        this.form.getForm().findField('host').setValue(connection.get('host'));
        this.form.getForm().findField('port').setValue(connection.get('port'));
        this.form
            .getForm()
            .findField('username')
            .setValue(connection.get('user'));
        this.host_id = connection.id;
    },

    onEditClick: function () {
        var values = this.form.getForm().getValues();
        deluge.client.web.edit_host(
            this.host_id,
            values.host,
            Number(values.port),
            values.username,
            values.password,
            {
                success: function (result) {
                    if (!result) {
                        console.log(result);
                        Ext.MessageBox.show({
                            title: _('Error'),
                            msg: String.format(_('Unable to edit host')),
                            buttons: Ext.MessageBox.OK,
                            modal: false,
                            icon: Ext.MessageBox.ERROR,
                            iconCls: 'x-deluge-icon-error',
                        });
                    } else {
                        this.fireEvent('hostedited');
                    }
                    this.hide();
                },
                scope: this,
            }
        );
    },

    onHide: function () {
        this.form.getForm().reset();
    },
});
