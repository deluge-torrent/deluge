# dcommon.py
#
# Copyright (C) Zach Tibbitts 2006 <zach@collegegeek.org>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# dcommon.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with main.py.  If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.

import sys, os, webbrowser

PROGRAM_NAME = "Deluge"
PROGRAM_VERSION = "0.5"
DELUGE_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
GLADE_DIR = DELUGE_DIR + "/glade"
PIXMAP_DIR = DELUGE_DIR + "/pixmaps"

def get_glade_file(fname):
	return GLADE_DIR + "/" + fname

def get_pixmap(fname):
	return PIXMAP_DIR + "/" + fname
	
def open_url_in_browser(dialog, link):
	try:
		webbrowser.open(link)
	except webbrowser.Error:
		print "Error: no webbrowser found"