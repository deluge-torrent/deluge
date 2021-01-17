/**
 * Ext.ux.layout.FormLayoutFix.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

// Taken from http://extjs.com/forum/showthread.php?t=75273
// remove spaces for hidden elements and make show(), hide(), enable() and disable() act on
// the label. don't use hideLabel with this.
Ext.override(Ext.layout.FormLayout, {
    renderItem: function (c, position, target) {
        if (
            c &&
            !c.rendered &&
            (c.isFormField || c.fieldLabel) &&
            c.inputType != 'hidden'
        ) {
            var args = this.getTemplateArgs(c);
            if (typeof position == 'number') {
                position = target.dom.childNodes[position] || null;
            }
            if (position) {
                c.formItem = this.fieldTpl.insertBefore(position, args, true);
            } else {
                c.formItem = this.fieldTpl.append(target, args, true);
            }
            c.actionMode = 'formItem';
            c.render('x-form-el-' + c.id);
            c.container = c.formItem;
            c.actionMode = 'container';
        } else {
            Ext.layout.FormLayout.superclass.renderItem.apply(this, arguments);
        }
    },
});
