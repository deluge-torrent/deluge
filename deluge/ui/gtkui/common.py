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
# 	Boston, MA    02110-1301, USA.
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
"""Common functions for various parts of gtkui to use."""

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade

import pkg_resources

from deluge.ui.client import aclient as client
import deluge.component as component
from deluge.log import LOG as log
import deluge.common

def get_logo(size):
    """Returns a deluge logo pixbuf based on the size parameter."""
    if deluge.common.windows_check():
        return gtk.gdk.pixbuf_new_from_file_at_size(deluge.common.get_pixmap("deluge.png"), \
            size, size)
    else:
        return gtk.gdk.pixbuf_new_from_file_at_size(deluge.common.get_pixmap("deluge.svg"), \
            size, size)

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
        menuitem.set_name(notset_label)
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
        menuitem.set_name(_("Other..."))
        menuitem.connect("activate", callback)
        menu.append(menuitem)

    return menu

def show_other_dialog(string, default=None):
    """Shows a dialog to get an 'other' speed and return the value"""
    dialog_glade = gtk.glade.XML(
        pkg_resources.resource_filename("deluge.ui.gtkui",
                                    "glade/dgtkpopups.glade"))
    speed_dialog = dialog_glade.get_widget("speed_dialog")
    spin_title = dialog_glade.get_widget("spin_title")
    spin_title.set_text(_("%s" % string))
    spin_speed = dialog_glade.get_widget("spin_speed")
    if default != None:
        spin_speed.set_value(default)
    spin_speed.select_region(0, -1)
    response = speed_dialog.run()
    if response == 1: # OK Response
        value = spin_speed.get_value()
    else:
        speed_dialog.destroy()
        return None

    speed_dialog.destroy()
    return value

def add_peer_dialog():
    dialog_glade = gtk.glade.XML(
        pkg_resources.resource_filename("deluge.ui.gtkui",
            "glade/dgtkpopups.glade"))
    peer_dialog = dialog_glade.get_widget("connect_peer_dialog")
    txt_ip = dialog_glade.get_widget("txt_ip")
    response = peer_dialog.run()
    if response:
        value = txt_ip.get_text()
        ip = value.split(":")[0]
        port = value.split(":")[1]
        if deluge.common.is_ip(ip):
            id = component.get("TorrentView").get_selected_torrent()
            log.debug("adding peer %s to %s", value, id)
            client.connect_peer(id, value)
    peer_dialog.destroy()
    return True
