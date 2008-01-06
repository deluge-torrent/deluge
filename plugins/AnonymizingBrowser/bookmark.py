# -*- coding: utf-8 -*-
#
# bookmark.py
#
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

import cPickle
import os.path
import pygtk
pygtk.require("2.0")
import gtk.glade
import deluge.common

class BookmarkManager:
    """class builds and displays our internal bookmark manager"""
    def __init__(self, path, parent, toolbutton):
        """show bookmark manager"""
        self.bookmarks = []
        self.toolbutton = toolbutton
        self.menu = gtk.Menu()
        self.parent = parent
        self.widgets = gtk.glade.XML(path + "/list_bookmarks.glade")
        self.list_dlg = self.widgets.get_widget("list_bookmarks_dialog")
        self.treeview = self.widgets.get_widget("bookmarks_treeview")
        self.add_bookmark_dialog = self.widgets.get_widget("add_bookmark_dialog")
        self.edit_bookmark_dialog = self.widgets.get_widget("edit_bookmark_dialog")
        if deluge.common.windows_check():
            self.add_bookmark_dialog.set_position(gtk.WIN_POS_CENTER_ALWAYS)
            self.edit_bookmark_dialog.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        else:
            self.list_dlg.set_icon(deluge.common.get_logo(18))
            self.edit_bookmark_dialog.set_icon(deluge.common.get_logo(18))
            self.add_bookmark_dialog.set_icon(deluge.common.get_logo(18))
        self.list_dlg.set_transient_for(self.parent.window)
        self.signal_dic = { "on_button_cancel_clicked" : self.on_button_cancel_clicked,
                            "on_button_ok_clicked" : self.on_button_ok_clicked,
                            "on_button_add_clicked" : self.on_button_add_clicked,
                            "on_button_edit_clicked" : self.on_button_edit_clicked,
                            "on_button_remove_clicked" : self.on_button_remove_clicked,
                            "on_button_add_ok_clicked" : self.on_button_add_ok_clicked,
                            "on_button_add_cancel_clicked" : self.on_button_add_cancel_clicked,
                            "on_button_edit_ok_clicked" : self.on_button_edit_ok_clicked,
                            "on_button_edit_cancel_clicked" : self.on_button_edit_cancel_clicked,
                            "quit" : self.on_button_cancel_clicked
                         }
        self.widgets.signal_autoconnect(self.signal_dic)
        # Create a liststore for tier, url
        self.liststore = gtk.ListStore(str, str)
        
        # Create the columns
        self.treeview.append_column(
            gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=0))
        self.treeview.append_column(
            gtk.TreeViewColumn("URL", gtk.CellRendererText(), text=1))

        self.treeview.set_model(self.liststore)            
        self.liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.load_bookmarks()
        
        self.build_menu()

    def show(self):
        self.list_dlg.show()

    def hide(self):
        self.list_dlg.hide()
        if deluge.common.windows_check():
            path = os.path.join(deluge.common.CONFIG_DIR, "bookmarks.save")
        else:
            path = os.path.join(deluge.common.CONFIG_DIR, "mozilla", "bookmarks.save")
        try:
            bookmark_file = open(path, "wb")
            cPickle.dump(self.bookmarks, bookmark_file)
            bookmark_file.close()
        except Exception, e:
            print "Unable to save bookmarks file: %s", e

    def load_bookmarks(self):
        bookmarks = None
        if deluge.common.windows_check():
            path = os.path.join(deluge.common.CONFIG_DIR, "bookmarks.save")
        else:
            path = os.path.join(deluge.common.CONFIG_DIR, "mozilla", "bookmarks.save")

        if os.path.exists(path):
            try:
                bookmark_file = open(path, "rb")
                bookmarks = cPickle.load(bookmark_file)
                bookmark_file.close()
            except Exception, e:
                print "Unable to load bookmarks file: %s", e
        
        if bookmarks == None:
            return
        
        self.liststore.clear()
            
        for bookmark in bookmarks:
            self.liststore.append([bookmark["name"], bookmark["url"]])
        
        self.bookmarks = bookmarks
            
        self.build_menu()
    
    def build_menu(self):
        """Builds the bookmark menu"""
        self.menu = gtk.Menu()
        menuitem = gtk.MenuItem("Bookmark This Page...")
        menuitem.connect("activate", self.menuitem_activate)
        self.menu.append(menuitem)
        menuitem = gtk.SeparatorMenuItem()
        self.menu.append(menuitem)
        # Iterate through the bookmark list and make menuitems for them
        def add_menuitem(model, path, row, data):
            menuitem = gtk.MenuItem(model.get_value(row, 0))
            menuitem.connect("activate", self.menuitem_activate)
            self.menu.append(menuitem)
        
        self.liststore.foreach(add_menuitem, None)
        self.menu.show_all()
        # Set the new menu on the toolbutton
        self.toolbutton.set_menu(self.menu)
        
    def add_bookmark(self, name, url):
        """Adds a bookmark to the list"""
        self.liststore.append([name, url])
        self.build_menu()

    def get_selected(self):
        """Returns the selected bookmark"""
        return self.treeview.get_selection().get_selected()[1]

    def on_button_add_clicked(self, widget):
        # Show the add bookmark dialog
        self.add_bookmark_dialog.show()
        self.widgets.get_widget("entry_add_name").grab_focus()

    def on_button_edit_clicked(self, widget):
        # Show the edit bookmark dialog
        selected = self.get_selected()
        if selected != None:
            self.edit_bookmark_dialog.show()
            self.widgets.get_widget("entry_edit_name").grab_focus()
            self.widgets.get_widget("entry_edit_name").set_text(self.liststore.\
                get_value(selected, 0))
            self.widgets.get_widget("entry_edit_url").set_text(self.liststore.\
                get_value(selected, 1))

    def on_button_add_ok_clicked(self, widget):
        # Get values from the entry widgets
        name = self.widgets.get_widget("entry_add_name").get_text()
        url = self.widgets.get_widget("entry_add_url").get_text()
        
        self.add_bookmark(name, url)
        # Clear the entry widget and hide the dialog
        self.widgets.get_widget("entry_add_name").set_text("")
        self.widgets.get_widget("entry_add_url").set_text("")
        self.add_bookmark_dialog.hide()

    def on_button_add_cancel_clicked(self, widget, arg=None):
        # Clear the entry widget and hide the dialog
        self.widgets.get_widget("entry_add_name").set_text("")
        self.widgets.get_widget("entry_add_url").set_text("")
        self.add_bookmark_dialog.hide()
        if arg != None:
            return True
        
    def on_button_edit_ok_clicked(self, widget):
        # Get values from the entry widgets
        name = self.widgets.get_widget("entry_edit_name").get_text()
        url = self.widgets.get_widget("entry_edit_url").get_text()
        selected = self.get_selected()
        if selected != None:
            self.liststore.remove(selected)
        self.add_bookmark(name, url)
        self.build_menu()

        # Clear the entry widget and hide the dialog
        self.widgets.get_widget("entry_edit_name").set_text("")
        self.widgets.get_widget("entry_edit_url").set_text("")
        self.edit_bookmark_dialog.hide()

    def on_button_edit_cancel_clicked(self, widget, arg=None):
        # Clear the entry widget and hide the dialog
        self.widgets.get_widget("entry_edit_name").set_text("")
        self.widgets.get_widget("entry_edit_url").set_text("")
        self.edit_bookmark_dialog.hide()
        if arg != None:
            return True
        
    def on_button_remove_clicked(self, widget):
        selected = self.get_selected()
        if selected != None:
            self.liststore.remove(selected)

        self.build_menu()
        
    def on_button_cancel_clicked(self, widget, arg=None):
        self.load_bookmarks()
        self.hide()
        if arg != None:
            return True
        
    def on_button_ok_clicked(self, widget):
        def each(model, path, iter, data):
            bookmark = {}
            bookmark["name"] = model.get_value(iter, 0)
            bookmark["url"] = model.get_value(iter, 1)
            self.bookmarks.append(bookmark)
        self.bookmarks = []
        self.liststore.foreach(each, None)
        self.hide()

    def menuitem_activate(self, widget):
        text = widget.get_child().get_text()
        def load_url(model, path, row, data):
            if model.get_value(row, 0) == text:
                # Grab the URL and load it
                url = model.get_value(row, 1)
                self.parent.txt_url.set_text(url)
                self.parent.load_url()
        if text == "Bookmark This Page...":
            # Show the add bookmark dialog
            self.add_bookmark_dialog.show()
            self.widgets.get_widget("entry_add_name").grab_focus()
            self.widgets.get_widget("entry_add_url").set_text(
                self.parent.txt_url.get_text())
            self.on_button_ok_clicked(widget)
            return
            
        self.liststore.foreach(load_url, None)
