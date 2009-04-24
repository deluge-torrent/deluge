/*
Script: deluge-bars.js
    Contains all objects and functions related to the statusbar, toolbar and
	sidebar.

Copyright:
	(C) Damien Churchill 2009 <damoxc@gmail.com>
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, write to:
		The Free Software Foundation, Inc.,
		51 Franklin Street, Fifth Floor
		Boston, MA  02110-1301, USA.
*/

// These are just so gen_gettext.js will pick up the strings
// _('State')
// _('Tracker Host')

(function() {
	// Renderer for the items in the filter grids.
	function filterRenderer(value, p, r) {
		var lname = value.toLowerCase().replace('.', '_');
		
		var image = '';	
		if (r.store.id == 'tracker_host') {
			if (value != 'Error') {
				image = String.format('url(/tracker/{0})', value);
			} else {
				lname = null;
			}
		}
		if (image) {
			return String.format('<div class="x-deluge-filter" style="background-image: {2};">{0} ({1})</div>', value, r.data['count'], image);
		} else if (lname) {
			return String.format('<div class="x-deluge-filter x-deluge-{2}">{0} ({1})</div>', value, r.data['count'], lname);
		} else {
			return String.format('<div class="x-deluge-filter">{0} ({1})</div>', value, r.data['count']);
		}
	}
	
	Ext.deluge.Sidebar = Ext.extend(Ext.Panel, {
		
		// private
		panels: {},
		
		// private
		selected: null,
		
		constructor: function(config) {
			config = Ext.apply({
				id: 'sidebar',
				region: 'west',
				cls: 'deluge-sidebar',
				title: _('Filters'),
				layout: 'accordion',
				split: true,
				width: 200,
				minSize: 175,
				collapsible: true,
				margins: '5 0 0 5',
				cmargins: '5 0 0 5'
			}, config);
			Ext.deluge.Sidebar.superclass.constructor.call(this, config);
		},
		
		// private
		initComponent: function() {
			Ext.deluge.Sidebar.superclass.initComponent.call(this);
			Deluge.Events.on("disconnect", this.onDisconnect, this);
		},
		
		createFilter: function(filter, states) {
			var store = new Ext.data.SimpleStore({
				id: filter,
				fields: [
					{name: 'filter'},
					{name: 'count'}
				]
			});
			
			var title = filter.replace('_', ' ');
			var parts = title.split(' ');
			title = '';
			Ext.each(parts, function(part) {
				firstLetter = part.substring(0, 1);
				firstLetter = firstLetter.toUpperCase();
				part = firstLetter + part.substring(1);
				title += part + ' ';
			});
			
			var panel = new Ext.grid.GridPanel({
				id: filter + '-panel',
				store: store,
				title: _(title),
				columns: [
					{id: 'filter', sortable: false, renderer: filterRenderer, dataIndex: 'filter'}
				],	
				stripeRows: false,
				selModel: new Ext.grid.RowSelectionModel({
					singleSelect: true,
					listeners: {
						'rowselect': {fn: this.onFilterSelect, scope: this}
					}
				}),
				hideHeaders: true,
				autoExpandColumn: 'filter',
				deferredRender: false,
				autoScroll: true
			});
			store.loadData(states);
			this.add(panel);
			
			this.doLayout();
			this.panels[filter] = panel;
			
			if (!this.selected) {
				panel.getSelectionModel().selectFirstRow();
				this.selected = {
					row: 0,
					filter: states[0][0],
					panel: panel
				}
			}
		},
		
		getFilters: function() {
			var filters = {}
			if (!this.selected) {
				return filters;
			}
			if (!this.selected.filter || !this.selected.panel) {
				return filters;
			}
			var filterType = this.selected.panel.store.id;
			if (filterType == "state" && this.selected.filter == "All") {
				return filters;
			}
			
			filters[filterType] = this.selected.filter;
			return filters;
		},
		
		// private
		onDisconnect: function() {
			Ext.each(Ext.getKeys(this.panels), function(filter) {
				this.remove(filter + '-panel');
			}, this);
			this.panels.empty();
			this.selected = null;
		},
		
		onFilterSelect: function(selModel, rowIndex, record) {
			if (!this.selected) needsUpdate = true;
			else if (this.selected.row != rowIndex) needsUpdate = true;
			else needsUpdate = false;
			this.selected = {
				row: rowIndex,
				filter: record.get('filter'),
				panel: this.panels[record.store.id]
			}
			
			if (needsUpdate) Deluge.UI.update();
		},
		
		update: function(filters) {
			for (var filter in filters) {
				var states = filters[filter];
				if (Ext.getKeys(this.panels).indexOf(filter) > -1) {
					this.updateFilter(filter, states);
				} else {
					this.createFilter(filter, states);
				}
			}
			
			// Perform a cleanup of fitlers that aren't enabled any more
			Ext.each(Ext.keys(this.panels), function(filter) {
				if (Ext.keys(filters).indexOf(filter) == -1) {
					// We need to remove the panel
				}
			});
		},
		
		updateFilter: function(filter, states) {
			this.panels[filter].store.loadData(states);
			if (this.selected && this.selected.panel == this.panels[filter]) {
				this.panels[filter].getSelectionModel().selectRow(this.selected.row);
			}
		}
		
	});
	Deluge.Sidebar = new Ext.deluge.Sidebar();
})();