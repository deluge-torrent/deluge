# netgraph plugin

class plugin_NetGraph:
	def __init__(self, path, deluge_core, deluge_interface):
		import gtk
		self.parent   = deluge_interface
		self.location = path
		self.core = deluge_core

		self.image  = gtk.Image()

		self.viewPort = gtk.Viewport()
		self.viewPort.add(self.image)

		self.scrolledWindow = gtk.ScrolledWindow()
		self.scrolledWindow.add(self.viewPort)
		self.scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

		self.topWidget = self.scrolledWindow

		self.parentNotebook = self.parent.notebook
#		print "Parent NOTEBOOK:", self.parentNotebook
		self.parentNotebook.append_page(self.topWidget, gtk.Label("NetGraph"))
#		print "My INDEX in parentNoteBook:", self.index

		self.image.show()
		self.viewPort.show()
		self.scrolledWindow.show()

		self.length = 60

		self.width  = -1
		self.height = -1

		import pango

		self.pangoContext = self.parent.window.get_pango_context()
		self.pangoLayout = pango.Layout(self.pangoContext)

		self.savedUpSpeeds   = []
		self.savedDownSpeeds = []

		self.bootupRuns = 3  # This ensures that we pass the resizing phase, with scrollbars, etc.
									# So the first time it is viewed, we are all ready

	def unload(self): # Shutdown is called when the plugin is deactivated
		numPages = self.parentNotebook.get_n_pages()
		for page in range(numPages):
			if self.parentNotebook.get_nth_page(page) == self.topWidget:
				self.parentNotebook.remove_page(page)
				break

	def configure(self):
		pass

	def update(self):
		import gtk
		session_info = self.core.get_state()
		self.savedUpSpeeds.insert(0, session_info['upload_rate'])
		if len(self.savedUpSpeeds) > self.length:
			self.savedUpSpeeds.pop()
		self.savedDownSpeeds.insert(0, session_info['download_rate'])
		if len(self.savedDownSpeeds) > self.length:
			self.savedDownSpeeds.pop()

		if not self.parentNotebook.get_nth_page(self.parentNotebook.get_current_page()) == \
				 self.topWidget and not self.bootupRuns > 0:
			return

		self.bootupRuns = max(self.bootupRuns - 1, 0)

		extraWidth  = self.scrolledWindow.get_vscrollbar().get_allocation().width  * 1.5
		extraHeight = self.scrolledWindow.get_hscrollbar().get_allocation().height * 1.5
		allocation = self.scrolledWindow.get_allocation()
		allocation.width  = int(allocation.width)  - extraWidth
		allocation.height = int(allocation.height) - extraHeight

		# Don't try to allocate a size too small, or you might crash
		if allocation.width < 2 or allocation.height < 2:
			return

#		savedDownSpeeds = [1,2,3,2,1]
#		savedUpSpeeds = [5,8,0,0,1,2]

#		allocation = self.image.get_allocation()
#		allocation.width  = 300
#		allocation.height = 200

		if not allocation.width == self.width or not allocation.height == self.height:
#			print "New Pixmap!"
			self.width  = allocation.width
			self.height = allocation.height

			self.networkPixmap = gtk.gdk.Pixmap(None, self.width, self.height, 24)
			self.image.set_from_pixmap(self.networkPixmap, None)
			self.ctx = self.networkPixmap.cairo_create()

		self.networkPixmap.draw_rectangle(self.image.get_style().white_gc,True, 0, 0, self.width, self.height)

		maxSpeed = max(max(self.savedDownSpeeds),max(self.savedUpSpeeds))

		if maxSpeed == 0:
			return

		maxSpeed = maxSpeed*1.1 # Give some extra room on top

		self.drawSpeedPoly(self.savedDownSpeeds, (0.5,1,   0.5, 1.0),    maxSpeed, True)
		self.drawSpeedPoly(self.savedDownSpeeds, (0,  0.75,0,   1.0),    maxSpeed, False)

		self.drawSpeedPoly(self.savedUpSpeeds,   (0.33,0.33,1.0,  0.5),  maxSpeed, True)
		self.drawSpeedPoly(self.savedUpSpeeds,   (0,   0,   1.0,  0.75), maxSpeed, False)

		meanUpSpeed   = sum(self.savedUpSpeeds)  /len(self.savedUpSpeeds)
		meanDownSpeed = sum(self.savedDownSpeeds)/len(self.savedDownSpeeds)
		shownSpeed    = max(meanUpSpeed, meanDownSpeed)
		
		import dcommon

		self.pangoLayout.set_text(dcommon.frate(shownSpeed))
		self.networkPixmap.draw_layout(self.image.get_style().black_gc,
												 4,
												 int(self.height - 1 - (self.height*shownSpeed/maxSpeed)),
												 self.pangoLayout)

		self.networkPixmap.draw_line(self.image.get_style().black_gc,
											  0,			  int(self.height - (self.height*shownSpeed/maxSpeed)),
											  self.width, int(self.height - (self.height*shownSpeed/maxSpeed)))

		self.networkPixmap.draw_rectangle(self.image.get_style().black_gc,False, 0, 0, self.width-1, self.height-1)

		self.image.queue_draw()

	def tracePath(self, speeds, maxSpeed):
		lineWidth = 4

		self.ctx.set_line_width(lineWidth)

		self.ctx.move_to(self.width + lineWidth,self.height + lineWidth)
		self.ctx.line_to(self.width + lineWidth,int(self.height-(self.height*speeds[0]/maxSpeed)))

		for i in range(len(speeds)):
			self.ctx.line_to(int(self.width-1-((i*self.width)/(self.length-1))),
									int(self.height-1-(self.height*speeds[i]/maxSpeed)))

		self.ctx.line_to(int(self.width-1-(((len(speeds)-1)*self.width)/(self.length-1))),
								int(self.height)-1 + lineWidth)

		self.ctx.close_path()

	def drawSpeedPoly(self, speeds, color, maxSpeed, fill):

		self.tracePath(speeds, maxSpeed)
		self.ctx.set_source_rgba(color[0],color[1],color[2], color[3])

		if fill:
			self.ctx.fill()
		else:
			self.ctx.stroke()


### Register plugin with Deluge

register_plugin("Network Activity Graph",		# The name of the plugin
				plugin_NetGraph,			# The plugin's class
				"0.2",				# The plugin's version number
				"Network Activity Graph plugin\n\nWritten by Kripkenstein",	# A description of the plugin
				config=False,			# If the plugin can be configured
				default=False,			# If the plugin should be loaded by default
				requires="0.5.0",		# Required version of Deluge
				interface="gtk",		# Required Deluge interface
				required_plugins=None	# Any plugins that must be loaded before this
				)
