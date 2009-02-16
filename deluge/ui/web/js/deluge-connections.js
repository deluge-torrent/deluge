Deluge.Connections = {
    onClose: function(e) {
		$clear(Deluge.Connections.running);
    },
    
    onConnect: function(e) {
    },
	
	onShow: function(window) {
		Deluge.Connections.running = Deluge.Connections.runCheck.periodical(2000);
		Deluge.Connections.runCheck();
	},
	
	runCheck: function() {
		Deluge.Client.web.get_hosts({
			onSuccess: Deluge.Connections.onGetHosts
		});
	},
	
	onGetHosts: function(hosts) {
		Deluge.Connections.Store.loadData(hosts);
	}
}

Deluge.Connections.Store = new Ext.data.SimpleStore({
	fields: [
		{name: 'status', mapping: 5},
		{name: 'host', mapping: 1},
		{name: 'port', mapping: 2},
		{name: 'version', mapping: 6}
	]
});

var renderHost = function(value, p, r) {
	return value + ':' + r.data['port']
}

Deluge.Connections.Grid = new Ext.grid.GridPanel({
	store: Deluge.Connections.Store,
	cls: 'deluge-torrents',
	columns: [
		{header: "Status", width: 55, sortable: true, renderer: Deluge.Formatters.plain, dataIndex: 'status'},
		{id:'host', header: "Host", width: 150, sortable: true, renderer: renderHost, dataIndex: 'host'},
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
    }],
	listeners: {
		'show': Deluge.Connections.onShow
	}
});