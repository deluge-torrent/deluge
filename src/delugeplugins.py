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
	def __init__(self):
		self.plugin_dirs = []
		self.plugins = {}
	
	def add_plugin_dir(self, directory):
		self.plugin_dirs.append(directory)
		
	def scan_for_plugins(self):
		register_plugin = self.register_plugin
		for folder in self.plugin_dirs:
			print "Looking in", folder
			plugin_folders = os.listdir(folder)
			for plugin in plugin_folders:
				if os.path.isfile(folder + plugin + "/plugin.py"):
					execfile(folder + plugin + "/plugin.py")
	
	def register_plugin(self,
						name,
						plugin_class,
						version,
						description,
						config=False,
						default=False,
						requires=None,
						interface=None,
						required_plugins=None):
		self.plugins[name] = (plugin_class, version, description, config, default, requires, interface, required_plugins)

## Few lines of code to test functionality
if __name__ == "__main__":
	p = PluginManager()
	p.add_plugin_dir("plugins/")
	p.scan_for_plugins()
	for x in p.plugins:
		print x
		for y in p.plugins[x]:
			print "\t", y