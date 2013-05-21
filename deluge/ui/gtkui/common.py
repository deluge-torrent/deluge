#
# common.py
#
# Copyright (C) 2008 Marcos Pinto ('markybob') <markybob@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

"""Common functions for various parts of gtkui to use."""

import os

import pygtk
pygtk.require('2.0')
import gtk
import logging
import cPickle
import shutil

import deluge.component as component
import deluge.common

log = logging.getLogger(__name__)

def get_logo(size):
    """Returns a deluge logo pixbuf based on the size parameter."""
    if deluge.common.windows_check() or deluge.common.osx_check():
        return gtk.gdk.pixbuf_new_from_file_at_size(deluge.common.get_pixmap("deluge.png"), \
            size, size)
    else:
        try:
            return gtk.gdk.pixbuf_new_from_file_at_size(deluge.common.get_pixmap("deluge.svg"), \
            size, size)
        except Exception, e:
            log.warning(e)

def build_menu_radio_list(value_list, callback, pref_value=None,
    suffix=None, show_notset=False, notset_label=None, notset_lessthan=0,
    show_other=False, show_activated=False, activated_label=None):
    # Build a menu with radio menu items from a list and connect them to
    # the callback. The pref_value is what you would like to test for the
    # default active radio item.
    if notset_label is None:
        notset_label = _("Unlimited")

    if activated_label is None:
        activated_label = _("Activated")

    menu = gtk.Menu()
    group = None
    if show_activated is False:
        if pref_value > -1 and pref_value not in value_list:
            value_list.pop()
            value_list.append(pref_value)

        for value in sorted(value_list):
            if suffix != None:
                menuitem = gtk.RadioMenuItem(group, str(value) + " " + \
                    suffix)
            else:
                menuitem = gtk.RadioMenuItem(group, str(value))

            group = menuitem

            if value == pref_value and pref_value != None:
                menuitem.set_active(True)

            if callback != None:
                menuitem.connect("toggled", callback)

            menu.append(menuitem)

    if show_activated is True:
        for value in sorted(value_list):
            menuitem = gtk.RadioMenuItem(group, str(activated_label))

            group = menuitem

            if value == pref_value and pref_value != None:
                menuitem.set_active(True)

            if callback != None:
                menuitem.connect("toggled", callback)

            menu.append(menuitem)

    if show_notset:
        menuitem = gtk.RadioMenuItem(group, notset_label)
        menuitem.set_name("unlimited")
        if pref_value < notset_lessthan and pref_value != None:
            menuitem.set_active(True)
        if show_activated and pref_value == 1:
            menuitem.set_active(True)
        menuitem.connect("toggled", callback)
        menu.append(menuitem)

    # Add the Other... menuitem
    if show_other is True:
        menuitem = gtk.SeparatorMenuItem()
        menu.append(menuitem)
        menuitem = gtk.MenuItem(_("Other..."))
        menuitem.set_name("other")
        menuitem.connect("activate", callback)
        menu.append(menuitem)

    return menu

def show_other_dialog(header, type_str, image_stockid=None, image_filename=None, default=0):
    """
    Shows a dialog with `header` as the header text and `type_str`
    as the type text.  The type of spinbutton (int or float) is determined by
    `default` type.

    :param header: str, the header label text
    :param type_str: str, the type label text, what comes after the spinbutton
    :param image_stockid: gtkStockId, the stock id of the image in the header
    :param image_filename: str, filename of icon in pixmaps folder
    :param default: the default value in the spinbutton

    :returns: None, int or float from spinbutton depending on `default`.
        None is returned if the user clicks on Cancel.
    :rtype: None, int or float

    :raises TypeError: if `default` is not of type int or float

    """
    if type(default) != int and type(default) != float:
        raise TypeError("default value needs to be an int or float")

    builder = gtk.Builder()
    builder.add_from_file(deluge.common.resource_filename(
        "deluge.ui.gtkui", os.path.join("glade", "other_dialog.ui")
    ))
    dialog = builder.get_object("other_dialog")
    dialog.set_transient_for(component.get("MainWindow").window)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.set_title("")
    builder.get_object("label_header").set_markup("<b>" + header + "</b>")
    builder.get_object("label_type").set_text(type_str)
    if image_stockid:
        builder.get_object("image").set_from_stock(image_stockid, gtk.ICON_SIZE_LARGE_TOOLBAR)
    if image_filename:
        # Hack for Windows since it doesn't support svg
        if os.path.splitext(image_filename)[1] == ".svg" and (deluge.common.windows_check() or deluge.common.osx_check()):
            image_filename = os.path.splitext(image_filename)[0] + "16.png"
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
            deluge.common.get_pixmap(image_filename), 32, 32)
        builder.get_object("image").set_from_pixbuf(pixbuf)

    spinbutton = builder.get_object("spinbutton")
    if type(default) == float:
        spinbutton.set_digits(1)

    # Set default value and select text
    spinbutton.set_value(default)
    spinbutton.select_region(0, -1)

    value = None
    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        if type(default) == int:
            value = spinbutton.get_value_as_int()
        else:
            value = spinbutton.get_value()

    dialog.destroy()
    return value

def reparent_iter(treestore, itr, parent, move_siblings=False):
    """
    This effectively moves itr plus it's children to be a child of parent in treestore

    :param treestore: gtkTreeStore, the treestore
    :param itr: gtkTreeIter, the iter to move
    :param parent: gtkTreeIter, the new parent for itr
    :param move_siblings: bool. if True, it will move all itr's siblings to parent
    """
    src = itr
    def move_children(i, dest):
        while i:
            n = treestore.append(dest, treestore.get(i, *xrange(treestore.get_n_columns())))
            to_remove = i
            if treestore.iter_children(i):
                move_children(treestore.iter_children(i), n)
            if i != src:
                i = treestore.iter_next(i)
            else:
                # This is the source iter, we don't want other iters in it's level
                if not move_siblings:
                    i = None
            treestore.remove(to_remove)

    move_children(itr, parent)

def get_deluge_icon():
    """
    Returns the deluge icon for use in setting a dialogs icon.  It will first
    attempt to get the icon from the theme and will fallback to using an image
    that is distributed with the package.

    """
    if deluge.common.windows_check():
        return get_logo(32)
    else:
        try:
            icon_theme = gtk.icon_theme_get_default()
            return icon_theme.load_icon("deluge", 64, 0)
        except:
            return get_logo(64)

def associate_magnet_links(overwrite=False):
    """
    Associates magnet links to Deluge.

    :param overwrite: if this is True, the current setting will be overwritten
    :type overwrite: bool
    :returns: True if association was set
    :rtype: bool

    """
    if not deluge.common.windows_check():
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
    filename: Filename to be saved to config
    state: The data to be pickled and written to file
    """
    from deluge.configmanager import get_config_dir
    filepath = os.path.join(get_config_dir(), "gtkui_state", filename)
    filepath_bak = filepath + ".bak"

    try:
        if os.path.isfile(filepath):
            log.info("Creating backup of %s at: %s", filename, filepath_bak)
            shutil.copy2(filepath, filepath_bak)
    except IOError as ex:
        log.error("Unable to backup %s to %s: %s", filepath, filepath_bak, ex)
    else:
        log.info("Saving the %s at: %s", filename, filepath)
        try:
            with open(filepath, "wb") as _file:
                # Pickle the state object
                cPickle.dump(state, _file)
                _file.flush()
                os.fsync(_file.fileno())
        except (IOError, EOFError, cPickle.PicklingError) as ex:
            log.error("Unable to save %s: %s", filename, ex)
            if os.path.isfile(filepath_bak):
                log.info("Restoring backup of %s from: %s", filename, filepath_bak)
                shutil.move(filepath_bak, filepath)

def load_pickled_state_file(filename):
    """Loads a file from the config directory, attempting backup if original fails to load.
    filename: Filename to be loaded from config
    returns unpickled state
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
        except (IOError, cPickle.UnpicklingError), ex:
            log.warning("Unable to load %s: %s", _filepath, ex)
        else:
            log.info("Successfully loaded %s: %s", filename, _filepath)
            return state
