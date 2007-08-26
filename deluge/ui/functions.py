#
# functions.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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

import os.path
import pickle

import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade

from deluge.log import LOG as log

def get_core():
    """Get the core object and return it"""
    log.debug("Getting core proxy object from DBUS..")
    # Get the proxy object from DBUS
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.deluge_torrent.Deluge", 
                               "/org/deluge_torrent/Core")
    core = dbus.Interface(proxy, "org.deluge_torrent.Deluge")
    log.debug("Got core proxy object..")
    return core
    
def get_core_plugin(plugin):
    """Get the core plugin object and return it"""
    log.debug("Getting core plugin %s from DBUS..", plugin)
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.deluge_torrent.Deluge", 
                               "/org/deluge_torrent/Plugin/" + plugin)
    core = dbus.Interface(proxy, "org.deluge_torrent.Deluge." + plugin)
    return core
    
def add_torrent_file(torrent_files):
    """Adds torrent files to the core
        Expects a list of torrent files
    """
    if torrent_files is None:
        log.debug("No torrent files selected..")
        return
    log.debug("Attempting to add torrent files: %s", torrent_files)
    core = get_core()
    for torrent_file in torrent_files:
        # Open the .torrent file for reading because we need to send it's
        # contents to the core.
        f = open(torrent_file, "rb")
        # Get the filename because the core doesn't want a path.
        (path, filename) = os.path.split(torrent_file)
        core.add_torrent_file(filename, f.read())
        f.close()

def remove_torrent(torrent_ids):
    """Removes torrent_ids from the core.. Expects a list of torrent_ids"""
    log.debug("Attempting to removing torrents: %s", torrent_ids)
    core = get_core()
    for torrent_id in torrent_ids:
        core.remove_torrent(torrent_id)
        
def pause_torrent(torrent_ids):
    """Pauses torrent_ids"""
    core = get_core()
    for torrent_id in torrent_ids:
        core.pause_torrent(torrent_id)

def resume_torrent(torrent_ids):
    """Resume torrent_ids"""
    core = get_core()
    for torrent_id in torrent_ids:
        core.resume_torrent(torrent_id)
        
def get_torrent_info(core, torrent_id):
    """Builds the info dictionary and returns it"""
    info = core.get_torrent_info(torrent_id)
    # Join the array of bytes into a string for pickle to read
    info = "".join(chr(b) for b in info)
    # De-serialize the object
    info = pickle.loads(info)
    return info
    
def get_torrent_status(core, torrent_id, keys):
    """Builds the status dictionary and returns it"""
    status = core.get_torrent_status(torrent_id, keys)
    # Join the array of bytes into a string for pickle to read
    status = "".join(chr(b) for b in status)
    # De-serialize the object
    status = pickle.loads(status)
    return status
