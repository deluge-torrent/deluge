/*
Script: Deluge.Sidebar.js
    Contains all objects and functions related to the statusbar, toolbar and
        sidebar.

Copyright:
    (C) Damien Churchill 2009-2010 <damoxc@gmail.com>
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

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.

*/

// These are just so gen_gettext.py will pick up the strings
// _('State')
// _('Tracker Host')

(function() {
    // Renderer for the items in the filter grids.
    function filterRenderer(value, p, r) {
        var lname = value.toLowerCase().replace('.', '_');

        var image = '';	
        if (r.store.id == 'tracker_host') {
            if (value != 'Error') {
                image = String.format('url(' + Deluge.config.base + 'tracker/{0})', value);
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

	/**
	 * @class Ext.deluge.Sidebar
	 * @author Damien Churchill <damoxc@gmail.com>
	 * @version 1.3
	 */
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
            var store = new Ext.data.ArrayStore({
                idIndex: 0,
                fields: [
                    {name: 'filter'},
                    {name: 'count'}
                ]
            });
			store.id = filter;
    
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
                border: false,
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
        
            if (Deluge.config['sidebar_show_zero'] == false) {
                states = this.removeZero(states);
            }
        
            store.loadData(states);
            this.add(panel);
        
            this.doLayout();
            this.panels[filter] = panel;
        
			panel.getSelectionModel().selectFirstRow();
        },
    
        getFilters: function() {
            var filters = {}

			// Grab the filters from each of the filter panels
			this.items.each(function(panel) {
				var sm = panel.getSelectionModel();

				if (!sm.hasSelection()) return;
				
				var filter = sm.getSelected();
				var filterType = panel.getStore().id;

				if (filter.id == "All") return;

				filters[filterType] = filter.id;
			}, this);

            return filters;
        },
    
        // private
        onDisconnect: function() {
            Ext.each(Ext.getKeys(this.panels), function(filter) {
                this.remove(filter + '-panel');
            }, this);
            this.panels = {};
            this.selected = null;
        },
    
        onFilterSelect: function(selModel, rowIndex, record) {
            Deluge.UI.update();
        },
    
        /**
        * Remove the states with zero torrents in them.
        */
        removeZero: function(states) {
            var newStates = [];
            Ext.each(states, function(state) {
                if (state[1] > 0 || state[0] == _('All')) {
                    newStates.push(state);
                }
            });
            return newStates;
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
                    this.panels[filter]
                }
            }, this);
        },
    
        updateFilter: function(filter, states) {
            if (Deluge.config['sidebar_show_zero'] == false) {
                states = this.removeZero(states);
            }
    
			var store = this.panels[filter].getStore();
			Ext.each(states, function(s, i) {
				var record = store.getAt(i);
				record.beginEdit();
				record.set('filter', s[0]);
				record.set('count', s[1]);
				record.endEdit();
				record.commit();
			}, this);
        }
    });
    Deluge.Sidebar = new Ext.deluge.Sidebar();
})();
