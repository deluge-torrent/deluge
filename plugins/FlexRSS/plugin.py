class plugin_FlexRSS_Config:
	feeds_counter = 0
	filters_counter = 0
	feeds = None
	filters = None

# 	def listFilters(self):
# 		if not self.filters:
# 			return

# 		print 'Filters:'
# 		for filter in self.filters:
# 			print '+ id:       %d' % filter['id'] 
# 			print '  name:     %s' % filter['name'] 
# 			print '  type:     %s' % filter['type'] 
# 			print '  patterns:'
# 			for p in filter['patterns']:
# 				print '  + [%s]' % p[1]
# 				print '    %s' % p[0]

# 	def listFeeds(self):
# 		if not self.feeds:
# 			return

# 		print 'Feeds:'
# 		for feed in self.feeds:
# 			print '+ id:       %d' % feed['id']
# 			print '  name:     %s' % feed['name']
# 			print '  url:      %s' % feed['url']
# 			print '  interval: %d' % feed['interval']

	def getFilter(self, id):
		if not self.filters:
			return None

		for filter in self.filters:
			if filter['id'] == id:
				return filter

		return None

	def setFilter(self, id, key, value):
		filter = self.getFilter(id)

		if not filter:
			return False
		else:
			filter[key] = value
			return True

	def addFilter(self, name, type, patterns, feeds):
		id = self.feeds_counter + 1
		self.feeds_counter = id

		if not self.filters:
			self.filters = []

		filter = { "id"       : id,
				   "name"     : name,
				   "type"     : type,
				   "patterns" : patterns,
				   "feeds"    : feeds,
				   "history"  : {} }

		self.filters.append(filter)

		return id

	def deleteFilter(self, id):
		if not self.filters:
			return False

		i = 0
		while i < len(self.filters):
			if self.filters[i]['id'] == id:
				del self.filters[i]
				return True
			i = i + 1

	def checkHistory(self, id, type, data):
		filter = self.getFilter(id)

		if not filter:
			return False

		try:
			if type == 'TV Show':
				filter['history'][type][data['series']].index(data['episode'])
				return True
			elif type == 'TV Show (dated)':
				filter['history'][type][data['year']][data['month']].index(data['day'])
				return True
			else:
				filter['history'][type].index(data['url'])
				return True
		except:
			return False

	def addHistory(self, id, type, data):
		filter = self.getFilter(id)

		if not filter:
			return False

		if type == 'TV Show':
			if not filter['history'].has_key(type):
				filter['history'][type] = {}
			if not filter['history'][type].has_key(data['series']):
				filter['history'][type][data['series']] = []
			filter['history'][type][data['series']].append(data['episode'])
		elif type == 'TV Show (dated)':
			if not filter['history'].has_key(type):
				filter['history'][type] = {}
			if not filter['history'][type].has_key(data['year']):
				filter['history'][type][data['year']] = {}
			if not filter['history'][type][data['year']].has_key(data['month']):
				filter['history'][type][data['year']][data['month']] = []
			filter['history'][type][data['year']][data['month']].append(data['day'])
		else:
			if not filter['history'].has_key(type):
				filter['history'][type] = []
			filter['history'][type].append(data['url'])

	def getFeed(self, id):
		if not self.feeds:
			return None

		for feed in self.feeds:
			if feed['id'] == id:
				return feed

		return None

	def setFeed(self, id, key, value):
		feed = self.getFeed(id)

		if not feed:
			return False
		else:
			feed[key] = value
			return True

	def addFeed(self, name, url, interval):
		# Uhhh... no ++? WTF is the increment operator?
		id = self.feeds_counter + 1
		self.feeds_counter = id

		if not self.feeds:
			self.feeds = []

		self.feeds.append({ "id"       : id,
							"name"     : name,
							"url"      : url,
							"interval" : interval })

		return id

	def deleteFeed(self, id):
		if not self.feeds:
			return False

		i = 0
		while i < len(self.feeds):
			if self.feeds[i]['id'] == id:
				del self.feeds[i]
				return True
			i = i + 1

class plugin_FlexRSS:
	config = None
	glade = None
	feeds = None

	def load_config(self):
		import deluge.common, os

		file = deluge.common.CONFIG_DIR + "/flexrss.dat"
		if os.path.isfile(file):
			import pickle

			fd = open(file, 'r')
			self.config = pickle.load(fd)
			fd.close()
		else:
			self.config = plugin_FlexRSS_Config()

	def write_config(self):
		import deluge.common, os, pickle

		file = deluge.common.CONFIG_DIR + "/flexrss.dat"
		fd = open(file, 'w')
		pickle.dump(self.config, fd)
		fd.close()

	def configure_cb_closed(self, args):
		self.glade = None

	def configure_cb_feed_new(self, args):
		feed = { "name"     : 'Untitled',
			 "url"      : 'http://',
			 "interval" : 900,
			 "id"       : 0 }

		feed["id"] = self.config.addFeed(feed["name"], feed["url"], feed["interval"])

		view = self.glade.get_widget("FlexRSS_Feeds")
		model = view.get_model()
		view.get_selection().select_iter(model.append(None, (feed["id"], feed["name"], feed["url"])))

	def configure_cb_feed_selected(self, selection):
		model, iter = selection.get_selected()

		if not iter:
			return

		parent = model.iter_parent(iter)
		if parent: # Selected a filter
			iter = parent

		# We want to edit a feed.
		feed = self.config.getFeed(model.get_value(iter, 0))
		if not feed:
			print 'Error: could not find feed #' + str(model.get_value(iter, 0))
			return

		self.glade.get_widget("FlexRSS_EditFeed_Name").set_text(feed["name"])
		self.glade.get_widget("FlexRSS_EditFeed_URL").set_text(feed["url"])
		self.glade.get_widget("FlexRSS_EditFeed_Interval").set_text(str(feed["interval"]))
		self.glade.get_widget('FlexRSS_Feeds_Editor').show()

	def configure_cb_feed_delete(self, arg, id=None):
		if not id:
			# Which feed is selected?
			selection = self.glade.get_widget("FlexRSS_Feeds").get_selection()
			model, iter = selection.get_selected()

			if not iter:
				return

			id = model.get_value(iter, 0)
		else:
			model = self.glade.get_widget("FlexRSS_Feeds").get_model()
			iter = model.get_iter_first()
			while iter:
				if model.get_value(iter, 0) == id:
					break
				iter = model.iter_next(iter)

		if not iter:
			print 'Couldn\'t find feed.'
			return

		# Remove from config
		if not self.config.deleteFeed(id):
			print 'Unable to delete feed #' + str(id)
			return

		# Remove from UI
		model.remove(iter)

		self.write_config()

		# We are no longer editing a feed, so hide the editing widgets.
		self.glade.get_widget('FlexRSS_Feeds_Editor').hide()

	def configure_cb_feed_save(self, arg, id=None):
		if not id:
			# Which feed is selected?
			selection = self.glade.get_widget("FlexRSS_Feeds").get_selection()
			model, iter = selection.get_selected()

			if not iter:
				return

			id = model.get_value(iter, 0)
		else:
			model = self.glade.get_widget("FlexRSS_Feeds").get_model()
			iter = model.iter_first()
			while iter:
				if model.get_value(iter, 0) == id:
					break
				iter = iter.iter_next(iter)

		if not iter:
			print 'Couldn\'t find feed.'
			return

		# Update configuration
		self.config.setFeed(id, "name", self.glade.get_widget("FlexRSS_EditFeed_Name").get_text())
		self.config.setFeed(id, "url", self.glade.get_widget("FlexRSS_EditFeed_URL").get_text())
		self.config.setFeed(id, "interval", int(self.glade.get_widget("FlexRSS_EditFeed_Interval").get_text()))
		self.write_config()

		# Update UI
		feed = self.config.getFeed(id)
		model.set_value(iter, 0, feed["id"])
		model.set_value(iter, 1, feed["name"])
		model.set_value(iter, 2, feed["url"])

		if not self.feeds.has_key(id):
			self.feeds[id] = { 'cfg'     : feed,
							   'updated' : 0,
							   'data'    : [] }

	def configure_cb_filter_new(self, arg, test_pattern=None):
		filter = { "name"     : "Untitled",
				   "type"     : "Generic",
				   "patterns" : [('', 'Title')],
				   "feeds"    : [0],
				   "id"       : 0 }

		if test_pattern:
			# Try to guess a good pattern
			import re, string

			trans_table = string.maketrans(' ', '.')

			# TV Show
			exp = re.compile('(.*).([0-9]+)x([0-9]+)', re.IGNORECASE)
			match = exp.match(test_pattern)
			if match:
				pattern = match.group(1).lower().translate(trans_table) + '.%sx%e'
				filter['patterns'][0] = (pattern, 'Title')
				filter['name'] = match.group(1)
				filter['type'] = 'TV Show'

			if not match:
				exp = re.compile('(.*).S([0-9]+)E([0-9]+)', re.IGNORECASE)
				match = exp.match(test_pattern)
				if match:
					pattern = match.group(1).lower().translate(trans_table) + '.S%sE%e'
					filter['patterns'][0] = (pattern, 'Title')
					filter['name'] = match.group(1)
					filter['type'] = 'TV Show'

			if not match:
				exp = re.compile('(.*).([0-9]{4}).([0-9]{1,2}).([0-9]{1,2})', re.IGNORECASE)
				match = exp.match(test_pattern)
				if match:
					pattern = None
					if ((int(match.group(3)) <= 12) and (int(match.group(4)) <= 31)):
						pattern = match.group(1).lower().translate(trans_table) + '.%Y.%m.%d'
					elif ((int(match.group(3)) <= 31) and (int(match.group(4)) <= 12)):
						pattern = match.group(1).lower().translate(trans_table) + '.%Y.%d.%m'

					if pattern:
						filter['patterns'][0] = (pattern, 'Title')
						filter['name'] = match.group(1)
						filter['type'] = 'TV Show (dated)'
					else:
						match = None

			if not match:
				exp = re.compile('(.*).([0-9]+)', re.IGNORECASE)
				match = exp.match(test_pattern)
				if match:
					pattern = match.group(1).lower().translate(trans_table) + '.%e'
					filter['patterns'][0] = (pattern, 'Title')
					filter['name'] = match.group(1)
					filter['type'] = 'TV Show'

		# Add to config
		filter['id'] = self.config.addFilter(filter['name'], filter['type'], filter['patterns'], 'feeds')

		# Add to UI
		self.configure_ui_add_filter(self.config.getFilter(filter['id']), test_pattern)

	def configure_cb_filter_selected(self, selection):
		model, iter = selection.get_selected()

		if not iter:
			return

		# We want to edit a filter.
		filter = self.config.getFilter(model.get_value(iter, 0))
		if not filter:
			print 'Error: could not find filter #' + str(model.get_value(iter, 0))
			return

		self.glade.get_widget('FlexRSS_Filters_Name').set_text(filter['name'])

		if filter['type'] == 'TV Show':
			type_i = 1
		elif filter['type'] == 'TV Show (dated)':
			type_i = 2
		else:
			type_i = 0

		self.glade.get_widget('FlexRSS_Filters_Type').set_active(type_i)

		selection = self.glade.get_widget('FlexRSS_Filters_Feed').get_selection()
		selection.unselect_all()
		feed_model = self.glade.get_widget('FlexRSS_Filters_Feed').get_model()
		for i in filter['feeds']:
			if i == 0:
				selection.select_all()
			else:
				iter = feed_model.get_iter_first()
				while iter:
					if feed_model.get_value(iter, 0) == i:
						selection.select_iter(iter)
					iter = feed_model.iter_next(iter)

		filter_patterns = self.glade.get_widget('FlexRSS_Filter_Patterns_List')
		for child in filter_patterns.get_children():
			child.destroy()
		for pattern in filter['patterns']:
			self.configure_ui_add_pattern(pattern)

	def configure_cb_filter_save(self, arg):
		# Which feed is selected?
		selection = self.glade.get_widget("FlexRSS_Filters_List").get_selection()
		model, iter = selection.get_selected()

		if not iter:
			return

		id = model.get_value(iter, 0)
		name = self.glade.get_widget('FlexRSS_Filters_Name').get_text()
		self.config.setFilter(id, 'name', name)
		iter = model.get_iter_first()
		while iter:
			if model.get_value(iter, 0) == id:
				model.set_value(iter, 1, name)
			iter = model.iter_next(iter)

		type = self.glade.get_widget('FlexRSS_Filters_Type').get_active()
		if type == 1:
			type_s = 'TV Show'
		elif type == 2:
			type_s = 'TV Show (dated)'
		else:
			type_s = 'Generic'
		self.config.setFilter(id, 'type', type_s)

		model, paths = self.glade.get_widget('FlexRSS_Filters_Feed').get_selection().get_selected_rows()
		feeds = []
		for path in paths:
			feeds.append(model.get_value(model.get_iter(path), 0))
		if len(feeds) == 0:
			feeds.append(0)
		self.config.setFilter(id, 'feeds', feeds)

		patterns = []
		filter_patterns = self.glade.get_widget('FlexRSS_Filter_Patterns_List')
		for i in filter_patterns.get_children():
			data = i.get_children()
			pattern = data[0].get_text()
			if data[2].get_active() == 1:
				type = 'Link'
			else:
				type = 'Title'
			patterns.append((pattern, type))
		self.config.setFilter(id, 'patterns', patterns)

		self.write_config()

	def configure_cb_remove_pattern(self, arg):
		arg.get_parent().destroy()

	def configure_ui_add_pattern(self, pattern):
		import gtk, gobject

		filter_patterns = self.glade.get_widget('FlexRSS_Filter_Patterns_List')

		hbox = gtk.HBox()
		filter_patterns.pack_start(hbox)

		input = gtk.Entry()
		input.set_text(pattern[0])
		input.connect("changed", self.configure_cb_test_filter)

		on = gtk.Label()
		on.set_text('On')
		on.show()

		combo = gtk.combo_box_new_text()
		combo.append_text('Title')
		combo.append_text('Link')
		if pattern[1] == 'Link':
			combo.set_active(1)
		else:
			combo.set_active(0)

		remove = gtk.Button(stock=gtk.STOCK_REMOVE)
		remove.connect("pressed", self.configure_cb_remove_pattern)

		hbox.pack_start(input)
		hbox.pack_start(on, expand=False)
		hbox.pack_start(combo, expand=False)
		hbox.pack_start(remove, expand=False)

		hbox.show_all()

	def configure_cb_add_pattern(self, args):
		self.configure_ui_add_pattern(('', 'Title'))

	def configure_ui_add_filter(self, filter, test_pattern=None):
		if not filter:
			print 'No filter to add'
			return None

		model = self.glade.get_widget("FlexRSS_Filters_List").get_model()
		iter = model.append(None, (filter['id'], filter['name']))

		if not iter:
			return

		view = self.glade.get_widget("FlexRSS_Filters_List")
		model = view.get_model()
		view.get_selection().select_iter(iter)

		if test_pattern:
			self.glade.get_widget('FlexRSS_Filters_Test_Pattern').set_text(test_pattern)
			self.configure_cb_test_filter(None)

		self.glade.get_widget('FlexRSS_MainNotebook').set_current_page(1)

	def configure_ui_test_result(self, result):
		if result:
			self.glade.get_widget('FlexRSS_Filters_Test_Result').set_text('Match')
		else:
			self.glade.get_widget('FlexRSS_Filters_Test_Result').set_text('Doesn\'t match')

		type = self.glade.get_widget('FlexRSS_Filters_Type').get_active()

		if type == 0: # Generic
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow').hide()
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated').hide()
		elif type == 1: # TV Show
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow').show()
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated').hide()
			if result:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Series').set_text(str(result['series']))
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Episode').set_text(str(result['episode']))
			else:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Series').set_text('0')
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Episode').set_text('0')
		else: # TV Show (dated)
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow').hide()
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated').show()
			if result:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Year').set_text(str(result['year']))
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Month').set_text(str(result['month']))
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Day').set_text(str(result['day']))
			else:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Year').set_text('0')
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Month').set_text('0')
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Day').set_text('0')

	def configure_cb_test_filter(self, filter):
		subject = self.glade.get_widget('FlexRSS_Filters_Test_Pattern').get_text()

		if len(subject) > 1:
			type = self.glade.get_widget('FlexRSS_Filters_Type').get_active()
			if type == 1:
				type_s = 'TV Show'
			elif type == 2:
				type_s = 'TV Show (dated)'
			else:
				type_s = 'Generic'

			filter_patterns = self.glade.get_widget('FlexRSS_Filter_Patterns_List')
			for i in filter_patterns.get_children():
				data = i.get_children()
				pattern = data[0].get_text()
				if len(pattern):
					result = self.test_pattern(type_s, subject, pattern)
					if result:
						self.configure_ui_test_result(result)
						return

			self.configure_ui_test_result(False)

	def configure_cb_delete_filter(self, arg):
		# Which filter is selected?
		selection = self.glade.get_widget("FlexRSS_Filters_List").get_selection()
		model, iter = selection.get_selected()

		if not iter:
			return

		id = model.get_value(iter, 0)

		# Remove from config
		if not self.config.deleteFilter(id):
			print 'Unable to delete filter #' + str(id)
			return
		self.write_config()

		# Remove from UI
		model.remove(iter)

		# Fuck it--just leave the crap in the widgets. Todo: fix it so
		# the save button will create a new filter if it must.

	def configure_cb_feed_refresh(self, caller, id=None):
		if not id:
			selection = self.glade.get_widget("FlexRSS_Feeds").get_selection()
			model, iter = selection.get_selected()

			if not iter:
				return

			id = model.get_value(iter, 0)

		if id:
			self.parse_feed(id)

	def configure_cb_feed_popup(self, view, event):
		if event.button != 3:
			return

		model = view.get_model()
		coords = event.get_coords()
		path = view.get_path_at_pos(int(coords[0]), int(coords[1]))
		if path:
			iter = model.get_iter(path[0])
		else:
			iter = None

		import gtk

		popup = gtk.Menu()

		if iter:
			id = model.get_value(iter, 0)
			if id: # Feed
				item_refresh = gtk.MenuItem("Refresh")
				item_refresh.connect("activate", self.configure_cb_feed_refresh, id)
				popup.append(item_refresh)
				item_delete = gtk.MenuItem("Delete")
				item_delete.connect("activate", self.configure_cb_feed_delete, id)
				popup.append(item_delete)
			else: # Filter
				item_filter = gtk.MenuItem("Create filter")
				item_filter.connect("activate", self.configure_cb_filter_new, model.get_value(iter, 1))
				popup.append(item_filter)
		else: # Neither
			item_new = gtk.MenuItem("New feed")
			item_new.connect("activate", self.configure_cb_feed_new)
			popup.append(item_new)

		popup.popup(None, None, None, event.button, event.time)
		popup.show_all()

	def configure(self):
		if self.glade: # Dialog already running
			return

		import gtk, gtk.glade, gobject

		self.glade = gtk.glade.XML(self.path + "/FlexRSS.glade")

		# Intialize feed lists
		feeds_model = gtk.TreeStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING)
		feeds_view = self.glade.get_widget("FlexRSS_Feeds")
		filters_feeds_view = self.glade.get_widget("FlexRSS_Filters_Feed")
		feeds_view.set_model(feeds_model)
		filters_feeds_view.set_model(feeds_model)

		# Setup columns for feeds tab
		renderer_name = gtk.CellRendererText()
		column_name = gtk.TreeViewColumn("Name", renderer_name, text=1)
		feeds_view.append_column(column_name)
		renderer_url = gtk.CellRendererText()
		column_url = gtk.TreeViewColumn("URL", renderer_url, text=2)
		feeds_view.append_column(column_url)

		# Set callback for when selection is changed in feeds tab
		# I can't figure out how to do this in Glade
		feeds_view.get_selection().connect("changed", self.configure_cb_feed_selected)

		# Setup columns for feed list on filters tab
		renderer_name = gtk.CellRendererText()
		column_name = gtk.TreeViewColumn("Name", renderer_name, text=1)
		filters_feeds_view.append_column(column_name)

		# Allow multiple selections of feeds in filters tab
		# I can't figure out how to do this in Glade
		filters_feeds_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

		# Populate feed lists
		if self.config.feeds:
			for feed in self.config.feeds:
				this_feed = feeds_model.append(None, (feed['id'], feed['name'], feed['url']))
				for item in self.feeds[feed['id']]['data']:
					feeds_model.append(this_feed, (0, item['title'], item['link']))
					

		# Initialize filters list
		filters_model = gtk.TreeStore(gobject.TYPE_INT, gobject.TYPE_STRING)
		filters_view = self.glade.get_widget("FlexRSS_Filters_List")
		filters_view.set_model(filters_model)

		# Setup columns for filters list
		renderer_name = gtk.CellRendererText()
		column_name = gtk.TreeViewColumn("Name", renderer_name, text=1)
		filters_view.append_column(column_name)

		# Set callback for when selection is changed in feeds tab
		# I can't figure out how to do this in Glade
		filters_view.get_selection().connect("changed", self.configure_cb_filter_selected)

		# Populate filters list
		if self.config.filters:
			for filter in self.config.filters:
				filters_model.append(None, (filter['id'], filter['name']))

		# Callbacks for UI events
		actions = { # Feeds tab
			    "on_FlexRSS_MainWindow_destroy"       : self.configure_cb_closed,
			    "on_FlexRSS_Feeds_New_pressed"        : self.configure_cb_feed_new,
			    "on_FlexRSS_Feeds_Save_pressed"       : self.configure_cb_feed_save,
			    "on_FlexRSS_Feeds_Delete_pressed"     : self.configure_cb_feed_delete,
				"on_FlexRSS_Feeds_button_press_event" : self.configure_cb_feed_popup,

			    # Filters tab
			    "on_FlexRSS_Filters_Add_pressed"       : self.configure_cb_filter_new,
			    "on_FlexRSS_Action_Save_pressed"       : self.configure_cb_filter_save,
			    "on_FlexRSS_Filter_Patern_Add_pressed" : self.configure_cb_add_pattern,
				"on_FlexRSS_Filters_Test_Pattern"      : self.configure_cb_test_filter,
				"on_FlexRSS_Filters_Delete_pressed"    : self.configure_cb_delete_filter }
		self.glade.signal_autoconnect(actions)

		self.glade.get_widget("FlexRSS_MainWindow").show()

	def cmp_history(a, b):
		try:
			if a.has_key('series'):
				if a['series'] > b['series']:
					return 1
				elif a['series'] < b['series']:
					return -1
				else:
					if a['episode'] > b['episode']:
						return 1
					elif a['episode'] < b['episode']:
						return -1
					else:
						return 0
		except:
			return 0

	def strptime2regex(self, input):
		# Does'n exactly live up to its name yet. Currently just
		# replaces %y,%Y,%m,%d with named patterns. In the future, it
		# would be nice to allow escaping (e.g., %%Y means literal %Y)
		# and expand it to support other formats.
		patterns = [('%Y', '(?P<Y>[0-9]{4})'),
					('%y', '(?P<y>[0-9]{2})'),
					('%m', '(?P<m>[0-9]{1,2})'),
					('%d', '(?P<d>[0-9]{1,2})')]

		out = input
		for p in patterns:
			out = out.replace(p[0], p[1])

		return out

	def replace_tv_show_patterns(self, input):
		patterns = [('%s', '(?P<series>[0-9]+)'),
					('%e', '(?P<episode>[0-9]+)')]

		out = input
		for p in patterns:
			out = out.replace(p[0], p[1])

		return out

	def test_pattern(self, type, subject, pattern):
		import re, time
		result = False

		if type == 'TV Show (dated)':
			pattern = self.strptime2regex(pattern)
		elif type == 'TV Show':
			pattern = self.replace_tv_show_patterns(pattern)

		# Wow, so this is lame...
		if pattern[0] != '^':
			pattern = '.*' + pattern

		try:
			exp = re.compile(pattern, re.IGNORECASE)
		except:
			print 'Broken expression: ' + pattern
			return False

		match = exp.match(subject)
		if match:
			print 'Match: ' + subject
			print '       ' + pattern
			if type == 'TV Show':
				try:
					series = int(match.group('series'))
				except:
					try:
						series = int(match.group('season'))
					except:
						series = 0

				try:
					episode = int(match.group('episode'))
				except:
					episode = 0

				result = { 'series'  : series,
						   'episode' : episode }

			elif type == 'TV Show (dated)':
				try:
					year = int(match.group('Y'))
				except:
					try:
						year = int(match.group('y'))
						if year > 70:
							year += 1900
						else:
							year += 2000
					except:
						year = 0

				try:
					month = int(match.group('m'))
				except:
					month = 0

				try:
					day = int(match.group('d'))
				except:
					day = 0

				result = { 'year'  : year,
						   'month' : month,
						   'day'   : day }

			else:
				result = True

		return result

	def parse_feed(self, id):
		import time, feedparser

		feed = self.config.getFeed(id)

		print 'Updating feed #' + str(id)
		parsed = feedparser.parse(feed['url'])
		if (not parsed) or (not parsed.entries):
			print 'Unable to parse feed: ' + feed['url']
			return

		data = []

		for entry in parsed.entries:
			try:
				data.append({ 'title' : entry['title'],
							  'link'  : entry.links[0]['href'] })
			except:
				continue

			if self.config.filters:
				for filter in self.config.filters:
					if not ((feed['id'] in filter['feeds']) or (0 in filter['feeds'])):
						continue

					for pattern in filter['patterns']:
						# (setq python-indent 4
						#       tab-width 4)
						# Okay, I dislike python substantially less now.
						try:
							if pattern[1] == 'Title':
								subject = entry['title']
							else:
								subject = entry['links'][0]['href']
						except:
							print 'Unable to find subject.'

						match = self.test_pattern(filter['type'], subject, pattern[0])
						if match:
							# Filter matched. Check history to see if
							# we should download it.
							if filter['type'] == 'Generic': # Dirty hack.
								match = { 'url' : entry.links[0]['href'] }

							if not self.config.checkHistory(filter['id'], filter['type'], match):
								self.config.addHistory(filter['id'], filter['type'], match)
								self.write_config()
								print 'Downloading'
								self.interface.interactive_add_torrent_url(entry.links[0]['href'])
							else:
								print 'Skipping (history)'

			self.feeds[feed['id']]['data'] = data
			if self.glade: # Update config window...
				# Todo: Fix this. It was just easier to clear
				# everything and rebuild from scratch
				feeds_model = self.glade.get_widget("FlexRSS_Feeds").get_model()
				feeds_model.clear()

				for feed in self.config.feeds:
					this_feed = feeds_model.append(None, (feed['id'], feed['name'], feed['url']))
					for item in self.feeds[feed['id']]['data']:
						feeds_model.append(this_feed, (0, item['title'], item['link']))
	def update(self):
		import time

		current_time = time.time()

		# I feel dirty for this. Oh, how I miss C.
		for id in self.feeds:
			if (current_time - self.feeds[id]['cfg']['interval']) > self.feeds[id]['updated']:
				self.feeds[id]['updated'] = current_time
				self.parse_feed(self.feeds[id]['cfg']['id'])

	def __init__(self, path, core, interface):
		self.path = path
		self.core = core
		self.interface = interface

		self.load_config()

		self.feeds = {}
		if self.config.feeds:
			for feed in self.config.feeds:
				self.feeds[feed['id']] = { 'cfg'     : feed,
										   'updated' : 0,
										   'data'    : [] }

		# Debugging stuff
		# self.configure()
		# self.config.listFilters()
		# self.config.listFeeds()
