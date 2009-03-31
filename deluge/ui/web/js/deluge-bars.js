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

Deluge.ToolBar = {
	connected_buttons: [
		'create', 'add', 'remove', 'pause', 'resume', 'up', 'down'
	],
	
	onTorrentAdd: function() {
		Deluge.Add.Window.show();
	},
	
	onConnect: function() {
		$each(this.connected_buttons, function(button_id) {
			this.Bar.items.get(button_id).enable();
		}, this);
	},
	
	onDisconnect: function() {
		$each(this.connected_buttons, function(button_id) {
			this.Bar.items.get(button_id).disable();
		}, this);
	},
	
	onLogin: function() {
		this.Bar.items.get('logout').enable();
	},
	
	onLogout: function() {
		this.Bar.items.get('logout').disable();
		Deluge.Events.fire('logout');
		Deluge.Login.Window.show();
	},
	
	onConnectionManagerClick: function(item) {
		Deluge.Connections.Window.show();
	},
	
	onTorrentAction: function(item) {
		var selection = Deluge.Torrents.getSelections();
		var ids = new Array();
		$each(selection, function(record) {
			ids.include(record.id);
		});
		
		switch (item.id) {
			case 'remove':
				Deluge.Client.core.remove_torrent(ids, null, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
			case 'pause':
			case 'resume':
				Deluge.Client.core[item.id + '_torrent'](ids, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
			case 'up':
			case 'down':
				Deluge.Client.core['queue_' + item.id](ids, {
					onSuccess: function() {
						Deluge.Ui.update();
					}
				});
				break;
		}
	},
	
	onToolbarRender: function(toolbar) {
		Deluge.Events.on('connect', this.onConnect.bindWithEvent(this));
		Deluge.Events.on('login', this.onLogin.bindWithEvent(this));
	}
}

Deluge.ToolBar.Bar = new Ext.Toolbar({
	items: [
		{
			id: 'create',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Create'),
			icon: '/icons/create.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'add',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Add'),
			icon: '/icons/add.png',
			handler: Deluge.ToolBar.onTorrentAdd
		},{
			id: 'remove',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Remove'),
			icon: '/icons/remove.png',
			handler: Deluge.ToolBar.onTorrentAction
		},'|',{
			id: 'pause',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Pause'),
			icon: '/icons/pause.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'resume',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Resume'),
			icon: '/icons/start.png',
			handler: Deluge.ToolBar.onTorrentAction
		},'|',{
			id: 'up',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Up'),
			icon: '/icons/up.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'down',
			cls: 'x-btn-text-icon',
			disabled: true,
			text: _('Down'),
			icon: '/icons/down.png',
			handler: Deluge.ToolBar.onTorrentAction
		},'|',{
			id: 'preferences',
			cls: 'x-btn-text-icon',
			text: _('Preferences'),
			icon: '/icons/preferences.png',
			handler: Deluge.ToolBar.onTorrentAction
		},{
			id: 'connectionman',
			cls: 'x-btn-text-icon',
			text: _('Connection Manager'),
			iconCls: 'x-deluge-connections',
			handler: Deluge.ToolBar.onConnectionManagerClick,
			scope: Deluge.ToolBar
		},'->',{
			id: 'help',
			cls: 'x-btn-text-icon',
			disabled: true,
			icon: '/icons/help.png',
			text: _('Help'),
			handler: Deluge.ToolBar.onHelpClick,
			scope: Deluge.ToolBar
		},{
			id: 'logout',
			cls: 'x-btn-text-icon',
			icon: '/icons/logout.png',
			disabled: true,
			text: _('Logout'),
			handler: Deluge.ToolBar.onLogout,
			scope: Deluge.ToolBar
		}
	],		
	listeners: {'render': Deluge.ToolBar.onToolbarRender, scope: Deluge.ToolBar}
});

Deluge.StatusBar = {
	onRender: function() {
		this.bound = {
			onConnect: this.onConnect.bindWithEvent(this),
			onDisconnect: this.onDisconnect.bindWithEvent(this)
		}
		
		Deluge.Events.on('connect', this.bound.onConnect);
		Deluge.Events.on('disconnect', this.bound.onDisconnect);
	},
	
	createButtons: function() {
		this.Bar.add({
			id: 'statusbar-connections',
			text: '200 (200)',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-connections',
			menu: Deluge.Menus.Connections
		}, '-', {
			id: 'statusbar-downspeed',
			text: '9.8KiB/s (30 KiB/s)',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-downloading',
			menu: Deluge.Menus.Download
		}, '-', {
			id: 'statusbar-upspeed',
			text: '9.8KiB/s (30 KiB/s)',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-seeding',
			menu: Deluge.Menus.Upload
		}, '-', {
			id: 'statusbar-traffic',
			text: '1.53/2,65 KiB/s',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-traffic'
		}, '-', {
			id: 'statusbar-dht',
			text: '161',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-dht'
		});
		this.created = true;
	},
	
	onConnect: function() {
		this.Bar.setStatus({
			iconCls: 'x-connected',
			text: ''
		});
		if (!this.created) this.createButtons();
		else {
			this.Bar.items.each(function(item) {
				item.show();
				item.enable();
			});
		}
	},
	
	onDisconnect: function() {
		this.Bar.clearStatus({useDefaults:true});
		this.Bar.items.each(function(item) {
			item.hide();
			item.disable();
		});
	},
	
	update: function(stats) {
		function addSpeed(val) {return val + ' KiB/s'}
		
		var updateStat = function(name, config) {
			var item = this.Bar.items.get('statusbar-' + name);
			if (config.limit.value == -1) {
				var str = (config.value.formatter) ? config.value.formatter(config.value.value) : config.value.value;
			} else {
				var value = (config.value.formatter) ? config.value.formatter(config.value.value) : config.value.value;
				var limit = (config.limit.formatter) ? config.limit.formatter(config.limit.value) : config.limit.value;
				var str = String.format(config.format, value, limit);
			}
			item.setText(str);
		}.bind(this);
		
		updateStat('connections', {
			value: {value: stats.num_connections},
			limit: {value: stats.max_num_connections},
			format: '{0} ({1})'
		});

		updateStat('downspeed', {
			value: {
				value: stats.download_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_download,
				formatter: addSpeed
			},
			format: '{0} ({1})'
		});

		updateStat('upspeed', {
			value: {
				value: stats.upload_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_upload,
				formatter: addSpeed
			},
			format: '{0} ({1})'
		});
		
		updateStat('traffic', {
			value: {
				value: stats.payload_download_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.payload_upload_rate,
				formatter: Deluge.Formatters.speed
			},
			format: '{0}/{1}'
		});

		this.Bar.items.get('statusbar-dht').setText(stats.dht_nodes);

		function updateMenu(menu, stat) {
			var item = menu.items.get(stat)
			if (!item) {
				item = menu.items.get('other')
			}
			item.setChecked(true);
		}
		
		updateMenu(Deluge.Menus.Connections, stats.max_num_connections);
		updateMenu(Deluge.Menus.Download, stats.max_download);
		updateMenu(Deluge.Menus.Upload, stats.max_upload);
	}
}

Deluge.StatusBar.Bar = new Ext.StatusBar({
	id: 'deluge-statusbar',
	defaultIconCls: 'x-not-connected',
	defaultText: _('Not Connected'),
	listeners: {'render': {scope: Deluge.StatusBar, fn: Deluge.StatusBar.onRender}}
});

Deluge.SideBar = {
	panels: new Hash(),
	
	onRender: function(bar) {
		this.Bar = bar;
		Deluge.Events.on("disconnect", this.onDisconnect.bindWithEvent(this));
		this.selected = null;
	},
	
	onDisconnect: function() {
		this.panels.getKeys().each(function(el) {
			this.Bar.remove(el + '-panel');
		}, this);
		this.panels.empty();
		this.selected = null;
	},
	
	renderer: function(value, p, r) {
		var lname = value.toLowerCase().replace('.', '_');
		
		var image = '';		
		if (r.store.id == 'tracker_host') {
			if (value != 'Error') {
				image = String.format('url(/tracker/{0})', value);
			}
		}
		return String.format('<div class="x-deluge-filter x-deluge-{2}" style="background-image: {3};">{0} ({1})</div>', value, r.data['count'], lname, image);
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
	
	update: function(filters) {
		filters = new Hash(filters);
		filters.each(function(states, filter) {
			if (this.panels.has(filter)) {
				this.updateFilter(filter, states);
			} else {
				this.createFilter(filter, states);
			}
		}, this);
		
		// Perform a cleanup of fitlers that aren't enabled any more
		$each(this.panels.getKeys(), function(filter) {
			if (!filters.has(filter)) {
				// We need to remove the panel
			}
		});
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
        parts.each(function(part) {
            firstLetter = part.substring(0, 1);
            firstLetter = firstLetter.toUpperCase();
            part = firstLetter + part.substring(1);
            title += part + ' ';
        });
		
		var panel = new Ext.grid.GridPanel({
			id: filter + '-panel',
			store: store,
			title: title,
			columns: [
				{id: 'filter', sortable: false, renderer: this.renderer, dataIndex: 'filter'}
			],	
			stripeRows: false,
			selModel: new Ext.grid.RowSelectionModel({
				singleSelect: true,
				listeners: {
					'rowselect': this.onSelect.bindWithEvent(this)
				}
			}),
			hideHeaders: true,
			autoExpandColumn: 'filter',
			deferredRender: false,
			autoScroll: true,
			margins: '5 5 5 5'
		});
		store.loadData(states);
		this.Bar.add(panel);
		
		this.Bar.doLayout();
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
	
	onSelect: function(selModel, rowIndex, record) {
		if (!this.selected) needsUpdate = true;
		else if (this.selected.row != rowIndex) needsUpdate = true;
		else needsUpdate = false;
		this.selected = {
			row: rowIndex,
			filter: record.get('filter'),
			panel: this.panels[record.store.id]
		}
		
		if (needsUpdate) Deluge.Ui.update();
	},
	
	updateFilter: function(filter, states) {
		this.panels[filter].store.loadData(states);
		if (this.selected && this.selected.panel == this.panels[filter]) {
			this.panels[filter].getSelectionModel().selectRow(this.selected.row);
		}
	}
};

Deluge.SideBar.Config = {
	region: 'west',
	id: 'sidebar',
	cls: 'deluge-sidebar',
	title: _('Filters'),
	layout: 'accordion',
	split: true,
	width: 200,
	minSize: 175,
	collapsible: true,
	margins: '5 0 0 5',
	listeners: {'render': {scope: Deluge.SideBar, fn: Deluge.SideBar.onRender}}
}