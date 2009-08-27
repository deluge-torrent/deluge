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
				}, {
					cls: 'x-btn-text-icon',
					text: _('Rescan'),
					handler: this.onRescanPlugins,
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
		this.grid.on('cellclick', this.onCellClick, this);
		Deluge.Preferences.on('show', this.onPreferencesShow, this);
	},
	
	disablePlugin: function(plugin) {
		Deluge.Client.core.disable_plugin(plugin);
	},
	
	enablePlugin: function(plugin) {
		Deluge.Client.core.enable_plugin(plugin);
	},
	
	setInfo: function(plugin) {
		var values = plugin || this.defaultValues;
		this.pluginInfo.body.dom.innerHTML = this.pluginTemplate.apply(values);
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
	
	onGotAvailablePlugins: function(plugins) {
		this.availablePlugins = plugins;
		Deluge.Client.core.get_enabled_plugins({
			success: this.onGotEnabledPlugins,
			scope: this
		});
	},
	
	onGotEnabledPlugins: function(plugins) {
		this.enabledPlugins = plugins;
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
	
	onPluginSelect: function(selmodel, rowIndex, r) {
		Deluge.Client.web.get_plugin_info(r.get('plugin'), {
			success: this.onGotPluginInfo,
			scope: this
		});
	},
	
	onPreferencesShow: function() {
		Deluge.Client.core.get_available_plugins({
			success: this.onGotAvailablePlugins,
			scope: this
		});
	},
	
	onShow: function() {
		Ext.deluge.preferences.Plugins.superclass.onShow.call(this);
		this.setInfo();
		var plugins = [];
		Ext.each(this.availablePlugins, function(plugin) {
			if (this.enabledPlugins.indexOf(plugin) > -1) {
				plugins.push([true, plugin]);
			} else {
				plugins.push([false, plugin]);
			}
		}, this);
		this.grid.getStore().loadData(plugins);
	}
});
Deluge.Preferences.addPage(new Ext.deluge.preferences.Plugins());