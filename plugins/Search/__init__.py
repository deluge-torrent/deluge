# -*- coding: utf-8 -*-
#
# plugin.py
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


plugin_name = "Torrent Search"
plugin_author = "Marcos Pinto"
plugin_version = "0.3"
plugin_description = _("Search for torrents anonymously")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return Search(path, core, interface)

### The Plugin ###
import deluge
import deluge.common
import gtk
import os.path

class Search:
    def __init__(self, path, core, interface):
        print "Found TorrentSearch plugin..."
        import gtk, gtk.glade, os
        import deluge.dgtk, deluge.pref
        self.interface = interface
        self.config_file = os.path.join(deluge.common.CONFIG_DIR, "newsearch.conf")
        self.config = deluge.pref.Preferences(self.config_file, False,
                      defaults={'YouTorrent': 'http://www.youtorrent.com/tag/?q=${query}',
                                'Pirate Bay' : 'http://thepiratebay.org/search/${query}/0/7/0',
                                'Google' : "http://www.google.com/cse?cx=010331601\
931556850092%3Apfadwhze_jy&q=${query}&sa=Search&cof=FORID%3A1",
                                'Mininova' : 'http://www.mininova.org/search/?search=${query}/seeds',
                                'isoHunt' : "http://isohunt.com/torrents/?ihq=${query}"})
        try:
            self.config.load()
        except IOError:
            pass

        glade = gtk.glade.XML(path + "/searchdlg.glade")
        self.dlg = glade.get_widget("search_dialog")
        if not deluge.common.windows_check():
            self.dlg.set_icon(deluge.common.get_logo(18))
        self.view = glade.get_widget("search_view")
        model = gtk.ListStore(str, str)
        self.view.set_model(model)
        deluge.dgtk.add_text_column(self.view, _("Name"), 0, width=80)
        deluge.dgtk.add_text_column(self.view, _("Search String"), 1)
        self.field_name = glade.get_widget("field_name")
        self.field_search = glade.get_widget("field_search")
        self.button_add = glade.get_widget("button_addsearch")
        self.button_del = glade.get_widget("button_delsearch")
        dic = { "add_clicked"    : self.add_clicked,
                "del_clicked"    : self.del_clicked,
                "row_clicked"    : self.row_clicked,
                "text_changed"    : self.text_changed }
        glade.signal_autoconnect(dic)
        self.view.get_selection().set_select_function(self.row_clicked)
        ### Note: All other plugins should use self.interface.toolbar
        ### when adding items to the toolbar
        self.se = ''
        self.toolbar = self.interface.wtree.get_widget("tb_left")
        self.search_entry = gtk.Entry()
        self.search_entry.connect("activate", self.torrent_search) 
        self.search_item = gtk.ToolItem()
        self.search_item.add(self.search_entry)
        self.search_icon = gtk.Image()
        self.search_icon.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.menu_button = gtk.MenuToolButton(self.search_icon, _("Choose an Engine"))
        self.menu_button.set_is_important(True)
        self.menu_button.connect("clicked", self.torrent_search)
        self.menu = gtk.Menu()
        self.manage_item = gtk.ImageMenuItem(_("Manage Engines"))
        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.manage_item.set_image(self.image)
        self.manage_item.connect("activate", self.configure)
        self.menu.add(self.manage_item)
        self.menu_button.set_menu(self.menu)
        self.toolbar.insert(self.menu_button, -1)
        self.toolbar.insert(self.search_item, -1)
        self.populate_search_menu()
        self.toolbar.show_all()
        self.search_item.show_all()
        self.menu_button.show_all()
        self.menu.show_all()

    def unload(self):
        self.config.save(self.config_file)
        self.toolbar.remove(self.search_item)
        self.toolbar.remove(self.menu_button)

    def text_changed(self, args):
        a = (self.field_name.get_text() != "")
        b = (self.field_search.get_text() != "")
        if(a and b):
            self.button_add.set_sensitive(1)
        else:
            self.button_add.set_sensitive(0)

    def add_clicked(self, args):
        self.view.get_model().append([self.field_name.get_text(),
                    self.field_search.get_text()])
        self.field_name.set_text("")
        self.field_search.set_text("")
            
    def del_clicked(self, args):
        (model, selection) = self.view.get_selection().get_selected()
        model.remove(selection)
        self.button_del.set_sensitive(0)
            
    def row_clicked(self, args):
        self.button_del.set_sensitive(1)
        return True
    
    def configure(self, widget=None):
        import gtk, gtk.glade
        from deluge import common
        self.dlg.show_all()
        model = self.view.get_model()
        model.clear()
        for name in self.config.keys():
            self.view.get_model().append( (name, self.config.get(name)) )
        self.button_add.set_sensitive(0)
        self.button_del.set_sensitive(0)
        result = self.dlg.run()
        self.dlg.hide_all()
        if result == 1:
            self.config.clear()
            the_iter = model.get_iter_first()
            while the_iter is not None:
                self.config.set(model.get_value(the_iter, 0), model.get_value(the_iter, 1))
                the_iter = model.iter_next(the_iter)
            self.config.save(self.config_file)
        self.populate_search_menu()
        

    def torrent_search(self, widget=None):
        if self.search_entry.get_text() != "":
            from deluge import common
            print "Searching with engine", self.se
            url = self.config.get(self.se)
            entry = self.search_entry.get_text()
            entry = entry.replace(' ', '+')
            url = url.replace('${query}', entry)
            print 'URL =', url
            print 'Entry =', entry
            common.open_url_in_browser(url)
        
    def populate_search_menu(self):
        import gtk
        self.menu_button.set_label(_("Choose an Engine"))
        for child in self.menu.get_children():
            self.menu.remove(child)
        group = None
        i = 0
        for engine in self.config.keys():
            rmi = gtk.RadioMenuItem(None, engine)
            rmi.eng_name = engine
            rmi.connect("activate", self.select_search, rmi.eng_name)
            if (group != None):
                rmi.set_group(group)
            else:
                group = rmi
                rmi.set_active(1)
            self.menu.insert(rmi, i)
            i = i + 1
            rmi.show()
        self.menu.insert(self.manage_item, i)
        self.menu.show()

    def select_search(self, menuitem, engine_string):
        self.menu_button.set_label(_("Search ") + engine_string)
        self.se = engine_string
