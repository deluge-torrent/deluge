Deluge.UI = {
	initialize: function() {
		this.torrents = {};
		this.torrentIds = [];
		Deluge.Client = new JSON.RPC('/json/rpc');
		
		var theme = Cookie.read('theme');
		if (theme) this.setTheme(theme);
		else this.setTheme('classic');
		
		this.bound = {
			updated: this.updated.bindWithEvent(this),
			resized: this.resized.bindWithEvent(this),
			toolbar_click: this.toolbar_click.bindWithEvent(this),
			file_priorities: this.file_priorities.bindWithEvent(this),
			labelsChanged: this.labelsChanged.bindWithEvent(this)
		};
		this.loadUi.delay(100, this);
	},
	
	loadUi: function() {
		this.vbox = new Widgets.VBox('page', {expand: true});
		
		this.toolbar = new Deluge.Widgets.Toolbar();
		this.addWindow = new Deluge.Widgets.AddWindow();
		this.prefsWindow = new Deluge.Widgets.PreferencesWindow();
		
		this.statusbar = new Deluge.Widgets.StatusBar();
		this.labels = new Deluge.Widgets.Labels()
		this.details = new Deluge.Widgets.Details()
		
		this.initialize_grid()
		
		this.split_horz = new Widgets.SplitPane('top', this.labels, this.grid, {
			pane1: {min: 150},
			pane2: {min: 100, expand: true}
		});
		var details = $W('details')
		this.split_vert = new Widgets.SplitPane('main', this.split_horz, details, {
			direction: 'vertical',
			pane1: {min: 100, expand: true},
			pane2: {min: 200}
		});
		
		this.vbox.addBox(this.toolbar, {fixed: true});
		this.vbox.addBox(this.split_vert);
		this.vbox.addBox(this.statusbar, {fixed: true});
		this.vbox.calculatePositions();
		this.details.expand()
		
		this.toolbar.addEvent('button_click', this.bound.toolbar_click);
		this.details.addEvent('filesAction', this.bound.file_priorities)
		this.labels.addEvent('stateChanged', this.bound.labelsChanged)
		details.addEvent('resize', function(e) {
			this.details.expand()
		}.bindWithEvent(this))
		
		window.addEvent('resize', this.bound.resized);
		Deluge.UI.update();
		$('overlay').destroy();
	},
	
	initialize_grid: function() {
		this.grid = new Deluge.Widgets.TorrentGrid('torrents')
		
		var menu = new Widgets.PopupMenu()
		menu.add([
			{type:'text',action:'pause',text:'Pause',icon:'/static/images/tango/pause.png'},
			{type:'text',action:'resume',text:'Resume',icon:'/static/images/tango/start.png'},
			{type:'seperator'},
			{type:'submenu',text:'Options',icon:'/static/images/tango/preferences-system.png',items: [
				{type:'submenu',text:'D/L Speed Limit',icon:'/pixmaps/downloading16.png',items: [
					{type:'text',action:'max_download_speed',value:5,text:'5 KiB/s'},
					{type:'text',action:'max_download_speed',value:10,text:'10 KiB/s'},
					{type:'text',action:'max_download_speed',value:30,text:'30 KiB/s'},
					{type:'text',action:'max_download_speed',value:80,text:'80 KiB/s'},
					{type:'text',action:'max_download_speed',value:300,text:'300 KiB/s'},
					{type:'text',action:'max_download_speed',value:-1,text:'Unlimited'}
				]},
				{type:'submenu',text:'U/L Speed Limit',icon:'/pixmaps/seeding16.png',items: [
					{type:'text',action:'max_upload_speed',value:5,text:'5 KiB/s'},
					{type:'text',action:'max_upload_speed',value:10,text:'10 KiB/s'},
					{type:'text',action:'max_upload_speed',value:30,text:'30 KiB/s'},
					{type:'text',action:'max_upload_speed',value:80,text:'80 KiB/s'},
					{type:'text',action:'max_upload_speed',value:300,text:'300 KiB/s'},
					{type:'text',action:'max_upload_speed',value:-1,text:'Unlimited'}
				]},
				{type:'submenu',text:'Connection Limit',icon:'/static/images/tango/connections.png',items: [
					{type:'text',action:'max_connections',value:50,text:'50'},
					{type:'text',action:'max_connections',value:100,text:'100'},
					{type:'text',action:'max_connections',value:200,text:'200'},
					{type:'text',action:'max_connections',value:300,text:'300'},
					{type:'text',action:'max_connections',value:500,text:'500'},
					{type:'text',action:'max_connections',value:-1,text:'Unlimited'}
				]},
				{type:'submenu',text:'Upload Slot Limit',icon:'/template/static/icons/16/view-sort-ascending.png',items: [
					{type:'text',action:'max_upload_slots',value:0,text:'0'},
					{type:'text',action:'max_upload_slots',value:1,text:'1'},
					{type:'text',action:'max_upload_slots',value:2,text:'2'},
					{type:'text',action:'max_upload_slots',value:3,text:'3'},
					{type:'text',action:'max_upload_slots',value:5,text:'5'},
					{type:'text',action:'max_upload_slots',value:-1,text:'Unlimited'}
				]},
				{type:'toggle',action:'auto_managed',value:false,text:'Auto Managed'}
			]},
			{type:'seperator'},
			{type:'submenu',text:'Queue',icon:'/template/static/icons/16/view-sort-descending.png',items:[
				{type:'text',action:'top',text:'Top',icon:'/static/images/tango/go-top.png'},
				{type:'text',action:'up',text:'Up',icon:'/static/images/tango/queue-up.png'},
				{type:'text',action:'down',text:'Down',icon:'/static/images/tango/queue-down.png'},
				{type:'text',action:'bottom',text:'Bottom',icon:'/static/images/tango/go-bottom.png'}
			]},
			{type: 'seperator'}, 
			{type:'text',action:'update_tracker',text:'Update Tracker',icon:'/template/static/icons/16/view-refresh.png'},
			{type:'text',action:'edit_trackers',text:'Edit Trackers',icon:'/template/static/icons/16/gtk-edit.png'},
			{type:'seperator'},
			{type:'submenu',action:'remove',value:0,text:'Remove Torrent',icon:'/static/images/tango/list-remove.png', items:[
				{type:'text',action:'remove',value:0,text:'From Session'},
				{type:'text',action:'remove',value:1,text:'... and delete Torrent file'},
				{type:'text',action:'remove',value:2,text:'... and delete Downloaded files'},
				{type:'text',action:'remove',value:3,text:'... and delete All files'}
			]},
			{type:'seperator'},
			{type:'text',action:'force_recheck',text:'Force Recheck',icon:'/static/images/tango/edit-redo.png'},
			{type:'text',action:'move_storage',text:'Move Storage',icon:'/static/images/tango/move.png'}
		]);

		menu.addEvent('action', function(e) {
			this.torrent_action(e.action, e.value)
		}.bind(this))

		this.grid.addEvent('row_menu', function(e) {
			e.stop()
			var value = this.grid.selectedRow.torrent.is_auto_managed;
			menu.items[3].items[4].set(value)
			menu.torrent_id = e.row_id
			menu.show(e)
		}.bindWithEvent(this))
		
		this.grid.addEvent('selectedchanged', function(e) {
			if ($chk(this.grid.selectedRow))
				this.details.update(this.grid.selectedRow.id);
			else
				this.details.update(null);
		}.bindWithEvent(this))
	},
	
	setTheme: function(name, fn) {
		this.theme = name;
		if (this.themecss) this.themecss.destroy();
		this.themecss = new Asset.css('/template/static/themes/' + name + '/style.css');
		Cookie.write('theme', name);
		if (this.vbox) this.vbox.refresh();
	},
	
	run: function() {
		if (!this.running) {
			this.running = this.update.periodical(2000, this);
		}
	},
	
	stop: function() {
		if (this.running) {
			$clear(this.running);
			this.running = false;
		}
	},
	
	update: function() {
		filter = {}
		if (this.labels.state != 'All') filter.state = this.labels.state
		Deluge.Client.update_ui(Deluge.Keys.Grid, filter, {
			onSuccess: this.bound.updated
		})
	},
	
	updated: function(data) {
		this.torrents = new Hash(data.torrents);
		this.stats = data.stats;
		this.filters = data.filters
		this.torrents.each(function(torrent, torrent_id) {
			torrent.id = torrent_id;
		})
		this.grid.update_torrents(this.torrents);
		this.statusbar.update(this.stats);
		
		if ($chk(this.grid.selectedRow))
			this.details.update(this.grid.selectedRow.id);
		else
			this.details.update(null);
		
		this.labels.update(this.filters)
	},
	
	file_priorities: function(event) {
		Deluge.Client.get_torrent_status(event.torrentId, ['file_priorities'], {
			onSuccess: function(result) {
				var priorities = result.file_priorities
				priorities.each(function(priority, index) {
					if (event.files.contains(index)) priorities[index] = event.action
				})
				Deluge.Client.set_torrent_file_priorities(event.torrentId, priorities, {
					onSuccess: function(response) {
						this.details.update(event.torrentId)
					}.bindWithEvent(this)	
				})
			}.bindWithEvent(this)
		})
	},
	
	resized: function(event) {
		this.vbox.calculatePositions();
	},
	
	toolbar_click: function(event) {
		this.torrent_action(event.action);
	},
	
	labelsChanged: function(event) {
		this.update()
	},
	
	torrent_action: function(action, value) {
		var torrentIds = this.grid.get_selected_torrents()
		switch (action) {
			case 'resume':
				Deluge.Client.resume_torrent(torrentIds)
				break;
			case 'pause':
				Deluge.Client.pause_torrent(torrentIds)
				break;
			case 'top':
				Deluge.Client.queue_top(torrentIds)
				break;
			case 'up':
				Deluge.Client.queue_up(torrentIds)
				break;
			case 'down':
				Deluge.Client.queue_down(torrentIds)
				break;
			case 'bottom':
				Deluge.Client.queue_bottom(torrentIds)
				break;
			case 'force_recheck':
				Deluge.Client.force_recheck(torrentIds)
				break;
			case 'update_tracker':
				Deluge.Client.force_reannounce(torrentIds)
				break;
			case 'max_download_speed':
				torrentIds.each(function(torrentId) {
					Deluge.Client.set_torrent_max_download_speed(torrentId, value.toInt())
				})
				break;
			case 'max_upload_speed':
				torrentIds.each(function(torrentId) {
					Deluge.Client.set_torrent_max_upload_speed(torrentId, value.toInt())
				})
				break;
			case 'max_connections':
				torrentIds.each(function(torrentId) {
					Deluge.Client.set_torrent_max_connections(torrentId, value.toInt())
				})
				break;
			case 'max_upload_slots':
				torrentIds.each(function(torrentId) {
					Deluge.Client.set_torrent_max_upload_slots(torrentId, value.toInt())
				})
				break;
			case 'auto_managed':
				torrentIds.each(function(torrentId) {
					Deluge.Client.set_torrent_auto_managed(torrentId, value)
				})
				break;
			case 'add':
				this.addWindow.show()
				break;
			case 'remove':
				var removeTorrent = false, removeFiles = false;
				if (value == 1) removeTorrent = true;
				else if (value == 2) removeFiles = true;
				else if (value > 3) {
					removeTorrent = true;
					removeFiles = true;
				}
				Deluge.Client.remove_torrent(torrentIds, removeTorrent, removeFiles);
				break;
			case 'preferences':
				this.prefsWindow.show()
				break;
			default:
				break;
		}
		this.update()
	}
};

window.addEvent('domready', function(e) {
	Deluge.UI.initialize();
	Deluge.UI.run();
});


