/*!
 * label.js
 * 
 * Copyright (c) Damien Churchill 2010 <damoxc@gmail.com>
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
Ext.ns('Deluge.ux');

/**
 * @class Deluge.ux.LabelOptionsWindow
 * @extends Ext.Window
 */
Deluge.ux.LabelOptionsWindow = Ext.extend(Ext.Window, {

	title: _('Label Options'),
	width:  350,
	height: 400,
	
	initComponent: function() {
		Deluge.ux.LabelOptionsWindow.superclass.initComponent.call(this);
		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Ok'), this.onOkClick, this);

		this.add({
			xtype: 'tabpanel',
			height: 335,
			border: false,
			items: [{
				title: _('Maximum')
			}, {
				title: _('Queue')
			}, {
				title: _('Location')
			}, {
				title: _('Trackers')
			}]
		});
	},

	show: function(label) {
		Deluge.ux.LabelOptionsWindow.superclass.show.call(this);
		this.label = label;
		this.setTitle(_('Label Options') + ': ' + this.label); 
	},

	onCancelClick: function() {
		this.hide();
	},

	onOkClick: function() {
		this.hide();
	}

});


Ext.ns('Deluge.plugins');

/**
 * @class Deluge.plugins.LabelPlugin
 * @extends Deluge.Plugin
 */
Deluge.plugins.LabelPlugin = Ext.extend(Deluge.Plugin, {

	name: 'Label',

	createMenu: function() {
		this.labelMenu = new Ext.menu.Menu({
			items: [{
				text: _('Add Label'),
				iconCls: 'icon-add'
			}, {
				text: _('Remove Label'),
				disabled: true,
				iconCls: 'icon-remove',
				handler: this.onLabelRemoveClick,
				scope: this
			}, {
				text: _('Label Options'),
				disabled: true,
				handler: this.onLabelOptionsClick,
				scope: this
			}]
		});
	},
	
	onDisable: function() {
	    
	},
	
	onEnable: function() {
		deluge.sidebar.on('filtercreate', this.onFilterCreate, this);
		Deluge.FilterPanel.templates.label = '<div class="x-deluge-filter x-deluge-{filter:lowercase}"><tpl if="filter">{filter}</tpl><tpl if="!filter">no label</tpl> ({count})</div>';
	},

	onFilterCreate: function(sidebar, filter) {
		if (filter.filter != 'label') return;
		filter.list.on('contextmenu', this.onLabelContextMenu, this);
		filter.header.on('contextmenu', this.onLabelHeaderContextMenu, this);
		this.filter = filter;
	},

	onLabelContextMenu: function(dv, i, node, e) {
		e.preventDefault();
		if (!this.labelMenu) this.createMenu();
		this.labelMenu.items.get(1).setDisabled(false);
		this.labelMenu.items.get(2).setDisabled(false);
		dv.select(i);
		this.labelMenu.showAt(e.getXY());
	},

	onLabelHeaderContextMenu: function(e, t) {
		e.preventDefault();
		if (!this.labelMenu) this.createMenu();
		this.labelMenu.items.get(1).setDisabled(true);
		this.labelMenu.items.get(2).setDisabled(true);
		this.labelMenu.showAt(e.getXY());
	},

	onLabelOptionsClick: function() {
		if (!this.labelOpts) this.labelOpts = new Deluge.ux.LabelOptionsWindow();
		this.labelOpts.show(this.filter.getFilter());
	},

	onLabelRemoveClick: function() {
		deluge.client.label.remove(this.filter.getFilter(), {
			success: function() {
				deluge.ui.update();
			}
		});
	}
});
Deluge.registerPlugin('Label', Deluge.plugins.LabelPlugin);
