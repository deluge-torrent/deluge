# Popup Notifier plugin

class plugin_PopupNotifier:
	def __init__(self, path, deluge_core, deluge_interface):
#		print "PopupNotifierI being created now"
		self.parent = deluge_interface
		self.location = path
		import dcommon, dgtk, pref
		try:
			import pynotify
			self.pynotify = pynotify # We must save this, because as a plugin, our globals will die
		except:
			dgtk.show_popup_warning(self. parent.window, "PopupNotifier: not all necessary dependencies are installed. To install them, on Ubuntu run: apt-get python-notify notification-daemon")
			return

		if not self.pynotify.init("Deluge"):
			dgtk.show_popup_warning(self. parent.window, "PopupNotifier: Cannot initialize pynotify, no notifications will be shown.")

		self.severities = { "I": 1, "W": 2, "C": 3, "F": 4 }

		self.severityTexts = {
				self.severities["I"]: "Informative - can be easily ignored",
				self.severities["W"]: "Warning - may be of interest",
				self.severities["C"]: "Critical - should never be ignored",
				self.severities["F"]: "Fatal - normal operation will probably not continue" }

		self.severityToUrgency = { "I": pynotify.URGENCY_LOW,
											"W": pynotify.URGENCY_NORMAL,
											"C": pynotify.URGENCY_NORMAL,
											"F": pynotify.URGENCY_CRITICAL }

		self.config = pref.Preferences(dcommon.CONFIG_DIR + '/popupnotify.conf')

		userSeverity = self.config.get('plugin_popupnotifier_severity', default=self.severities["W"])
		
		self.minSeverity = int(userSeverity)

		if self.minSeverity is None:
			self.minSeverity = self.severities['I']

		self.icon = "file://" + dccommon.get_pixmap("deluge32.png")

		# Connect signal in the parent
		# self.handlerID = self.parent.messageList.connect("insert-text", self.signal)

	def unload(self):
#		print "PopupNotifierI is shutting down now"
		# self.parent.messageList.disconnect(self.handlerID)
		pass

	def update(self):
#		print "PopupNotifier Updating..."
		pass

	def signal(self, textbuffer, iter, text, length):
#		print "Signal occured, need to show: ", text
		severity = text[0]
		if self.severities[severity] >= self.minSeverity:
			startIndex = text.find("] ")+2
			note = self.pynotify.Notification("Deluge", text[startIndex:], self.icon)
			note.set_urgency(self.severityToUrgency[severity])
			if not note.show():
				print "Failed to send notification:", text

	def configure(self):
		self.gladefile = self.location + "/PopupNotifierConfig.glade"
		self.wTree = gtk.glade.XML(self.gladefile, "PopupNotifierConfig")
		self.dlg = self.wTree.get_widget("PopupNotifierConfig")

		self.severitySelector   = self.wTree.get_widget("severity_selector")
		self.severitySelector.set_value(self.minSeverity)
		self.severitySelector.connect("change-value", self.dlgChangeValue)

		self.severityDescriptor = self.wTree.get_widget("severity_descriptor")
#		self.descriptorTextBuffer = gtk.TextBuffer()
#		self.severityDescriptor.set_buffer(self.descriptorTextBuffer)

		self.dlgShowText()

		# Show and run

		self.dlg.show_all()

		if self.dlg.run() == 1:
			self.minSeverity = int(self.severitySelector.get_value())
			self.config.set('plugin_popupnotifier_severity', self.minSeverity)
#		else:
#			print "Cancelled"

		self.dlg.destroy()
		self.config.save_to_file()

	def dlgChangeValue(self, range, scroll, value):
		self.severitySelector.set_value(round(value))
		self.dlgShowText()
		return True

	def dlgShowText(self):
		severity = int(self.severitySelector.get_value())
		self.severityDescriptor.set_text(self.severityTexts[severity])


### MAIN

register_plugin("Popup Notifier",		# The name of the plugin
				plugin_PopupNotifier,			# The plugin's class
				"0.2",				# The plugin's version number
				"Popup Notifier plugin\n\nWritten by Kripkenstein",	# A description of the plugin
				config=True,			# If the plugin can be configured
				default=False,			# If the plugin should be loaded by default
				requires="0.5.0",		# Required version of Deluge
				interface="gtk",		# Required Deluge interface
				required_plugins=None	# Any plugins that must be loaded before this
				)
