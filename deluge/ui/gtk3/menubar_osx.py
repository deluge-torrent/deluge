# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from gi.repository.Gdk import ModifierType
from gi.repository.Gtk import SeparatorMenuItem, accel_groups_from_object
from gi.repository.Gtk.AccelFlags import VISIBLE

from deluge.configmanager import ConfigManager


def accel_swap(item, group, skey, smod, dkey, dmod):
    # Accel map hack broken, see ticket #3078
    # item.remove_accelerator(group, ord(skey), smod)
    item.add_accelerator('activate', group, ord(dkey), dmod, VISIBLE)


def accel_meta(item, group, key):
    accel_swap(item, group, key, ModifierType.CONTROL_MASK, key, ModifierType.META_MASK)


def menubar_osx(gtkui, osxapp):
    main_builder = gtkui.mainwindow.get_builder()
    menubar = main_builder.get_object('menubar')
    group = accel_groups_from_object(gtkui.mainwindow.window)[0]

    config = ConfigManager('gtk3ui.conf')

    # NOTE: accel maps doesn't work with glade file format
    # because of libglade not setting MenuItem accel groups
    # That's why we remove / set accelerators by hand... (dirty)
    # Clean solution: migrate glades files to gtkbuilder format
    file_menu = main_builder.get_object('menu_file').get_submenu()
    file_items = file_menu.get_children()
    accel_meta(file_items[0], group, 'o')
    accel_meta(file_items[1], group, 'n')
    quit_all_item = file_items[3]
    accel_swap(
        quit_all_item,
        group,
        'q',
        ModifierType.SHIFT_MASK | ModifierType.CONTROL_MASK,
        'q',
        ModifierType.SHIFT_MASK | ModifierType.META_MASK,
    )
    for item in range(2, len(file_items)):  # remove quits
        file_menu.remove(file_items[item])

    menu_widget = main_builder.get_object('menu_edit')
    edit_menu = menu_widget.get_submenu()
    edit_items = edit_menu.get_children()
    pref_item = edit_items[0]
    accel_swap(
        pref_item, group, 'p', ModifierType.CONTROL_MASK, ',', ModifierType.META_MASK
    )
    edit_menu.remove(pref_item)

    conn_item = edit_items[1]
    accel_meta(conn_item, group, 'm')
    edit_menu.remove(conn_item)

    menubar.remove(menu_widget)

    help_menu = main_builder.get_object('menu_help').get_submenu()
    help_items = help_menu.get_children()
    about_item = help_items[4]
    help_menu.remove(about_item)
    help_menu.remove(help_items[3])  # separator

    menubar.hide()
    osxapp.set_menu_bar(menubar)
    # populate app menu
    osxapp.insert_app_menu_item(about_item, 0)
    osxapp.insert_app_menu_item(SeparatorMenuItem(), 1)
    osxapp.insert_app_menu_item(pref_item, 2)
    if not config['standalone']:
        osxapp.insert_app_menu_item(conn_item, 3)
    if quit_all_item.get_visible():
        osxapp.insert_app_menu_item(SeparatorMenuItem(), 4)
        osxapp.insert_app_menu_item(quit_all_item, 5)
