Deluge.Connections = {
	
    onClose: function(e) {
		$clear(Deluge.Connections.running);
		Deluge.Connections.Window.hide();
    },
    
    onConnect: function(e) {
		$clear(Deluge.Connections.running);
		Deluge.Connections.Window.hide();
		var selected = Deluge.Connections.Grid.getSelectionModel().getSelected();
		var id = selected.id;
		Deluge.Client.web.connect(id, {
			onSuccess: function(methods) {
				Deluge.Client = new JSON.RPC('/json', {
					methods: methods
				});
				Deluge.Events.fire("connect");
			}
		});
    },
	
	onGetHosts: function(hosts) {
		Deluge.Connections.Store.loadData(hosts);
		var selection = Deluge.Connections.Grid.getSelectionModel();
		selection.selectRow(Deluge.Connections.selectedRow);
	},
	
	onSelect: function(selModel, rowIndex, record) {
		Deluge.Connections.selectedRow = rowIndex;
	},
	
	onShow: function(window) {
		Deluge.Connections.running = Deluge.Connections.runCheck.periodical(2000);
		Deluge.Connections.runCheck();
	},
	
	runCheck: function() {
		Deluge.Client.web.get_hosts({
			onSuccess: Deluge.Connections.onGetHosts
		});
	}
}

Deluge.Connections.Store = new Ext.data.SimpleStore({
	fields: [
		{name: 'status', mapping: 3},
		{name: 'host', mapping: 1},
		{name: 'port', mapping: 2},
		{name: 'version', mapping: 4}
	],
	id: 0
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
	selModel: new Ext.grid.RowSelectionModel({
		singleSelect: true,
		listeners: {'rowselect': Deluge.Connections.onSelect}
	}),
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
		'hide': Deluge.Connections.onClose,
		'show': Deluge.Connections.onShow
	}
});