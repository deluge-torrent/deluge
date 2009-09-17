ExamplePlugin = Ext.extend(Deluge.Plugin, {
	constructor: function(config) {
		config = Ext.apply({
			name: "Example"
		}, config);
		ExamplePlugin.superclass.constructor.call(this, config);
	},
	
	onDisable: function() {
		Deluge.Preferences.removePage(this.prefsPage);
	},
	
	onEnable: function() {
		this.prefsPage = new ExamplePreferencesPanel();
		this.prefsPage = Deluge.Preferences.addPage(this.prefsPage);
	}
});
new ExamplePlugin();