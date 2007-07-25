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

import logging
import os.path
import pickle

try:
    import dbus, dbus.service
    dbus_version = getattr(dbus, "version", (0,0,0))
    if dbus_version >= (0,41,0) and dbus_version < (0,80,0):
        import dbus.glib
    elif dbus_version >= (0,80,0):
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)
    else:
        pass
except: dbus_imported = False
else: dbus_imported = True

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade

from addtorrentdialog import AddTorrentDialog
from deluge.ui.ui import UI

# Get the logger
log = logging.getLogger("deluge")

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
    
def add_torrent_file():
    """Opens a file chooser dialog and adds any files selected to the core"""
    at_dialog = AddTorrentDialog()
    torrent_files = at_dialog.run()
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

def queue_top(torrent_ids):
    """Attempts to queue all torrent_ids to the top"""
    log.debug("Attempting to queue to top these torrents: %s", torrent_ids)
    core = get_core()
    for torrent_id in torrent_ids:
        core.queue_top(torrent_id)
        
def queue_up(torrent_ids):
    """Attempts to queue all torrent_ids up"""
    log.debug("Attempting to queue up these torrents: %s", torrent_ids)
    core = get_core()
    for torrent_id in torrent_ids:
        core.queue_up(torrent_id)

def queue_down(torrent_ids):
    """Attempts to queue all torrent_ids down"""
    log.debug("Attempting to queue down these torrents: %s", torrent_ids)
    core = get_core()
    for torrent_id in torrent_ids:
        core.queue_down(torrent_id)

def queue_bottom(torrent_ids):
    """Attempts to queue all torrent_ids to the bottom"""
    log.debug("Attempting to queue to bottom these torrents: %s", torrent_ids)
    core = get_core()
    for torrent_id in torrent_ids:
        core.queue_bottom(torrent_id)

def get_torrent_info(core, torrent_id):
    """Builds the info dictionary and returns it"""
    info = core.get_torrent_info(torrent_id)
    # Join the array of bytes into a string for pickle to read
    info = "".join(chr(b) for b in info)
    # De-serialize the object
    info = pickle.loads(info)
    return info
    
def get_torrent_status(core, torrent_id):
    """Builds the status dictionary and returns it"""
    status = core.get_torrent_status(torrent_id)
    # Join the array of bytes into a string for pickle to read
    status = "".join(chr(b) for b in status)
    # De-serialize the object
    status = pickle.loads(status)
    return status
