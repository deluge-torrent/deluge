/*!
 * Ext.ux.form.RadioGroup.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */

// Allow radiogroups to be treated as a single form element.
Ext.override(Ext.form.RadioGroup, {

    afterRender: function() {
		this.items.each(function(i) {
	    	this.relayEvents(i, ['check']);
		}, this);
		if (this.lazyValue) {
			this.setValue(this.value);
			delete this.value;
			delete this.lazyValue;
		}
		Ext.form.RadioGroup.superclass.afterRender.call(this)
    },

    getName: function() {
		return this.items.first().getName();
    },

    getValue: function() {
		return this.items.first().getGroupValue();
    },

    setValue: function(v) {
		if (!this.items.each) {
			this.value = v;
			this.lazyValue = true;
			return;
		}
		this.items.each(function(item) {
			if (item.rendered) {
				var checked = (item.el.getValue() == String(v));
				item.el.dom.checked = checked;
				item.el.dom.defaultChecked = checked;
				item.wrap[checked ? 'addClass' : 'removeClass'](item.checkedCls);
			}
		});
    }
});
