#!/usr/bin/python

class plugin_Example:
	def __init__(self, deluge_core, deluge_interface):
		self.core = deluge_core
		self.interface = deluge_interface
	
	def unload(self):
		pass
	
	def update(self):
		pass
	

register_plugin("Example",
				plugin_Example,
				"0.2",
				"An example plugin",
				requires="0.5.0")