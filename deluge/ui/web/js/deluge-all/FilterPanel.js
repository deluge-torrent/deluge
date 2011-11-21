/*!
 * Deluge.FilterPanel.js
 *
 * Copyright (c) Damien Churchill 2009-2011 <damoxc@gmail.com>
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

/**
 * @class Deluge.FilterPanel
 * @extends Ext.panel.Panel
 */
Ext.define('Deluge.FilterPanel', {
    extend: 'Ext.panel.Panel',

    autoScroll: true,
    border: false,
    show_zero: null,
    title: ' ',

    initComponent: function() {
        this.callParent(arguments);
        this.filterType = this.initialConfig.filter;

        this.on('activate', function() {
            console.log('activate');
        });

        this.on('show', function() {
            console.log('show');
        });

        this.on('render', function() {
            console.log('render');
        });

        var title = this.filterType.replace('_', ' '),
            parts = title.split(' '),
            title = '';
        Ext.each(parts, function(p) {
            fl = p.substring(0, 1).toUpperCase();
            title += fl + p.substring(1) + ' ';
        });
        this.title = _(title);

        if (Deluge.FilterPanel.templates[this.filterType]) {
            var tpl = Deluge.FilterPanel.templates[this.filterType];
        } else {
            var tpl = '<div class="x-deluge-filter x-deluge-{filter:lowercase}">{filter} ({count})</div>';
        }

        this.grid = this.add({
            xtype: 'grid',
            border: false,
            singleSelect: true,
            hideHeaders: true,
            reserveScrollOffset: true,
            store: Ext.create('Ext.data.Store', {
                model: 'Deluge.data.Filter',
                proxy: {
                    type: 'memory'
                }
            }),
            columns: [{
                xtype: 'templatecolumn',
                sortable: false,
                tpl: tpl,
                dataIndex: 'filter',
                flex: 1
            }]
        });
        this.relayEvents(this.grid, ['selectionchange']);
    },

    getSelectionModel: function() {
        return this.grid.getSelectionModel();
    },

    /**
     * Return the currently selected filter state
     * @returns {String} the current filter state
     */
    getState: function() {
        var sm = this.grid.getSelectionModel()
        if (!sm.hasSelection()) return;

        var state = sm.getLastSelected(),
            stateId = state.getId();
        if (stateId == 'All') return;
        return stateId;
    },

    /**
     * Return the current states in the filter
     */
    getStates: function() {
        return this.states;
    },

    /**
     * Return the Store for the ListView of the FilterPanel
     * @returns {Ext.data.Store} the ListView store
     */
    getStore: function() {
        return this.grid.getStore();
    },

    /**
     * Update the states in the FilterPanel
     */
    updateStates: function(states) {
        this.states = {};
        Ext.each(states, function(state) {
            this.states[state[0]] = state[1];
        }, this);

        var show_zero = (this.show_zero == null) ? deluge.config.sidebar_show_zero : this.show_zero;
        if (!show_zero) {
            var newStates = [];
            Ext.each(states, function(state) {
                if (state[1] > 0 || state[0] == _('All')) {
                    newStates.push(state);
                }
            });
            states = newStates;
        }

        var store = this.getStore(),
            sm = this.grid.getSelectionModel(),
            filters = {};
        Ext.each(states, function(s, i) {
            var record = store.getById(s[0]);
            if (!record) {
                record = Ext.create('Deluge.data.Filter', {
                    filter: s[0],
                    count: [1]
                });
                record.setId(s[0]);
                store.insert(i, [record]);
            } else {
                record.beginEdit();
                record.set('filter', s[0]);
                record.set('count', s[1]);
                record.endEdit();
            }
            filters[s[0]] = true;
        }, this);

        store.each(function(record) {
            if (filters[record.getId()]) return;
            var r = sm.getLastSelected();
            store.remove(record);
            if (r === undefined)
                return;
            if (r.getId() == record.getId()) {
                sm.select(0);
            }
        }, this);

        store.sync();

        if (!sm.hasSelection()) {
            //sm.select(0);
        }
    }
});

Deluge.FilterPanel.templates = {
    'tracker_host':  '<div class="x-deluge-filter" style="background-image: url(' + deluge.config.base + 'tracker/{filter});">{filter} ({count})</div>'
}
