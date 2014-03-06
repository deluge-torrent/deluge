/*!
 * Deluge.Searchbar.js
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

/**
 * @class Deluge.Searchbar
 * @author bro.devel+deluge@gmail.com
 * @version 1.3
 */
Deluge.Searchbar = Ext.extend(Ext.Panel, {

    constructor: function(config) {
        config = Ext.apply({
            id: 'searchbar',
            region: 'west',
            cls: 'deluge-searchbar',
            title: _('Search'),
            layout: 'accordion',
            split: true,
            width: 200,
            width: 20,
            minSize: 100,
            collapsible: true,
            margins: '5 0 0 5',
            cmargins: '5 0 0 5'
        }, config);
        Deluge.Searchbar.superclass.constructor.call(this, config);
    },

    // private
    initComponent: function() {
        Deluge.Sidebar.superclass.initComponent.call(this);
        this.createSearchPanel();
    },

    createSearchPanel: function() {
        this.panel = new Deluge.SearchPanel();
        this.add(this.panel);
        this.doLayout();
    },

    getFilter: function(filter) {
        return this.panel.getSearchValue();
    },

    onFilterSelect: function(selModel, rowIndex, record) {
        deluge.ui.update();
    },

    update: function(filters) {
    }
});
