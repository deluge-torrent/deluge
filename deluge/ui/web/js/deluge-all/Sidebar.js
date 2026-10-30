/**
 * Deluge.Sidebar.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

// These are just so gen_gettext.py will pick up the strings
// _('State')
// _('Tracker Host')

/**
 * @class Deluge.Sidebar
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 */
Deluge.Sidebar = Ext.extend(Ext.Panel, {
    // private
    panels: {},

    // private
    selected: null,

    constructor: function (config) {
        config = Ext.apply(
            {
                id: 'sidebar',
                region: 'west',
                cls: 'deluge-sidebar',
                title: _('Filters'),
                layout: 'accordion',
                split: true,
                width: 200,
                minSize: 100,
                collapsible: true,
            },
            config
        );
        Deluge.Sidebar.superclass.constructor.call(this, config);
    },

    // private
    searchDelay: 250,

    // private
    initComponent: function () {
        this.searchField = new Ext.form.TextField({
            emptyText: _('Filter by name...'),
            enableKeyEvents: true,
            listeners: {
                keyup: this.onSearchChange,
                render: function (field) {
                    // keyup misses paste and autofill; input catches every edit.
                    field.getEl().on('input', this.onSearchChange, this);
                },
                scope: this,
            },
        });
        this.searchTask = new Ext.util.DelayedTask(deluge.ui.update, deluge.ui);
        this.tbar = [this.searchField];

        Deluge.Sidebar.superclass.initComponent.call(this);
        deluge.events.on('disconnect', this.onDisconnect, this);
        this.on('resize', this.onResize, this);
    },

    createFilter: function (filter, states) {
        var panel = new Deluge.FilterPanel({
            filter: filter,
        });
        panel.on('selectionchange', function (view, nodes) {
            deluge.ui.update();
        });
        this.add(panel);

        this.doLayout();
        this.panels[filter] = panel;

        if (panel.header) {
            panel.header.on('click', function (header) {
                if (!deluge.config.sidebar_multiple_filters) {
                    deluge.ui.update();
                }
                if (!panel.list.getSelectionCount()) {
                    panel.list.select(0);
                }
            });
        }
        this.fireEvent('filtercreate', this, panel);

        panel.updateStates(states);
        this.fireEvent('afterfiltercreate', this, panel);
    },

    getFilter: function (filter) {
        return this.panels[filter];
    },

    getFilterStates: function () {
        var states = {};

        if (deluge.config.sidebar_multiple_filters) {
            // Grab the filters from each of the filter panels
            this.items.each(function (panel) {
                var state = panel.getState();
                if (state == null) return;
                states[panel.filterType] = state;
            }, this);
        } else {
            var panel = this.getLayout().activeItem;
            if (panel) {
                var state = panel.getState();
                if (!state == null) return;
                states[panel.filterType] = state;
            }
        }

        // The name search sits outside the accordion so it always applies.
        var search = this.searchField.getValue();
        if (search) {
            states['name'] = search;
        }

        return states;
    },

    hasFilter: function (filter) {
        return this.panels[filter] ? true : false;
    },

    // private
    onDisconnect: function () {
        for (var filter in this.panels) {
            this.remove(this.panels[filter]);
        }
        this.panels = {};
        this.selected = null;
    },

    onFilterSelect: function (selModel, rowIndex, record) {
        deluge.ui.update();
    },

    // private
    onResize: function (panel, adjWidth) {
        if (Ext.isNumber(adjWidth)) {
            this.searchField.setWidth(adjWidth - 6);
        }
    },

    // private
    onSearchChange: function () {
        this.deselectNonMatching();
        this.searchTask.delay(this.searchDelay);
    },

    // The torrent grid only drops non-matching torrents after the next
    // server update. Until then they are still shown and may be selected,
    // so deselect them now to keep actions such as remove from reaching
    // torrents that are being filtered out.
    deselectNonMatching: function () {
        var search = this.searchField.getValue().toLowerCase();
        if (!search) return;

        var store = deluge.torrents.getStore();
        var selModel = deluge.torrents.getSelectionModel();
        Ext.each(selModel.getSelections(), function (record) {
            var name = (record.get('name') || '').toLowerCase();
            if (name.indexOf(search) == -1) {
                selModel.deselectRow(store.indexOf(record));
            }
        });
    },

    update: function (filters) {
        for (var filter in filters) {
            var states = filters[filter];
            if (Ext.getKeys(this.panels).indexOf(filter) > -1) {
                this.panels[filter].updateStates(states);
            } else {
                this.createFilter(filter, states);
            }
        }

        // Perform a cleanup of fitlers that are not enabled any more.
        Ext.each(
            Ext.keys(this.panels),
            function (filter) {
                if (Ext.keys(filters).indexOf(filter) == -1) {
                    // We need to remove the panel
                    this.remove(this.panels[filter]);
                    this.doLayout();
                    delete this.panels[filter];
                }
            },
            this
        );
    },
});
