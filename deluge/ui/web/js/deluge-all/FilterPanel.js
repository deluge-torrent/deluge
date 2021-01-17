/**
 * Deluge.FilterPanel.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * @class Deluge.FilterPanel
 * @extends Ext.list.ListView
 */
Deluge.FilterPanel = Ext.extend(Ext.Panel, {
    autoScroll: true,

    border: false,

    show_zero: null,

    initComponent: function () {
        Deluge.FilterPanel.superclass.initComponent.call(this);
        this.filterType = this.initialConfig.filter;
        var title = '';
        if (this.filterType == 'state') {
            title = _('States');
        } else if (this.filterType == 'tracker_host') {
            title = _('Trackers');
        } else if (this.filterType == 'owner') {
            title = _('Owner');
        } else if (this.filterType == 'label') {
            title = _('Labels');
        } else {
            (title = this.filterType.replace('_', ' ')),
                (parts = title.split(' ')),
                (title = '');
            Ext.each(parts, function (p) {
                fl = p.substring(0, 1).toUpperCase();
                title += fl + p.substring(1) + ' ';
            });
        }
        this.setTitle(_(title));

        if (Deluge.FilterPanel.templates[this.filterType]) {
            var tpl = Deluge.FilterPanel.templates[this.filterType];
        } else {
            var tpl =
                '<div class="x-deluge-filter x-deluge-{filter:lowercase}">{filter} ({count})</div>';
        }

        this.list = this.add({
            xtype: 'listview',
            singleSelect: true,
            hideHeaders: true,
            reserveScrollOffset: true,
            store: new Ext.data.ArrayStore({
                idIndex: 0,
                fields: ['filter', 'count'],
            }),
            columns: [
                {
                    id: 'filter',
                    sortable: false,
                    tpl: tpl,
                    dataIndex: 'filter',
                },
            ],
        });
        this.relayEvents(this.list, ['selectionchange']);
    },

    /**
     * Return the currently selected filter state
     * @returns {String} the current filter state
     */
    getState: function () {
        if (!this.list.getSelectionCount()) return;

        var state = this.list.getSelectedRecords()[0];
        if (!state) return;
        if (state.id == 'All') return;
        return state.id;
    },

    /**
     * Return the current states in the filter
     */
    getStates: function () {
        return this.states;
    },

    /**
     * Return the Store for the ListView of the FilterPanel
     * @returns {Ext.data.Store} the ListView store
     */
    getStore: function () {
        return this.list.getStore();
    },

    /**
     * Update the states in the FilterPanel
     */
    updateStates: function (states) {
        this.states = {};
        Ext.each(
            states,
            function (state) {
                this.states[state[0]] = state[1];
            },
            this
        );

        var show_zero =
            this.show_zero == null
                ? deluge.config.sidebar_show_zero
                : this.show_zero;
        if (!show_zero) {
            var newStates = [];
            Ext.each(states, function (state) {
                if (state[1] > 0 || state[0] == 'All') {
                    newStates.push(state);
                }
            });
            states = newStates;
        }

        var store = this.getStore();
        var filters = {};
        Ext.each(
            states,
            function (s, i) {
                var record = store.getById(s[0]);
                if (!record) {
                    record = new store.recordType({
                        filter: s[0],
                        count: s[1],
                    });
                    record.id = s[0];
                    store.insert(i, record);
                }
                record.beginEdit();
                record.set('filter', _(s[0]));
                record.set('count', s[1]);
                record.endEdit();
                filters[s[0]] = true;
            },
            this
        );

        store.each(function (record) {
            if (filters[record.id]) return;
            store.remove(record);
            var selected = this.list.getSelectedRecords()[0];
            if (!selected) return;
            if (selected.id == record.id) {
                this.list.select(0);
            }
        }, this);

        store.commitChanges();

        if (!this.list.getSelectionCount()) {
            this.list.select(0);
        }
    },
});

Deluge.FilterPanel.templates = {
    tracker_host:
        '<div class="x-deluge-filter" style="background-image: url(' +
        deluge.config.base +
        'tracker/{filter});">{filter} ({count})</div>',
};
