# A simple plugin to display Hello, World

class plugin_Hello:
	def __init__(self, path, deluge_core, deluge_interface):
		self.path = path
		self.core = deluge_core
		self.interface = deluge_interface
	
	def unload(self):
		pass
	
	def update(self):
		print "Hello, World!"

register_plugin("Hello World",
				plugin_Hello,
				"1.0",
				'Displays "Hello, World"',
				requires="0.5.0")
