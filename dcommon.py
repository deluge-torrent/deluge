#!/usr/bin/env python2.4
#
# Deluge common class
# For functions and variables that
#  need to be accessed globally.

import sys, os, webbrowser

PROGRAM_NAME = "Deluge Torrent"
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