#!/usr/bin/python

class plugin_Example:
	def __init__(self, path, deluge_core, deluge_interface):
		self.path = path
		self.core = deluge_core
		self.interface = deluge_interface
		print "Example Plugin loaded"
	
	def unload(self):
		print "Example Plugin unloaded"
	
	def update(self):
		print "Hello World, from Example Plugin"
	
	
	

register_plugin("Example Plugin",
				plugin_Example,
				"0.2",
				"An example plugin",
				config=True,
				default=False,
				requires="0.5.0",
				interface="gtk",
				required_plugins=None)
