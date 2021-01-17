/**
 * Deluge.OtherLimitWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * @class Deluge.OtherLimitWindow
 * @extends Ext.Window
 */
Deluge.OtherLimitWindow = Ext.extend(Ext.Window, {
    layout: 'fit',
    width: 210,
    height: 100,
    constrainHeader: true,
    closeAction: 'hide',

    initComponent: function () {
        Deluge.OtherLimitWindow.superclass.initComponent.call(this);
        this.form = this.add({
            xtype: 'form',
            baseCls: 'x-plain',
            bodyStyle: 'padding: 5px',
            layout: 'hbox',
            layoutConfig: {
                pack: 'start',
            },
            items: [
                {
                    xtype: 'spinnerfield',
                    name: 'limit',
                },
            ],
        });
        if (this.initialConfig.unit) {
            this.form.add({
                border: false,
                baseCls: 'x-plain',
                bodyStyle: 'padding: 5px',
                html: this.initialConfig.unit,
            });
        } else {
            this.setSize(180, 100);
        }

        this.addButton(_('Cancel'), this.onCancelClick, this);
        this.addButton(_('OK'), this.onOkClick, this);
        this.afterMethod('show', this.doFocusField, this);
    },

    setValue: function (value) {
        this.form.getForm().setValues({ limit: value });
    },

    onCancelClick: function () {
        this.form.getForm().reset();
        this.hide();
    },

    onOkClick: function () {
        var config = {};
        config[this.group] = this.form.getForm().getValues().limit;
        deluge.client.core.set_config(config, {
            success: function () {
                deluge.ui.update();
            },
        });
        this.hide();
    },

    doFocusField: function () {
        this.form.getForm().findField('limit').focus(true, 10);
    },
});
