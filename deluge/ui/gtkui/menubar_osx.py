# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from deluge.configmanager import ConfigManager
from gi.repository import Gdk, Gtk


def accel_swap(item, group, skey, smod, dkey, dmod):
    item.remove_accelerator(group, ord(skey), smod)
    item.add_accelerator("activate", group, ord(dkey), dmod, Gtk.AccelFlags.VISIBLE)


def accel_meta(item, group, key):
    accel_swap(item, group, key, Gdk.ModifierType.CONTROL_MASK, key, Gdk.EventMask.META_MASK)


def menubar_osx(gtkui, osxapp):
    window = gtkui.mainwindow
    main_builder = window.get_builder()
    menubar = main_builder.get_object("menubar")
    group = Gtk.accel_groups_from_object(window.window)[0]

    config = ConfigManager("gtkui.conf")

    # NOTE: accel maps doesn't work with glade file format
    # because of libglade not setting MenuItem accel groups
    # That's why we remove / set accelerators by hand... (dirty)
    # Clean solution: migrate glades files to gtkbuilder format
    file_menu = main_builder.get_object("menu_file").get_submenu()
    file_items = file_menu.get_children()
    accel_meta(file_items[0], group, 'o')
    accel_meta(file_items[1], group, 'n')
    quit_all_item = file_items[3]
    accel_swap(quit_all_item, group, 'q', Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK,
               'q', Gdk.ModifierType.SHIFT_MASK | Gdk.EventMask.META_MASK)
    for item in range(2, len(file_items)):  # remove quits
        file_menu.remove(file_items[item])

    menu_widget = main_builder.get_object("menu_edit")
    edit_menu = menu_widget.get_submenu()
    edit_items = edit_menu.get_children()
    pref_item = edit_items[0]
    accel_swap(pref_item, group, 'p', Gdk.ModifierType.CONTROL_MASK, ',', Gdk.EventMask.META_MASK)
    edit_menu.remove(pref_item)

    conn_item = edit_items[1]
    accel_meta(conn_item, group, 'm')
    edit_menu.remove(conn_item)

    menubar.remove(menu_widget)

    help_menu = main_builder.get_object("menu_help").get_submenu()
    help_items = help_menu.get_children()
    about_item = help_items[4]
    help_menu.remove(about_item)
    help_menu.remove(help_items[3])  # separator

    menubar.hide()
    osxapp.set_menu_bar(menubar)
    # populate app menu
    osxapp.insert_app_menu_item(about_item, 0)
    osxapp.insert_app_menu_item(Gtk.SeparatorMenuItem(), 1)
    osxapp.insert_app_menu_item(pref_item, 2)
    if not config["classic_mode"]:
        osxapp.insert_app_menu_item(conn_item, 3)
    if quit_all_item.get_visible():
        osxapp.insert_app_menu_item(Gtk.SeparatorMenuItem(), 4)
        osxapp.insert_app_menu_item(quit_all_item, 5)
