class plugin_Hello:
	def __init__(self, path, deluge_core, deluge_interface):
		self.path = path
		self.core = deluge_core
		self.interface = deluge_interface
		print "Hello World loaded"
	
	def unload(self):
		print "Hello World unloaded"
	
	def update(self):
		print "Hello, World!"
	
	
	

register_plugin("Hello World",
				plugin_Hello,
				"1.0",
				'Displays "Hello, World"',
				config=False,
				default=False,
				requires="0.5.0",
				interface=None,
				required_plugins=None)
