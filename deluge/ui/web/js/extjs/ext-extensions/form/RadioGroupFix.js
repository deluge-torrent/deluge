/**
 * Ext.ux.form.RadioGroup.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

// Allow radiogroups to be treated as a single form element.
Ext.override(Ext.form.RadioGroup, {
    afterRender: function () {
        this.items.each(function (i) {
            this.relayEvents(i, ['check']);
        }, this);
        if (this.lazyValue) {
            this.setValue(this.value);
            delete this.value;
            delete this.lazyValue;
        }
        Ext.form.RadioGroup.superclass.afterRender.call(this);
    },

    getName: function () {
        return this.items.first().getName();
    },

    getValue: function () {
        return this.items.first().getGroupValue();
    },

    setValue: function (v) {
        if (!this.items.each) {
            this.value = v;
            this.lazyValue = true;
            return;
        }
        this.items.each(function (item) {
            if (item.rendered) {
                var checked = item.el.getValue() == String(v);
                item.el.dom.checked = checked;
                item.el.dom.defaultChecked = checked;
                item.wrap[checked ? 'addClass' : 'removeClass'](
                    item.checkedCls
                );
            }
        });
    },
});
