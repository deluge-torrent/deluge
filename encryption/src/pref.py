# pref.py
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


# Preferences is basically a wrapper around a simple Python dictionary
# object.  However, this class provides a few extra features on top of
# the built in class that Deluge can take advantage of.
class Preferences:
	def __init__(self, filename=None, defaults=None):
		self.mapping = {}
		self.config_file = filename
		if self.config_file is not None:
			self.load_from_file(self.config_file)
		if defaults is not None:
			for key in defaults.keys():
				self.mapping.setdefault(key, defaults[key])
	
	# Allows you to access an item in a Preferences objecy by calling
	# instance[key] rather than instance.get(key).  However, this will
	# return the value as the type it is currently in memory, so it is
	# advisable to use get() if you need the value converted.
	def __getitem__(self, key):
		return self.mapping[key]
	
	def __setitem__(self, key, value):
		self.mapping[key] = value
	
	def __delitem__(self, key):
		del self.mapping[key]
	
	def __len__(self):
		return len(self.mapping)
	
	def has_key(self, key): return self.mapping.has_key(key)
	def items(self): return self.mapping.items()
	def keys(self): return self.mapping.keys()
	def values(self): return self.mapping.values()
	
	def save_to_file(self, filename=None):
		if filename is None:
			filename = self.config_file
		f = open(filename, mode='w')
		keys = self.mapping.keys()
		keys.sort()
		for key in keys:
			f.write(key)
			f.write(' = ')
			f.write(str(self.mapping[key]))
			f.write('\n')
		f.flush()
		f.close()
		self.config_file = filename
	
	def load_from_file(self, filename=None):
		if filename is None:
			filename = self.config_file
		f = open(filename, mode='r')
		for line in f:
			try:
				(key, value) = line.split('=', 1)
				key = key.strip(' \n')
				value = value.strip(' \n')
				self.mapping[key] = value
			except ValueError:
				pass
		f.close()
		self.config_file = filename
	
	def set(self, key, value):
		self.mapping[key] = value	
	
	def get(self, key, kind=None, default=None):
		if not key in self.mapping.keys():
			if default is not None:
				self.mapping[key] = default
				return default
			else:
				raise KeyError
		result = self.mapping[key]
		if kind == None:
			pass
		elif kind == bool:
			if isinstance(result, str):
				result = not (result.lower() == "false")
			elif isinstance(result, int):
				result = not (result == 0)
			else:
				result = False
		elif kind == int:
			try:
				result = int(result)
			except ValueError:
				result = int(float(result))
		elif kind == float:
			result = float(result)		
		elif kind == str:
			result = str(result)
		else:
			pass
		
		return result
	
	def remove(self, key):
		self.mapping.pop(key)
	
	def clear(self):
		self.mapping.clear()
		
	def printout(self):
		for key in self.mapping.keys():
			print key, ':', self.mapping[key]
		
