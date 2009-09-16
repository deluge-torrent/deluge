/*
Script: Deluge.Preferences.Plugins.js
	The plugins preferences page.

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

Ext.namespace('Ext.deluge.preferences');
Ext.deluge.preferences.Plugins = Ext.extend(Ext.Panel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Plugins'),
			layout: 'border',
			height: 400,
			cls: 'x-deluge-plugins'
		}, config);
		Ext.deluge.preferences.Plugins.superclass.constructor.call(this, config);
	},

	pluginTemplate: new Ext.Template(
		'<dl class="singleline">' +
			'<dt>Author:</dt><dd>{author}</dd>' +
			'<dt>Version:</dt><dd>{version}</dd>' +
			'<dt>Author Email:</dt><dd>{email}</dd>' +
			'<dt>Homepage:</dt><dd>{homepage}</dd>' +
			'<dt>Details:</dt><dd>{details}</dd>' +
		'</dl>'
	),

	initComponent: function() {
		Ext.deluge.preferences.Plugins.superclass.initComponent.call(this);
		this.defaultValues = {
			'version': '',
			'email': '',
			'homepage': '',
			'details': ''
		};
		this.pluginTemplate.compile();

		var checkboxRenderer = function(v, p, record){
			p.css += ' x-grid3-check-col-td'; 
			return '<div class="x-grid3-check-col'+(v?'-on':'')+'"> </div>';
		}
	
		this.grid = this.add({
			xtype: 'grid',
			region: 'center',
			store: new Ext.data.SimpleStore({
				fields: [
					{name: 'enabled', mapping: 0},
					{name: 'plugin', mapping: 1}
				]
			}),
			columns: [{
				id: 'enabled',
				header: _('Enabled'),
				width: 50,
				sortable: true,
				renderer: checkboxRenderer,
				dataIndex: 'enabled'
			}, {
				id: 'plugin',
				header: _('Plugin'),
				sortable: true,
				dataIndex: 'plugin'
			}],	
			stripeRows: true,
			selModel: new Ext.grid.RowSelectionModel({
				singleSelect: true,
				listeners: {
					'rowselect': {
						fn: this.onPluginSelect,
						scope: this
					}
				}
			}),
			autoExpandColumn: 'plugin',
			deferredRender: false,
			autoScroll: true,
			margins: '5 5 5 5',
			bbar: new Ext.Toolbar({
				items: [{
					cls: 'x-btn-text-icon',
					iconCls: 'x-deluge-add',
					text: _('Install'),
					handler: this.onInstallPlugin,
					scope: this
				}, '->', {
					cls: 'x-btn-text-icon',
					text: _('Find More'),
					handler: this.onFindMorePlugins,
					scope: this
				}]
			})
		});
	
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			region: 'south',
			title: _('Info'),
			autoHeight: true,
			labelWidth: 1
		});
		this.pluginInfo = fieldset.add({
			xtype: 'panel',
			border: false,
			bodyCfg: {
				style: 'margin-left: 10px'
			}
		});
	
		this.on('show', this.onShow, this);
		this.pluginInfo.on('render', this.onPluginInfoRender, this);
		this.grid.on('cellclick', this.onCellClick, this);
		Deluge.Preferences.on('show', this.onPreferencesShow, this);
		Deluge.Events.on('PluginDisabledEvent', this.onPluginDisabled, this);
		Deluge.Events.on('PluginEnabledEvent', this.onPluginsEnabled, this);
	},

	disablePlugin: function(plugin) {
		Deluge.Client.core.disable_plugin(plugin);
	},

	enablePlugin: function(plugin) {
		Deluge.Client.core.enable_plugin(plugin);
	},

	setInfo: function(plugin) {
		if (!this.pluginInfo.rendered) return;
		var values = plugin || this.defaultValues;
		this.pluginInfo.body.dom.innerHTML = this.pluginTemplate.apply(values);
	},
	
	updatePlugins: function() {
		Deluge.Client.web.get_plugins({
			success: this.onGotPlugins,
			scope: this
		});
	},

	updatePluginsGrid: function() {
		var plugins = [];
		Ext.each(this.availablePlugins, function(plugin) {
			if (this.enabledPlugins.indexOf(plugin) > -1) {
				plugins.push([true, plugin]);
			} else {
				plugins.push([false, plugin]);
			}
		}, this);
		this.grid.getStore().loadData(plugins);
	},

	onCellClick: function(grid, rowIndex, colIndex, e) {
		if (colIndex != 0) return;
		var r = grid.getStore().getAt(rowIndex);
		r.set('enabled', !r.get('enabled'));
		r.commit();
		if (r.get('enabled')) {
			this.enablePlugin(r.get('plugin'));
		} else {
			this.disablePlugin(r.get('plugin'));
		}
	},

	onFindMorePlugins: function() {
		window.open('http://dev.deluge-torrent.org/wiki/Plugins');
	},

	onGotPlugins: function(plugins) {
		this.enabledPlugins = plugins.enabled_plugins;
		this.availablePlugins = plugins.available_plugins;
		this.setInfo();
		this.updatePluginsGrid();
	},

	onGotPluginInfo: function(info) {
		var values = {
			author: info['Author'],
			version: info['Version'],
			email: info['Author-email'],
			homepage: info['Home-page'],
			details: info['Description']
		}
		this.setInfo(values);
		delete info;
	},

	onPluginEnabled: function(pluginName) {
		var index = this.grid.getStore().find('plugin', pluginName);
		var plugin = this.grid.getStore().getAt(index);
		plugin.set('enabled', true);
		plugin.commit();
	},
	
	onPluginDisabled: function(pluginName) {
		var index = this.grid.getStore().find('plugin', pluginName);
		var plugin = this.grid.getStore().getAt(index);
		plugin.set('enabled', false);
		plugin.commit();
	},

	onPluginSelect: function(selmodel, rowIndex, r) {
		Deluge.Client.web.get_plugin_info(r.get('plugin'), {
			success: this.onGotPluginInfo,
			scope: this
		});
	},

	onPreferencesShow: function() {
		this.updatePlugins();
	},

	onPluginInfoRender: function(ct, position) {
		this.setInfo();
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Plugins());