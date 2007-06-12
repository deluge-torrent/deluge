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
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

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
				if os.path.isfile(os.path.join(folder, plugin, "plugin.py")):
					self.path = os.path.join(folder, plugin)
					execfile(os.path.join(folder, plugin, "plugin.py"))
	
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
	
	def register_plugin(self, name, plugin_class, author, version, description, config=False):
		self.available_plugins[name] = {'class': plugin_class, 
										'author': author,
										'version': version, 
										'description': description, 
										'config': config, 
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
