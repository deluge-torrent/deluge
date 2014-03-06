/*!
 * Deluge.SearchPanel.js
 *
 * Copyright (c) bendikro 2015 <bro.devel+deluge@gmail.com>
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
 * @class Deluge.SearchPanel
 * @extends Ext.list.ListView
 */
Deluge.SearchPanel = Ext.extend(Ext.Panel, {
    autoScroll: true,
    border: false,
    show_zero: null,

    initComponent: function() {
        Deluge.SearchPanel.superclass.initComponent.call(this);
        this.filterType = this.initialConfig.filter;
        this.setTitle('');

        if (Deluge.SearchPanel.templates[this.filterType]) {
            var tpl = Deluge.SearchPanel.templates[this.filterType];
        } else {
            var tpl = '<div class="x-deluge-filter x-deluge-{filter:lowercase}">{filter} ({count})</div>';
        }

        this.textfield = this.add({
            xtype:'textfield',
            name:'Search',
            fieldLabel:'Name',
            id:'search-field',
            listeners: {
                specialkey: function(f,e) {
                    if (e.getKey() == e.ENTER) {
                        deluge.ui.update();
                    }
                }
            }
        });
    },

    getSearchValue: function() {
        return Ext.getCmp('search-field').getValue();
    },

});

Deluge.SearchPanel.templates = {
    'tracker_host':  '<div class="x-deluge-filter" style="background-image: url(' + deluge.config.base + 'tracker/{filter});">{filter} ({count})</div>'
}
