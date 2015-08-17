# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Marcos Mobley ('markybob') <markybob@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
"""Common functions for various parts of gtkui to use."""

import contextlib
import cPickle
import logging
import os
import shutil
import sys

import gtk
import pygtk
from gobject import GError

import deluge.common

pygtk.require('2.0')


log = logging.getLogger(__name__)


def get_logo(size):
    """A Deluge logo.

    Params:
        size (int): Size of logo in pixels

    Returns:
        gtk.gdk.Pixbuf: deluge logo
    """
    filename = "deluge.svg"
    if deluge.common.windows_check() or deluge.common.osx_check():
        filename = "deluge.png"
    try:
        return gtk.gdk.pixbuf_new_from_file_at_size(deluge.common.get_pixmap(filename), size, size)
    except GError as ex:
        log.warning(ex)


def build_menu_radio_list(value_list, callback, pref_value=None, suffix=None, show_notset=False,
                          notset_label="∞", notset_lessthan=0, show_other=False):
    """Build a menu with radio menu items from a list and connect them to the callback.

    Params:
    value_list [list]: List of values to build into a menu.
    callback (function): The function to call when menu item is clicked.
    pref_value (int): A preferred value to insert into value_list
    suffix (str): Append a suffix the the menu items in value_list.
    show_notset (bool): Show the unlimited menu item.
    notset_label (str): The text for the unlimited menu item.
    notset_lessthan (int): Activates the unlimited menu item if pref_value is less than this.
    show_other (bool): Show the `Other` menu item.

    The pref_value is what you would like to test for the default active radio item.

    Returns:
        gtk.Menu: The menu radio
    """
    menu = gtk.Menu()
    group = None

    if pref_value > -1 and pref_value not in value_list:
        value_list.pop()
        value_list.append(pref_value)

    for value in sorted(value_list):
        item_text = str(value)
        if suffix:
            item_text += " " + suffix
        menuitem = gtk.RadioMenuItem(group, item_text)
        group = menuitem
        if pref_value and value == pref_value:
            menuitem.set_active(True)
        if callback:
            menuitem.connect("toggled", callback)
        menu.append(menuitem)

    if show_notset:
        menuitem = gtk.RadioMenuItem(group, notset_label)
        menuitem.set_name("unlimited")
        if pref_value and pref_value < notset_lessthan:
            menuitem.set_active(True)
        menuitem.connect("toggled", callback)
        menu.append(menuitem)

    if show_other:
        menuitem = gtk.SeparatorMenuItem()
        menu.append(menuitem)
        menuitem = gtk.MenuItem(_("Other..."))
        menuitem.set_name("other")
        menuitem.connect("activate", callback)
        menu.append(menuitem)

    return menu


def reparent_iter(treestore, itr, parent, move_siblings=False):
    """
    This effectively moves itr plus it's children to be a child of parent in treestore

    Params:
        treestore (gtkTreeStore): the treestore
        itr (gtkTreeIter): the iter to move
        parent (gtkTreeIter): the new parent for itr
        move_siblings (bool): if True, it will move all itr's siblings to parent
    """
    src = itr

    def move_children(i, dest):
        while i:
            n_cols = treestore.append(dest, treestore.get(i, *xrange(treestore.get_n_columns())))
            to_remove = i
            if treestore.iter_children(i):
                move_children(treestore.iter_children(i), n_cols)
            if i != src:
                i = treestore.iter_next(i)
            else:
                # This is the source iter, we don't want other iters in it's level
                if not move_siblings:
                    i = None
            treestore.remove(to_remove)

    move_children(itr, parent)


def get_deluge_icon():
    """The deluge icon for use in dialogs.

    It will first attempt to get the icon from the theme and will fallback to using an image
    that is distributed with the package.

    Returns:
        gtk.gdk.Pixbuf: the deluge icon
    """
    if deluge.common.windows_check():
        return get_logo(32)
    else:
        try:
            icon_theme = gtk.icon_theme_get_default()
            return icon_theme.load_icon("deluge", 64, 0)
        except GError:
            return get_logo(64)


def associate_magnet_links(overwrite=False):
    """
    Associates magnet links to Deluge.

    Params:
        overwrite (bool): if this is True, the current setting will be overwritten

    Returns:
        bool: True if association was set
    """

    if deluge.common.windows_check():
        import _winreg

        try:
            hkey = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "Magnet")
        except WindowsError:
            overwrite = True
        else:
            _winreg.CloseKey(hkey)

        if overwrite:
            deluge_exe = os.path.join(os.path.dirname(sys.executable), "deluge.exe")
            try:
                magnet_key = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT, "Magnet")
            except WindowsError:
                # Could not create for all users, falling back to current user
                magnet_key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, "Software\\Classes\\Magnet")

            _winreg.SetValue(magnet_key, "", _winreg.REG_SZ, "URL:Magnet Protocol")
            _winreg.SetValueEx(magnet_key, "URL Protocol", 0, _winreg.REG_SZ, "")
            _winreg.SetValueEx(magnet_key, "BrowserFlags", 0, _winreg.REG_DWORD, 0x8)
            _winreg.SetValue(magnet_key, "DefaultIcon", _winreg.REG_SZ, "{},0".format(deluge_exe))
            _winreg.SetValue(magnet_key, r"shell\open\command", _winreg.REG_SZ, '"{}" "%1"'.format(deluge_exe))
            _winreg.CloseKey(magnet_key)

    # Don't try associate magnet on OSX see: #2420
    elif not deluge.common.osx_check():
        # gconf method is only available in a GNOME environment
        try:
            import gconf
        except ImportError:
            log.debug("gconf not available, so will not attempt to register magnet uri handler")
            return False
        else:
            key = "/desktop/gnome/url-handlers/magnet/command"
            gconf_client = gconf.client_get_default()
            if (gconf_client.get(key) and overwrite) or not gconf_client.get(key):
                # We are either going to overwrite the key, or do it if it hasn't been set yet
                if gconf_client.set_string(key, "deluge '%s'"):
                    gconf_client.set_bool("/desktop/gnome/url-handlers/magnet/needs_terminal", False)
                    gconf_client.set_bool("/desktop/gnome/url-handlers/magnet/enabled", True)
                    log.info("Deluge registered as default magnet uri handler!")
                    return True
                else:
                    log.error("Unable to register Deluge as default magnet uri handler.")
                    return False
    return False


def save_pickled_state_file(filename, state):
    """Save a file in the config directory and creates a backup

    Params:
        filename (str): Filename to be saved to config
        state (state): The data to be pickled and written to file
    """
    from deluge.configmanager import get_config_dir
    filepath = os.path.join(get_config_dir(), "gtkui_state", filename)
    filepath_bak = filepath + ".bak"
    filepath_tmp = filepath + ".tmp"

    try:
        if os.path.isfile(filepath):
            log.debug("Creating backup of %s at: %s", filename, filepath_bak)
            shutil.copy2(filepath, filepath_bak)
    except IOError as ex:
        log.error("Unable to backup %s to %s: %s", filepath, filepath_bak, ex)
    else:
        log.info("Saving the %s at: %s", filename, filepath)
        try:
            with open(filepath_tmp, "wb") as _file:
                # Pickle the state object
                cPickle.dump(state, _file)
                _file.flush()
                os.fsync(_file.fileno())
            shutil.move(filepath_tmp, filepath)
        except (IOError, EOFError, cPickle.PicklingError) as ex:
            log.error("Unable to save %s: %s", filename, ex)
            if os.path.isfile(filepath_bak):
                log.info("Restoring backup of %s from: %s", filename, filepath_bak)
                shutil.move(filepath_bak, filepath)


def load_pickled_state_file(filename):
    """Loads a file from the config directory, attempting backup if original fails to load.

    Params:
        filename (str): Filename to be loaded from config

    Returns:
        state: the unpickled state
    """
    from deluge.configmanager import get_config_dir
    filepath = os.path.join(get_config_dir(), "gtkui_state", filename)
    filepath_bak = filepath + ".bak"
    old_data_filepath = os.path.join(get_config_dir(), filename)

    for _filepath in (filepath, filepath_bak, old_data_filepath):
        log.info("Opening %s for load: %s", filename, _filepath)
        try:
            with open(_filepath, "rb") as _file:
                state = cPickle.load(_file)
        except (IOError, cPickle.UnpicklingError) as ex:
            log.warning("Unable to load %s: %s", _filepath, ex)
        else:
            log.info("Successfully loaded %s: %s", filename, _filepath)
            return state


@contextlib.contextmanager
def listview_replace_treestore(listview):
    """Prepare a listview's treestore to be entirely replaced.

    Params:
        listview: a listview backed by a treestore
    """
    # From http://faq.pygtk.org/index.py?req=show&file=faq13.043.htp
    # "tips for improving performance when adding many rows to a Treeview"
    listview.freeze_child_notify()
    treestore = listview.get_model()
    listview.set_model(None)
    treestore.clear()
    treestore.set_default_sort_func(lambda *args: 0)
    original_sort = treestore.get_sort_column_id()
    treestore.set_sort_column_id(-1, gtk.SORT_ASCENDING)

    yield

    if original_sort != (None, None):
        treestore.set_sort_column_id(*original_sort)

    listview.set_model(treestore)
    listview.thaw_child_notify()
