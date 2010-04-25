/*!
 * Deluge.FilterPanel.js
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
Ext.ns('Deluge');

/**
 * @class Deluge.FilterPanel
 * @extends Ext.list.ListView
 */
Deluge.FilterPanel = Ext.extend(Ext.Panel, {
	
	border: false,

	initComponent: function() {
		Deluge.FilterPanel.superclass.initComponent.call(this);
		this.filterType = this.initialConfig.filter;

		var title = this.filterType.replace('_', ' '),
			parts = title.split(' '),
			title = '';
		Ext.each(parts, function(p) {
			fl = p.substring(0, 1).toUpperCase();
			title += fl + p.substring(1) + ' ';
		});
		this.setTitle(_(title));

		if (Deluge.FilterPanel.templates[this.filterType]) {
			var tpl = Deluge.FilterPanel.templates[this.filterType];
		} else {
			var tpl = '<div class="x-deluge-filter x-deluge-{filter:lowercase}">{filter} ({count})</div>';
		}

		this.list = this.add({
			xtype: 'listview',
			singleSelect: true,
			hideHeaders: true,
			reserveScrollOffset: true,
			store: new Ext.data.ArrayStore({
				idIndex: 0,
				fields: ['filter', 'count']
			}),
			columns: [{
				id: 'filter',
				sortable: false,
				tpl: tpl,
				dataIndex: 'filter'
			}]
		});
		this.relayEvents(this.list, ['selectionchange']);
		this.list.afterMethod('bindStore', this.doBindStore, this);
	},

	// private
	doBindStore: function() {
		this.list.select(0);
	},

	/**
	 * Return the currently selected filter
	 * @returns {String} the current filter
	 */
	getFilter: function() {
		if (!this.list.getSelectionCount()) return;

		var filter = this.list.getSelectedRecords()[0];
		if (filter.id == 'All') return;
		return filter.id;
	},

	/**
	 * Return the Store for the ListView of the FilterPanel
	 * @returns {Ext.data.Store} the ListView store
	 */
	getStore: function() {
		return this.list.getStore();
	}
});

Deluge.FilterPanel.templates = {
	'tracker_host':  '<div class="x-deluge-filter" style="background-image: url(' + deluge.config.base + 'tracker/{filter});">{filter} ({count})</div>'
}
