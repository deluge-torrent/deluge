#!/usr/bin/env python2.4
#
# Deluge common class
# For functions and variables that
#  need to be accessed globally.

import deluge, dcommon

import sys, os, gettext
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade


class DelugeGTK:
	def __init__(self):
		self.gladefile = dcommon.get_glade_file("delugegtk.glade")
		self.wtree = gtk.glade.XML(self.gladefile)
		self.window = self.wtree.get_widget("main_window")
		if(self.window):
			self.window.connect("destroy", gtk.main_quit)
		self.window.set_title(dcommon.PROGRAM_NAME + " " + dcommon.PROGRAM_VERSION)
		self.window.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		actions = 	{
					## File Menu
					"new_torrent": self.new_torrent,
					"add_torrent": self.add_torrent,
					"pref_clicked": self.show_preferences_dialog,
					"plugins_clicked": self.show_plugins_dialog,
					## Torrent Menu
					"show_info": self.show_info_pane,
					## Help Menu
					"show_about_dialog": self.show_about_dialog,
					}
		self.wtree.signal_autoconnect(actions)
		
		## Create the about dialog
		gtk.about_dialog_set_url_hook(dcommon.open_url_in_browser)
		self.abt = gtk.AboutDialog()
		self.abt.set_name(dcommon.PROGRAM_NAME)
		self.abt.set_version(dcommon.PROGRAM_VERSION)
		self.abt.set_website("http://deluge-torrent.org")
		self.abt.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		self.abt.set_logo(gtk.gdk.pixbuf_new_from_file(
				dcommon.get_pixmap("deluge256.png")))
		## Create the preferences dialog
		self.prf = self.wtree.get_widget("pref_dialog")
		self.prf.set_icon_from_file(dcommon.get_pixmap("deluge32.png"))
		
		
	
	def new_torrent(self, obj):
		pass
		
	def add_torrent(self, obj):
		pass
		
	def show_preferences_dialog(self, obj):
		self.prf.show_all()
		self.wtree.get_widget("pref_notebook").set_current_page(0)
		self.prf.run()
		self.prf.hide_all()

	def show_plugins_dialog(self, obj):
		self.prf.show_all()
		self.wtree.get_widget("pref_notebook").set_current_page(2)
		self.prf.run()
		self.prf.hide_all()

	def show_info_pane(self, obj):
		if(obj.get_active()):
			self.wtree.get_widget("torrent_info").show()
		else:
			self.wtree.get_widget("torrent_info").hide()
		
				
		
	def show_about_dialog(self, obj):
		self.abt.show_all()
		self.abt.run()
		self.abt.hide_all()

		

if __name__ == "__main__":
	dgtk = DelugeGTK()
	gtk.main()