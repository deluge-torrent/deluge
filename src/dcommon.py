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

import sys, os, os.path, webbrowser
import xdg, xdg.BaseDirectory

import gettext

PROGRAM_NAME = "Deluge"
PROGRAM_VERSION = "0.4.90.1"

CONFIG_DIR = xdg.BaseDirectory.save_config_path('deluge')

GLADE_DIR  = sys.prefix + '/share/deluge/glade'
PIXMAP_DIR = sys.prefix + '/share/deluge/pixmaps'
PLUGIN_DIR = sys.prefix + '/share/deluge/plugins'


class DelugePreferences:
	def __init__(self):
		self.pref = {}
	
	def set(self, key, value):
		self.pref[key] = value
	
	def get(self, key, kind=None):
		result = self.pref[key]
		if kind == None:
			return result
		elif kind == bool:
			# Python interprets bool("False") as True, so we must compensate for this
			if isinstance(result, str):
				return (result.lower() == "true")
			elif isinstance(result, int):
				return not (result == 0)
			else:
				return False
		elif kind == int:
			try:
				return int(result)
			except ValueError:
				return int(float(result))
			except:
				return 0
		elif kind == float:
			return float(result)
		elif kind == str:
			return str(result)
		else:
			return result
	
	def keys(self):
		return self.pref.keys()
	
	def clear(self):
		self.pref.clear()
	
	def load_from_file(self, filename):
		f = open(filename, mode='r')
		for line in f:
			try:
				(key, value) = line.split("=", 1)
				key = key.strip(" \n")
				value = value.strip(" \n")
				self.pref[key] = value
			except ValueError:
				pass
		f.close()
	
	def save_to_file(self, filename):
		f = open(filename, mode='w')
		f.write('#%s preferences file\n\n'%PROGRAM_NAME)
		for key in self.pref.keys():
			f.write(key)
			f.write(' = ')
			f.write(str(self.pref[key]))
			f.write('\n')
		f.flush()
		f.close()

def estimate_eta(state):
	try:
		return ftime(get_eta(state["total_size"], state["total_download"], state["download_rate"]))
	except ZeroDivisionError:
		return _("Infinity")
	
def get_eta(size, done, rate):
	return int( (size - done) / rate )

# Returns formatted string describing filesize
# fsize_b should be in bytes
# Returned value will be in either KB, MB, or GB
def fsize(fsize_b):
	fsize_kb = float (fsize_b / 1024.0)
	if fsize_kb < 1000:
		return '%.1f KB'%fsize_kb
	fsize_mb = float (fsize_kb / 1024.0)
	if fsize_mb < 1000:
		return '%.1f MB'%fsize_mb
	fsize_gb = float (fsize_mb / 1024.0)
	return '%.1f GB'%fsize_gb

# Returns a formatted string representing a percentage
def fpcnt(dec):
	return '%.2f%%'%(dec * 100)

# Returns a formatted string representing transfer rate
def frate(bps):
	return '%s/s'%(fsize(bps))

def fseed(state):
	return str(str(state['num_seeds']) + " (" + str(state['total_seeds']) + ")")
	
def fpeer(state):
	return str(str(state['num_peers']) + " (" + str(state['total_peers']) + ")")
	
def ftime(seconds):
	if seconds < 60:
		return '%ds'%(seconds)
	minutes = int(seconds/60)
	seconds = seconds % 60
	if minutes < 60:
		return '%dm %ds'%(minutes, seconds)
	hours = int(minutes/60)
	minutes = minutes % 60
	if hours < 24:
		return '%dh %dm'%(hours, minutes)
	days = int(hours/24)
	hours = hours % 24
	if days < 7:
		return '%dd %dh'%(days, hours)
	weeks = int(days/7)
	days = days % 7
	if weeks < 10:
		return '%dw %dd'%(weeks, days)
	return 'unknown'


def get_glade_file(fname):
	return GLADE_DIR + "/" + fname

def get_pixmap(fname):
	return PIXMAP_DIR + "/" + fname
	
def open_url_in_browser(link, foobar=None):
	try:
		webbrowser.open(link)
	except webbrowser.Error:
		print _("Error: no webbrowser found")
