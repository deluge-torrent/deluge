/*!
 * Ext.ux.form.ToggleField.js
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
Ext.namespace("Ext.ux.form");

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

	initComponent: function() {
		Ext.ux.form.ToggleField.superclass.initComponent.call(this);

		this.toggle = new Ext.form.Checkbox();
		this.toggle.on('check', this.onToggleCheck, this);

		this.input = new Ext.form.TextField({
			disabled: true
		});
	},

	onRender: function(ct, position) {
		if (!this.el) {
			this.panel = new Ext.Panel({
				cls: this.groupCls,
				layout: 'table',
				layoutConfig: {
					columns: 2
				},
				border: false,
				renderTo: ct
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
	onResize: function(w, h) {
		this.panel.setSize(w, h);
		this.panel.doLayout();

		// we substract 10 for the padding :-)
		var inputWidth = w - this.toggle.getSize().width - 25;
		this.input.setSize(inputWidth, h);
	},

	onToggleCheck: function(toggle, checked) {
		this.input.setDisabled(!checked);
	}
});
Ext.reg('togglefield', Ext.ux.form.ToggleField);
