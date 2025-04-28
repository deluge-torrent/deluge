#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from gi.repository import Gtk

from deluge.configmanager import ConfigManager

macos_main_window_accelmap = {
    '<Deluge-MainWindow>/File/Add Torrent': '<Meta>o',
    '<Deluge-MainWindow>/File/Create Torrent': '<Meta>n',
    '<Deluge-MainWindow>/File/Quit & Shutdown Daemon': '<Meta><Shift>q',
    '<Deluge-MainWindow>/File/Quit': '<Meta>q',
    '<Deluge-MainWindow>/Edit/Preferences': '<Meta>comma',
    '<Deluge-MainWindow>/Edit/Connection Manager': '<Meta>m',
    '<Deluge-MainWindow>/View/Find ...': '<Meta>f',
    '<Deluge-MainWindow>/Help/FAQ': '<Meta>question',
}


def menubar_osx(gtkui, osxapp):
    # Change key shortcuts
    for accel_path, accelerator in macos_main_window_accelmap.items():
        accel_key, accel_mods = Gtk.accelerator_parse(accelerator)
        Gtk.AccelMap.change_entry(accel_path, accel_key, accel_mods, True)

    main_builder = gtkui.mainwindow.get_builder()
    menubar = main_builder.get_object('menubar')

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
