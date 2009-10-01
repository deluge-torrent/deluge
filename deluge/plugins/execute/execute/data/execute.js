/*
Script: execute.js
    The client-side javascript code for the Execute plugin.

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

(function() {
    EVENT_MAP = {
	'complete': _('Torrent Complete'),
	'added': _('Torrent Added')
    }
    EVENTS = ['complete', 'added']
	
    ExecutePanel = Ext.extend(Ext.Panel, {
	constructor: function(config) {
	    config = Ext.apply({
		border: false,
		title: _('Execute'),
		layout: 'border'
	    }, config);
	    ExecutePanel.superclass.constructor.call(this, config);
	},
	    
	initComponent: function() {
	    ExecutePanel.superclass.initComponent.call(this);
	    this.commands = this.add({
		xtype: 'grid',
		region: 'center',
		store: new Ext.data.SimpleStore({
		    fields: [
			{name: 'event', mapping: 1},
			{name: 'name', mapping: 2}
		    ],
		    id: 0
		}),
		columns: [{
		    width: 70,
		    header: _('Event'),
		    sortable: true,
		    renderer: fplain,
		    dataIndex: 'event'
		}, {
		    id: 'name',
		    header: _('Command'),
		    sortable: true,
		    renderer: fplain,
		    dataIndex: 'name'
		}],
		stripRows: true,
		selModel: new Ext.grid.RowSelectionModel({
		    singleSelect: true
		}),
		autoExpandColumn: 'name'
	    });
		
	    this.details = this.add({
		xtype: 'tabpanel',
		region: 'south',
		activeTab: 0
	    });
	    
	    this.add = this.details.add({
		title: _('Add')
	    });
	    this.edit = this.details.add({
		title: _('Edit')
	    });
	},
	
	onShow: function() {
	    ExecutePanel.superclass.onShow.call(this);
	    Deluge.Client.execute.get_commands({
		success: function(commands) {
		    this.commands.getStore().loadData(commands);
		},
		scope: this
	    });
	}
    });
	
    ExecutePlugin = Ext.extend(Deluge.Plugin, {
	constructor: function(config) {
	    config = Ext.apply({
		    name: "Execute"
	    }, config);
	    ExecutePlugin.superclass.constructor.call(this, config);
	},
	
	onDisable: function() {
	    Deluge.Preferences.removePage(this.prefsPage);
	},
	
	onEnable: function() {
	    this.prefsPage = new ExecutePanel();
	    this.prefsPage = Deluge.Preferences.addPage(this.prefsPage);
	}
    });
    new ExecutePlugin();
})();