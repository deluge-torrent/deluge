# An example plugin for use with Deluge

# This plugin is intended to be used with Deluge's default GTK interface
class plugin_Example: # The plugin's class
	## Your plugin's contructor should follow this format
	## path				= A string containing the path to the plugin
	## deluge_core		= The active instance of the Deluge Manager
	## deluge_interface = The active instance of the Deluge Interface
	def __init__(self, path, deluge_core, deluge_interface):
		# Save the path, interface, and core so they can be used later
		self.path = path
		self.core = deluge_core
		self.interface = deluge_interface
		# Classes must be imported as they are needed from within
		# the plugin's functions
		import dcommon, gtk, gtk.glade, dgtk, pref
		# Create an options file and try to load existing Values
		self.config_file = dcommon.CONFIG_DIR + "/example.conf"
		self.config = pref.Preferences()
		try:
			self.config.load_from_file(self.config_file)
		except IOError:
			# File does not exist
			pass
		
		# Extract the configuration dialog from the gladefile
		self.glade = gtk.glade.XML(path + "/example.glade")
		self.dialog = self.glade.get_widget("dialog")
		self.dialog.set_icon_from_file(self.path + "/example-plugin.png")
		# Access the interface's toolbar
		self.toolbar = self.interface.toolbar
		# Make a toolbar button
		icon = gtk.Image()
		icon.set_from_file(self.path + "/example-plugin.png") # Toolbar items should be 22x22 pixel images
		self.button = gtk.ToolButton(icon_widget=icon, label="Example Plugin")
		self.button.connect("clicked", self.clicked) # Connect the signal handler for the button
		self.toolbar.add(self.button) # Add button to toolbar
		self.button.show_all() # Show the button
	
	
	## unload is called when the plugin is removed or Deluge is shut down
	def unload(self):
		self.toolbar.remove(self.button) # Remove the button from the toolbar
		self.config.save_to_file(self.config_file)
	
	## update will be called every UPDATE_INTERVAL (usually about 1 second)
	def update(self):
		# As this plugin doesn't need to do anything every interval, this
		# function will remain empty
		pass

	## This will be only called if your plugin is configurable
	def configure(self):
		entry1 = self.glade.get_widget("entry1")
		entry2 = self.glade.get_widget("entry2")
		try:
			entry1.set_text(self.config.get("option1"))
			entry2.set_text(self.config.get("option2"))
		except KeyError:
			entry1.set_text("")
			entry2.set_text("")
		self.dialog.show()
		response = self.dialog.run()
		self.dialog.hide()
		if response:
			self.config.set("option1", entry1.get_text())
			self.config.set("option2", entry2.get_text())
		
		
	
	## This will be called whenever self.button is clicked
	def clicked(self, button):
		# Build a dialog from scratch rather than from a glade file
		import gtk
		dialog = gtk.Dialog(title="Example Plugin", parent=self.interface.window,
				buttons=(gtk.STOCK_OK, 0))
		dialog.set_icon_from_file(self.path + "/example-plugin.png")
		try:
			text = 	"This is a popup notification from Example Plugin\n" + \
					"Your value for option1 is %s\n"%self.config.get("option1") + \
					"and option2 is %s"%self.config.get("option2")
		except KeyError:
			text =  "This is a popup notification from Example Plugin\n" + \
					"If you had set options by configuring this plugin,\n" + \
					"they would appear here"
		label = gtk.Label(text)
		dialog.vbox.pack_start(label)			
		
		dialog.show_all()
		dialog.run()
		dialog.hide()
		dialog.destroy()
	

register_plugin("Example Plugin",		# The name of the plugin
				plugin_Example,			# The plugin's class
				"0.5.0",				# The plugin's version number
				"An example plugin",	# A description of the plugin
				config=True,			# If the plugin can be configured
				default=False,			# If the plugin should be loaded by default
				requires="0.5.0",		# Required version of Deluge
				interface="gtk",		# Required Deluge interface
				required_plugins=None	# Any plugins that must be loaded before this
				)
