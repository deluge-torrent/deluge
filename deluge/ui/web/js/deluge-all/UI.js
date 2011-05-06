/*!
 * Deluge.UI.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
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
 * @static
 * @class Deluge.UI
 * The controller for the whole interface, that ties all the components
 * together and handles the 2 second poll.
 */
deluge.ui = {

	errorCount: 0,

	filters: null,

	/**
	 * @description Create all the interface components, the json-rpc client
	 * and set up various events that the UI will utilise.
	 */
	initialize: function() {
		deluge.add = new Deluge.add.AddWindow();
		deluge.details = new Deluge.details.DetailsPanel();
		deluge.connectionManager = new Deluge.ConnectionManager();
		deluge.editTrackers = new Deluge.EditTrackersWindow();
		deluge.login = new Deluge.LoginWindow();
		deluge.preferences = new Deluge.preferences.PreferencesWindow();
		deluge.sidebar = new Deluge.Sidebar();
		deluge.statusbar = new Deluge.Statusbar();

		this.MainPanel = new Ext.Panel({
			id: 'mainPanel',
			iconCls: 'x-deluge-main-panel',
			title: 'Deluge',
			layout: 'border',
			tbar: deluge.toolbar,
			items: [
				deluge.sidebar,
				deluge.details,
				deluge.torrents
			],
			bbar: deluge.statusbar
		});

		this.Viewport = new Ext.Viewport({
			layout: 'fit',
			items: [this.MainPanel]
		});

		deluge.events.on("connect", this.onConnect, this);
		deluge.events.on("disconnect", this.onDisconnect, this);
		deluge.events.on('PluginDisabledEvent', this.onPluginDisabled, this);
		deluge.events.on('PluginEnabledEvent', this.onPluginEnabled, this);
		deluge.client = new Ext.ux.util.RpcClient({
			url: deluge.config.base + 'json'
		});

		// enable all the already active plugins
		for (var plugin in Deluge.pluginStore) {
			plugin = Deluge.createPlugin(plugin);
			plugin.enable();
			deluge.plugins[plugin.name] = plugin;
		}

		// Initialize quicktips so all the tooltip configs start working.
		Ext.QuickTips.init();

		deluge.client.on('connected', function(e) {
			deluge.login.show();
		}, this, {single: true});

		this.update = this.update.createDelegate(this);
		this.checkConnection = this.checkConnection.createDelegate(this);

		this.originalTitle = document.title;
	},

	checkConnection: function() {
		deluge.client.web.connected({
			success: this.onConnectionSuccess,
			failure: this.onConnectionError,
			scope: this
		});
	},

	update: function() {
		var filters = deluge.sidebar.getFilterStates();
		this.oldFilters = this.filters;
		this.filters = filters;

		deluge.client.web.update_ui(Deluge.Keys.Grid, filters, {
			success: this.onUpdate,
			failure: this.onUpdateError,
			scope: this
		});
		deluge.details.update();
	},

	onConnectionError: function(error) {

	},

	onConnectionSuccess: function(result) {
		deluge.statusbar.setStatus({
			iconCls: 'x-deluge-statusbar icon-ok',
			text: _('Connection restored')
		});
		clearInterval(this.checking);
		if (!result) {
			deluge.connectionManager.show();
		}
	},

	onUpdateError: function(error) {
		if (this.errorCount == 2) {
			Ext.MessageBox.show({
				title: 'Lost Connection',
				msg: 'The connection to the webserver has been lost!',
				buttons: Ext.MessageBox.OK,
				icon: Ext.MessageBox.ERROR
			});
			deluge.events.fire('disconnect');
			deluge.statusbar.setStatus({
				text: 'Lost connection to webserver'}
			);
			this.checking = setInterval(this.checkConnection, 2000);
		}
		this.errorCount++;
	},

	/**
	 * @static
	 * @private
	 * Updates the various components in the interface.
	 */
	onUpdate: function(data) {
		if (!data['connected']) {
			deluge.connectionManager.disconnect(true);
			return;
		}

		if (deluge.config.show_session_speed) {
			document.title = this.originalTitle +
				' (Down: ' + fspeed(data['stats'].download_rate, true) +
				' Up: ' + fspeed(data['stats'].upload_rate, true) + ')';
		}
		if (Ext.areObjectsEqual(this.filters, this.oldFilters)) {
			deluge.torrents.update(data['torrents']);
		} else {
			deluge.torrents.update(data['torrents'], true);
		}
		deluge.statusbar.update(data['stats']);
		deluge.sidebar.update(data['filters']);
		this.errorCount = 0;
	},

	/**
	 * @static
	 * @private
	 * Start the Deluge UI polling the server and update the interface.
	 */
	onConnect: function() {
		if (!this.running) {
			this.running = setInterval(this.update, 2000);
			this.update();
		}
		deluge.client.web.get_plugins({
			success: this.onGotPlugins,
			scope: this
		});
	},

	/**
	 * @static
	 * @private
	 */
	onDisconnect: function() {
		this.stop();
	},

	onGotPlugins: function(plugins) {
		Ext.each(plugins.enabled_plugins, function(plugin) {
			if (deluge.plugins[plugin]) return;
			deluge.client.web.get_plugin_resources(plugin, {
				success: this.onGotPluginResources,
				scope: this
			});
		}, this);
	},

	onPluginEnabled: function(pluginName) {
		if (deluge.plugins[pluginName]) {
			deluge.plugins[pluginName].enable();
		} else {
			deluge.client.web.get_plugin_resources(pluginName, {
				success: this.onGotPluginResources,
				scope: this
			});
		}
	},

	onGotPluginResources: function(resources) {
		var scripts = (Deluge.debug) ? resources.debug_scripts : resources.scripts;
		Ext.each(scripts, function(script) {
			Ext.ux.JSLoader({
				url: deluge.config.base + script,
				onLoad: this.onPluginLoaded,
				pluginName: resources.name
			});
		}, this);
	},

	onPluginDisabled: function(pluginName) {
		deluge.plugins[pluginName].disable();
	},

	onPluginLoaded: function(options) {
		// This could happen if the plugin has multiple scripts
		if (!Deluge.hasPlugin(options.pluginName)) return;

		// Enable the plugin
		plugin = Deluge.createPlugin(options.pluginName);
		plugin.enable();
		deluge.plugins[plugin.name] = plugin;
	},

	/**
	 * @static
	 * Stop the Deluge UI polling the server and clear the interface.
	 */
	stop: function() {
		if (this.running) {
			clearInterval(this.running);
			this.running = false;
			deluge.torrents.getStore().removeAll();
		}
	}
}

Ext.onReady(function(e) {
	deluge.ui.initialize();
});
