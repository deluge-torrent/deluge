Deluge.Statusbar = Ext.extend(Ext.ux.StatusBar, {
	constructor: function(config) {
		config = Ext.apply({
			id: 'deluge-statusbar',
			defaultIconCls: 'x-not-connected',
			defaultText: _('Not Connected')
		}, config);
		Deluge.Statusbar.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Deluge.Statusbar.superclass.initComponent.call(this);
		
		deluge.events.on('connect', this.onConnect, this);
		deluge.events.on('disconnect', this.onDisconnect, this);
	},
	
	createButtons: function() {
		this.buttons = this.add({
			id: 'statusbar-connections',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-connections',
			tooltip: _('Connections'),
			menu: deluge.menus.connections
		}, '-', {
			id: 'statusbar-downspeed',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-downloading',
			tooltip: _('Download Speed'),
			menu: deluge.menus.download
		}, '-', {
			id: 'statusbar-upspeed',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-seeding',
			tooltip: _('Upload Speed'),
			menu: deluge.menus.upload
		}, '-', {
			id: 'statusbar-traffic',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-traffic',
			tooltip: _('Protocol Traffic Download/Upload')
		}, '-', {
			id: 'statusbar-dht',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-dht',
			tooltip: _('DHT Nodes')
		}, '-', {
			id: 'statusbar-freespace',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-freespace',
			tooltip: _('Freespace in download location')
		});
		this.created = true;
	},
	
	onConnect: function() {
		this.setStatus({
			iconCls: 'x-connected',
			text: ''
		});
		if (!this.created) {
			this.createButtons();
		} else {
			Ext.each(this.buttons, function(item) {
				item.show();
				item.enable();
			});
		}
		this.doLayout();
	},

	onDisconnect: function() {
		this.clearStatus({useDefaults:true});
		Ext.each(this.buttons, function(item) {
			item.hide();
			item.disable();
		});
		this.doLayout();
	},
	
	update: function(stats) {
		if (!stats) return;
		
		function addSpeed(val) {return val + ' KiB/s'}
		
		var updateStat = function(name, config) {
			var item = this.items.get('statusbar-' + name);
			if (config.limit.value > 0) {
				var value = (config.value.formatter) ? config.value.formatter(config.value.value, true) : config.value.value;
				var limit = (config.limit.formatter) ? config.limit.formatter(config.limit.value, true) : config.limit.value;
				var str = String.format(config.format, value, limit);
			} else {
				var str = (config.value.formatter) ? config.value.formatter(config.value.value, true) : config.value.value;
			}
			item.setText(str);
		}.createDelegate(this);
		
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
				value: stats.download_protocol_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.upload_protocol_rate,
				formatter: Deluge.Formatters.speed
			},
			format: '{0}/{1}'
		});

		this.items.get('statusbar-dht').setText(stats.dht_nodes);
		this.items.get('statusbar-freespace').setText(fsize(stats.free_space));
		
		deluge.menus.connections.setValue(stats.max_num_connections);
		deluge.menus.download.setValue(stats.max_download);
		deluge.menus.upload.setValue(stats.max_upload);
	}
});
deluge.statusbar = new Deluge.Statusbar();
