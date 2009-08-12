(function() {	
	Ext.deluge.Statusbar = Ext.extend(Ext.StatusBar, {
		constructor: function(config) {
			config = Ext.apply({
				id: 'deluge-statusbar',
				defaultIconCls: 'x-not-connected',
				defaultText: _('Not Connected')
			}, config);
			Ext.deluge.Statusbar.superclass.constructor.call(this, config);
		},
		
		initComponent: function() {
			Ext.deluge.Statusbar.superclass.initComponent.call(this);
			
			Deluge.Events.on('connect', this.onConnect, this);
			Deluge.Events.on('disconnect', this.onDisconnect, this);
		},
		
		createButtons: function() {
			this.add({
				id: 'statusbar-connections',
				text: ' ',
				cls: 'x-btn-text-icon',
				iconCls: 'x-deluge-connections',
				menu: Deluge.Menus.Connections
			}, '-', {
				id: 'statusbar-downspeed',
				text: ' ',
				cls: 'x-btn-text-icon',
				iconCls: 'x-deluge-downloading',
				menu: Deluge.Menus.Download
			}, '-', {
				id: 'statusbar-upspeed',
				text: ' ',
				cls: 'x-btn-text-icon',
				iconCls: 'x-deluge-seeding',
				menu: Deluge.Menus.Upload
			}, '-', {
				id: 'statusbar-traffic',
				text: ' ',
				cls: 'x-btn-text-icon',
				iconCls: 'x-deluge-traffic'
			}, '-', {
				id: 'statusbar-dht',
				text: ' ',
				cls: 'x-btn-text-icon',
				iconCls: 'x-deluge-dht'
			});
			this.created = true;
		},
		
		onConnect: function() {
			this.setStatus({
				iconCls: 'x-connected',
				text: ''
			});
			if (!this.created) this.createButtons();
			else {
				this.items.each(function(item) {
					item.show();
					item.enable();
				});
			}
		},
	
		onDisconnect: function() {
			this.clearStatus({useDefaults:true});
			this.items.each(function(item) {
				item.hide();
				item.disable();
			});
		},
		
		update: function(stats) {
			if (!stats) return;
			
			function addSpeed(val) {return val + ' KiB/s'}
			
			var updateStat = function(name, config) {
				var item = this.items.get('statusbar-' + name);
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
					value: stats.download_rate - stats.payload_download_rate,
					formatter: Deluge.Formatters.speed
				},
				limit: {
					value: stats.upload_rate - stats.payload_upload_rate,
					formatter: Deluge.Formatters.speed
				},
				format: '{0}/{1}'
			});
	
			this.items.get('statusbar-dht').setText(stats.dht_nodes);
	
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
	});
	Deluge.Statusbar = new Ext.deluge.Statusbar();
})();