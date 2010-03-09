Ext.namespace('Deluge');
Deluge.FileBrowser = Ext.extend(Ext.Window, {

	title: 'Filebrowser',

	width:  500,
	height: 400,

	tbar: {
		items: [{
			cls: 'x-btn-icon',
			iconCls: 'icon-back'
		}]
	},
	
	initComponent: function() {
		Deluge.FileBrowser.superclass.initComponent.call(this);
	}

});
