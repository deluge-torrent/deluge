/**
 * Deluge.EditTrackerWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * @class Deluge.EditTrackerWindow
 * @extends Ext.Window
 */
Deluge.EditTrackerWindow = Ext.extend(Ext.Window, {
    title: _('Edit Tracker'),
    layout: 'fit',
    width: 375,
    height: 110,
    plain: true,
    closable: true,
    resizable: false,
    constrainHeader: true,
    bodyStyle: 'padding: 5px',
    buttonAlign: 'right',
    closeAction: 'hide',
    iconCls: 'x-deluge-edit-trackers',

    initComponent: function () {
        Deluge.EditTrackerWindow.superclass.initComponent.call(this);

        this.addButton(_('Cancel'), this.onCancelClick, this);
        this.addButton(_('Save'), this.onSaveClick, this);
        this.on('hide', this.onHide, this);

        this.form = this.add({
            xtype: 'form',
            defaultType: 'textfield',
            baseCls: 'x-plain',
            labelWidth: 55,
            items: [
                {
                    fieldLabel: _('Tracker:'),
                    labelSeparator: '',
                    name: 'tracker',
                    anchor: '100%',
                },
            ],
        });
    },

    show: function (record) {
        Deluge.EditTrackerWindow.superclass.show.call(this);

        this.record = record;
        this.form.getForm().findField('tracker').setValue(record.data['url']);
    },

    onCancelClick: function () {
        this.hide();
    },

    onHide: function () {
        this.form.getForm().findField('tracker').setValue('');
    },

    onSaveClick: function () {
        var url = this.form.getForm().findField('tracker').getValue();
        this.record.set('url', url);
        this.record.commit();
        this.hide();
    },
});
