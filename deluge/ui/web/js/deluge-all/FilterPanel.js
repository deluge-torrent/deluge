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

/**
 * @class Deluge.TextFilterPanel
 * @extends Ext.Panel
 *
 * A sidebar filter panel that renders a debounced text input instead of a
 * list of (value, count) rows. Used for free-text filters such as 'keyword'
 * and 'name' that have no enumerable values to display.
 *
 * Public interface mirrors Deluge.FilterPanel so Sidebar can treat both
 * types uniformly:
 *   filterType  {String}  — the filter key (e.g. 'name', 'keyword')
 *   getState()  {String|null} — current text value, or null when blank
 *   updateStates(states) — no-op (no count list to render)
 *   fires 'selectionchange' when the value changes (after 350 ms debounce)
 */
Deluge.TextFilterPanel = Ext.extend(Ext.Panel, {
    border: false,

    initComponent: function () {
        Deluge.TextFilterPanel.superclass.initComponent.call(this);
        this.filterType = this.initialConfig.filter;

        var title = this.filterType.replace(/_/g, ' ');
        title = title.replace(/\b\w/g, function (c) {
            return c.toUpperCase();
        });
        this.setTitle(_(title));

        // Add the field config — it is not instantiated until render time in
        // ExtJS 3, so this.field must be retrieved in afterrender.
        this.add({
            xtype: 'textfield',
            emptyText: _('Filter...'),
            enableKeyEvents: true,
            style: { margin: '4px' },
            width: '90%',
        });

        this.on('afterrender', function () {
            this.field = this.items.get(0);

            var DEBOUNCE_MS = 350;
            var debounceTimer = null;
            var fireChange = function () {
                this.fireEvent('selectionchange', this);
            }.createDelegate(this);

            this.field.on('keyup', function () {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(fireChange, DEBOUNCE_MS);
            });
        }, this);
    },

    /**
     * Returns the current text value, or null when the field is empty.
     * Returns null before render (field not yet instantiated).
     */
    getState: function () {
        if (!this.field) return null;
        var val = this.field.getValue();
        return val && val.length > 0 ? val : null;
    },

    /** No-op — text panels have no enumerable states to update. */
    updateStates: function (states) {},
});

Deluge.FilterPanel.templates = {
    tracker_host:
        '<div class="x-deluge-filter" style="background-image: url(' +
        deluge.config.base +
        'tracker/{filter});">{filter:htmlEncode} ({count})</div>',
};
