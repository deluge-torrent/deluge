def gtk_treeview_search_cb_stristr(model, column, key, iter, data=None):
	value = model.get_value(iter, column)
	if value.lower().find(key.lower()) > -1:
		return False
	else:
		return True

class plugin_FlexRSS_Config:
	constants = {
		'Generic'         : 0,
		'TV Show'         : 1,
		'TV Show (dated)' : 2 }
	feeds_counter = 0
	filters_counter = 0
	feeds = None
	filters = None
	version = 0
	show_toolbar_button = False
	threaded_retrieval = False

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
				   "history"  : {},
				   "path"     : None,
				   "enabled"  : True,
				   "queue_top": False,
				   "pause"    : False,
				   "delete"   : False}

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
			if type == self.constants['TV Show']:
				filter['history'][type][data['series']].index(data['episode'])
				return True
			elif type == self.constants['TV Show (dated)']:
				filter['history'][type][data['year']][data['month']].index(data['day'])
				return True
			else:
				filter['history'][type].index(data['url'])
				return True
		except:
			return False

	def checkRange(self, id, type, data):
		filter = self.getFilter(id)

		if not filter:
			return False

		if type == self.constants['TV Show']:
			if filter['history'][type].has_key('from'):
				if data['series'] < filter['history'][type]['from']['season']:
					return False
				elif data['series'] == filter['history'][type]['from']['season']:
					if data['episode'] < filter['history'][type]['from']['episode']:
						return False

			if filter['history'][type].has_key('thru'):
				if data['series'] > filter['history'][type]['thru']['season']:
					return False
				elif data['series'] == filter['history'][type]['thru']['season']:
					if data['episode'] > filter['history'][type]['thru']['episode']:
						return False

			return True

		elif type == self.constants['TV Show (dated)']:
			if filter['history'][type].has_key('from'):
				if data['year'] < filter['history'][type]['from']['year']:
					return False
				elif data['year'] == filter['history'][type]['from']['year']:
					if data['month'] < filter['history'][type]['from']['month']:
						return False
					elif data['month'] == filter['history'][type]['from']['month']:
						if data['day'] < filter['history'][type]['from']['day']:
							return False

			if filter['history'][type].has_key('thru'):
				if data['year'] > filter['history'][type]['thru']['year']:
					return False
				elif data['year'] == filter['history'][type]['thru']['year']:
					if data['month'] > filter['history'][type]['thru']['month']:
						return False
					elif data['month'] == filter['history'][type]['thru']['month']:
						if data['day'] > filter['history'][type]['thru']['day']:
							return False

			return True

		else:
			return True

	def addHistory(self, id, type, data):
		filter = self.getFilter(id)

		if not filter:
			return False

		if type == self.constants['TV Show']:
			if not filter['history'].has_key(type):
				filter['history'][type] = {}
			if not filter['history'][type].has_key(data['series']):
				filter['history'][type][data['series']] = []
			filter['history'][type][data['series']].append(data['episode'])
		elif type == self.constants['TV Show (dated)']:
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
			try:
				filter['history'][type].append(data['url'])
			except AttributeError, e:
				filter['history'][type] = [data['url']]

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
							"interval" : interval,
							"enabled"  : True })

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
	toolbar_button = None
	history_calendarbuttons = None

	def update_config(self):
		if self.config.version >= 5:
			return

		if self.config.version < 1:
			print 'Updating config to v1'
			i = 0
			while i < len(self.config.filters):
				self.config.filters[i]['enabled'] = True
				i = i + 1

		if self.config.version < 2:
			print 'Updating config to v2'
			i = 0
			while i < len(self.config.feeds):
				self.config.feeds[i]['enabled'] = True
				i = i + 1

		if self.config.version < 3:
			print 'Updating config to v3'
			i = 0
			while i < len(self.config.filters):
				type_s = self.config.filters[i]['type']
				type_i = self.config.constants[type_s]
				if self.config.filters[i]['history'].has_key(type_s):
					history = { type_i: self.config.filters[i]['history'][type_s] }
					self.config.filters[i]['history'] = history
				self.config.filters[i]['type'] = self.config.constants[self.config.filters[i]['type']];
				i = i + 1

		if self.config.version < 4:
			print 'Updating config to v4'
			i = 0
			while i < len(self.config.filters):
				self.config.filters[i]['queue_top'] = False
				self.config.filters[i]['pause'] = False
				i = i + 1

		if self.config.version < 5:
			print 'Updating config to v5'
			i = 0
			while i < len(self.config.filters):
				self.config.filters[i]['delete'] = False
				i = i + 1

		self.config.version = 5
		self.write_config()

	def load_config(self):
		import deluge.common, os, cookielib

		file = deluge.common.CONFIG_DIR + "/flexrss.dat"
		if os.path.isfile(file):
			import pickle

			fd = open(file, 'r')
			self.config = pickle.load(fd)
			fd.close()
		else:
			self.config = plugin_FlexRSS_Config()
			self.config.version = 5

		self.update_config()

		cookie_file = deluge.common.CONFIG_DIR + "/flexrss-cookies.txt"
		self.cookies = cookielib.MozillaCookieJar()
		if os.path.isfile(cookie_file):
			self.cookies.load(cookie_file)

	def write_config(self, write_cookies=False):
		import deluge.common, os, pickle

		file = deluge.common.CONFIG_DIR + "/flexrss.dat"
		fd = open(file, 'w')
		pickle.dump(self.config, fd)
		fd.close()

		if write_cookies:
			print "Saving cookies."
			self.cookies.save(deluge.common.CONFIG_DIR + "/flexrss-cookies.txt")

	def configure_cb_closed(self, args):
		self.glade = None
		self.history_calendarbuttons = None

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
			self.glade.get_widget('FlexRSS_Filters_Test_Pattern').set_text(model.get_value(iter, 1))
			self.configure_cb_test_filter(None)

			iter = parent

		# We want to edit a feed.
		feed = self.config.getFeed(model.get_value(iter, 0))
		if not feed:
			print 'Error: could not find feed #' + str(model.get_value(iter, 0))
			return

		self.glade.get_widget("FlexRSS_EditFeed_Name").set_text(feed["name"])
		self.glade.get_widget("FlexRSS_EditFeed_URL").set_text(feed["url"])
		self.glade.get_widget("FlexRSS_EditFeed_Interval").set_text(str(feed["interval"]))
		if feed["enabled"] == True:
			self.glade.get_widget("FlexRSS_EditFeed_Status_Enabled").set_active(True)
		else:
			self.glade.get_widget("FlexRSS_EditFeed_Status_Disabled").set_active(True)
		self.glade.get_widget('FlexRSS_Feeds_Editor').show()

	def configure_cb_feed_delete(self, arg, id=None):
		if not id:
			# Which feed is selected?
			selection = self.glade.get_widget("FlexRSS_Feeds").get_selection()
			model, iter = selection.get_selected()

			if not iter:
				return

			id = model.get_value(iter, 0)
			if id == 0:
				id = model.get_value(model.iter_parent(iter), 0)
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
			if id == 0:
				iter = model.iter_parent(iter)
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
		interval = self.configure_ui_get_text_as_int("FlexRSS_EditFeed_Interval", 900)
		if interval < 300:
			# It's just not polite to hit a server that often.
			self.glade.get_widget("FlexRSS_EditFeed_Interval").set_text('300')
			interval = 300
		self.config.setFeed(id, "interval", interval)
		self.config.setFeed(id, "enabled", self.glade.get_widget("FlexRSS_EditFeed_Status_Enabled").get_active())
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

	def escape_regex_special_chars(self, pattern):
		escape_chars = '[]()^$\\.?*+|'
		out = []
		for c in pattern:
			try:
				escape_chars.index(c)
				out.append('\\' + c)
			except:
				out.append(c)
		return ''.join(out)

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
			exp = re.compile(r'(.*?)S([0-9]+)E([0-9]+)', re.IGNORECASE)
			match = exp.match(test_pattern)
			if match:
				pattern = self.escape_regex_special_chars(match.group(1)).lower().translate(trans_table) + 's%se%e'
				filter['patterns'][0] = (pattern, 'Title')
				filter['name'] = match.group(1)
				filter['type'] = self.config.constants['TV Show']

			if not match:
				exp = re.compile(r'(.*?)([0-9]{4}).([0-9]{1,2}).([0-9]{1,2})', re.IGNORECASE)
				match = exp.match(test_pattern)
				if match:
					pattern = None
					if ((int(match.group(3)) <= 12) and (int(match.group(4)) <= 31)):
						pattern = self.escape_regex_special_chars(match.group(1)).lower().translate(trans_table) + '%Y.%m.%d'
					elif ((int(match.group(3)) <= 31) and (int(match.group(4)) <= 12)):
						pattern = self.escape_regex_special_chars(match.group(1)).lower().translate(trans_table) + '%Y.%d.%m'

					if pattern:
						filter['patterns'][0] = (pattern, 'Title')
						filter['name'] = match.group(1)
						filter['type'] = self.config.constants['TV Show (dated)']
					else:
						match = None

			if not match:
				exp = re.compile(r'(.*?)([0-9]{2}).([0-9]{2}).([0-9]{2})', re.IGNORECASE)
				match = exp.match(test_pattern)
				if match:
					pattern = None
					if ((int(match.group(2)) <= 12) and (int(match.group(3)) <= 31)):
						pattern = self.escape_regex_special_chars(match.group(1)).lower().translate(trans_table) + '%m.%d.%y'
					elif ((int(match.group(3)) <= 31) and (int(match.group(2)) <= 12)):
						pattern = self.escape_regex_special_chars(match.group(1)).lower().translate(trans_table) + '%d.%m.%y'

					if pattern:
						filter['patterns'][0] = (pattern, 'Title')
						filter['name'] = match.group(1)
						filter['type'] = self.config.constants['TV Show (dated)']
					else:
						match = None

			if not match:
				exp = re.compile(r'(.*?)([0-9]+)([x\.\-_]{1})([0-9]+)', re.IGNORECASE)
				match = exp.match(test_pattern)
				if match:
					pattern = self.escape_regex_special_chars(match.group(1)).lower().translate(trans_table) + '%s' + self.escape_regex_special_chars(match.group(3)) + '%e'
					filter['patterns'][0] = (pattern, 'Title')
					filter['name'] = match.group(1)
					filter['type'] = self.config.constants['TV Show']

			if not match:
				exp = re.compile(r'(.*?)([0-9]+)$', re.IGNORECASE)
				match = exp.match(test_pattern)
				if match:
					pattern = self.escape_regex_special_chars(match.group(1)).lower().translate(trans_table) + '%e'
					filter['patterns'][0] = (pattern, 'Title')
					filter['name'] = match.group(1)
					filter['type'] = self.config.constants['TV Show']

		# Add to config
		filter['id'] = self.config.addFilter(filter['name'], filter['type'], filter['patterns'], [0])

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

		self.configure_ui_reset_filter()

		self.glade.get_widget('FlexRSS_Filters_Name').set_text(filter['name'])

		if filter['type'] == self.config.constants['TV Show']:
			type_i = 1
		elif filter['type'] == self.config.constants['TV Show (dated)']:
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

		for pattern in filter['patterns']:
			self.configure_ui_add_pattern(pattern)

		if filter['type'] == self.config.constants['TV Show']:
			if filter['history'].has_key(filter['type']) and filter['history'][filter['type']].has_key('from'):
				self.glade.get_widget('FlexRSS_History_TVShow_From_Enabled').set_active(True)
				self.glade.get_widget('FlexRSS_History_TVShow_From_Season').set_sensitive(True)
				self.glade.get_widget('FlexRSS_History_TVShow_From_Episode').set_sensitive(True)
				self.glade.get_widget('FlexRSS_History_TVShow_From_Season').set_text(str(filter['history'][filter['type']]['from']['season']))
				self.glade.get_widget('FlexRSS_History_TVShow_From_Episode').set_text(str(filter['history'][filter['type']]['from']['episode']))
			else:
				self.glade.get_widget('FlexRSS_History_TVShow_From_Enabled').set_active(False)
				self.glade.get_widget('FlexRSS_History_TVShow_From_Season').set_sensitive(False)
				self.glade.get_widget('FlexRSS_History_TVShow_From_Episode').set_sensitive(False)
				self.glade.get_widget('FlexRSS_History_TVShow_From_Season').set_text('0')
				self.glade.get_widget('FlexRSS_History_TVShow_From_Episode').set_text('0')

			if filter['history'].has_key(filter['type']) and filter['history'][filter['type']].has_key('thru'):
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Enabled').set_active(True)
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Season').set_sensitive(True)
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Episode').set_sensitive(True)
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Season').set_text(str(filter['history'][filter['type']]['thru']['season']))
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Episode').set_text(str(filter['history'][filter['type']]['thru']['episode']))
			else:
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Enabled').set_active(False)
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Season').set_sensitive(False)
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Episode').set_sensitive(False)
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Season').set_text('0')
				self.glade.get_widget('FlexRSS_History_TVShow_Thru_Episode').set_text('0')

			self.glade.get_widget("FlexRSS_History_TVShow_Dated").hide()
			self.glade.get_widget("FlexRSS_History_TVShow").show()
			self.glade.get_widget("FlexRSS_Filter_History_Range").show()
		elif filter['type'] == self.config.constants['TV Show (dated)']:
			import time

			cal_from, cal_thru = self.history_calendarbuttons
			today = time.localtime()

			if filter['history'].has_key(filter['type']) and filter['history'][filter['type']].has_key('from'):
				self.glade.get_widget('FlexRSS_History_TVShow_Dated_From_Enabled').set_active(True)
				cal_from.set_sensitive(True)
				cal_from.set_date(filter['history'][filter['type']]['from']['year'],
								  filter['history'][filter['type']]['from']['month'],
								  filter['history'][filter['type']]['from']['day'])
			else:
				self.glade.get_widget('FlexRSS_History_TVShow_Dated_From_Enabled').set_active(False)
				cal_from.set_sensitive(False)
				cal_from.set_date(today[0], today[1], today[2])

			if filter['history'].has_key(filter['type']) and filter['history'][filter['type']].has_key('thru'):
				self.glade.get_widget('FlexRSS_History_TVShow_Dated_Thru_Enabled').set_active(True)
				cal_thru.set_sensitive(True)
				cal_thru.set_date(filter['history'][filter['type']]['thru']['year'],
								  filter['history'][filter['type']]['thru']['month'],
								  filter['history'][filter['type']]['thru']['day'])
			else:
				self.glade.get_widget('FlexRSS_History_TVShow_Dated_Thru_Enabled').set_active(False)
				cal_thru.set_sensitive(False)
				cal_thru.set_date(today[0], today[1], today[2])

			self.glade.get_widget("FlexRSS_History_TVShow").hide()
			self.glade.get_widget("FlexRSS_History_TVShow_Dated").show()
			self.glade.get_widget("FlexRSS_Filter_History_Range").show()
		else:
			self.glade.get_widget("FlexRSS_History_TVShow").hide()
			self.glade.get_widget("FlexRSS_History_TVShow_Dated").hide()
			self.glade.get_widget("FlexRSS_Filter_History_Range").hide()

		self.glade.get_widget('FlexRSS_Filter_Download_QueueTop').set_active(filter.get('queue_top', False))
		self.glade.get_widget('FlexRSS_Filter_Download_Pause').set_active(filter.get('pause', False))
		self.glade.get_widget('FlexRSS_Filter_Download_Delete').set_active(filter.get('delete', False))

		self.configure_cb_test_filter(None)

		if filter['path'] != None:
			self.glade.get_widget('FlexRSS_Filter_Output_Location').set_current_folder(filter['path'])
			self.glade.get_widget('FlexRSS_Filter_Output_Type_Custom').set_active(True)
		else:
			self.glade.get_widget('FlexRSS_Filter_Output_Type_Default').set_active(True)

		replace = filter.get('replace', {'pattern': '', 'with': ''})
		self.glade.get_widget('FlexRSS_Filter_Rewrite_Pattern').set_text(replace['pattern'])
		self.glade.get_widget('FlexRSS_Filter_Rewrite_Replacement').set_text(replace['with'])

	def configure_cb_filter_history_toggle(self, box):
		name = box.get_name()
		active = box.get_active()

		if name == 'FlexRSS_History_TVShow_From_Enabled':
			self.glade.get_widget('FlexRSS_History_TVShow_From_Season').set_sensitive(active)
			self.glade.get_widget('FlexRSS_History_TVShow_From_Episode').set_sensitive(active)
		elif name == 'FlexRSS_History_TVShow_Thru_Enabled':
			self.glade.get_widget('FlexRSS_History_TVShow_Thru_Season').set_sensitive(active)
			self.glade.get_widget('FlexRSS_History_TVShow_Thru_Episode').set_sensitive(active)
		elif name == 'FlexRSS_History_TVShow_Dated_From_Enabled':
			self.history_calendarbuttons[0].set_sensitive(active)
		elif name == 'FlexRSS_History_TVShow_Dated_Thru_Enabled':
			self.history_calendarbuttons[1].set_sensitive(active)

		self.configure_cb_test_filter(None)

	def configure_ui_get_text_as_int(self, widget_name, default=0):
		try:
			return int(self.glade.get_widget(widget_name).get_text())
		except:
			return default

	def configure_ui_get_history_restriction(self):
		h_from = None
		h_thru = None

		type = self.glade.get_widget('FlexRSS_Filters_Type').get_active()
		if type == 1:
			type_s = self.config.constants['TV Show']
		elif type == 2:
			type_s = self.config.constants['TV Show (dated)']
		else:
			type_s = self.config.constants['Generic']

		if type_s == self.config.constants['TV Show']:
			if self.glade.get_widget('FlexRSS_History_TVShow_From_Enabled').get_active():
				from_season = self.configure_ui_get_text_as_int('FlexRSS_History_TVShow_From_Season')
				from_episode = self.configure_ui_get_text_as_int('FlexRSS_History_TVShow_From_Episode')
				h_from = {'season': from_season, 'episode': from_episode}
		elif type_s == self.config.constants['TV Show (dated)']:
			if self.glade.get_widget('FlexRSS_History_TVShow_Dated_From_Enabled').get_active():
				from_y, from_m, from_d = self.history_calendarbuttons[0].get_date()
				h_from = {'year': from_y, 'month': from_m, 'day': from_d}

		if type_s == self.config.constants['TV Show']:
			if self.glade.get_widget('FlexRSS_History_TVShow_Thru_Enabled').get_active():
				thru_season = self.configure_ui_get_text_as_int('FlexRSS_History_TVShow_Thru_Season')
				thru_episode = self.configure_ui_get_text_as_int('FlexRSS_History_TVShow_Thru_Episode')
				h_thru = {'season': thru_season, 'episode': thru_episode}
		elif type_s == self.config.constants['TV Show (dated)']:
			if self.glade.get_widget('FlexRSS_History_TVShow_Dated_Thru_Enabled').get_active():
				thru_y, thru_m, thru_d = self.history_calendarbuttons[1].get_date()
				h_thru = {'year': thru_y, 'month': thru_m, 'day': thru_d}

		return (h_from, h_thru)

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
			type_s = self.config.constants['TV Show']
		elif type == 2:
			type_s = self.config.constants['TV Show (dated)']
		else:
			type_s = self.config.constants['Generic']
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

		if self.glade.get_widget('FlexRSS_Filter_Output_Type_Custom').get_active():
			path = self.glade.get_widget('FlexRSS_Filter_Output_Location').get_current_folder()
		else:
			path = None

		self.config.setFilter(id, 'path', path)

		self.config.setFilter(id, 'queue_top', self.glade.get_widget('FlexRSS_Filter_Download_QueueTop').get_active())
		self.config.setFilter(id, 'pause', self.glade.get_widget('FlexRSS_Filter_Download_Pause').get_active())
		self.config.setFilter(id, 'delete', self.glade.get_widget('FlexRSS_Filter_Download_Delete').get_active())

		filter = self.config.getFilter(id)

		h_from, h_thru = self.configure_ui_get_history_restriction()
		if filter['type'] != self.config.constants['Generic']:
			if not filter['history'].has_key(filter['type']):
				filter['history'][filter['type']] = {}

			if h_from != None:
				filter['history'][filter['type']]['from'] = h_from
			else:
				if filter['history'][filter['type']].has_key('from'):
					del filter['history'][filter['type']]['from']

				if h_thru != None:
					filter['history'][filter['type']]['thru'] = h_thru
				else:
					if filter['history'][filter['type']].has_key('thru'):
						del filter['history'][filter['type']]['thru']

		filter['replace'] = { 'pattern': self.glade.get_widget('FlexRSS_Filter_Rewrite_Pattern').get_text(),
							  'with'   : self.glade.get_widget('FlexRSS_Filter_Rewrite_Replacement').get_text() }

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

		self.configure_ui_reset_filter()

		model = self.glade.get_widget("FlexRSS_Filters_List").get_model()
		iter = model.append((filter['id'], filter['name'], filter['enabled']))

		if not iter:
			return

		view = self.glade.get_widget("FlexRSS_Filters_List")
		model = view.get_model()
		view.get_selection().select_iter(iter)

		if test_pattern:
			self.glade.get_widget('FlexRSS_Filters_Test_Pattern').set_text(test_pattern)
			self.configure_cb_test_filter(None)

		self.glade.get_widget('FlexRSS_MainNotebook').set_current_page(1)

	def configure_ui_test_result(self, result, h_match=False):
		if result and h_match:
			self.glade.get_widget('FlexRSS_Filters_Test_Result').set_text('Match')
		else:
			self.glade.get_widget('FlexRSS_Filters_Test_Result').set_text('Doesn\'t match')

		type = self.glade.get_widget('FlexRSS_Filters_Type').get_active()

		if type == 0: # Generic
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow').hide()
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated').hide()
			self.glade.get_widget('FlexRSS_History_TVShow').hide()
			self.glade.get_widget('FlexRSS_History_TVShow_Dated').hide()
		elif type == 1: # TV Show
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow').show()
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated').hide()
			self.glade.get_widget('FlexRSS_History_TVShow').show()
			self.glade.get_widget('FlexRSS_History_TVShow_Dated').hide()
			if result:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Series').set_text(str(result['series']))
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Episode').set_text(str(result['episode']))
			else:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Series').set_text('0')
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Episode').set_text('0')
		else: # TV Show (dated)
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow').hide()
			self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated').show()
			self.glade.get_widget('FlexRSS_History_TVShow').hide()
			self.glade.get_widget('FlexRSS_History_TVShow_Dated').show()
			if result:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Year').set_text(str(result['year']))
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Month').set_text(str(result['month']))
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Day').set_text(str(result['day']))
			else:
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Year').set_text('0')
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Month').set_text('0')
				self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated_Day').set_text('0')

	def configure_cb_test_filter(self, source=None, date=None):
		subject = self.glade.get_widget('FlexRSS_Filters_Test_Pattern').get_text()

		type = self.glade.get_widget('FlexRSS_Filters_Type').get_active()
		if type == 1:
			type_s = self.config.constants['TV Show']
		elif type == 2:
			type_s = self.config.constants['TV Show (dated)']
		else:
			type_s = self.config.constants['Generic']

		filter_patterns = self.glade.get_widget('FlexRSS_Filter_Patterns_List')
		for i in filter_patterns.get_children():
			data = i.get_children()
			pattern = data[0].get_text()
			result = self.test_pattern(type_s, subject, pattern)
			if result:
				# Pattern matched, let's try history restriction.
				h_from, h_thru = self.configure_ui_get_history_restriction()
				h_match = self.test_range(type_s, result, h_from, h_thru)
				self.configure_ui_test_result(result, h_match)
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

		self.configure_ui_reset_filter()

	def configure_cb_feed_refresh(self, caller, id=None):
		if not id:
			selection = self.glade.get_widget("FlexRSS_Feeds").get_selection()
			model, iter = selection.get_selected()

			if not iter:
				return

			id = model.get_value(iter, 0)

		if id:
			if ( self.config.threaded_retrieval ):
				import threading
				threading.Thread(target=self.parse_feed, args=(id,)).start()
			else:
				self.parse_feed(id)

	def configure_cb_download_torrent(self, caller, url):
		self.download_torrent(url)

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
				item_refresh = gtk.MenuItem(_("Refresh feed"))
				item_refresh.connect("activate", self.configure_cb_feed_refresh, id)
				popup.append(item_refresh)

				item_delete = gtk.MenuItem(_("Delete feed"))
				item_delete.connect("activate", self.configure_cb_feed_delete, id)
				popup.append(item_delete)

			else: # Filter
				item_filter = gtk.MenuItem(_("Create filter"))
				item_filter.connect("activate", self.configure_cb_filter_new, model.get_value(iter, 1))
				popup.append(item_filter)

				item_download = gtk.MenuItem(_("Download torrent"))
				item_download.connect("activate", self.configure_cb_download_torrent, model.get_value(iter, 2))
				popup.append(item_download)

		else: # Neither
			item_new = gtk.MenuItem("New feed")
			item_new.connect("activate", self.configure_cb_feed_new)
			popup.append(item_new)

		popup.popup(None, None, None, event.button, event.time)
		popup.show_all()

	def configure_cb_output_set(self, chooser):
		self.glade.get_widget('FlexRSS_Filter_Output_Type_Custom').set_active(True)

	def configure_ui_reset_filter(self):
		# Just resets the crap in the filter tab to defaults.
		self.glade.get_widget('FlexRSS_Filters_Name').set_text('')
		self.glade.get_widget('FlexRSS_Filters_Type').set_active(0)
		self.glade.get_widget('FlexRSS_Filters_Feed').get_selection().unselect_all()
		for filter in self.glade.get_widget('FlexRSS_Filter_Patterns_List').get_children():
			filter.destroy()
		self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow').hide()
		self.glade.get_widget('FlexRSS_Filters_Test_Results_TVShow_Dated').hide()
		file_chooser = self.glade.get_widget('FlexRSS_Filter_Output_Location')
		file_chooser.set_current_folder(self.interface.config.get('default_download_path'))
		self.glade.get_widget('FlexRSS_Filter_Output_Type_Default').set_active(True)

	def strcasecmp(self, s1, s2):
		try:
			t1 = s1.lower()
			t2 = s2.lower()

			if s1 < s2:
				return -1
			elif s1 > s2:
				return 1
		except:
			pass

		return 0

	def configure_ui_sort_cmp(self, model, iter1, iter2, user_data=None):
		if (model.get_value(iter1, 0) == 0) or (model.get_value(iter2, 0) == 0):
			return 0

		return self.strcasecmp(model.get_value(iter1, 1), model.get_value(iter2, 1))

	def configure_cb_filter_toggled(self, renderer, path):
		old_val = renderer.get_active()
		model = self.glade.get_widget('FlexRSS_Filters_List').get_model()
		iter = model.get_iter(path)
		if old_val:
			model.set_value(iter, 2, False)
			self.config.setFilter(model.get_value(iter, 0), 'enabled', False)
		else:
			model.set_value(iter, 2, True)
			self.config.setFilter(model.get_value(iter, 0), 'enabled', True)
		self.write_config()

	def configure_cb_cookie_new(self, src):
		self.configure_ui_cookie_reset()
		self.glade.get_widget("FlexRSS_Cookies_Editor").show()

	def configure_cb_cookie_save(self, src):
		import cookielib, time

		domain = self.glade.get_widget("FlexRSS_Cookie_Domain").get_text()
		path = self.glade.get_widget("FlexRSS_Cookie_Path").get_text()
		name = self.glade.get_widget("FlexRSS_Cookie_Name").get_text()
		value = self.glade.get_widget("FlexRSS_Cookie_Value").get_text()

		if (domain == ""):
			return

		if path == '':
			path = '/'

		# Fragile.
		self.cookies._policy._now = self.cookies._now = int(time.time())
		cookie = self.cookies._cookie_from_cookie_tuple((name, value, {"domain": domain, "path":path, "expires":2147483647}, {}), None)

		self.cookies.set_cookie(cookie)
		self.configure_ui_add_cookie(None, cookie)
		self.configure_ui_cookie_reset()
		self.glade.get_widget("FlexRSS_Cookies_Editor").hide()
		self.write_config(True)

	def configure_ui_add_cookie(self, model, cookie):
		if cookie.domain[0] == '.':
			domain = cookie.domain[1:]
		else:
			domain = cookie.domain

		if model == None:
			model = self.glade.get_widget("FlexRSS_Cookies_List").get_model()

		parent = None
		iter = model.get_iter_first()
		while iter:
			t = model.get_value(iter, 0)
			if t == domain:
				parent = iter
				break
			iter = model.iter_next(iter)

		if parent == None:
			parent = model.append(iter, (domain, "", "", ""))
		model.append(parent, (cookie.domain, cookie.path, cookie.name, cookie.value))

	def configure_ui_cookie_reset(self):
		self.glade.get_widget("FlexRSS_Cookie_Domain").set_text('')
		self.glade.get_widget("FlexRSS_Cookie_Path").set_text('/')
		self.glade.get_widget("FlexRSS_Cookie_Name").set_text('')
		self.glade.get_widget("FlexRSS_Cookie_Value").set_text('')

	def configure_cb_cookie_selected(self, selection):
		model, iter = selection.get_selected()

		self.configure_ui_cookie_reset()
		self.glade.get_widget("FlexRSS_Cookies_Editor").hide()

	def configure_cb_cookie_delete(self, src):
		selection = self.glade.get_widget("FlexRSS_Cookies_List").get_selection()
		model, iter = selection.get_selected()

		domain = None
		path = None
		name = None

		if not model.iter_has_child(iter):
			path = model.get_value(iter, 1)
			name = model.get_value(iter, 2)
		domain = model.get_value(iter, 0)

		try:
			self.cookies.clear("." + domain, path, name)
		except:
			pass
		try:
			self.cookies.clear(domain, path, name)
		except:
			pass

		# UI
		if model.iter_has_child(iter):
			i = model.iter_children(iter)
			while model.remove(i):
				pass
			model.remove(iter)
		else:
			p = model.iter_parent(iter)
			model.remove(iter)
			if not model.iter_has_child(p):
				model.remove(p)

		self.write_config(True)

	def configure_cb_toolbar_clicked(self, button):
		self.configure()

	def configure_ui_show_toolbar_button(self):
		if self.toolbar_button == None:
			import gtk
            import os

			icon = gtk.Image()
			icon.set_from_file(os.path.join(self.path, "FlexRSS.png"))
			self.toolbar_button = gtk.ToolButton(icon_widget=icon, label="FlexRSS")
			self.toolbar_button.connect("clicked", self.configure_cb_toolbar_clicked)
			self.interface.toolbar.add(self.toolbar_button)
			self.toolbar_button.show_all()

	def configure_cb_toolbar_toggled(self, box):
		if box.get_active():
			self.configure_ui_show_toolbar_button()
			self.config.show_toolbar_button = True
			self.write_config()
		else:
			self.toolbar_button.destroy()
			self.toolbar_button = None
			self.config.show_toolbar_button = False
			self.write_config()

	def configure_cb_threaded_toggled(self, box):
		self.config.threaded_retrieval = box.get_active()
		self.write_config()

	def configure(self, widget=None):
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
		feeds_model.set_sort_func(1, self.configure_ui_sort_cmp)
		feeds_model.set_sort_column_id(1, gtk.SORT_ASCENDING)

		# Setup columns for feeds tab
		renderer_name = gtk.CellRendererText()
		column_name = gtk.TreeViewColumn(_("Feed Name"), renderer_name, text=1)
		feeds_view.append_column(column_name)
		renderer_url = gtk.CellRendererText()
		column_url = gtk.TreeViewColumn(_("URL"), renderer_url, text=2)
		feeds_view.append_column(column_url)
		feeds_view.set_search_column(1)
		feeds_view.set_search_equal_func(gtk_treeview_search_cb_stristr)

		# Set callback for when selection is changed in feeds tab
		# I can't figure out how to do this in Glade
		feeds_view.get_selection().connect("changed", self.configure_cb_feed_selected)

		# Setup columns for feed list on filters tab
		renderer_name = gtk.CellRendererText()
		column_name = gtk.TreeViewColumn(_("Feed Name"), renderer_name, text=1)
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
		filters_model = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
		filters_view = self.glade.get_widget("FlexRSS_Filters_List")
		filters_view.set_model(filters_model)
		feeds_model.set_sort_func(1, self.configure_ui_sort_cmp)
		filters_model.set_sort_column_id(1, gtk.SORT_ASCENDING)

		# Setup columns for filters list
		renderer_enabled = gtk.CellRendererToggle()
		column_enabled = gtk.TreeViewColumn(_("Enabled"), renderer_enabled, active=2)
		filters_view.append_column(column_enabled)
		renderer_enabled.connect('toggled', self.configure_cb_filter_toggled)
		renderer_name = gtk.CellRendererText()
		column_name = gtk.TreeViewColumn(_("Filter Name"), renderer_name, text=1)
		filters_view.append_column(column_name)

		# Set callback for when selection is changed in feeds tab
		# I can't figure out how to do this in Glade
		filters_view.get_selection().connect("changed", self.configure_cb_filter_selected)

		# Populate filters list
		if self.config.filters:
			for filter in self.config.filters:
				filters_model.append((filter['id'], filter['name'], filter['enabled']))

		# Filter types
		filter_types = self.glade.get_widget('FlexRSS_Filters_Type')
		filter_types.append_text(_("Generic"))
		filter_types.append_text(_("TV Show"))
		filter_types.append_text(_("TV Show (dated)"))

		# Calendar buttons for dated tv show history restrictions
		from CalendarButton import CalendarButton
		dated_from = CalendarButton()
		dated_from.connect('date-selected', self.configure_cb_test_filter)
		dated_to = CalendarButton()
		dated_to.connect('date-selected', self.configure_cb_test_filter)
		dated_from.show()
		dated_to.show()
		history_table = self.glade.get_widget('FlexRSS_History_TVShow_Dated')
		history_table.attach(dated_from, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)
		history_table.attach(dated_to, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)
		self.history_calendarbuttons = (dated_from, dated_to)

		# Initialize cookies list
		cookies_model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		cookies_view = self.glade.get_widget("FlexRSS_Cookies_List")
		cookies_view.set_model(cookies_model)
		cookies_view.get_selection().connect("changed", self.configure_cb_cookie_selected)

		# Setup column for cookies
		domain_renderer = gtk.CellRendererText()
		domain_column = gtk.TreeViewColumn(_("Domain"), domain_renderer, text=0)
		path_renderer = gtk.CellRendererText()
		path_column = gtk.TreeViewColumn(_("Path"), path_renderer, text=1)
		name_renderer = gtk.CellRendererText()
		name_column = gtk.TreeViewColumn(_("Name"), name_renderer, text=2)
		value_renderer = gtk.CellRendererText()
		value_column = gtk.TreeViewColumn(_("Value"), value_renderer, text=3)
		cookies_view.append_column(domain_column)
		cookies_view.append_column(path_column)
		cookies_view.append_column(name_column)
		cookies_view.append_column(value_column)

		for cookie in self.cookies:
			self.configure_ui_add_cookie(cookies_model, cookie)

		# Interface
		self.glade.get_widget("FlexRSS_Interface_ShowButton").set_active(self.config.show_toolbar_button)
		self.glade.get_widget("FlexRSS_Retrieval_Threaded").set_active(self.config.threaded_retrieval)

		# Callbacks for UI events
		actions = {
			# Feeds tab
			"on_FlexRSS_MainWindow_destroy"           : self.configure_cb_closed,
			"on_FlexRSS_Feeds_New_pressed"            : self.configure_cb_feed_new,
			"on_FlexRSS_Feeds_Save_pressed"           : self.configure_cb_feed_save,
			"on_FlexRSS_Feeds_Delete_pressed"         : self.configure_cb_feed_delete,
			"on_FlexRSS_Feeds_button_press_event"     : self.configure_cb_feed_popup,

			# Filters tab
			"on_FlexRSS_Filters_Add_pressed"          : self.configure_cb_filter_new,
			"on_FlexRSS_Action_Save_pressed"          : self.configure_cb_filter_save,
			"on_FlexRSS_Filter_Patern_Add_pressed"    : self.configure_cb_add_pattern,
			"on_FlexRSS_Filters_Type_changed"         : self.configure_cb_test_filter,
			"on_FlexRSS_Filters_Test_Pattern"         : self.configure_cb_test_filter,
			"on_FlexRSS_Filters_Delete_pressed"       : self.configure_cb_delete_filter,
			"on_FlexRSS_History_TVShow_From_Enabled_toggled" : self.configure_cb_filter_history_toggle,
			"on_FlexRSS_History_TVShow_Thru_Enabled_toggled" : self.configure_cb_filter_history_toggle,
			"on_FlexRSS_History_TVShow_Dated_From_Enabled_toggled" : self.configure_cb_filter_history_toggle,
			"on_FlexRSS_History_TVShow_Dated_Thru_Enabled_toggled" : self.configure_cb_filter_history_toggle,
			"on_FlexRSS_History_TVShow_From_Season_changed" : self.configure_cb_test_filter,
			"on_FlexRSS_History_TVShow_From_Episode_changed" : self.configure_cb_test_filter,
			"on_FlexRSS_History_TVShow_Thru_Season_changed" : self.configure_cb_test_filter,
			"on_FlexRSS_History_TVShow_Thru_Episode_changed" : self.configure_cb_test_filter,

			# Configuration tab
			"on_FlexRSS_Cookie_New_pressed"           : self.configure_cb_cookie_new,
			"on_FlexRSS_Cookie_Save_pressed"          : self.configure_cb_cookie_save,
			"on_FlexRSS_Cookie_Delete_pressed"        : self.configure_cb_cookie_delete,
			"on_FlexRSS_Interface_ShowButton_toggled" : self.configure_cb_toolbar_toggled,
			"on_FlexRSS_Retrieval_Threaded_toggled"   : self.configure_cb_threaded_toggled }
		if hasattr(self.interface, 'interactive_add_torrent_path'):
			actions["on_FlexRSS_Filter_Output_Location_current_folder_changed"] = self.configure_cb_output_set
		else:
			self.glade.get_widget('FlexRSS_Filter_Output').hide()
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
		patterns = [('%s', '(?P<s>[0-9]+)'),
					('%e', '(?P<e>[0-9]+)')]

		out = input
		for p in patterns:
			out = out.replace(p[0], p[1])

		return out

	def test_range(self, type, data, h_from=None, h_thru=None):
		if type == self.config.constants['TV Show']:
			if h_from != None:
				if data['series'] < h_from['season']:
					return False
				elif data['series'] == h_from['season']:
					if data['episode'] < h_from['episode']:
						return False

			if h_thru != None:
				if data['series'] > h_thru['season']:
					return False
				elif data['series'] == h_thru['season']:
					if data['episode'] > h_thru['episode']:
						return False

			return True

		elif type == self.config.constants['TV Show (dated)']:
			if h_from != None:
				if data['year'] < h_from['year']:
					return False
				elif data['year'] == h_from['year']:
					if data['month'] < h_from['month']:
						return False
					elif data['month'] == h_from['month']:
						if data['day'] < h_from['day']:
							return False

			if h_thru != None:
				if data['year'] < h_thru['year']:
					return False
				elif data['year'] == h_thru['year']:
					if data['month'] < h_thru['month']:
						return False
					elif data['month'] == h_thru['month']:
						if data['day'] < h_thru['day']:
							return False

			return True

		else:
			return True

	def test_pattern(self, type, subject, pattern):
		import re, time
		result = False

		if len(pattern) < 1:
			return False

		if type == self.config.constants['TV Show (dated)']:
			pattern = self.strptime2regex(pattern)
		elif type == self.config.constants['TV Show']:
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
# 			print 'Match: ' + subject
# 			print '       ' + pattern
			if type == self.config.constants['TV Show']:
				try:
					series = int(match.group('s'))
				except:
					series = 0

				try:
					episode = int(match.group('e'))
				except:
					episode = 0

				result = { 'series'  : series,
						   'episode' : episode }

			elif type == self.config.constants['TV Show (dated)']:
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

	def make_opener(self):
		import urllib2

		return urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))

	def make_request(self, location, referer=None):
		import urllib2, deluge.common

		req = urllib2.Request(location)
		req.add_header("User-Agent", "FlexRSS/%d.%d.%d (%s/%s)" % (self.version[0], self.version[1], self.version[2], deluge.common.PROGRAM_NAME, deluge.common.PROGRAM_VERSION))
		if referer != None:
			req.add_header('Referer', referer)

		return req

	def open_url(self, location):
		return self.make_opener().open(self.make_request(location))

	def download_torrent(self, location, path=None, queue_top=False, pause=False, referer=None):
		import tempfile, os, deluge.core

		try:
			fd = self.open_url(location)
		except:
			return False

		inf = fd.info()
		if inf["content-type"] != "application/x-bittorrent":
			print "Warning: torrent content-type not application/x-bittorrent"

		(tmpfd, filename) = tempfile.mkstemp(".torrent", "flexrss-")
		tfd = os.fdopen(tmpfd, 'wb')
		tfd.write(fd.read())
		fd.close()
		tfd.close()

		unique_id = False

		try:
			if path is None:
				path = self.interface.config.get('default_download_path')
			unique_id = self.interface.manager.add_torrent(filename, path, self.interface.config.get('use_compact_storage'))
			self.interface.torrent_model_append(unique_id)

			if queue_top == True:
				try:
					self.interface.manager.queue_top(unique_id)
				except:
					pass
			if pause == True:
				try:
					self.interface.manager.set_user_pause(unique_id, True)
				except:
					pass
		except deluge.core.DuplicateTorrentError, e:
			print 'FlexRSS: torrent already exists.'
			return True
		except:
			print '*** FlexRSS error: unable to add torrent.'
			return False

		return True

	def parse_feed(self, id):
		import time, feedparser, urllib2, cookielib

		feed = self.config.getFeed(id)

		#print 'Parsing feed: ' + feed['url']
 		try:
			parsed = feedparser.parse(self.open_url(feed['url']))
			if (not parsed) or (not parsed.entries):
				print 'Unable to parse feed: ' + feed['url']
				return
		except:
			print 'Unable to update feed: ' + feed['url']
			return
		#print 'Retrieval successful: ' + feed['url']

		data = []

		for entry in parsed.entries:
			entryTitle = entry['title']

			try:
				entryLink = entry.links[0]['href']
			except:
				try:
					entryLink = entry.enclosures[0]['href']
				except:
					print "Skipping %s\n" % entryTitle
					continue

			try:
				data.append({ 'title': entryTitle, 'link': entryLink })
			except:
				continue

			if self.config.filters:
				for filter in self.config.filters:
					try:
						if not ((feed['id'] in filter['feeds']) or (0 in filter['feeds'])):
							continue
					except TypeError:
						filter['feeds'] = [0]

					if filter['enabled'] != True:
						continue

					for pattern in filter['patterns']:
						# (setq python-indent 4
						#       tab-width 4)
						# Okay, I dislike python substantially less now.
						# Edit (~a month later): I still dislike it a lot, though.
						try:
							if pattern[1] == 'Title':
								subject = entryTitle
							else:
								subject = entryLink
						except:
							print 'Unable to find subject.'

						match = self.test_pattern(filter['type'], subject, pattern[0])
						if match:
							# Filter matched. Check history to see if
							# we should download it.
							if filter['type'] == self.config.constants['Generic']: # Dirty hack.
								match = { 'url' : entryLink }

							torrent_url = entryLink
							replace = filter.get('replace', {'pattern': '', 'with': ''})
							if len(replace['pattern']) > 0:
								try:
									import re

									p = re.compile(replace['pattern'], re.IGNORECASE)
									torrent_url = p.sub(replace['with'], torrent_url)
								except:
									print '*** FlexRSS error: s/%s/%s/i failed.' % (replace['pattern'], replace['with'])
									return

							if not self.config.checkHistory(filter['id'], filter['type'], match):
								print filter
								if filter.has_key('history'):
									res = False

									if filter['type'] == self.config.constants['Generic']:
										if filter['history'].get(filter['type'], []).count(torrent_url) == 0:
											res = self.download_torrent(torrent_url, filter.get('path', None), filter['queue_top'], filter['pause'], feed['url'])
									else:
										h_from = filter['history'][filter['type']].get('from', None)
										h_thru = filter['history'][filter['type']].get('thru', None)
										if self.test_range(filter['type'], match, h_from, h_thru):
											res = self.download_torrent(torrent_url, filter.get('path', None), filter['queue_top'], filter['pause'], feed['url'])

									print res
									if res == True:
										if filter['delete'] == True:
											self.config.deleteFilter(filter['id'])
											self.write_config()

											model = self.glade.get_widget("FlexRSS_Filters_List").get_model()
											iter = model.get_iter_first();
											while iter != None:
												if model.get_value(iter, 0) == filter['id']:
													model.remove(iter)
													break
												iter = model.iter_next(iter)
										else:
											self.config.addHistory(filter['id'], filter['type'], match)
										self.write_config()

			self.feeds[feed['id']]['data'] = data
			if self.glade: # Update config window...
				feeds_model = self.glade.get_widget("FlexRSS_Feeds").get_model()
				iter = feeds_model.get_iter_first()
				while iter != None:
					if id == feeds_model.get_value(iter, 0):
						break
					iter = feeds_model.iter_next(iter)

				i = feeds_model.iter_children(iter)
				if i != None:
					while feeds_model.remove(i):
						pass

				for item in data:
					feeds_model.append(iter, (0, item['title'], item['link']))

	def update(self):
		import time, threading

		current_time = time.time()

		# I feel dirty for this. Oh, how I miss C.
		for id in self.feeds:
			if self.feeds[id]['cfg']['enabled'] == True:
				if (current_time - self.feeds[id]['cfg']['interval']) > self.feeds[id]['updated']:
					self.feeds[id]['updated'] = current_time
					if ( self.config.threaded_retrieval ):
						threading.Thread(target=self.parse_feed, args=(self.feeds[id]['cfg']['id'],)).start()
					else:
						self.parse_feed(self.feeds[id]['cfg']['id'])
	
	def unload(self):
		if self.toolbar_button:
			self.toolbar_button.destroy()
			self.toolbar_button = None

	def deluge_version_compare(self, version):
		import deluge.common
		va = deluge.common.PROGRAM_VERSION.split('.')
		dv = int(va[0]) * 1000000
		dv = dv + (int(va[1]) * 10000)
		dv = dv + (int(va[2]) * 100)
		if len(va) >= 4:
			dv = dv + int(va[3])

		if dv < version:
			return -1
		elif dv > version:
			return 1
		else:
			return 0

	def __init__(self, path, core, interface, defaults):
		self.path = path
		self.core = core
		self.interface = interface
		self.version = defaults['VERSION']

		self.load_config()

		if self.config.show_toolbar_button == True:
			self.configure_ui_show_toolbar_button()

		self.feeds = {}
		if self.config.feeds:
			for feed in self.config.feeds:
				self.feeds[feed['id']] = { 'cfg'     : feed,
										   'updated' : 0,
										   'data'    : [] }

		# Debugging
		# self.configure()
