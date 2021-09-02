# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Marcos Mobley ('markybob') <markybob@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
"""Common functions for various parts of gtkui to use."""
from __future__ import unicode_literals

import contextlib
import logging
import os
import shutil
import sys

import six.moves.cPickle as pickle  # noqa: N813
from gi.repository.Gdk import SELECTION_CLIPBOARD, SELECTION_PRIMARY, Display
from gi.repository.GdkPixbuf import Colorspace, Pixbuf
from gi.repository.GLib import GError
from gi.repository.Gtk import (
    Clipboard,
    IconTheme,
    Menu,
    MenuItem,
    RadioMenuItem,
    SeparatorMenuItem,
    SortType,
)

from deluge.common import PY2, get_pixmap, is_ip, osx_check, windows_check

log = logging.getLogger(__name__)


def cmp(x, y):
    """Replacement for built-in function cmp that was removed in Python 3.

    Compare the two objects x and y and return an integer according to
    the outcome. The return value is negative if x < y, zero if x == y
    and strictly positive if x > y.
    """

    try:
        return (x > y) - (x < y)
    except TypeError:
        # Handle NoneType comparison
        if x is None:
            if y is None:
                return 0
            return -1
        elif y is None:
            return 1
        else:
            raise


def create_blank_pixbuf(size=16):
    pix = Pixbuf.new(Colorspace.RGB, True, 8, size, size)
    pix.fill(0x0)
    return pix


def get_pixbuf(filename):
    try:
        return Pixbuf.new_from_file(get_pixmap(filename))
    except GError as ex:
        log.warning(ex)
        return create_blank_pixbuf()


# Status icons.. Create them from file only once to avoid constantly re-creating them.
icon_downloading = get_pixbuf('downloading16.png')
icon_seeding = get_pixbuf('seeding16.png')
icon_inactive = get_pixbuf('inactive16.png')
icon_alert = get_pixbuf('alert16.png')
icon_queued = get_pixbuf('queued16.png')
icon_checking = get_pixbuf('checking16.png')


def get_pixbuf_at_size(filename, size):
    if not os.path.isabs(filename):
        filename = get_pixmap(filename)
    try:
        return Pixbuf.new_from_file_at_size(filename, size, size)
    except GError as ex:
        # Failed to load the pixbuf (Bad image file), so return a blank pixbuf.
        log.warning(ex)
        return create_blank_pixbuf(size)


def get_logo(size):
    """A Deluge logo.

    Params:
        size (int): Size of logo in pixels

    Returns:
        Pixbuf: deluge logo
    """
    filename = 'deluge.svg'
    if windows_check():
        filename = 'deluge.png'
    return get_pixbuf_at_size(filename, size)


def build_menu_radio_list(
    value_list,
    callback,
    pref_value=None,
    suffix=None,
    show_notset=False,
    notset_label='∞',
    notset_lessthan=0,
    show_other=False,
):
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
        Menu: The menu radio
    """
    menu = Menu()
    # Create menuitem to prevent unwanted toggled callback when creating menu.
    menuitem = RadioMenuItem()
    group = menuitem.get_group()

    if pref_value > -1 and pref_value not in value_list:
        value_list.pop()
        value_list.append(pref_value)

    for value in sorted(value_list):
        item_text = str(value)
        if suffix:
            item_text += ' ' + suffix
        menuitem = RadioMenuItem.new_with_label(group, item_text)
        if pref_value and value == pref_value:
            menuitem.set_active(True)
        if callback:
            menuitem.connect('toggled', callback)
        menu.append(menuitem)

    if show_notset:
        menuitem = RadioMenuItem.new_with_label(group, notset_label)
        menuitem.set_name('unlimited')
        if pref_value and pref_value < notset_lessthan:
            menuitem.set_active(True)
        menuitem.connect('toggled', callback)
        menu.append(menuitem)

    if show_other:
        menuitem = SeparatorMenuItem()
        menu.append(menuitem)
        menuitem = MenuItem.new_with_label(_('Other...'))
        menuitem.set_name('other')
        menuitem.connect('activate', callback)
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
            n_cols = treestore.append(
                dest, treestore.get(i, *range(treestore.get_n_columns()))
            )
            to_remove = i
            if treestore.iter_children(i):
                move_children(treestore.iter_children(i), n_cols)
            if not move_siblings and i == src:
                i = None
            else:
                i = treestore.iter_next(i)

            treestore.remove(to_remove)

    move_children(itr, parent)


def get_deluge_icon():
    """The deluge icon for use in dialogs.

    It will first attempt to get the icon from the theme and will fallback to using an image
    that is distributed with the package.

    Returns:
        Pixbuf: the deluge icon
    """
    if windows_check():
        return get_logo(32)
    else:
        try:
            icon_theme = IconTheme.get_default()
            return icon_theme.load_icon('deluge', 64, 0)
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

    if windows_check():
        try:
            import winreg
        except ImportError:
            import _winreg as winreg  # For Python 2.

        try:
            hkey = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 'Magnet')
        except WindowsError:
            overwrite = True
        else:
            winreg.CloseKey(hkey)

        if overwrite:
            deluge_exe = os.path.join(os.path.dirname(sys.executable), 'deluge.exe')
            try:
                magnet_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, 'Magnet')
            except WindowsError:
                # Could not create for all users, falling back to current user
                magnet_key = winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER, 'Software\\Classes\\Magnet'
                )

            winreg.SetValue(magnet_key, '', winreg.REG_SZ, 'URL:Magnet Protocol')
            winreg.SetValueEx(magnet_key, 'URL Protocol', 0, winreg.REG_SZ, '')
            winreg.SetValueEx(magnet_key, 'BrowserFlags', 0, winreg.REG_DWORD, 0x8)
            winreg.SetValue(
                magnet_key, 'DefaultIcon', winreg.REG_SZ, '{},0'.format(deluge_exe)
            )
            winreg.SetValue(
                magnet_key,
                r'shell\open\command',
                winreg.REG_SZ,
                '"{}" "%1"'.format(deluge_exe),
            )
            winreg.CloseKey(magnet_key)

    # Don't try associate magnet on OSX see: #2420
    elif not osx_check():
        # gconf method is only available in a GNOME environment
        try:
            import gi

            gi.require_version('GConf', '2.0')
            from gi.repository import GConf
        except ValueError:
            log.debug(
                'gconf not available, so will not attempt to register magnet URI handler'
            )
            return False
        else:
            key = '/desktop/gnome/url-handlers/magnet/command'
            gconf_client = GConf.Client.get_default()
            if (gconf_client.get(key) and overwrite) or not gconf_client.get(key):
                # We are either going to overwrite the key, or do it if it hasn't been set yet
                if gconf_client.set_string(key, 'deluge "%s"'):
                    gconf_client.set_bool(
                        '/desktop/gnome/url-handlers/magnet/needs_terminal', False
                    )
                    gconf_client.set_bool(
                        '/desktop/gnome/url-handlers/magnet/enabled', True
                    )
                    log.info('Deluge registered as default magnet URI handler!')
                    return True
                else:
                    log.error(
                        'Unable to register Deluge as default magnet URI handler.'
                    )
                    return False
    return False


def save_pickled_state_file(filename, state):
    """Save a file in the config directory and creates a backup

    Params:
        filename (str): Filename to be saved to config
        state (state): The data to be pickled and written to file
    """
    from deluge.configmanager import get_config_dir

    filepath = os.path.join(get_config_dir(), 'gtk3ui_state', filename)
    filepath_bak = filepath + '.bak'
    filepath_tmp = filepath + '.tmp'

    try:
        if os.path.isfile(filepath):
            log.debug('Creating backup of %s at: %s', filename, filepath_bak)
            shutil.copy2(filepath, filepath_bak)
    except IOError as ex:
        log.error('Unable to backup %s to %s: %s', filepath, filepath_bak, ex)
    else:
        log.info('Saving the %s at: %s', filename, filepath)
        try:
            with open(filepath_tmp, 'wb') as _file:
                # Pickle the state object
                pickle.dump(state, _file, protocol=2)
                _file.flush()
                os.fsync(_file.fileno())
            shutil.move(filepath_tmp, filepath)
        except (IOError, EOFError, pickle.PicklingError) as ex:
            log.error('Unable to save %s: %s', filename, ex)
            if os.path.isfile(filepath_bak):
                log.info('Restoring backup of %s from: %s', filename, filepath_bak)
                shutil.move(filepath_bak, filepath)


def load_pickled_state_file(filename):
    """Loads a file from the config directory, attempting backup if original fails to load.

    Params:
        filename (str): Filename to be loaded from config

    Returns:
        state: the unpickled state
    """
    from deluge.configmanager import get_config_dir

    filepath = os.path.join(get_config_dir(), 'gtk3ui_state', filename)
    filepath_bak = filepath + '.bak'

    for _filepath in (filepath, filepath_bak):
        log.info('Opening %s for load: %s', filename, _filepath)
        try:
            with open(_filepath, 'rb') as _file:
                if PY2:
                    state = pickle.load(_file)
                else:
                    state = pickle.load(_file, encoding='utf8')
        except (IOError, pickle.UnpicklingError) as ex:
            log.warning('Unable to load %s: %s', _filepath, ex)
        else:
            log.info('Successfully loaded %s: %s', filename, _filepath)
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
    treestore.set_sort_column_id(-1, SortType.ASCENDING)

    yield

    if original_sort != (None, None):
        treestore.set_sort_column_id(*original_sort)

    listview.set_model(treestore)
    listview.thaw_child_notify()


def get_clipboard_text():
    text = (
        Clipboard.get(SELECTION_CLIPBOARD).wait_for_text()
        or Clipboard.get(SELECTION_PRIMARY).wait_for_text()
    )
    if text:
        return text.strip()


def windowing(like):
    return like.lower() in str(type(Display.get_default())).lower()


def parse_ip_port(text):
    """Return an IP and port from text.

    Parses both IPv4 and IPv6.

    Params:
        text (str): Text to be parsed for IP and port.

    Returns:
        tuple: (ip (str), port (int))

    """
    if '.' in text:
        # ipv4
        ip, __, port = text.rpartition(':')
    elif '[' in text:
        # ipv6
        ip, __, port = text.partition('[')[2].partition(']:')
    else:
        return None, None

    if ip and is_ip(ip) and port.isdigit():
        return ip, int(port)
    else:
        return None, None
