

class plugin_RSS:
	def __init__(self, path, deluge_core, deluge_interface):
		#set up system thingies
		import gtk, gtk.glade, os, ConfigParser, feedparser
		import deluge.common, deluge.dgtk, deluge.pref
		from time import asctime
		self.path = path
		self.core = deluge_core
		self.interface = deluge_interface
		#set up feeds file
		self.feeds_config = ConfigParser.ConfigParser()
		self.feeds_file = deluge.common.CONFIG_DIR + "/feeds.conf"
		if not os.path.isfile(self.feeds_file):
			f = open(self.feeds_file, mode='w')
			f.flush()
			f.close()
		self.feeds_config.read(self.feeds_file)
		#set up filters file
		self.filters_config = ConfigParser.ConfigParser()
		self.filters_file = deluge.common.CONFIG_DIR + "/filters.conf"
		if not os.path.isfile(self.filters_file):
			f = open(self.filters_file, mode='w')
			f.flush()
			f.close()
		self.filters_config.read(self.filters_file)
		#set up the preferences dialog
		glade = gtk.glade.XML(path + "/rss.glade")
		self.dlg = glade.get_widget("dialog")
		self.dlg.set_icon_from_file(self.path + "/rss.png")
		#set up the feeds list viewer
		self.feeds_view = glade.get_widget("feeds_view")
		model = gtk.ListStore(str, str, str)
		self.feeds_view.set_model(model)
		deluge.dgtk.add_text_column(self.feeds_view, "Name", 0)
		deluge.dgtk.add_text_column(self.feeds_view, "URL", 1)
		deluge.dgtk.add_text_column(self.feeds_view, "Last Entry Date", 2)
		#set up the torrents list viewer
		self.torrents_view = glade.get_widget("torrents_view")
		model = gtk.ListStore(str, str, str, str)
		self.torrents_view.set_model(model)
		deluge.dgtk.add_text_column(self.torrents_view, "Feed", 0)
		deluge.dgtk.add_text_column(self.torrents_view, "Name", 1)
		deluge.dgtk.add_text_column(self.torrents_view, "URL", 2)
		deluge.dgtk.add_text_column(self.torrents_view, "Date", 3)
		# Setup the filters list viewer
		self.filters_view = glade.get_widget("filters_view")
		model = gtk.ListStore(str)
		self.filters_view.set_model(model)
		deluge.dgtk.add_text_column(self.filters_view, "Name", 0)
		# set up the feed choice combobox
		self.feedchoice_combo = glade.get_widget("feedchoice_combo")
		model = gtk.ListStore(str)
		self.feedchoice_combo.set_model(model)
		cell = gtk.CellRendererText()
		self.feedchoice_combo.pack_start(cell, True)
		self.feedchoice_combo.add_attribute(cell, 'text', 0) 
		# set up the torrents feed choice combobox
		self.torrents_fcc = glade.get_widget("torrents_fcc")
		model = gtk.ListStore(str)
		self.torrents_fcc.set_model(model)
		cell = gtk.CellRendererText()
		self.torrents_fcc.pack_start(cell, True)
		self.torrents_fcc.add_attribute(cell, 'text', 0) 
		#set up the rest of the GUI elements
		self.name_entry = glade.get_widget("name_entry")		
		self.url_entry = glade.get_widget("url_entry")
		self.button_addfeed = glade.get_widget("button_addfeed")
		self.button_delfeed = glade.get_widget("button_delfeed")
		self.chkfeeds = glade.get_widget("chkfeeds")
		self.filtername_entry = glade.get_widget("filtername_entry")
		self.filterexp_entry = glade.get_widget("filterexp_entry")
		self.checkonstart_button = glade.get_widget("checkonstart_button")
		self.update_entry = glade.get_widget("update_entry")
		#Connect event signals
		self.filters_view.connect("cursor-changed", self.filter_row_clicked)
		dic = {	"addfeed_clicked" : self.addfeed_clicked,
				"delfeed_clicked" : self.delfeed_clicked,
				"addfilter_clicked" : self.addfilter_clicked,
				"delfilter_clicked" : self.delfilter_clicked,
				"row_clicked" : self.row_clicked,
				"feedtext_changed" : self.feedtext_changed,
				"filtername_lostfocus" : self.filtername_lostfocus,
				"filterexp_lostfocus" : self.filterexp_lostfocus,
				"feedchoice_combo_changed" : self.feedchoice_combo_changed,
				"torrents_fcc_changed" : self.torrents_fcc_changed,
				"torrents_view_row_activated" : self.torrents_view_row_activated,
				"chkfeeds_clicked" : self.chkfeeds_clicked }
		glade.signal_autoconnect(dic)
		self.feeds_view.get_selection().set_select_function(self.row_clicked)
		self.timer = 0
		self.torrents_list = []
		#self.checkfeeds()
		# Access the interface's toolbar
		self.toolbar = self.interface.toolbar
		# Make a toolbar button
		icon = gtk.Image()
		icon.set_from_file(self.path + "/rss.png") # Toolbar items should be 22x22 pixel images
		self.button = gtk.ToolButton(icon_widget=icon, label="RSS")
		self.button.connect("clicked", self.rss_clicked) # Connect the signal handler for the button
		self.toolbar.add(self.button) # Add button to toolbar
		self.button.show_all() # Show the button
		self.checkonstart = False
		#load options
		if self.feeds_config.has_option("DEFAULT", "interval"):
			self.interval = self.feeds_config.getint("DEFAULT", "interval")
			self.update_entry.set_text(self.feeds_config.get("DEFAULT", "interval"))
		else:
			self.interval = 900
			self.feeds_config.set("DEFAULT", "interval", 900)
		if self.feeds_config.has_option("DEFAULT", "checkonstart"):
			self.checkonstart = self.feeds_config.getboolean("DEFAULT", "checkonstart")
			self.checkonstart_button.set_active(self.checkonstart)
		else:
			self.checkonstart = False
			self.feeds_config.set("DEFAULT", "checkonstart", False)
		if self.checkonstart_button.get_active():
			self.timer = self.interval - 5

	def rss_clicked(self, button):
		self.configure(self)
	
	def unload(self):
		self.toolbar.remove(self.button) # Remove the button from the toolbar
		f = open(self.feeds_file, "w")
		self.feeds_config.write(f)
		f.close()
	
	def feedtext_changed(self, args):
		a = (self.name_entry.get_text() != "")
		b = (self.url_entry.get_text() != "")
		if(a and b):
			self.button_addfeed.set_sensitive(1)
		else:
			self.button_addfeed.set_sensitive(0)

	def addfeed_clicked(self, args):
		self.feeds_view.get_model().append([self.name_entry.get_text(),
					self.url_entry.get_text(), ""])
		self.feedchoice_combo.append_text(self.name_entry.get_text())
		self.torrents_fcc.append_text(self.name_entry.get_text())
		self.feeds_config.add_section(self.name_entry.get_text())
		self.feeds_config.set(self.name_entry.get_text(), "url", self.url_entry.get_text())
		self.feeds_config.set(self.name_entry.get_text(), "lastchecked", "")
		self.name_entry.set_text("")
		self.url_entry.set_text("")

	def delfeed_clicked(self, args):
		(model, selection) = self.feeds_view.get_selection().get_selected()
		text = self.feeds_view.get_model().get_value(selection, 0)
		model2 = self.feedchoice_combo.get_model()
		model3 = self.torrents_fcc.get_model()
		the_iter = model2.get_iter_first()
		print text
		while the_iter is not None:
			print model2.get_value(the_iter, 0)
			if (model2.get_value(the_iter, 0) == text):
				remove_iter = the_iter
			the_iter = model2.iter_next(the_iter)
		model2.remove(remove_iter)
		the_iter = model3.get_iter_first()
		while the_iter is not None:
			print model3.get_value(the_iter, 0)
			if (model3.get_value(the_iter, 0) == text):
				remove_iter = the_iter
			the_iter = model3.iter_next(the_iter)
		model3.remove(remove_iter)
		model.remove(selection)
		for filt in self.filters_config.sections():
			if self.filters_config.get(filt, "feed") == text:
				self.filters_config.set(filt, "feed", "All")
		self.feeds_config.remove_section(text)
		self.button_delfeed.set_sensitive(0)
		
	def row_clicked(self, args):
		self.button_delfeed.set_sensitive(1)
		return True

	def addfilter_clicked(self, args):
		unique = True
		for filt in self.filters_config.sections():
			if filt == "New Filter":
				unique = False

		if unique:
			self.current_filter = "New Filter"
			self.filters_config.add_section("New Filter")
			new_iter = self.filters_view.get_model().append(["New Filter"])
			self.filters_view.get_selection().select_iter(new_iter)
			self.filters_config.set("New Filter", "filterexp", "")
			self.filters_config.set("New Filter", "feed", "All")
			self.filtername_entry.set_text("New Filter")
			self.feedchoice_combo.set_active(0)

			self.filtername_entry.set_sensitive(1)
			self.filterexp_entry.set_sensitive(1)
			self.feedchoice_combo.set_sensitive(1)
			self.filterexp_entry.set_text("")
			self.filtername_entry.grab_focus()

	def delfilter_clicked(self, args):
		model, selection = self.filters_view.get_selection().get_selected()
		self.filters_config.remove_section(self.current_filter)
		model.remove(selection)
		self.current_filter = None

		self.filtername_entry.set_text("")
		self.filterexp_entry.set_text("")
		self.feedchoice_combo.set_active(-1)
		self.filtername_entry.set_sensitive(0)
		self.filterexp_entry.set_sensitive(0)
		self.feedchoice_combo.set_sensitive(0)

	def filter_row_clicked(self, widget):
		selection = self.filters_view.get_selection()
		model, selection_iter = selection.get_selected()
		print model
		print selection_iter
		self.current_filter = self.filters_view.get_model().get_value(selection_iter, 0)
		self.filtername_entry.set_text(self.current_filter)
		self.filterexp_entry.set_text(self.filters_config.get(self.current_filter, "filterexp"))
		feed = self.filters_config.get(self.current_filter, "feed")
		model2 = self.feedchoice_combo.get_model()
		the_iter = model2.get_iter_first()
		while the_iter is not None:
			#print model2.get_value(the_iter, 0)
			if (model2.get_value(the_iter, 0) == feed):
				set_iter = the_iter
			the_iter = model2.iter_next(the_iter)
		self.feedchoice_combo.set_active_iter(set_iter)

		self.filtername_entry.set_sensitive(1)
		self.filterexp_entry.set_sensitive(1)
		self.feedchoice_combo.set_sensitive(1)

	def filtername_lostfocus(self, args, spare):
		(model, selection) = self.filters_view.get_selection().get_selected()
		old_filtername = self.filters_view.get_model().get_value(selection, 0)
		self.filters_config.remove_section(old_filtername)
		model.remove(selection)

		self.current_filter = self.filtername_entry.get_text()
		new_iter = self.filters_view.get_model().append([self.current_filter])
		self.filters_view.get_selection().select_iter(new_iter)
		self.filters_config.add_section(self.current_filter)
		self.filters_config.set(self.current_filter, "filterexp", self.filterexp_entry.get_text())
		self.filters_config.set(self.current_filter, "feed", self.feedchoice_combo.get_active_text())

	def filterexp_lostfocus(self, args, spare):
		self.filters_config.set(self.current_filter, "filterexp", self.filterexp_entry.get_text())

	def feedchoice_combo_changed(self, args):
		self.filters_config.set(self.current_filter, "feed", self.feedchoice_combo.get_active_text())

	def torrents_fcc_changed(self, args):
		model = self.torrents_view.get_model()
		model.clear()
		if self.torrents_fcc.get_active_text() == "All":
			for (date, feed, title, link) in self.torrents_list:
				self.torrents_view.get_model().append((feed, title, link, date))
		else:
			for (date, feed, title, link) in self.torrents_list:
				if feed == self.torrents_fcc.get_active_text():
					self.torrents_view.get_model().append((feed, title, link, date))

	def torrents_view_row_activated(self, widget, spare1, spare2):
		selection = widget.get_selection()
		model, selection_iter = selection.get_selected()
		self.interface.interactive_add_torrent_url(widget.get_model().get_value(selection_iter, 2))
		

	def chkfeeds_clicked(self, args):
		self.checkfeeds()

	def checkfeeds(self):
		import feedparser, datetime
		from time import asctime, strptime

		avail = {}
		sorted = {}
		self.torrents_list = []
		for name in self.feeds_config.sections():
			print "Attempting to parse " + name
			tmp = feedparser.parse(self.feeds_config.get(name, "url"))
			try:
				print "Parsed " + tmp['feed']['title']
				avail[name] = True
			except:
				print "Failed to download/parse " + name
				avail[name] = False
			if avail[name]:
				entries = []
				entries.extend( tmp[ "items" ] )
				decorated = [(entry["date_parsed"], entry) for entry in entries]
				tmplist = [(entry["date_parsed"], name, entry["title"], entry.enclosures[0].href) for entry in entries]
				decorated.sort()
				self.torrents_list.extend(tmplist)
				#decorated.reverse() # for most recent entries first
				sorted[name] = [entry for (date,entry) in decorated]

		model = self.torrents_view.get_model()
		model.clear()
		self.torrents_list.sort()
		self.torrents_list.reverse()
		#self.torrents_view.get_model().append([entry for entry in self.torrents_list])
		for (date,feed,title,link) in self.torrents_list:
			self.torrents_view.get_model().append((feed, title, link, date))
		#for key in sorted.keys():
		#	print "listing entries in " + key
		#	
		#	for entry in sorted[key]:
		#		print entry.title
		#		for enclosure in entry.enclosures:
		#			self.torrents_view.get_model().append( (key, entry.title, enclosure.href, entry.date_parsed) )

		checked = {}
		for name in self.filters_config.sections():
			checkfiltername = name
			checkfilterexp = self.filters_config.get(name, "filterexp")
			checkfilterfeed = self.filters_config.get(name, "feed")
			print "filter: " + checkfiltername
			print "search: " + checkfilterexp
			print "feed: " + checkfilterfeed
			if checkfilterfeed == "All":
				#print "made it to 'All'"
				for feedname in sorted.keys():
					if avail[feedname]:
						print feedname + " last checked: " + self.feeds_config.get(feedname, "lastchecked")
						if self.feeds_config.get(feedname, "lastchecked") != "":
							lastchecked = strptime(self.feeds_config.get(feedname, "lastchecked"))
						else:
							lastchecked = strptime(asctime(sorted[feedname][0].date_parsed))
						#print "searching feed: " + feedname
						for entry in sorted[feedname]:
							#print entry.title + ": " + asctime(entry.date_parsed)
							if (strptime(asctime(entry.date_parsed)) > lastchecked):
								#print entry.date_parsed
								#print " > "
								#print lastchecked
								if entry.title.find(checkfilterexp) != -1:
									#print "contains" + checkfilterexp
									for enclosure in entry.enclosures:
										print enclosure.href
										self.interface.interactive_add_torrent_url(enclosure.href)
										#self.feeds_config.set(feedname, "lastchecked", asctime(entry.date_parsed))
			else:
				if avail[checkfilterfeed]:
					print "searching feed: " + checkfilterfeed
					if self.feeds_config.get(checkfilterfeed, "lastchecked") != "":
						lastchecked = strptime(self.feeds_config.get(checkfilterfeed, "lastchecked"))
					else:
						#print sorted[checkfilterfeed][1].date_parsed
						lastchecked = strptime(asctime(sorted[checkfilterfeed][0].date_parsed))
					print "lastchecked: " + asctime(lastchecked)
					for entry in sorted[checkfilterfeed]:
						#print entry.title + ": " + asctime(entry.date_parsed)
						if (strptime(asctime(entry.date_parsed)) > lastchecked):
							#print entry.date_parsed
							#print " > "
							#print lastchecked
							if (entry.title.find(checkfilterexp) != -1):
								#print "contains" + checkfilterexp
								for enclosure in entry.enclosures:
									print enclosure.href
									self.interface.interactive_add_torrent_url(enclosure.href)
									#self.feeds_config.set(checkfilterfeed, "lastchecked", asctime(entry.date_parsed))

		for name in avail.keys():
			if avail[name]:
				self.feeds_config.set(name, "lastchecked", asctime(sorted[name][len(sorted[name])-1].date_parsed))

		self.timer = 0




	def configure(self, widget=None):
		import gtk, gtk.glade
		from deluge import common
		self.dlg.show_all()
		model = self.feeds_view.get_model()
		model.clear()
		model2 = self.feedchoice_combo.get_model()
		model2.clear()
		model3 = self.filters_view.get_model()
		model3.clear()
		model4 = self.torrents_fcc.get_model()
		model4.clear()
		self.filtername_entry.set_text("")
		self.filterexp_entry.set_text("")
		self.name_entry.set_text("")
		self.url_entry.set_text("")
		self.feedchoice_combo.append_text("All")
		self.torrents_fcc.append_text("All")
		self.torrents_fcc.set_active(0)
		for name in self.feeds_config.sections():
			self.feeds_view.get_model().append( (name, self.feeds_config.get(name, "url"), self.feeds_config.get(name, "lastchecked") ) )
			self.feedchoice_combo.append_text(name)
			self.torrents_fcc.append_text(name)
		for filters in self.filters_config.sections():
			self.filters_view.get_model().append( ([filters]) )
		#self.checkfeeds()
		self.button_addfeed.set_sensitive(0)
		self.button_delfeed.set_sensitive(0)
		self.filtername_entry.set_sensitive(0)
		self.filterexp_entry.set_sensitive(0)
		self.feedchoice_combo.set_sensitive(0)
		self.update_entry.set_text(str(self.interval))
		self.checkonstart_button.set_active(self.checkonstart)
		result = self.dlg.run()
		self.dlg.hide_all()
		if result == 1:
			self.timer = 0
			self.interval = self.update_entry.get_text()
			self.feeds_config.set("DEFAULT", "interval", self.update_entry.get_text())
			self.feeds_config.set("DEFAULT", "checkonstart", self.checkonstart_button.get_active())
			f = open(self.filters_file, "w")
			self.filters_config.write(f)
			f.close()
			f = open(self.feeds_file, "w")
			self.feeds_config.write(f)
			f.close()
			

	def update(self):
		#print "tick"
		self.timer += 1
		if self.timer >= self.interval:
			print "BONG!"
			self.checkfeeds()
			self.timer = 0

