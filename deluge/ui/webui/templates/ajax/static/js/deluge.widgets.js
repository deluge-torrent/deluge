/*
 * Script: deluge.widgets.js
 *  Collection of widgets for use in the deluge web-ui
 *
 * Copyright:
 *   Damien Churchill (c) 2008
 */

var Deluge = $empty;

Deluge.Keys = {
	Grid: 		['queue', 'name', 'total_size', 'state', 'progress',
				'num_seeds', 'total_seeds', 'num_peers', 'total_peers',
				'download_payload_rate', 'upload_payload_rate', 'eta', 'ratio',
				'distributed_copies' ,'is_auto_managed'],
	
	Statistics: ['total_done', 'total_payload_download', 'total_uploaded',
				'total_payload_upload', 'next_announce', 'tracker_status',
				'num_pieces', 'piece_length', 'is_auto_managed', 'active_time',
				'seeding_time',	'seed_rank'],
	
	Files: 		['files', 'file_progress', 'file_priorities'],
	
	Peers:		['peers', 'seeds'],
	
	Details:	['name', 'save_path', 'total_size', 'num_files', 'tracker_status', 'tracker'],
	
	Options:	['max_download_speed', 'max_upload_speed', 'max_connections',
				'max_upload_slots','is_auto_managed', 'stop_at_ratio',
				'stop_ratio', 'remove_at_ratio', 'private', 'prioritize_first_last']
}

Deluge.Keys.Statistics.extend(Deluge.Keys.Grid)

Deluge.Widgets = $empty;

Deluge.Widgets.Details = new Class({
	Extends: Widgets.Tabs,
	
	initialize: function() {
		this.parent($$('#details .mooui-tabs')[0])
		
		this.statistics = new Deluge.Widgets.StatisticsPage()
		this.details = new Deluge.Widgets.DetailsPage()
		this.files = new Deluge.Widgets.FilesPage()
		this.peers = new Deluge.Widgets.PeersPage()
		this.options = new Deluge.Widgets.OptionsPage()
		
		this.addPage(this.statistics)
		this.addPage(this.details)
		this.addPage(this.files)
		this.addPage(this.peers)
		this.addPage(this.options)
		this.addEvent('pageChanged', function(e) {
			this.update(this.torrentId);
		}.bindWithEvent(this));
		this.addEvent('resize', this.resized.bindWithEvent(this))
		
		this.files.addEvent('menuAction', function(e) {
			files = []
			this.files.grid.get_selected().each(function(file) {
				files.push(file.fileIndex)
			})
			e.files = files
			this.fireEvent('filesAction', e)
		}.bindWithEvent(this))
	},
	
	keys: {
		0: Deluge.Keys.Statistics,
		1: Deluge.Keys.Details,
		2: Deluge.Keys.Files,
		3: Deluge.Keys.Peers,
		4: Deluge.Keys.Options
	},
	
	update: function(torrentId) {
		this.torrentId = torrentId
		if (!this.torrentId) return
		var keys = this.keys[this.currentPage], page = this.pages[this.currentPage];
		Deluge.Client.get_torrent_status(torrentId, keys, {
			onSuccess: function(torrent) {
				torrent.id = torrentId
				if (page.update) page.update(torrent)
			}.bindWithEvent(this)
		})
	},
	
	resized: function(event) {
		this.pages.each(function(page) {
			page.getSizeModifiers()
			page.sets({
				width: event.width - page.element.modifiers.x,
				height: event.height - page.element.modifiers.y - 28
			})
		})
	}
});

Deluge.Widgets.StatisticsPage = new Class({
	Extends: Widgets.TabPage,
	
	options: {
		url: '/template/render/html/tab_statistics.html'
	},
	
	initialize: function() {
		this.parent('Statistics')
	},
	
	update: function(torrent) {
		var data = {
			downloaded: torrent.total_done.toBytes()+' ('+torrent.total_payload_download.toBytes()+')',
			uploaded: torrent.total_uploaded.toBytes()+' ('+torrent.total_payload_upload.toBytes()+')',
			share: torrent.ratio.toFixed(3),
			announce: torrent.next_announce.toTime(),
			tracker_status: torrent.tracker_status,
			downspeed: torrent.download_payload_rate.toSpeed(),
			upspeed: torrent.upload_payload_rate.toSpeed(),
			eta: torrent.eta.toTime(),
			pieces: torrent.num_pieces + ' (' + torrent.piece_length.toBytes() + ')',
			seeders: torrent.num_seeds + ' (' + torrent.total_seeds + ')',
			peers: torrent.num_peers + ' (' + torrent.total_peers + ')',
			avail: torrent.distributed_copies.toFixed(3),
			active_time: torrent.active_time.toTime(),
			seeding_time: torrent.seeding_time.toTime(),
			seed_rank: torrent.seed_rank
		}
		
		if (torrent.is_auto_managed) {data.auto_managed = 'True'}
		else {data.auto_managed = 'False'}
		
		this.element.getElements('dd').each(function(item) {
			item.set('text', data[item.getProperty('class')])
		}, this)
	}
})

Deluge.Widgets.DetailsPage = new Class({
	Extends: Widgets.TabPage,
	
	options: {
		url: '/template/render/html/tab_details.html'
	},
	
	initialize: function() {
		this.parent('Details')
	},
	
	update: function(torrent) {
		var data = {
			torrent_name: torrent.name,
			hash: torrent.id,
			path: torrent.save_path,
			size: torrent.total_size.toBytes(),
			files: torrent.num_files,
			status: torrent.tracker_status,
			tracker: torrent.tracker
		}
		this.element.getElements('dd').each(function(item) {
			item.set('text', data[item.getProperty('class')])
		}, this)
	}
})

Deluge.Widgets.FilesGrid = new Class({
	Extends: Widgets.DataGrid,
	
	options: {
		columns: [
			{name: 'filename',text: 'Filename',type:'text',width: 350},
			{name: 'size',text: 'Size',type:'bytes',width: 80},
			{name: 'progress',text: 'Progress',type:'progress',width: 180},
			{name: 'priority',text: 'Priority',type:'icon',width: 150}
		]
	},
	
	priority_texts: {
		0: 'Do Not Download',
		1: 'Normal Priority',
		2: 'High Priority',
		5: 'Highest Priority'
	},
	
	priority_icons: {
		0: '/static/images/tango/process-stop.png',
		1: '/template/static/icons/16/gtk-yes.png',
		2: '/static/images/tango/queue-down.png',
		5: '/static/images/tango/go-bottom.png'
	},
	
	initialize: function(element, options) {
		this.parent(element, options)
		var menu = new Widgets.PopupMenu()
		$A([0,1,2,5]).each(function(index) {
			menu.add({
				type:'text',
				action: index,
				text: this.priority_texts[index],
				icon: this.priority_icons[index]
			})
		}, this)
		
		menu.addEvent('action', function(e) {
			e = {
				action: e.action,
				torrentId: menu.row.torrentId
			}
			this.fireEvent('menuAction', e)
		}.bind(this))
		
		this.addEvent('row_menu', function(e) {
			e.stop()
			menu.row = e.row
			menu.show(e)
		})
	},
	
	clear: function() {
		this.rows.empty()
		this.body.empty()
		this.render()
	},
	
	update_files: function(torrent) {
		torrent.files.each(function(file) {
			var p = torrent.file_priorities[file.index]
			var priority = {text:this.priority_texts[p], icon:this.priority_icons[p]}
			
			var percent = torrent.file_progress[file.index]*100.0;
			row = {
				id: torrent.id + '-' + file.index,
				data: {
					filename: file.path,
					size: file.size,
					progress: {percent: percent, text: percent.toFixed(2) + '%'},
					priority: priority
				},
				fileIndex: file.index,
				torrentId: torrent.id
				
			}
			if (this.has(row.id)) {
				this.updateRow(row, true)
			} else {
				this.addRow(row, true)
			}
		}, this)
		this.render()
	}
});

Deluge.Widgets.FilesPage = new Class({
	Extends: Widgets.TabPage,
	
	options: {
		url: '/template/render/html/tab_files.html'
	},
	
	initialize: function(el) {
		this.parent('Files')
		this.torrentId = -1
		this.addEvent('loaded', this.loaded.bindWithEvent(this))
		this.addEvent('resize', this.resized.bindWithEvent(this))
	},
	
	loaded: function(event) {
		this.grid = new Deluge.Widgets.FilesGrid('files')		
		this.grid.addEvent('menuAction', this.menu_action.bindWithEvent(this))
		
		if (this.been_resized) {
			this.resized(this.been_resized)
			delete this.been_resized
		}
	},
	
	resize_check: function(event) {
		
	},
	
	resized: function(e) {
		if (!this.grid) {
			this.been_resized = e;
			return
		}
		
		this.element.getPadding()
		this.grid.sets({
			width: e.width - this.element.padding.x,
			height: e.height - this.element.padding.y
		})
	},
	
	menu_action: function(e) {
		this.fireEvent('menuAction', e)
	},
	
	update: function(torrent) {
		if (this.torrentId != torrent.id) {
			this.torrentId = torrent.id
			this.grid.rows.empty()
			this.grid.body.empty()
		}
		this.grid.update_files(torrent)
	}
})

Deluge.Widgets.PeersPage = new Class({
	Extends: Widgets.TabPage,
	
	options: {
		url: '/template/render/html/tab_peers.html'
	},
	
	initialize: function(el) {
		this.parent('Peers')
		this.addEvent('resize', this.resized.bindWithEvent(this))
		this.addEvent('loaded', this.loaded.bindWithEvent(this))
	},
	
	loaded: function(event) {
		this.grid = new Widgets.DataGrid($('peers'), {
			columns: [
				{name: 'country',type:'image',width: 20},
				{name: 'address',text: 'Address',type:'text',width: 80},
				{name: 'client',text: 'Client',type:'text',width: 180},
				{name: 'downspeed',text: 'Down Speed',type:'speed',width: 100},
				{name: 'upspeed',text: 'Up Speed',type:'speed',width: 100},
			]})
		this.torrentId = -1
		if (this.been_resized) {
			this.resized(this.been_resized)
			delete this.been_resized
		}
	},
	
	resized: function(e) {
		if (!this.grid) {
			this.been_resized = e;
			return
		}
		
		this.element.getPadding()
		this.grid.sets({
			width: e.width - this.element.padding.x,
			height: e.height - this.element.padding.y
		})
	},
	
	update: function(torrent) {
		if (this.torrentId != torrent.id) {
			this.torrentId = torrent.id
			this.grid.rows.empty()
			this.grid.body.empty()
		}
		var peers = []
		torrent.peers.each(function(peer) {
			if (peer.country.strip() != '') {
				peer.country = '/pixmaps/flags/' + peer.country.toLowerCase() + '.png'
			} else {
				peer.country = '/templates/static/images/spacer.gif'
			}
			row = {
				id: peer.ip,
				data: {
					country: peer.country,
					address: peer.ip,
					client: peer.client,
					downspeed: peer.down_speed,
					upspeed: peer.up_speed
					}
				}
			if (this.grid.has(row.id)) {
				this.grid.updateRow(row, true)
			} else {
				this.grid.addRow(row, true)
			}
			peers.include(peer.ip)
		}, this)
		
		this.grid.rows.each(function(row) {
			if (!peers.contains(row.id)) {
				row.element.destroy()
				this.grid.rows.erase(row)
			}
		}, this)
		this.grid.render()
	}
});

Deluge.Widgets.OptionsPage = new Class({
	Extends: Widgets.TabPage,
	
	options: {
		url: '/template/render/html/tab_options.html'
	},
	
	initialize: function() {
		if (!this.element)
			this.parent('Options');
		this.addEvent('loaded', function(event) {
			this.loaded(event)
		}.bindWithEvent(this))
	},
	
	loaded: function(event) {
		this.bound = {
			apply: this.apply.bindWithEvent(this),
			reset: this.reset.bindWithEvent(this)
		}
		this.form = this.element.getElement('form');
		this.changed = new Hash()
		this.form.getElements('input').each(function(el) {
			if (el.type == 'button') return;
			el.focused = false
			el.addEvent('change', function(e) {
				if (!this.changed[this.torrentId])
					this.changed[this.torrentId] = {}
				if (el.type == 'checkbox')
					this.changed[this.torrentId][el.name] = el.checked;
				else
					this.changed[this.torrentId][el.name] = el.value;
			}.bindWithEvent(this));
			el.addEvent('focus', function(e) {
				el.focused = true;
			});
			el.addEvent('blur', function(e) {
				el.focused = false;
			});
		}, this);
		
		this.form.apply.addEvent('click', this.bound.apply);
		this.form.reset.addEvent('click', this.bound.reset);
	},
	
	apply: function(event) {
		if (!this.torrentId) return
		var changed = this.changed[this.torrentId]
		if ($defined(changed['is_auto_managed'])) {
			changed['auto_managed'] = changed['is_auto_managed']
			delete changed['is_auto_managed']
		}
		Deluge.Client.set_torrent_options(this.torrentId, changed, {
			onSuccess: function(event) {
				delete this.changed[this.torrentId]
			}.bindWithEvent(this)
		})
	},
	
	reset: function(event) {
		if (this.torrentId) {
			delete this.changed[this.torrentId]
		}
		Deluge.Client.get_torrent_status(this.torrentId, Deluge.Keys.Options, {
			onSuccess: function(torrent) {
				torrent.id = this.torrentId
				this.update(torrent)
			}.bindWithEvent(this)
		})
	},
	
	update: function(torrent) {
		this.torrentId = torrent.id;
		$each(torrent, function(value, key) {
			var changed = this.changed[this.torrentId]
			if (changed && $defined(changed[key])) return;
			var type = $type(value);
			if (type == 'boolean') {
				this.form[key].checked = value;
			} else {
				if (!this.form[key].focused)
					this.form[key].value = value;
			};
			if (key == 'private' && value == 0) {
				this.form[key].disabled = true
				this.form[key].getParent().addClass('opt-disabled')
			}
		}, this);
	}
});

Deluge.Widgets.Toolbar = new Class({
	Implements: Events,
	Extends: Widgets.Base,
	
	initialize: function() {
		this.parent($('toolbar'))
		this.buttons = this.element.getFirst()
		this.info = this.element.getLast()
		this.buttons.getElements('li').each(function(el) {
			el.addEvent('click', function(e) {
				e.action = el.id
				this.fireEvent('button_click', e)
			}.bind(this))
		}, this)
	}
});

Deluge.Widgets.StatusBar = new Class({
	Extends: Widgets.Base,
	
	initialize: function() {
		this.parent($('status'));
		this.element.getElements('li').each(function(el) {
			this[el.id] = el;
		}, this);
	},
	
	update: function(stats) {
		this.connections.set('text', stats.num_connections);
		this.downspeed.set('text', stats.download_rate.toSpeed());
		this.upspeed.set('text', stats.upload_rate.toSpeed());
		this.dht.set('text', stats.dht_nodes);
	}
});

Deluge.Widgets.TorrentGrid = new Class({
	Extends: Widgets.DataGrid,
	
	options: {
		columns: [
			{name: 'number',text: '#',type:'number',width: 20},
			{name: 'name',text: 'Name',type:'icon',width: 350},
			{name: 'size',text: 'Size',type:'bytes',width: 80},
			{name: 'progress',text: 'Progress',type:'progress',width: 180},
			{name: 'seeders',text: 'Seeders',type:'text',width: 80},
			{name: 'peers',text: 'Peers',type:'text',width: 80},
			{name: 'down',text: 'Down Speed',type:'speed',width: 100},
			{name: 'up',text: 'Up Speed',type:'speed',width: 100},
			{name: 'eta',text: 'ETA',type:'time',width: 80},
			{name: 'ratio',text: 'Ratio',type:'number',width: 60},
			{name: 'avail',text: 'Avail.',type:'number',width: 60}
		]
	},
	
	icons: {
		'Downloading': '/pixmaps/downloading16.png',
		'Seeding': '/pixmaps/seeding16.png',
		'Queued': '/pixmaps/queued16.png',
		'Paused': '/pixmaps/inactive16.png',
		'Error': '/pixmaps/alert16.png',
		'Checking': '/pixmaps/inactive16.png'
	},
	
	get_selected_torrents: function() {
		var torrentIds = [];
		this.get_selected().each(function(row) {
			torrentIds.include(row.id);
		});
		return torrentIds;
	},
	
	set_torrent_filter: function(state) {
		state = state.replace(' ', '');
		this.filterer = function (r) {
			if (r.torrent.state == state) { return true } else { return false };
		};
		this.render();
	},
	
	update_torrents: function(torrents) {
		torrents.getKeys().each(function(torrentId) {
			var torrent = torrents[torrentId]
			var torrentIds = torrents.getKeys()
			if (torrent.queue == -1) {var queue = ''}
			else {var queue = torrent.queue + 1}
			var icon = this.icons[torrent.state]
			row = {
				id: torrentId,
				data: {
					number: queue,
					name: {text: torrent.name, icon: icon},
					size: torrent.total_size,
					progress: {percent: torrent.progress, text:torrent.state + ' ' + torrent.progress.toFixed(2) + '%'},
					seeders: torrent.num_seeds + ' (' + torrent.total_seeds + ')',
					peers: torrent.num_peers + ' (' + torrent.total_peers + ')',
					down: torrent.download_payload_rate,
					up: torrent.upload_payload_rate,
					eta: torrent.eta,
					ratio: torrent.ratio.toFixed(3),
					avail: torrent.distributed_copies.toFixed(3)
				},
				torrent: torrent
			}
			if (this.has(row.id)) {
				this.updateRow(row, true)
			} else {
				this.addRow(row, true)
			}
			
			this.rows.each(function(row) {
				if (!torrentIds.contains(row.id)) {
					row.element.destroy()
					this.rows.erase(row.id)
				}
			}, this)
		}, this)
		this.render()
	}
})

Deluge.Widgets.Labels = new Class({
	
	Extends: Widgets.Base,
	
	regex: /([\w]+)\s\((\d)\)/,
	
	initialize: function() {
		this.parent($('labels'))
		this.bound = {
			resized: this.resized.bindWithEvent(this),
			clickedState: this.clickedState.bindWithEvent(this)
		}
		
		this.list = new Element('ul')
		this.element.grab(this.list)
		this.addStates()
		this.state = 'All'
		this.islabels = false;
		this.addEvent('resize', this.resized)
	},
	
	addStates: function() {
		this.list.grab(new Element('li').set('text', 'All').addClass('all').addClass('activestate'))
		this.list.grab(new Element('li').set('text', 'Downloading').addClass('downloading'))
		this.list.grab(new Element('li').set('text', 'Seeding').addClass('seeding'))
		this.list.grab(new Element('li').set('text', 'Queued').addClass('queued'))
		this.list.grab(new Element('li').set('text', 'Paused').addClass('paused'))
		this.list.grab(new Element('li').set('text', 'Error').addClass('error'))
		this.list.grab(new Element('li').set('text', 'Checking').addClass('checking'))
		this.list.grab(new Element('hr'))
	},
	
	addLabel: function(name) {
		
	},
	
	clickedState: function(e) {
		if (this.islabels) {
			var old = this.list.getElement('.' + this.state.toLowerCase())
			old.removeClass('activestate')
			this.state = e.target.get('text').match(/^(\w+)/)[1]
			e.target.addClass('activestate')
			this.fireEvent('stateChanged', this.state)
		} else {
			
		}
	},
	
	update: function(filters) {
		if (filters.state.length == 1)
			this.updateNoLabels(filters);
		else
			this.updateLabels(filters)
	},
	
	updateNoLabels: function(filters) {
		this.islabels = false;
	},
	
	updateLabels: function(filters) {
		this.islabels = true;
		$each(filters.state, function(state) {
			var el = this.list.getElement('.' + state[0].toLowerCase())
			if (!el) return
			
			el.set('text', state[0] + ' (' + state[1] + ')')
			el.removeEvent('click', this.bound.clickedState)
			el.addEvent('click', this.bound.clickedState)
		}, this)
	},
	
	resized: function(event) {
		var height = this.element.getInnerSize().y;
		this.list.getSizeModifiers();
		height -= this.list.modifiers.y;
		this.list.setStyle('height', height)
	}
});

Deluge.Widgets.AddWindow = new Class({
	Extends: Widgets.Window,
	options: {
		width: 400,
		height: 200,
		title: 'Add Torrent',
		url: '/template/render/html/window_add_torrent.html'
	},
	
	initialize: function() {
		this.parent()
		this.addEvent('loaded', this.loaded.bindWithEvent(this))
	},
	
	loaded: function(event) {
		this.formfile = this.content.getChildren()[0];
		this.formurl = this.content.getChildren()[1];
		this.formurl.addEvent('submit', function(e) {
			e.stop();
			Deluge.Client.add_torrent_url(this.formurl.url.value, '', {})
			this.hide()
		}.bindWithEvent(this))
	}
});

Deluge.Widgets.PreferencesCategory = new Class({
	Extends: Widgets.TabPage,
});

Deluge.Widgets.PluginPreferencesCategory = new Class({
	Extends: Deluge.Widgets.PreferencesCategory
});

Deluge.Widgets.GenericPreferences = new Class({
	Extends: Deluge.Widgets.PreferencesCategory,
	
	initialize: function(name, options) {
		this.parent(name, options)
		this.core = true;
		this.addEvent('loaded', function(e) {
			this.form = this.element.getElement('form');
		}.bindWithEvent(this));
	},
	
	update: function(config) {
		this.fireEvent('beforeUpdate');
		this.original = config; 
		this.changed = new Hash();
		this.inputs = this.form.getElements('input, select');
		this.inputs.each(function(input) {
			if (!input.name) return;
			if (!$defined(config[input.name])) return;
			if (input.tagName.toLowerCase() == 'select') {
				var value = config[input.name].toString();
				input.getElements('option').each(function(option) {
					if (option.value == value) {
						option.selected = true;
					}
				});
			} else if (input.type == 'text') {
				input.value = config[input.name];
			} else if (input.type == 'checkbox') {
				input.checked = config[input.name];
			} else if (input.type == 'radio') {
				var value = config[input.name].toString()
				if (input.value == value) {
					input.checked = true;
				}
			}
			
			input.addEvent('change', function(el) {
				if (input.type == 'checkbox') {
					if (this.original[input.name] == input.checked) {
						if (this.changed[input.name])
							delete this.changed[input.name];
					} else {
						this.changed[input.name] = input.checked
					}
				} else {
					if (this.original[input.name] == input.value) {
						if (this.changed[input.name])
							delete this.changed[input.name];
					} else {
						this.changed[input.name] = input.value;
					}
				}
			}.bindWithEvent(this))
		}, this);
		this.fireEvent('update');
	},

	getConfig: function() {
		changed = {}
		this.changed.each(function(value, key) {
			var type = $type(this.original[key]);
			if (type == 'number') {
				changed[key] = value.toFloat();
			} else if (type == 'string') {
				changed[key] = value.toString();
			} else if (type == 'boolean') {
				changed[key] = value.toBoolean();
			}
		}, this);
		return changed;
	}
});

Deluge.Widgets.WebUIPreferences = new Class({
	Extends: Deluge.Widgets.GenericPreferences,
	
	options: {
		url: '/template/render/html/preferences_webui.html'
	},
	
	initialize: function() {
		this.parent('Web UI');
		this.core = false;
		this.addEvent('beforeUpdate', this.beforeUpdate.bindWithEvent(this));
		this.addEvent('update', this.updated.bindWithEvent(this));
	},
	
	beforeUpdate: function(event) {
		var templates = Deluge.Client.get_webui_templates({async: false});
		templates.each(function(template) {
			var option = new Element('option');
			option.set('text', template);
			this.form.template.grab(option);
		}, this);
	},
	
	updated: function(event) {
		if (this.form.template.value != 'ajax')
			this.form.theme.disabled = true;
		else
			this.form.theme.disabled = false;
			
		var theme = this.form.theme.getElement('option[value="' + Cookie.read('theme') + '"]')
		theme.selected = true
		
		this.form.template.addEvent('change', function(e) {
			if (this.form.template.value != 'ajax') {
				this.form.theme.disabled = true;
				this.form.theme.addClass('disabled')
				this.form.getElementById('lbl_theme').addClass('disabled')
			} else {
				this.form.theme.disabled = false;
				this.form.getElementById('lbl_theme').removeClass('disabled')
				this.form.theme.removeClass('disabled')
			}
		}.bindWithEvent(this));
	},
	
	apply: function() {
		Deluge.UI.setTheme(this.form.theme.value);
		Deluge.Client.set_webui_config(this.changed, {
			onSuccess: function(e) {
				if (this.changed['template']) location.reload(true);
			}.bindWithEvent(this)
		});
	}
});

Deluge.Widgets.PreferencesWindow = new Class({
	Extends: Widgets.Window,
	options: {
		width: 500,
		height: 430,
		title: 'Preferences',
		url: '/template/render/html/window_preferences.html'
	},
	
	initialize: function() {
		this.parent();
		this.categories = [];
		this.currentPage = -1;
		this.addEvent('loaded', this.loaded.bindWithEvent(this));
		this.addEvent('beforeShow', this.beforeShown.bindWithEvent(this));
	},
	
	loaded: function(event) {
		this.catlist = this.content.getElement('.categories ul');
		this.pages = this.content.getElement('.pref_pages');
		this.title = this.pages.getElement('h3');
		
		this.reset = this.content.getElement('.buttons .reset');
		this.apply = this.content.getElement('.buttons .apply');
		this.apply.addEvent('click', this.applied.bindWithEvent(this));
		
		this.webui = new Deluge.Widgets.WebUIPreferences();
		
		this.download = new Deluge.Widgets.GenericPreferences('Download', {
			url: '/template/render/html/preferences_download.html'
		});
		this.network = new Deluge.Widgets.GenericPreferences('Network', {
			url: '/template/render/html/preferences_network.html'
		});
		this.bandwidth = new Deluge.Widgets.GenericPreferences('Bandwidth', {
			url: '/template/render/html/preferences_bandwidth.html'
		});
		this.daemon = new Deluge.Widgets.GenericPreferences('Daemon', {
			url: '/template/render/html/preferences_daemon.html'
		});
		this.queue = new Deluge.Widgets.GenericPreferences('Queue', {
			url: '/template/render/html/preferences_queue.html'
		});
		
		this.addCategory(this.webui);
		this.addCategory(this.download);
		this.addCategory(this.network);
		this.addCategory(this.bandwidth);
		this.addCategory(this.daemon);
		this.addCategory(this.queue);
	},
	
	addCategory: function(category) {
		this.categories.include(category);
		var categoryIndex = this.categories.indexOf(category);
		
		var tab = new Element('li');
		tab.set('text', category.name);
		tab.addEvent('click', function(e) {
			this.select(categoryIndex);
		}.bindWithEvent(this));
		category.tab = tab;

		this.catlist.grab(tab);
		this.pages.grab(category.addClass('deluge-prefs-page'));
		
		
		if (this.currentPage < 0) {
			this.currentPage = categoryIndex;
			this.select(categoryIndex);
		};
	},
	
	select: function(id) {
		this.categories[this.currentPage].removeClass('deluge-prefs-page-active');
		this.categories[this.currentPage].tab.removeClass('deluge-prefs-active');
		this.categories[id].addClass('deluge-prefs-page-active');
		this.categories[id].tab.addClass('deluge-prefs-active');
		this.title.set('text', this.categories[id].name);
		this.currentPage = id;
		this.fireEvent('pageChanged');
	},
	
	applied: function(event) {
		var config = {};
		this.categories.each(function(category) {
			config = $merge(config, category.getConfig());
		});
		if ($defined(config['end_listen_port']) || $defined(config['start_listen_port'])) {
			var startport = $pick(config['start_listen_port'], this.config['listen_ports'][0]);
			var endport = $pick(config['end_listen_port'], this.config['listen_ports'][1]);
			delete config['end_listen_port'];
			delete config['start_listen_port'];
			config['listen_ports'] = [startport, endport];
		}
		Deluge.Client.set_config(config, {
			onSuccess: function(e) {
				this.hide();
			}.bindWithEvent(this)
		});
		this.webui.apply();
	},

	beforeShown: function(event) {
		// we want this to be blocking
		this.config = Deluge.Client.get_config({async: false});

		// Unfortunately we have to modify the listen ports preferences
		// in order to not have to modify the generic preferences class.
		this.config['start_listen_port'] = this.config['listen_ports'][0];
		this.config['end_listen_port'] = this.config['listen_ports'][1];

		// Iterate through the pages and set the fields
		this.categories.each(function(category) {
			if (category.update && category.core) category.update(this.config);
		}, this);
		
		// Update the config for the webui pages.
		var webconfig = Deluge.Client.get_webui_config({async: false});
		this.webui.update(webconfig);
	}
});
