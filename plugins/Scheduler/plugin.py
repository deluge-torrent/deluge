import deluge.common
import deluge.pref
import gtk
import copy
import time

class plugin_Scheduler:
	def __init__(self, path, deluge_core, deluge_interface):
		self.path = path
		self.core = deluge_core
		self.interface = deluge_interface
		self.config = deluge.pref.Preferences()

		self.days = [_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun")]
		self.config_file = deluge.common.CONFIG_DIR + "/scheduler.conf"
		self.status = -1

		#Load config
		try:
			self.config.load(self.config_file)

			self.status_table = self.config.get("scheduler_table")
			self.dllimit = self.config.get("scheduler_dl_limit")
			self.ullimit = self.config.get("scheduler_ul_limit")
		except:
			self.status_table = [[0] * 7 for dummy in xrange(24)]
			self.dllimit = self.ullimit = -1

	#remove speed limitations und unpause all torrents that were running before
	def unload(self):
		pass

	def update(self):
		time_now = time.localtime(time.time())

		if self.status != self.status_table[time_now[3]][time_now[6]]:
			self.status = self.status_table[time_now[3]][time_now[6]]
			if self.status == 0:
				print "[Scheduler] Normal"
			elif self.status == 1:
				print "[Scheduler] Limited (Down: " + str(self.dllimit/1024) + " Up: " + str(self.ullimit/1024) + ")"
			elif self.status == 2:
				print "[Scheduler] Paused"
			#gets called one time after statuschange

		#call stuff here every sec

	#Configuration dialog
	def configure(self):
		global scheduler_select

		#dialog
		dialog = gtk.Dialog(_("Scheduler Settings"),self.interface.window)
		dialog.set_default_size(600, 271)
		dialog.set_icon_from_file(self.path + "/scheduler.png")

		#buttons
		cancel_button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		ok_button = dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
		
		#text
		hover_text = gtk.Label()

		dllimit_label = gtk.Label(_("Limited Download Speed (KiB/s):"))
		ullimit_label = gtk.Label(_("Limited Upload Speed (KiB/s):"))

		#Select Widget
		drawing = scheduler_select(self.status_table, hover_text, self.days)

		#boxes
		vbox_main = gtk.VBox()
		hbox_main = gtk.HBox()
		vbox_sub = gtk.VBox()
		hbox_limit = gtk.HBox()

		#seperator
		sep = gtk.HSeparator()

		#spinbuttons

		dlinput = gtk.SpinButton()
		dlinput.set_numeric(True)	
		dlinput.set_range(-1, 2048)
		dlinput.set_increments(1, 10)
		if self.dllimit != -1:
			dlinput.set_value(self.dllimit/1024)
		else:
			dlinput.set_value(self.dllimit)

		ulinput = gtk.SpinButton()
		ulinput.set_numeric(True)
		ulinput.set_range(-1, 1024)
		ulinput.set_increments(1, 10)
		if self.ullimit != -1:
			ulinput.set_value(self.ullimit/1024)
		else:
			ulinput.set_value(self.ullimit)

		#pack
		dialog.vbox.pack_start(vbox_main)

		vbox_main.pack_start(hbox_main)
		vbox_main.pack_start(hover_text, False, True, 5)
		vbox_main.pack_start(sep, False, True)
		vbox_main.pack_start(hbox_limit, False, True, 5)

		hbox_main.pack_start(vbox_sub, False, True, 5)
		hbox_main.pack_start(drawing)

		hbox_limit.pack_start(dllimit_label, True, False)
		hbox_limit.pack_start(dlinput, True, False)
		hbox_limit.pack_start(ullimit_label, True, False)
		hbox_limit.pack_start(ulinput, True, False)

		#write weekdays
		for index in xrange(len(self.days)):
			vbox_sub.pack_start(gtk.Label(self.days[index]))

		#show
		dialog.show_all()

		#Save config	
		if dialog.run() == -5:
			self.status_table = copy.deepcopy(drawing.status_table)
			self.status = -1

			self.dllimit = int(dlinput.get_value())
			if self.dllimit != -1:
				self.dllimit *= 1024

			self.ullimit = int(ulinput.get_value())
			if self.ullimit != -1:
				self.ullimit *= 1024

			self.config.set("scheduler_table", drawing.status_table)
			self.config.set("scheduler_dl_limit", self.dllimit)
			self.config.set("scheduler_ul_limit", self.ullimit)
        	self.config.save(self.config_file)

		dialog.destroy()

class scheduler_select(gtk.DrawingArea):

	#connect signals - varaibles
	def __init__(self, data, label, days):
		gtk.DrawingArea.__init__(self)
		self.set_events(
			gtk.gdk.BUTTON_PRESS_MASK |
			gtk.gdk.BUTTON_RELEASE_MASK |
			gtk.gdk.POINTER_MOTION_MASK |
			gtk.gdk.LEAVE_NOTIFY_MASK
			)

		self.connect("expose_event", self.expose)
		self.connect("button_press_event", self.mouse_down)
		self.connect("button_release_event", self.mouse_up)
		self.connect("motion_notify_event", self.mouse_hover)
		self.connect("leave_notify_event", self.mouse_leave)

		self.colors = [
			[115.0/255, 210.0/255, 22.0/255],
			[237.0/255, 212.0/255, 0.0/255],
			[204.0/255, 0.0/255, 0.0/255]
			]
		self.modes = [_("normal"), _("limited"), _("paused")]
		self.status_table = data
		self.status_table_temp = copy.deepcopy(self.status_table)
		self.start_point = [0, 0]
		self.hover_point = [-1, -1]
		self.hover_label = label
		self.hover_days = days
		self.mouse_is_down = False

	#redraw the whole thing
	def expose(self, widget, event):
		self.context = self.window.cairo_create()
		self.context.set_line_width(1)
		self.context.rectangle(event.area.x, event.area.y,
			event.area.width, event.area.height)
		self.context.clip()

		width = self.window.get_size()[0]
		height = self.window.get_size()[1]

		for y in xrange(7):
			for x in xrange(24):
				self.context.set_source_rgba(
					self.colors[self.status_table_temp[x][y]][0],
					self.colors[self.status_table_temp[x][y]][1],
					self.colors[self.status_table_temp[x][y]][2], 0.65
					)
				self.context.rectangle(
					width*(6*x/145.0+1/145.0),
					height*(6*y/43.0+1/43.0),
					5*width/145.0,
					5*height/43.0
					)
				
				self.context.fill_preserve()
				self.context.set_source_rgba(0.4, 0.4, 0.4, 0.65)
				self.context.stroke()

	#coordinates --> which box
	def get_point(self, event):
		size = self.window.get_size()
		x = int((event.x-size[0]*0.5/145.0)/(6*size[0]/145.0))
		y = int((event.y-size[1]*0.5/43.0)/(6*size[1]/43.0))

		if x > 23: x = 23
		elif x < 0: x = 0
		if y > 6: y = 6
		elif y < 0: y = 0

		return [x,y]

	#mouse down
	def mouse_down(self, widget, event):
		self.mouse_is_down = True
		self.start_point = self.get_point(event)

	#if the same box -> change it
	def mouse_up(self, widget, event):
		self.mouse_is_down = False
		end_point = self.get_point(event)

		#change color on mouseclick depending on the button
		if end_point[0] is self.start_point[0] and end_point[1] is self.start_point[1]:
			if event.button == 1:
				self.status_table_temp[end_point[0]][end_point[1]] += 1
				if self.status_table_temp[end_point[0]][end_point[1]] > 2:
					self.status_table_temp[end_point[0]][end_point[1]] = 0
			elif event.button == 3:
				self.status_table_temp[end_point[0]][end_point[1]] -= 1
				if self.status_table_temp[end_point[0]][end_point[1]] < 0:
					self.status_table_temp[end_point[0]][end_point[1]] = 2
			self.queue_draw()

		self.status_table = copy.deepcopy(self.status_table_temp)

		self.set_infotext(end_point[0],end_point[1])

	def set_infotext(self, x, y):
		self.hover_label.set_text(self.hover_days[y] + " " + str(x) + ":00 - "
			+ str(x) + ":59" + " (" + self.modes[self.status_table_temp[x][y]] + ")")

	def clear_infotext(self):
		self.hover_label.set_text("")
		
	#if box changed and mouse is pressed draw all boxes from start point to end point
	#set hover text etc..
	def mouse_hover(self, widget, event):
		if self.get_point(event) != self.hover_point:
			self.hover_point = self.get_point(event)

			if self.mouse_is_down:
				self.status_table_temp = copy.deepcopy(self.status_table)

				points = [[self.hover_point[0], self.start_point[0]],
					[self.hover_point[1], self.start_point[1]]]

				for x in xrange(min(points[0]), max(points[0])+1):
					for y in xrange(min(points[1]), max(points[1])+1):
						self.status_table_temp[x][y] = self.status_table_temp[
							self.start_point[0]][self.start_point[1]]

				self.queue_draw()

			self.set_infotext(self.hover_point[0], self.hover_point[1])

	#clear hover text on mouse leave
	def mouse_leave(self, widget, event):
		self.clear_infotext()
		self.hover_point = [-1,-1]
