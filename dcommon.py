# dcommon.py
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

import sys, os, webbrowser

PROGRAM_NAME = "Deluge"
PROGRAM_VERSION = "0.4.9.0"
DELUGE_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
GLADE_DIR = DELUGE_DIR + "/glade"
PIXMAP_DIR = DELUGE_DIR + "/pixmaps"

class DelugePreferences:
	def __init__(self):
		self.pref = {}
	
	def set(self, key, value):
		self.pref[key] = value
	
	def get(self, key):
		return self.pref[key]
	
	def load_from_file(self, filename):
		f = open(filename, mode='r')
		for line in f:
			(key, value) = line.split("=")
			key = key.strip(" \n")
			value = value.strip(" \n")
			self.pref[key] = value
		f.close()
	
	def save_to_file(self, filename):
		f = open(filename, mode='w')
		for key in self.pref.keys():
			f.write(key)
			f.write(' = ')
			f.write(self.pref[key])
			f.write('\n')
		f.flush()
		f.close()

def get_glade_file(fname):
	return GLADE_DIR + "/" + fname

def get_pixmap(fname):
	return PIXMAP_DIR + "/" + fname
	
def open_url_in_browser(dialog, link):
	try:
		webbrowser.open(link)
	except webbrowser.Error:
		print "Error: no webbrowser found"