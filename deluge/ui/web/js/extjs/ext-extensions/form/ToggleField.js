/**
 * Ext.ux.form.ToggleField.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Ext.ux.form');

/**
 * Ext.ux.form.ToggleField class
 *
 * @author Damien Churchill
 * @version v0.1
 *
 * @class Ext.ux.form.ToggleField
 * @extends Ext.form.TriggerField
 */
Ext.ux.form.ToggleField = Ext.extend(Ext.form.Field, {
    cls: 'x-toggle-field',

    initComponent: function () {
        Ext.ux.form.ToggleField.superclass.initComponent.call(this);

        this.toggle = new Ext.form.Checkbox();
        this.toggle.on('check', this.onToggleCheck, this);

        this.input = new Ext.form.TextField({
            disabled: true,
        });
    },

    onRender: function (ct, position) {
        if (!this.el) {
            this.panel = new Ext.Panel({
                cls: this.groupCls,
                layout: 'table',
                layoutConfig: {
                    columns: 2,
                },
                border: false,
                renderTo: ct,
            });
            this.panel.ownerCt = this;
            this.el = this.panel.getEl();

            this.panel.add(this.toggle);
            this.panel.add(this.input);
            this.panel.doLayout();

            this.toggle.getEl().parent().setStyle('padding-right', '10px');
        }
        Ext.ux.form.ToggleField.superclass.onRender.call(this, ct, position);
    },

    // private
    onResize: function (w, h) {
        this.panel.setSize(w, h);
        this.panel.doLayout();

        // we substract 10 for the padding :-)
        var inputWidth = w - this.toggle.getSize().width - 25;
        this.input.setSize(inputWidth, h);
    },

    onToggleCheck: function (toggle, checked) {
        this.input.setDisabled(!checked);
    },
});
Ext.reg('togglefield', Ext.ux.form.ToggleField);
