#!/usr/bin/env python
#
# delugeplugins.py
#
# Copyright (C) Zach Tibbitts 2006 <zach@collegegeek.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.

import os

class PluginManager:
	def __init__(self, deluge_core, deluge_interface):
		self.plugin_dirs = []
		self.available_plugins = {}
		self.enabled_plugins = {}
		self.core = deluge_core
		self.interface = deluge_interface
	
	def add_plugin_dir(self, directory):
		self.plugin_dirs.append(directory)
		
	def scan_for_plugins(self):
		register_plugin = self.register_plugin
		for folder in self.plugin_dirs:
			plugin_folders = os.listdir(folder)
			for plugin in plugin_folders:
				if os.path.isfile(folder + "/" + plugin + "/plugin.py"):
					self.path = folder + "/" + plugin
					execfile(folder + "/" + plugin + "/plugin.py")
	
	def get_available_plugins(self):
		return self.available_plugins.keys()
	
	def get_plugin(self, name):
		return self.available_plugins[name]
	
	def enable_plugin(self, name):
		self.enabled_plugins[name] = self.available_plugins[name]['class'](
					self.available_plugins[name]['path'], self.core, self.interface)

	def get_enabled_plugins(self):
		return self.enabled_plugins.keys()

	def disable_plugin(self, name):
		self.enabled_plugins[name].unload()
		self.enabled_plugins.pop(name)
		
	def configure_plugin(self, name):
		self.enabled_plugins[name].configure()
	
	def update_active_plugins(self):
		for name in self.enabled_plugins.keys():
			self.enabled_plugins[name].update()
	
	def shutdown_all_plugins(self):
		for name in self.enabled_plugins.keys():
			self.enabled_plugins[name].unload()
		self.enabled_plugins.clear()
	
	def register_plugin(self, name, plugin_class, version, description, config=False,
		default=False, requires=None, interface=None, required_plugins=None):
		self.available_plugins[name] = {'class': plugin_class, 
										'version': version, 
										'description': description, 
										'config': config, 
										'default': default, 
										'requires': requires, 
										'interface': interface, 
										'req plugins': required_plugins,
										'path': self.path}

## Few lines of code to test functionality
if __name__ == "__main__":
	p = PluginManager()
	p.add_plugin_dir("plugins/")
	p.scan_for_plugins()
	for x in p.plugins:
		print x
		for y in p.plugins[x]:
			print "\t", y
