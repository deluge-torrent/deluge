Ext.namespace('Deluge');
Deluge.FileBrowser = Ext.extend(Ext.Window, {

	title: _('File Browser'),

	width:  500,
	height: 400,

	initComponent: function() {
		Deluge.FileBrowser.superclass.initComponent.call(this);

		this.add({
			xtype: 'toolbar',
			items: [{
				text: _('Back'),
				iconCls: 'icon-back'
			}, {
				text: _('Forward'),
				iconCls: 'icon-forward'
			}, {
				text: _('Up'),
				iconCls: 'icon-up'
			}, {
				text: _('Home'),
				iconCls: 'icon-home'
			}]
		});
	}

});
