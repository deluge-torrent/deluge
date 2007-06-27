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

import sys, os, os.path, webbrowser
import xdg, xdg.BaseDirectory

import gettext

PROGRAM_NAME = "Deluge"
PROGRAM_VERSION = "0.5.2"

CLIENT_CODE = "DE"
CLIENT_VERSION = "".join(PROGRAM_VERSION.split('.'))+"0"*(4 - len(PROGRAM_VERSION.split('.')))

CONFIG_DIR = xdg.BaseDirectory.save_config_path('deluge')

# the necessary substitutions are made at installation time
INSTALL_PREFIX = '@datadir@'
GLADE_DIR  = os.path.join(INSTALL_PREFIX, 'share', 'deluge', 'glade')
PIXMAP_DIR = os.path.join(INSTALL_PREFIX, 'share', 'deluge', 'pixmaps')
PLUGIN_DIR = os.path.join(INSTALL_PREFIX, 'share', 'deluge', 'plugins')

def estimate_eta(state):
	try:
		return ftime(get_eta(state["total_size"], state["total_done"], state["download_rate"]))
	except ZeroDivisionError:
		return _("Infinity")
	
def get_eta(size, done, rate):
	if (size - done) == 0:
		raise ZeroDivisionError
	return (size - done) / rate

# Returns formatted string describing filesize
# fsize_b should be in bytes
# Returned value will be in either KB, MB, or GB
def fsize(fsize_b):
	fsize_kb = float (fsize_b / 1024.0)
	if fsize_kb < 1000:
		return _("%.1f KiB")%fsize_kb
	fsize_mb = float (fsize_kb / 1024.0)
	if fsize_mb < 1000:
		return _("%.1f MiB")%fsize_mb
	fsize_gb = float (fsize_mb / 1024.0)
	return _("%.1f GiB")%fsize_gb

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
	return os.path.join(GLADE_DIR, fname)

def get_pixmap(fname):
	return os.path.join(PIXMAP_DIR, fname)
	
def open_url_in_browser(dialog, link):
	try:
		webbrowser.open(link)
	except webbrowser.Error:
		print _("Error: no webbrowser found")
		
# Encryption States
class EncState:
	forced, enabled, disabled = range(3)
	
class EncLevel:
	plaintext, rc4, both = range(3)

class ProxyType:
	none, socks4, socks5, socks5_pw, http, http_pw = range(6)
