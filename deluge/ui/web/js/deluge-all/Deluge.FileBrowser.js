Ext.namespace('Deluge');
Deluge.FileBrowser = Ext.extend(Ext.Window, {

	title: 'Filebrowser',

	width:  500,
	height: 400,

	initComponent: function() {
		Deluge.FileBrowser.superclass.initComponent.call(this);

		this.add({
			xtype: 'toolbar',
			items: [{
				cls: 'x-btn-icon',
				iconCls: 'icon-back'
			}, {
				cls: 'x-btn-icon',
				iconCls: 'icon-forward'
			}]
		});
	}

});
