Deluge.Connections = {
    onClose: function(e) {
    },
    
    onConnect: function(e) {
    }
}

Deluge.Connections.Store = new Ext.data.SimpleStore({
	fields: [
		{name: 'status'},
		{name: 'host'},
		{name: 'version'}
	]
});

Deluge.Connections.Grid = new Ext.grid.GridPanel({
	store: Deluge.Connections.Store,
	cls: 'deluge-torrents',
	columns: [
		{header: "Status", width: 55, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'status'},
		{id:'host', header: "Host", width: 150, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'host'},
		{header: "Version", width: 75, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'version'}
	],	
	stripeRows: true,
	autoExpandColumn: 'host',
	deferredRender:false,
	autoScroll:true,
	margins: '0 0 0 0'
});

Deluge.Connections.Window = new Ext.Window({
    layout: 'fit',
    width: 300,
    height: 200,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    title: _('Connection Manager'),
    items: [Deluge.Connections.Grid],
    buttons: [{
        text: _('Close'),
        handler: Deluge.Connections.onClose
    },{
        text: _('Connect'),
        handler: Deluge.Connections.onConnect
    }]
});