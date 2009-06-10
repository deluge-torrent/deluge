(function() {
	function createEl(parent, type) {
		var el = document.createElement(type);
		parent.appendChild(el);
		return el;
	}
	
	var DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
	
	ScheduleSelectPanel = Ext.extend(Ext.form.FieldSet, {
		constructor: function(config) {
			config = Ext.apply({
				title: _('Schedule'),
				autoHeight: true
			}, config);
			ScheduleSelectPanel.superclass.constructor.call(this, config);
		},
		
		onRender: function(ct, position) {
			ScheduleSelectPanel.superclass.onRender.call(this, ct, position);
			
			var dom = this.body.dom;
			var table = createEl(dom, 'table');
			
			Ext.each(DAYS, function(day) {
				var row = createEl(table, 'tr');
				var label = createEl(row, 'th');
				label.setAttribute('style', 'font-weight: bold; padding-right: 5px;');
				label.innerHTML = day;
				for (var hour = 0; hour < 24; hour++) {
					var cell = createEl(row, 'td');
					cell.setAttribute('style', 'border: 1px solid Green; width: 16px; height: 20px; background: LightGreen;');
				}
			});
		}
	});
	
	SchedulerPreferences = Ext.extend(Ext.Panel, {
		constructor: function(config) {
			config = Ext.apply({
				border: false,
				title: _('Scheduler')
			}, config);
			SchedulerPreferences.superclass.constructor.call(this, config);
		},
		
		initComponent: function() {
			SchedulerPreferences.superclass.initComponent.call(this);

			this.form = this.add({
				xtype: 'form',
				layout: 'form',
				border: false,
				autoHeight: true
			});
			
			this.schedule = this.form.add(new ScheduleSelectPanel());
			
			this.slowSettings = this.form.add({
				xtype: 'fieldset',
				title: _('Slow Settings'),
				autoHeight: true,
				defaultType: 'uxspinner'
			});
			
			this.downloadLimit = this.slowSettings.add({
				fieldLabel: _('Download Limit'),
				name: 'download_limit'
			});
			this.uploadLimit = this.slowSettings.add({
				fieldLabel: _('Upload Limit'),
				name: 'upload_limit'
			});
			this.activeTorrents = this.slowSettings.add({
				fieldLabel: _('Active Torrents'),
				name: 'active_torrents'
			});
		},
		
		onRender: function(ct, position) {
			SchedulerPreferences.superclass.onRender.call(this, ct, position);
			this.form.layout = new Ext.layout.FormLayout();
			this.form.layout.setContainer(this);
			this.form.doLayout();
		},
		
		onShow: function() {
			SchedulerPreferences.superclass.onShow.call(this);
		}
	});
	Deluge.Preferences.addPage(new SchedulerPreferences());
})();