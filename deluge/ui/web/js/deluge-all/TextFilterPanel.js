/**
 * Deluge.TextFilterPanel.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * @class Deluge.TextFilterPanel
 * @extends Ext.Panel
 *
 * A sidebar filter panel that renders a debounced text input instead of a
 * list of (value, count) rows. Used for free-text filters such as 'keyword'
 * and 'name' that have no enumerable values to display. Debounce is used
 * to avoid excessive UI updates while the user is typing when there are a
 * large number of torrents.
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

        // Currently the only text filters are 'name' and 'keyword', this is
        // included to mirror current FilterPanel behavior of title-casing filter names
        var title = this.filterType.replace(/_/g, ' ');
        title = title.replace(/\b\w/g, function (c) {
            return c.toUpperCase();
        });
        this.setTitle(_(title));

        this.add({
            xtype: 'textfield',
            emptyText: _('Filter...'),
            enableKeyEvents: true,
            style: { margin: '4px' },
            width: '90%',
        });

        this.on(
            'afterrender',
            function () {
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
            },
            this
        );
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
