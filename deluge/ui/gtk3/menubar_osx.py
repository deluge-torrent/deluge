# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals
from gi import require_version

require_version('Gtk', '3.0')
require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk

from deluge.configmanager import ConfigManager

def menubar_osx(gtkui, osxapp):

    def accel_swap(item, key, modifier):
        Gtk.AccelMap.change_entry(Gtk.MenuItem.get_accel_path(main_builder.get_object(item)), Gdk.keyval_from_name(key), modifier, True)

    main_builder = gtkui.mainwindow.get_builder()
    menubar = main_builder.get_object('menubar')
    group = Gtk.accel_groups_from_object(gtkui.mainwindow.window)[0]

    config = ConfigManager('gtk3ui.conf')
    file_menu = main_builder.get_object('menu_file').get_submenu()
    file_items = file_menu.get_children()
    quit_all_item = file_items[3]

    for item in range(2, len(file_items)):  # remove quits
        file_menu.remove(file_items[item])

    menu_widget = main_builder.get_object('menu_edit')
    edit_menu = menu_widget.get_submenu()
    edit_items = edit_menu.get_children()
    pref_item = edit_items[0]
    edit_menu.remove(pref_item)

    conn_item = edit_items[1]
    edit_menu.remove(conn_item)

    menubar.remove(menu_widget)

    help_menu = main_builder.get_object('menu_help').get_submenu()
    help_items = help_menu.get_children()
    about_item = help_items[4]
    help_menu.remove(about_item)
    help_menu.remove(help_items[3])  # separator

    # Change accelerators
    accel_swap('menuitem_addtorrent', 'o', Gdk.ModifierType.META_MASK)
    accel_swap('menuitem_createtorrent', 'n', Gdk.ModifierType.META_MASK)
    accel_swap('menuitem_quitdaemon', 'q', Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.META_MASK)
    accel_swap('menuitem_preferences', 'comma', Gdk.ModifierType.META_MASK)
    accel_swap('menuitem_connectionmanager', 'm', Gdk.ModifierType.META_MASK)
    accel_swap('find_menuitem', 'f', Gdk.ModifierType.META_MASK)
    accel_swap('menuitem_faq', 'question', Gdk.ModifierType.META_MASK)

    menubar.hide()
    osxapp.set_menu_bar(menubar)
    # populate app menu
    osxapp.insert_app_menu_item(about_item, 0)
    osxapp.insert_app_menu_item(Gtk.SeparatorMenuItem(), 1)
    osxapp.insert_app_menu_item(pref_item, 2)
    if not config['standalone']:
        osxapp.insert_app_menu_item(conn_item, 3)
    if quit_all_item.get_visible():
        osxapp.insert_app_menu_item(Gtk.SeparatorMenuItem(), 4)
        osxapp.insert_app_menu_item(quit_all_item, 5)