/**
 * Deluge.AddTrackerWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

// Custom VType validator for tracker urls
var trackerUrlTest = /(((^https?)|(^udp)):\/\/([\-\w]+\.)+\w{2,3}(\/[%\-\w]+(\.\w{2,})?)*(([\w\-\.\?\\\/+@&#;`~=%!]*)(\.\w{2,})?)*\/?)/i;
Ext.apply(Ext.form.VTypes, {
    trackerUrl: function (val, field) {
        return trackerUrlTest.test(val);
    },
    trackerUrlText: 'Not a valid tracker url',
});

/**
 * @class Deluge.AddTrackerWindow
 * @extends Ext.Window
 */
Deluge.AddTrackerWindow = Ext.extend(Ext.Window, {
    title: _('Add Tracker'),
    layout: 'fit',
    width: 375,
    height: 150,
    plain: true,
    closable: true,
    resizable: false,
    constrainHeader: true,
    bodyStyle: 'padding: 5px',
    buttonAlign: 'right',
    closeAction: 'hide',
    iconCls: 'x-deluge-edit-trackers',

    initComponent: function () {
        Deluge.AddTrackerWindow.superclass.initComponent.call(this);

        this.addButton(_('Cancel'), this.onCancelClick, this);
        this.addButton(_('Add'), this.onAddClick, this);
        this.addEvents('add');

        this.form = this.add({
            xtype: 'form',
            defaultType: 'textarea',
            baseCls: 'x-plain',
            labelWidth: 55,
            items: [
                {
                    fieldLabel: _('Trackers:'),
                    labelSeparator: '',
                    name: 'trackers',
                    anchor: '100%',
                },
            ],
        });
    },

    onAddClick: function () {
        var trackers = this.form.getForm().findField('trackers').getValue();
        trackers = trackers.split('\n');

        var cleaned = [];
        Ext.each(
            trackers,
            function (tracker) {
                if (Ext.form.VTypes.trackerUrl(tracker)) {
                    cleaned.push(tracker);
                }
            },
            this
        );
        this.fireEvent('add', cleaned);
        this.hide();
        this.form.getForm().findField('trackers').setValue('');
    },

    onCancelClick: function () {
        this.form.getForm().findField('trackers').setValue('');
        this.hide();
    },
});
