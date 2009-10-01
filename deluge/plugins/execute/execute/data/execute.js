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